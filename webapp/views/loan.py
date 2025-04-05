#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
import re
from datetime import datetime
from urllib.parse import urlparse

import peewee
from flask import Blueprint, jsonify, redirect, request, session, url_for
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_login import current_user, login_required
from weblib.roles import roles_required
from weblib.views import site

from webapp import CONFIG_QRCODE, CONFIG_REF_PREFIXES
from webapp.forms import CollectionFormManual, CollectionFormScan, ReintegrationForm
from webapp.items import GEAR
from webapp.models import Item
from webapp.requests import (
	borrow_item, get_borrowed_items, get_item, get_item_id, get_item_references, get_item_type, get_member, get_member_id,
	get_members_fullnames, get_type_and_id, give_back_item
)
from webapp.roles import ROLE_LENDER

_LOGGER = logging.getLogger(__name__)


loan_views = Blueprint('loan_views', __name__, template_folder="templates", static_folder="static")


@loan_views.before_request
@login_required
def before_request():
	pass


@loan_views.route('/loan')
def loan_tab():
	return redirect(url_for(".loan_collection_tab"))


def get_scanned_code_content(text, config_dict=None):
	config_dict = config_dict or CONFIG_QRCODE
	item_start = config_dict['item'].replace(r"%s", r"")
	if text.startswith(item_start):
		_LOGGER.info("Will search for scanned item '%s'", text)
		item_template = config_dict['item'].replace(r"%s", r"([A-Z]*)([0-9]*)")
		match = re.search(item_template, text)
		item_type, item_reference = match.group(1), match.group(2)
		item_type = [k for k, v in CONFIG_REF_PREFIXES.items() if item_type == v][0]
		return {
			'item_type': item_type,
			'item_reference': item_reference,
		}
	elif text.startswith(config_dict['license'].split('=')[0]):
		_LOGGER.info("Will search for scanned license '%s'", text)
		license_template = config_dict['license'].replace(r"%s", r"(.*)")
		try:
			license_nb = re.search(license_template.split('=')[1], text.split('=')[1]).group(1)
		except:
			_LOGGER.exception("Could not extract license")
		return {
			'license_nb': license_nb,
		}
	else:
		return {}


@loan_views.route('/loan/collection/collect.json', methods=['POST'])
@roles_required(ROLE_LENDER)
def loan_collection_json():
	LOAN_INVALID_SCANNED_TEXT = _("Scanned text is invalid")
	LOAN_INVALID_DATA = _("Invalid data")
	LOAN_ALREADY_BORROWED = _("%s has already been borrowed")
	LOAN_ITEM_BORROWED = _("%s borrowed by %s")

	form = (CollectionFormScan if session['use_scanner'] else CollectionFormManual)()

	def reply(is_success, message):
		timeout = float(CONFIG_QRCODE['popup_timeout'])
		return jsonify({'success': is_success, 'message': message, 'timeout': timeout})

	# if not form.validate():  can't validate dynamic selects :( must use WTF3.0.x for this
		# return reply(False, LOAN_INVALID_DATA)

	if "None" in (form.member.data, form.reason.data):
		return reply(False, LOAN_INVALID_DATA)
	else:
		session['loan_form'] = {
			'reason': form.reason.data,
			'member': form.member.data,
		}
		session.modified = True

	member_id = form.member.data
	usage_counter = int(form.reason.data)
	try:
		scanned_text = form.scanned_text.data
	except:
		scanned_text = None
	if scanned_text:
		scanned_code = get_scanned_code_content(scanned_text)
		if scanned_code.get('item_type') is not None:
			item_type = scanned_code.get('item_type')
			item_reference = scanned_code.get('item_reference')
			item_id = get_item_id(item_type, item_reference)
			item_name = Item.type.lut[item_type]
		elif scanned_code.get('license') is not None:
			return jsonify(get_member_id(scanned_code.get('license')))
		else:
			return reply(False, LOAN_INVALID_SCANNED_TEXT)
	else:
		item_id = form.item_reference.data
		item_name = Item.type.lut[get_item_type(item_id)]
		item_reference = get_item(item_id)['reference']

	member = get_member(member_id)
	member_name = " ".join((member['first_name'], member['last_name']))
	_LOGGER.info("User '%s' is lending item '%s %s' to member '%s' for '%s' usage(s)",
		current_user,
		item_name,
		item_reference,
		member_name,
		usage_counter,
	)
	try:
		borrow_item(item_id, current_user, member_id, datetime.now(), usage_counter)
	except peewee.DataError:
		_LOGGER.exception("Invalid data")
		return reply(False, LOAN_INVALID_DATA)
	except peewee.IntegrityError:
		_LOGGER.exception("Already borrowed exception")
		return reply(False, LOAN_ALREADY_BORROWED % ("%s %s" % (item_name, item_reference)))

	return reply(True, LOAN_ITEM_BORROWED % ("%s %s" % (item_name, item_reference), member_name))


@loan_views.route('/loan/collection.choices')
@roles_required(ROLE_LENDER)
def loan_collection_choices():
	return jsonify([(item_id, ref) for item_id, ref in get_item_references(request.args.get('get_children'), available_items_only=True)])


@loan_views.route('/loan/collection', methods=['GET'])
@roles_required(ROLE_LENDER)
def loan_collection_tab():

	if not urlparse(request.headers['Referer']).path.startswith("/loan/collection"):
		_LOGGER.info("Comming from another page -> reset the selected user and reason")
		session['loan_form'] = {}

	if request.args.get('use_scanner') == "toggle":
		use_scanner = session['use_scanner'] = not session['use_scanner']
		_LOGGER.info("Set use_scanner=%s", use_scanner)
	try:
		use_scanner = session['use_scanner']
	except KeyError:
		_LOGGER.info("Intitializing session['use_scanner']")
		use_scanner = session['use_scanner'] = True

	form = (CollectionFormScan if use_scanner else CollectionFormManual)()
	_LOGGER.debug("Form type is '%s'", type(form))

	form.member.choices = get_members_fullnames(with_guarantee_only=True)
	if session.get('loan_form'):
		form.reason.add_data(int(session['loan_form'].get('reason')))
		form.member.add_data(int(session['loan_form'].get('member')))

	if not use_scanner:
		ITEMS_TO_BORROW = [i for i in GEAR.borrowable_items if i.type in CONFIG_REF_PREFIXES]
		item_type = request.args.get('type', ITEMS_TO_BORROW[0].type)
		form.item_reference.parent_choices = [(item.type, item.i18n) for item in ITEMS_TO_BORROW if item.type == item_type] + [(item.type, item.i18n) for item in ITEMS_TO_BORROW if item.type != item_type]
		form.item_reference.choices_url = url_for(".loan_collection_choices")

	return site.render_page(
		is_display_main_tabs=False,
		form=form,
		fake_qrcodes=[CONFIG_QRCODE['item'] % ref for ref in CONFIG_QRCODE.get('fake_qrcodes', "").split(';') if ref],
		use_scanner=use_scanner,
	)


@loan_views.route('/loan/reintegration', methods=['GET', 'POST'])
@roles_required(ROLE_LENDER)
def loan_reintegration_tab():
	form = ReintegrationForm()
	now = datetime.now()
	if request.method == 'GET':
		if request.args.get('scanned_gear'):
			scanned_gear = request.args.get('scanned_gear')
			give_back_item(get_type_and_id(scanned_gear)[1], now)
			return redirect(url_for(".loan_reintegration_tab"))
		else:
			if not form.item.choices:
				form = None
			return site.render_page(
				is_display_main_tabs=False,
				form=form
			)
	elif request.method == 'POST':
		item = form.fields['item'].data
		_LOGGER.debug("Member is giving back item id '%s'", item)
		give_back_item(item, now)
		return redirect(url_for(".loan_reintegration_tab"))
