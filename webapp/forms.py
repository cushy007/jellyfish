#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import csv
import logging
import shlex
import subprocess
from os import chdir, getcwd
from os.path import join
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile

from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from weblib.forms import (
	BaseForm, BooleanField, DateField, DecimalField, DoubleSelectField, FileField, HiddenField, IntegerField, PriceField,
	SelectField, TextAreaField, TextField
)
from weblib.models import flask_db
from weblib.requests import DatabaseException
from weblib.utils import Shell

from webapp import CONFIG_CUSTOMIZATION
from webapp.models import Item, ItemState, Member, Servicing
from webapp.requests import delete_all_members, get_borrowed_items

_LOGGER = logging.getLogger(__name__)


OWNER_CLUBS = [(label, label) for label in CONFIG_CUSTOMIZATION['clubs'].split(';')]


class CommonItemForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),
	}


class ItemFirstStageForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'model': TextField(Item),
		'serial_nb': TextField(Item),
		'is_cold_water': BooleanField(Item),
		'is_nitrox': BooleanField(Item),

		'fastening': SelectField(Item, choices=[(key, value) for key, value in Item.fastening.lut.items()]),
	}


class ItemSecondStageForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'model': TextField(Item),
		'serial_nb': TextField(Item),
		'is_cold_water': BooleanField(Item),
		'is_nitrox': BooleanField(Item),
	}


class ItemOctopusForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'model': TextField(Item),
		'serial_nb': TextField(Item),
		'is_cold_water': BooleanField(Item),
		'is_nitrox': BooleanField(Item),
	}


class ItemManometerForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'model': TextField(Item),
		'serial_nb': TextField(Item),
		'is_nitrox': BooleanField(Item),
	}


class ItemSuitForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'model': TextField(Item),
		'gender': SelectField(Item, choices=[(key, value) for key, value in Item.gender.lut.items()]),
		'thickness': DecimalField(Item, step=0.5),
		'size_letter_min': TextField(Item),
		'size_letter_max': TextField(Item),
		'size_number_min': IntegerField(Item),
		'size_number_max': IntegerField(Item),
		'is_semi_dry': BooleanField(Item),
		'is_split_bottom_up': BooleanField(Item),
		'is_with_shorty': BooleanField(Item),
	}


class ItemTankForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'serial_nb': TextField(Item),
	}


class ItemBcdForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'model': TextField(Item),
		'serial_nb': TextField(Item),
		'size_letter_min': TextField(_l("Size")),
	}


class ItemHoodForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'thickness': DecimalField(Item, step=0.5),
		'size_letter_min': TextField(_l("Size")),
	}


class ItemFinsForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'is_apnea': BooleanField(Item),
		'size_letter_min': TextField(Item),
		'size_letter_max': TextField(Item),
		'size_number_min': IntegerField(Item),
		'size_number_max': IntegerField(Item),
	}


class ItemMonofinsForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'size_letter_min': TextField(Item),
		'size_letter_max': TextField(Item),
		'size_number_min': IntegerField(Item),
		'size_number_max': IntegerField(Item),
	}


class ItemBootForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'thickness': DecimalField(Item, step=0.5),
		'size_letter_min': TextField(Item),
		'size_letter_max': TextField(Item),
		'size_number_min': IntegerField(Item),
		'size_number_max': IntegerField(Item),
	}


class ItemMaskForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'size_age': SelectField(Item, choices=[(key, value) for key, value in Item.size_age.lut.items()]),
	}


class ItemSnorkleForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
	}


class ItemComputerForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'model': TextField(Item),
		'serial_nb': TextField(Item),
	}


class ItemLampForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'brand': TextField(Item),
		'model': TextField(Item),
	}


class ItemWeightForm(BaseForm):
	fields = {
		'type': HiddenField(),
		'reference': IntegerField(Item, required=True),
		'owner_club': SelectField(Item, choices=OWNER_CLUBS, default=1),
		'entry_date': DateField(Item, required=True, default="now"),

		'weight': IntegerField(Item),
	}


class ServicingForm(BaseForm):
	fields = {
		'item_id': HiddenField(),
		'date': DateField(Servicing, required=True, default="now"),
		'report_file': FileField(Servicing, required=True),
	}


COLLECTION_REASONS = (
	(1, _l("Swimming pool (1 dive)")),
	(2, _l("Day (2 dives)")),
	(4, _l("Week-end (4 dives)")),
	(10, _l("Week (10 dives)")),
)


class CollectionFormScan(BaseForm):
	fields = {
		'reason': SelectField(_l("Reason"), choices=COLLECTION_REASONS, default=2),
		'member': SelectField(_l("Member's name"), required=True),
		'scanned_text': HiddenField(),
	}


class CollectionFormManual(BaseForm):
	fields = {
		'reason': SelectField(_l("Reason"), choices=COLLECTION_REASONS),
		'member': SelectField(_l("Member's name"), required=True),
		'item_reference': DoubleSelectField((_l("Item type"), _l("Item reference")), parent_choices=()),
	}


class ReintegrationForm(BaseForm):
	fields = {
		'item': SelectField(_l("Item"), choices=get_borrowed_items),
	}


class MemberForm(BaseForm):
	fields = {
		'last_name': TextField(Member),
		'first_name': TextField(Member),
		'license_nb': TextField(Member),
		'has_guarantee': BooleanField(Member),
		'guarantee_end_date': DateField(Member, required=False),
	}

	# ~ def validate_license_nb(self, field):
		# ~ if len(field.data) < 50:
			# ~ raise validators.ValidationError('Name must be more than 50 characters')


class StateForm(BaseForm):
	fields = {
		'item_id': HiddenField(),
		'date': DateField(ItemState, required=True, default="now"),
		'is_present': BooleanField(ItemState, default=True),
		'is_usable': BooleanField(ItemState, default=True),
		'price':  PriceField(ItemState, default=0),
		'comment': TextAreaField(ItemState),
	}


class InventorySelectForm(BaseForm):
	fields = {
		'remaining_items': SelectField(_l("Remaining items"), choices=(), default=True),
	}


def restore_db(sql_dump_filepath):
	fmt_dict = {
		'dbname': "jellyfish",
		'sql_dump_filepath': sql_dump_filepath,
	}
	sh = Shell()
	_LOGGER.info("Restoring DB...")
	flask_db.database.close()
	sh.execute("psql jellyfish -c \"SELECT pid, (SELECT pg_terminate_backend(pid)) as killed from pg_stat_activity WHERE state LIKE 'idle';\"")
	_LOGGER.debug(sh.stdout)
	sh.execute("sudo -u postgres dropdb %(dbname)s" % fmt_dict)
	_LOGGER.debug(sh.stdout)
	sh.execute("sudo -u postgres createdb -T template0 %(dbname)s" % fmt_dict)
	_LOGGER.debug(sh.stdout)
	with open(sql_dump_filepath, 'rb') as fobj:
		stdin = fobj.read()
	sp = subprocess.Popen(shlex.split("sudo -u postgres psql --set ON_ERROR_STOP=on %(dbname)s" % fmt_dict), stdin=subprocess.PIPE)
	sp.communicate(input=stdin)
	if sh.retcode != 0:
		raise DatabaseException("Could not restore DB")
	_LOGGER.info("DB sucsessfuly restored")


def restore_db_action(file_content):
	tmpdir = mkdtemp()
	from_dir = getcwd()
	try:
		chdir(tmpdir)
		zip_filepath = "./zipfile.zip"
		with open(zip_filepath, 'wb') as f:
			f.write(file_content)
		_LOGGER.info("Exctracting dump to '%s'", tmpdir)
		with ZipFile(zip_filepath, 'r') as zipobj:
			zipobj.extract("jellyfish.sql")
		try:
			restore_db(join(tmpdir, "jellyfish.sql"))
		except DatabaseException:
			_LOGGER.exception("Restore DB failed")
	except:
		_LOGGER.exception("Zip extraction failed")
	finally:
		chdir(from_dir)
		_LOGGER.info("Cleanup temp dir '%s'", tmpdir)
		rmtree(tmpdir)


class UploadDBForm(BaseForm):
	fields = {
		'zipfile': FileField(_l("Database backup zip file"), required=True, action=restore_db_action),
	}


def populate_members(file_content):
	_LOGGER.info("Populating the members' list...")
	origin_dir = getcwd()
	try:
		tmpdir = mkdtemp()
		_LOGGER.info("Creating temporary working dir '%s'", tmpdir)
		chdir(tmpdir)
		filename = "members.csv"
		with open(filename, 'wb') as f:
			f.write(file_content)
		with open(filename, newline='') as fobj:
			csv_reader = csv.reader(fobj, delimiter=',')
			header_fields = ("last_name", "first_name", "license_nb")
			n_upplets = []
			for row in csv_reader:
				if csv_reader.line_num == 1:
					try:
						assert tuple(row) == header_fields
					except AssertionError:
						_LOGGER.exception("header '%s' is different from expected '%s'", row, header_fields)
						raise
				else:
					n_upplets.append([f.strip() for f in row])
		delete_all_members()
		for n_upplet in n_upplets:
			Member.create(**dict(zip(header_fields, n_upplet)))
	except:
		_LOGGER.exception("Error during file processing")
	finally:
		chdir(origin_dir)
		_LOGGER.info("Cleanup temporary working dir '%s'", tmpdir)
		rmtree(tmpdir)


class UploadMembersForm(BaseForm):
	fields = {
		'members_file': FileField(_l("Members csv file"), required=True, action=populate_members),
	}
