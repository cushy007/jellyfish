#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from datetime import datetime
from os import chdir, getcwd, mkdir, remove, walk
from os.path import dirname, expanduser, join
from shutil import copyfile, rmtree
from tempfile import mkdtemp
from zipfile import ZipFile

from flask import Blueprint, current_app, redirect, request, send_from_directory, url_for
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_login import login_required
from weblib.models import WEBLIB_MODELS
from weblib.roles import ROLE_USER, roles_required
from weblib.utils import Shell, mkstemp

from webapp import CONFIG_QRCODE, CONFIG_REF_PREFIXES
from webapp.forms import BaseForm, TextField, UploadDBForm, UploadMembersForm
from webapp.models import MODELS, Item
from webapp.qrcode_gen import generate_qrcodes
from webapp.requests import get_item_references, get_servicing_files
from webapp.views.main import site

_LOGGER = logging.getLogger(__name__)


admin_views = Blueprint('admin_views', __name__)


@admin_views.before_request
@login_required
@roles_required(ROLE_USER)
def before_request():
	pass


@admin_views.route('/admin')
def admin():
	return redirect(url_for(".admin_tools"))


@admin_views.route('/admin/tools', methods=['GET'])
def admin_tools():
	form_db_restore = UploadDBForm()
	form_members_import = UploadMembersForm()
	return site.render_page(
		form_db_restore=form_db_restore,
		form_members_import=form_members_import,
	)


def zipdir(dirpath, zip_filename):
	_LOGGER.info("Building a zip file '%s' from '%s''s content", zip_filename, dirpath)
	from_dir = getcwd()
	try:
		chdir(dirpath)
		filepaths = []
		for dir_path, _, filenames in walk("."):
			for filename in filenames:
				filepaths.append(join(dir_path, filename))
		with ZipFile(zip_filename, 'w') as zipobj:
			for filepath in filepaths:
				_LOGGER.debug("Adding '%s'", filepath)
				zipobj.write(filepath)
	except:
		_LOGGER.exception("Zip failed")
	finally:
		chdir(from_dir)

	return dirpath, zip_filename


class QRCodeListForm(BaseForm):  # FIXME translation
	fields = dict([(item_type, TextField("%s (%s)" % (_l(Item.type.lut[item_type]), prefix))) for item_type, prefix in CONFIG_REF_PREFIXES.items()])


@admin_views.route('/admin/qrcode', methods=['GET'])
def admin_qrcode():
	form = QRCodeListForm()

	holes = []
	for item_type in CONFIG_REF_PREFIXES:
		refs = set([r[1] for r in get_item_references(item_type)])
		if refs:
			exaust = set(range(1, max(refs) + 1))
			holes.extend([_cat(item_type, r) for r in sorted(list(exaust - refs))])
	_LOGGER.info("holes=%s", holes)

	return site.render_page(
		form=form,
	)


def _admin_qrcode_generate(references):
	_LOGGER.info("Generating QR codes...")
	tmpdir = mkdtemp()

	try:
		qr_list = [(CONFIG_QRCODE['item'] % ref, ref) for ref in references]
		generate_qrcodes(tmpdir, "page", qr_list)
		return send_from_directory(*zipdir(tmpdir, "QRcodes.zip"), as_attachment=True)
	finally:
		_LOGGER.info("Cleanup temp dir '%s'", tmpdir)
		rmtree(tmpdir)

	return redirect(url_for(".admin_qrcode"))


def _cat(data_txt, data_int):
	return "%s%d" % (data_txt, data_int)


@admin_views.route('/admin/qrcode/generate', methods=['GET'])
def admin_qrcode_generate_all():

	references = []
	for item_type, prefix in CONFIG_REF_PREFIXES.items():
		references.extend([_cat(prefix, r[1]) for r in get_item_references(item_type)])
	return _admin_qrcode_generate(references)


def build_items_list(item_type, items, get_item_references=get_item_references):
	refs = []
	if items == "*":
		return tuple([pair[1] for pair in get_item_references(item_type)])
	for i in items.split(','):
		try:
			a, b = i.split('-')
			refs.extend(range(int(a), int(b) + 1))
		except ValueError:
			refs.append(int(i))

	return tuple(refs)


@admin_views.route('/admin/qrcode/generate', methods=['POST'])
def _admin_qrcode_generate_from_list():
	form = QRCodeListForm()
	data = form
	references = []
	for item_type, prefix in CONFIG_REF_PREFIXES.items():
		item_refs = getattr(form, item_type).data
		if item_refs:
			_LOGGER.debug("item_type=%s, prefix=%s, item_refs=%s", item_type, prefix, item_refs)
			references.extend([_cat(prefix, int(r)) for r in build_items_list(item_type, item_refs)])
	return _admin_qrcode_generate(references)


def backup_db(destdir):
	db_name = current_app.config['DATABASE']['name']
	sh = Shell()

	_LOGGER.info("Creating an SQL backup of the database in '%s'", destdir)
	sql_filepath = "%s.sql" % join(destdir, db_name)
	cmd = "pg_dump --no-owner %s" % db_name
	_LOGGER.debug("Executing command '%s'", cmd)
	sh.execute(cmd, split_stdout_stderr=True)
	if sh.retcode == 0:
		try:
			with open(sql_filepath, 'w') as fobj:
				fobj.write("\n".join(sh.stdout))
		except UnicodeEncodeError:
			_LOGGER.exception("Ooops")
	else:
		_LOGGER.error("SQL backup failed : %s", sh.stderr)
		_LOGGER.error("SQL backup failed : %s", sh.stdout)

	_LOGGER.info("Creating a CSV backup of the database in '%s'", destdir)
	try:
		sql_cmd_file = mkstemp()
		destdir_csv = join(destdir, "csv")
		mkdir(destdir_csv)
		with open(sql_cmd_file, 'w') as fobj:
			for table_name in [m._meta.table_name.lower() for m in MODELS + WEBLIB_MODELS]:
				fobj.write(f"\\copy (SELECT * FROM \"{table_name}\" ORDER BY id) to '{destdir_csv}/{table_name}.csv' csv HEADER DELIMITER ';'\n")
		cmd = "psql %s -f %s" % (db_name, sql_cmd_file)
		_LOGGER.debug("Executing command '%s'", cmd)
		sh.execute(cmd, capture=False)
		if sh.retcode:
			_LOGGER.error("CSV backup failed")
	finally:
		remove(sql_cmd_file)
	try:
		mkdir(join(destdir, "servicings"))
	except Exception:
		_LOGGER.exception("Could not backup servicing files")
		return
	for hashed_filename, exported_filename in get_servicing_files():
		try:
			src = expanduser(f"~/{hashed_filename}")
			dst = join(destdir, "servicings", exported_filename)
			_LOGGER.debug("Copying file '%s' to '%s'", src, dst)
			copyfile(src, dst)
		except FileNotFoundError:
			_LOGGER.error("'%s' referenced in DB but not found on filesystem !", src)
		except Exception:
			_LOGGER.exception("Could not backup servicing files")


@admin_views.route('/admin/tools/db/backup', methods=['GET'])
def admin_tools_db_backup():
	_LOGGER.info("Backup DB...")
	tmpdir = mkdtemp()
	try:
		copyfile(join(dirname(dirname(__file__)), "..", "config.ini"), join(tmpdir, "config.ini"))
		backup_db(tmpdir)
		timestamp = datetime.strftime(datetime.now(), "%Y-%m-%dT%H-%M")
		return send_from_directory(*zipdir(tmpdir, "Jellyfish_%s.zip" % timestamp), as_attachment=True)
	except:
		_LOGGER.exception("DB backup failed")
	finally:
		_LOGGER.info("Cleanup temp dir '%s'", tmpdir)
		rmtree(tmpdir)


@admin_views.route('/admin/tools/db/restore', methods=['POST'])
def admin_tools_db_restore():
	_LOGGER.info("Restoring DB...")
	form = UploadDBForm()
	form.validate()
	return redirect(url_for('.admin_tools'))


@admin_views.route('/admin/tools/member/import', methods=['POST'])
def admin_tools_member_import():
	_LOGGER.info("Importing members...")
	form = UploadMembersForm()
	form.validate()
	return redirect(url_for('.admin_tools'))
