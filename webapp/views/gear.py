#
# Copyright 2021-2026, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from datetime import date, datetime
from os import environ

import peewee
from flask import Blueprint, jsonify, redirect, request, send_from_directory, session, url_for
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_login import login_required
from weblib.roles import ROLE_USER, roles_required
from weblib.table import Table
from weblib.views import crud_page, site

from webapp.forms import (
	CommonItemForm, ItemBcdForm, ItemBootForm, ItemComputerForm, ItemFinsForm, ItemFirstStageForm, ItemHoodForm,
	ItemLampForm, ItemManometerForm, ItemMaskForm, ItemMonofinsForm, ItemOctopusForm, ItemSecondStageForm, ItemSnorkleForm,
	ItemSuitForm, ItemTankForm, ItemWeightForm, ServicingForm, StateForm
)
from webapp.items import (
	GEAR, ITEM_TYPE_BACKPACK, ITEM_TYPE_BCD, ITEM_TYPE_BOOT, ITEM_TYPE_COMPUTER, ITEM_TYPE_FIN, ITEM_TYPE_FIRST_STAGE,
	ITEM_TYPE_FIRST_STAGE_AUXILIARY, ITEM_TYPE_FRISBEE, ITEM_TYPE_GLOVE, ITEM_TYPE_HOOD, ITEM_TYPE_LAMP,
	ITEM_TYPE_MANOMETER, ITEM_TYPE_MASK, ITEM_TYPE_MONOFIN, ITEM_TYPE_OCTOPUS, ITEM_TYPE_OXYMETER, ITEM_TYPE_PREMISES_KEY,
	ITEM_TYPE_RING, ITEM_TYPE_SECOND_STAGE, ITEM_TYPE_SNORKLE, ITEM_TYPE_SOCK, ITEM_TYPE_SUCKER, ITEM_TYPE_SUIT,
	ITEM_TYPE_TANK, ITEM_TYPE_WEIGHT
)
from webapp.models import Item, ItemState, Servicing
from webapp.requests import (
	DatabaseException, create_item, create_item_servicing, create_item_state, get_item, get_item_type,
	get_item_type_and_reference, get_items, get_regulators, get_running_inventory_date, trash_item, untrash_item
)
from webapp.tables import ITEMS_COLUMNS

_LOGGER = logging.getLogger(__name__)

ITEMS_COLUMNS = {
	ITEM_TYPE_FIRST_STAGE            : ItemFirstStageForm    ,
	ITEM_TYPE_FIRST_STAGE_AUXILIARY  : ItemFirstStageForm    ,
	ITEM_TYPE_SECOND_STAGE           : ItemSecondStageForm   ,
	ITEM_TYPE_OCTOPUS                : ItemOctopusForm       ,
	ITEM_TYPE_MANOMETER              : ItemManometerForm     ,
	ITEM_TYPE_TANK                   : ItemTankForm          ,
	ITEM_TYPE_BCD                    : ItemBcdForm           ,
	ITEM_TYPE_BACKPACK               : CommonItemForm        ,
	ITEM_TYPE_SUIT                   : ItemSuitForm          ,
	ITEM_TYPE_HOOD                   : ItemHoodForm          ,
	ITEM_TYPE_BOOT                   : ItemBootForm          ,
	ITEM_TYPE_SOCK                   : ItemBootForm          ,
	ITEM_TYPE_GLOVE                  : ItemHoodForm          ,
	ITEM_TYPE_FIN                    : ItemFinsForm          ,
	ITEM_TYPE_MONOFIN                : ItemMonofinsForm      ,
	ITEM_TYPE_MASK                   : ItemMaskForm          ,
	ITEM_TYPE_SNORKLE                : ItemSnorkleForm       ,
	ITEM_TYPE_COMPUTER               : ItemComputerForm      ,
	ITEM_TYPE_LAMP                   : ItemLampForm          ,
	ITEM_TYPE_WEIGHT                 : ItemWeightForm        ,
	ITEM_TYPE_SUCKER                 : CommonItemForm        ,
	ITEM_TYPE_RING                   : CommonItemForm        ,
	ITEM_TYPE_FRISBEE                : CommonItemForm        ,
	ITEM_TYPE_OXYMETER               : ItemLampForm          ,
	ITEM_TYPE_PREMISES_KEY           : CommonItemForm        ,
}

gear_views = Blueprint('gear_views', __name__, template_folder="templates", static_folder="static")


@gear_views.before_request
@login_required
def before_request():
	if get_running_inventory_date() is None:
		session['prev_url'] = None



def render_gear_page(template, group, item_type, **kwargs):
	return site.render_page(html_template=template,
		active_tab='gear',
		available_sub_tabs=GEAR.groups,
		active_sub_tab=GEAR[group],
		available_items=GEAR[group].items,
		active_item=GEAR[group][item_type],
		active_gear_item=GEAR[group][item_type],
		**kwargs
	)


@gear_views.route('/gear')
@roles_required(ROLE_USER)
def gear():
	return redirect("/gear/regulator")


@gear_views.route('/gear/<group>/<item_type>')
@roles_required(ROLE_USER)
def gear_table(group, item_type):
	if GEAR[group][item_type].is_composite:
		if group == 'regulator':
			table = get_regulators()
		else:
			table = get_regulators()  # TODO
	return render_gear_page("gear/table.html", group, item_type,
		content_url=url_for(".gear_table", group=group, item_type=item_type),
	)


@gear_views.route('/gear/<group>/<item_type>/gear.table')
def gear_table_json(group, item_type):
	table = Table("gear", title="", row_title_builder=lambda row: f"{Item.type.lut[item_type]} {row[1]}")

	def class_builder(fields_dict):
		return () if (fields_dict.get('is_present', False) and fields_dict.get('is_usable', False)) else ("unavailable", )

	table.build_from_request(get_items(item_type), class_builder=class_builder)
	table.buttons = (
		{'href': "/gear/item/info", 'i18n': _l("Item info")},
		{'href': "/gear/item/add_state", 'i18n': _l("Add state")},
		{'href': "/gear/item/add_servicing", 'i18n': _l("Add servicing")},
		{'href': "/gear/item/modify", 'i18n': _l("Modify item")},
		{'href': "/gear/item/delete", 'i18n': _l("Trash item"), 'confirmation_message': _l("Trash this item ?")},
	)
	return jsonify(table.dict)


@gear_views.route('/gear/<group>/<item_type>/trashed_gear.table')
def trashed_gear_table_json(group, item_type):
	table = Table("trashed_gear")
	table.build_from_request(get_items(item_type, trashed_only=True))
	table.buttons = (
		{'href': "/gear/item/untrash", 'i18n': _l("Untrash item")},
	)
	return jsonify(table.dict)


@gear_views.route('/gear/<group>')
@roles_required(ROLE_USER)
def gear_regulator(group):
	return redirect("/gear/%s/%s" % (group, GEAR[group].items[0].type))


@gear_views.route('/gear/<group>/<item_type>/add_item', methods=['GET', 'POST'])
@roles_required(ROLE_USER)
def gear_add_item(group, item_type):
	form = ITEMS_COLUMNS[item_type]()
	if request.method == 'GET':
		form.type.data = item_type
	elif form.validate():
		_LOGGER.info("Adding to the database the item '%s' ", form.dict)
		try:
			create_item(**form.dict)
		except peewee.IntegrityError as e:  # FIXME
			form.reference.error_messages = [str(e)]
		else:
			return redirect('/gear/%s/%s' % (group, item_type))
	return render_gear_page("gear/add.html", group, item_type, form=form)


@gear_views.route('/gear/item/info')
@gear_views.route('/gear/item/info/<item_id>')
@gear_views.route('/gear/item/info/<item_id>/<table_name>.table', methods=['GET'])
@gear_views.route('/gear/item/info/<item_id>/<table_name>/<crud_step>', methods=['GET', 'POST'])
@gear_views.route('/gear/item/info/<item_id>/<table_name>/upload/<filename>', methods=['GET'])  # TODO move this in crud_table
@roles_required(ROLE_USER)
def item_info(item_id=None, table_name=None, crud_step="read", filename=None):
	item_id = item_id or request.args['id']
	group, item_type = get_group_and_type(item_id)
	if filename is not None:
		return send_from_directory(environ.get('UPLOAD_DIR', environ['HOME']), filename)  #, as_attachment=True)
	return crud_page(table_name, crud_step,
		html_template="gear/item/info.html",
		item_name=Item.type.lut[get_item_type(item_id)],
		reference=get_item(item_id)['reference'],
		url=f"/gear/item/info/{item_id}",
		active_tab='gear',
		available_sub_tabs=GEAR.groups,
		active_sub_tab=GEAR[group],
		available_items=GEAR[group].items,
		active_item=GEAR[group][item_type],
		active_gear_item=GEAR[group][item_type],
		tables={
			'state': {
				'title': _("States"),
				'model_factory': ItemState,
				'columns': (ItemState.date, ItemState.is_present, ItemState.is_usable, ItemState.price, ItemState.comment),
				'where_predicate': (ItemState.item_id == item_id),
				'order_by': ItemState.date,
				'form_factory': StateForm,
			},
			'servicing': {
				'title': _("Servicings"),
				'model_factory': Servicing,
				'columns': (Servicing.date, Servicing.report_file),
				'where_predicate': (Servicing.item_id == item_id),
				'order_by': Servicing.date,
				'form_factory': ServicingForm,
			},
		},
	)


@gear_views.route('/gear/item/delete')
@roles_required(ROLE_USER)
def item_delete():
	item_id = request.args['id']
	_LOGGER.info("Deleting item '%s'", item_id)
	# TODO delete_item(item_id) if it has never been used (not referenced in loans, states...)
	trash_item(item_id)
	# TODO popup
	return redirect(request.headers['Referer'])


@gear_views.route('/gear/item/untrash')
@roles_required(ROLE_USER)
def item_untrash():
	item_id = request.args['id']
	_LOGGER.info("Restoring item '%s'", item_id)
	untrash_item(item_id)
	# TODO popup
	return redirect(request.headers['Referer'])


@gear_views.route('/gear/item/delete_batch', methods=['POST'])
@roles_required(ROLE_USER)
def item_delete_batch():
	items_id = [int(k) for k, v in request.form.items() if v == "on"]
	_LOGGER.info("Deleting items '%s'", items_id)
	for item_id in items_id:
		pass #cascade_delete_item(item_id)
	return redirect(request.headers['Referer'])


def get_group_and_type(item_id):
	item_type = get_item_type(item_id)
	group = GEAR.get_item_group(item_type).name
	return group, item_type


@gear_views.route('/gear/item/modify', methods=['GET', 'POST'])
@roles_required(ROLE_USER)
def item_modify():
	item_id = request.args.get('id') or request.form['id']
	item_type = get_item_type(item_id)
	form = ITEMS_COLUMNS[item_type]()
	if request.method == 'GET':
		form.reference.readonly = True
	elif request.method == 'POST':
		if form.validate():
			from copy import copy  # FIXME
			fd = copy(form.dict)
			fd.pop('type')
			_LOGGER.info("Modifying item '%s'", fd)
			query = Item.update(fd).where(Item.id == item_id)
			if query.execute() != 1:
				raise DatabaseException("Could not update item '%s'" % item_id)
			return redirect('/gear/%s/%s' % get_group_and_type(item_id))
		else:
			_LOGGER.info("Displaying errors for item '%s'", item_id)

	_LOGGER.info("Populating form for item '%s'", item_id)
	form.id.data = item_id
	for key, value in get_item(item_id).items():
		try:
			getattr(form, key).data = value
		except AttributeError:
			_LOGGER.warning("Attribute '%s' not found in the current form", key)
	return render_gear_page("gear/item/modify.html", *get_group_and_type(item_id), form=form)


@gear_views.route('/gear/item/add_state', methods=['GET', 'POST'])
@roles_required(ROLE_USER)
def item_add_state():
	form = StateForm()
	if request.method == 'GET':
		form.item_id.data = request.args['id']
		running_inventory_date = get_running_inventory_date()
		if running_inventory_date:
			form.date.data = running_inventory_date
			form.date.render_kw = {'readonly': True}  # FIXME handle this in my forms
		else:
			form.date.data = date.today()
	else:
		if not form.validate():
			_LOGGER.info("Displaying errors for item '%s'", form.item_id.data)
		else:
			_LOGGER.info("Add a state '%s' to the database", form.dict)
			create_item_state(**form.dict)
			return redirect(session.get('prev_url') or "/gear/%s/%s" % get_group_and_type(form.item_id.data))  # prev_url is for setting states while in an inventory
	return render_gear_page("gear/item/add_state.html",
		*get_group_and_type(form.item_id.data),
		form=form,
		item=get_item_type_and_reference(form.item_id.data)
	)


@gear_views.route('/gear/item/add_servicing', methods=['GET', 'POST'])
@roles_required(ROLE_USER)
def item_add_servicing():
	form = ServicingForm()
	if request.method == 'GET':
		form.item_id.data = request.args['id']
		if get_running_inventory_date():
			_LOGGER.warning("Can't service an item while an inventory is running.")
			return redirect("/gear/%s/%s" % get_group_and_type(form.item_id.data))
		else:
			form.date.data = date.today()
	else:
		if not form.validate():
			_LOGGER.info("Displaying errors for item '%s'", form.item_id.data)
		else:
			create_item_servicing(**form.dict)
			return redirect("/gear/%s/%s" % get_group_and_type(form.item_id.data))
	return render_gear_page("gear/item/add_servicing.html",
		*get_group_and_type(form.item_id.data),
		form=form,
		item=get_item_type_and_reference(form.item_id.data)
	)
