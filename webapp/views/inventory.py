#
# Copyright 2021-2026, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from datetime import date

from flask import Blueprint, jsonify, redirect, request, session, url_for
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_login import login_required
from weblib.roles import ROLE_USER, roles_required
from weblib.table import Table
from weblib.views import site

from webapp.forms import InventorySelectForm
from webapp.models import Item
from webapp.requests import (
	create_inventory, get_current_inventory_remaining_items, get_inventories, get_inventory, get_inventory_date,
	get_inventory_items_select_list, get_inventory_missing_items, get_inventory_unusable_items, get_items_count_table,
	get_items_estimations, get_items_estimations_table, get_latest_inventory_date, get_running_inventory_date,
	get_uninventoried_items, restart_inventory_campaign, stop_inventory_campaign
)
from webapp.roles import ROLE_LENDER

_LOGGER = logging.getLogger(__name__)


inventory_views = Blueprint('inventory_views', __name__, template_folder="templates", static_folder="static")


@inventory_views.before_request
@login_required
def before_request():
	pass


@inventory_views.route('/inventory', methods=['GET', 'POST'])
@roles_required(ROLE_USER, ROLE_LENDER)
def inventory_tab():
	today = date.today()
	running_inventory_date = get_running_inventory_date()
	session_inventory = session.setdefault('inventory', {})
	if request.args.get('start'):
		_LOGGER.info("Asked to start an inventory %s", get_latest_inventory_date())
		if running_inventory_date is not None:
			_LOGGER.warning("Inventory already started -> pass")
		elif get_latest_inventory_date() == today:
			_LOGGER.info(f"An inventory had already been started today -> reopening it")
			restart_inventory_campaign(get_inventory(get_latest_inventory_date()).id)
		else:
			_LOGGER.info(f"Creating an inventory at '{today}'")
			create_inventory(date=today)
		session_inventory['current_item_type'] = ""
		return redirect(url_for(".inventory_tab"))
	elif request.args.get('stop'):
		_LOGGER.info("Asked to stop the inventory")
		assert running_inventory_date is not None
		stop_inventory_campaign()
	elif request.args.get('select'):
		item_type = request.args.get('select')
		_LOGGER.info(f"Select box modified. Chosen item is '{item_type}'")
		session_inventory['current_item_type'] = item_type

	form = InventorySelectForm()
	form.remaining_items.choices = [(row[0], "%s (%s)" % (Item.type.lut[row[0]], row[1])) for row in get_inventory_items_select_list(running_inventory_date, session_inventory.get('current_item_type', ""))]

	if not session_inventory.get('current_item_type'):
		_LOGGER.info("No item selected yet -> autoselect the first of the list")
		session_inventory['current_item_type'] = form.remaining_items.choices[0][0]
		session.modified = True
	elif not [r for r in get_current_inventory_remaining_items(session_inventory['current_item_type']).query]:
		_LOGGER.info("No more '%s' to process during this inventory -> go to the next ones", session_inventory['current_item_type'])
		session_inventory['current_item_type'] = form.remaining_items.choices[0][0]
		session.modified = True

	_LOGGER.info("Current item type is '%s'", session_inventory['current_item_type'])

	running_inventory_date = get_running_inventory_date()
	return site.render_page(active_tab='inventory', active_sub_tab="",
		has_been_started_today=get_inventory(today) is not None,
		is_in_progress=bool(running_inventory_date),
		running_inventory_date=get_running_inventory_date(),
		form=form,
	)


@inventory_views.route('/inventory/current_remaining_items.table')
@roles_required(ROLE_USER, ROLE_LENDER)
def inventory_current_items_table():
	current_item_type = request.args.get('item_type') or session['inventory'].get('current_item_type')
	_LOGGER.info("Get remaining items for item type '%s'", current_item_type)
	session['inventory']['current_item_type'] = current_item_type
	if current_item_type is not None:
		session['prev_url'] = url_for(".inventory_tab") + "?select=" + current_item_type
	session.modified = True
	table = Table("current_remaining_items")
	table.build_from_request(get_current_inventory_remaining_items(current_item_type))
	table.action = {'href': "/gear/item/add_state"}
	return jsonify(table.dict)


@inventory_views.route('/inventory/inventories.table')
@roles_required(ROLE_USER, ROLE_LENDER)
def inventory_inventories_table():
	table = Table("inventories")
	table.build_from_request(get_inventories())
	table.buttons = (
		{'href': "/inventory/info", 'i18n': _l("Inventory info")},
		{'href': "/inventory/restart", 'i18n': _l("Restart inventory"), 'confirmation_message': _l("Restart this inventory ?")},
	)
	return jsonify(table.dict)


@inventory_views.route('/inventory/info')
@roles_required(ROLE_USER, ROLE_LENDER)
def inventory_info():
	inventory_id = request.args.get('id')
	inventory_date = get_inventory_date(inventory_id)
	_LOGGER.info("Will display '%s' inventory's info (inventory id is '%s')", inventory_date, inventory_id)

	return site.render_page(active_tab='inventory', active_sub_tab="",
		date=inventory_date,
		total_price=get_items_estimations(inventory_date),
		prices_by_item_type=get_items_estimations_table(inventory_date),
		nb_of_items_by_type=get_items_count_table(inventory_date),
		missing_items=get_inventory_missing_items(inventory_date),
		unusable_items=get_inventory_unusable_items(inventory_date),
		uninventoried_items=get_uninventoried_items(inventory_date),
	)


@inventory_views.route('/inventory/restart')
@roles_required(ROLE_USER, ROLE_LENDER)
def inventory_restart():
	inventory_id = request.args.get('id')
	_LOGGER.info(f"Restart the inventory with id '%s'", inventory_id)
	restart_inventory_campaign(inventory_id)
	session_inventory = session.setdefault('inventory', {})
	session_inventory['current_item_type'] = ""
	session.modified = True
	return redirect(url_for(".inventory_tab"))
