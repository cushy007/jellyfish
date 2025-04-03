#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from collections import namedtuple
from datetime import MINYEAR, date, datetime, timedelta
from itertools import dropwhile, takewhile
from os.path import splitext

from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from peewee import JOIN, SQL, Case, DoesNotExist, IntegrityError, ProgrammingError, fn
from weblib.models import User
from weblib.requests import TableRequestResult, request_table, translate_field, translate_row

from webapp import CONFIG_REF_PREFIXES
from webapp.items import ITEM_TYPE_MANOMETER, ITEM_TYPE_OCTOPUS, ITEM_TYPE_SECOND_STAGE, ITEM_USAGE_MAX
from webapp.models import Borrow, Inventory, IsComposedOf, Item, ItemState, Member, Servicing
from webapp.tables import ITEMS_COLUMNS, MANDATORY_ITEMS_COLUMNS

_LOGGER = logging.getLogger(__name__)

class DatabaseException(Exception):
	pass


class InventoryException(Exception):
	pass


def create_item_state(**kwargs): ItemState.create(**kwargs)
def create_item_servicing(**kwargs): Servicing.create(**kwargs)
def create_servicing(**kwargs): Servicing.create(**kwargs)
def create_is_composed_of(**kwargs): IsComposedOf.create(**kwargs)


########################################################################################################################
#################################################### Items #############################################################
########################################################################################################################
def create_item(**kwargs):
	item_type = kwargs['type']
	item_reference = kwargs['reference']
	query = (Item
		.select()
		.where(
			(Item.type == item_type)
			& (Item.reference == item_reference)
			& (Item.is_trashed == False)
		)
	)
	for row in query:
		raise IntegrityError(f"An item of the type '{item_type}' already exists with the same reference '{item_reference}'")
	Item.create(**kwargs)


def get_items(item_type, include_trashed=False, trashed_only=False, usable_only=False):
	#assert not (usable_only and (include_trashed or trashed_only))
	columns = MANDATORY_ITEMS_COLUMNS + ITEMS_COLUMNS[item_type]
	query = (Item
		.select(Item.id, *columns)
		.where(
			(Item.type == item_type)
			& ((Item.is_trashed == trashed_only) if not include_trashed else True)
		)
		.order_by(Item.reference)
		.tuples()
	)

	serviced_items = get_serviced_items(item_type)
	query_tuples = []
	for row in query:
		query_tuples.append(
			row
			+ get_items_last_state(item_type).get(row[0], (True, True))
			+ (row[0] in serviced_items, )
		)
	query_tuples = tuple(query_tuples)

	class ServicingStub:
		column_name = "is_serviced"
		i18n = _("Is serviced")

	return TableRequestResult(columns + (ItemState.is_present, ItemState.is_usable, ServicingStub), query_tuples)


def get_item(item_id, include_trashed=False):
	item_type = (Item
		.select(Item.type)
		.where(Item.id == item_id)
	)[0].type
	columns = MANDATORY_ITEMS_COLUMNS + ITEMS_COLUMNS[item_type]
	query = (Item
		.select(*columns)
		.where(
			(Item.id == item_id)
			& ((Item.is_trashed == False) if not include_trashed else True)
		)
		.dicts()
	)
	try:
		return query[0]
	except IndexError:
		return {}


def get_item_references(item_type, available_items_only=False):
	if available_items_only:
		subq = (Borrow
			.select()
			.where(
				(Borrow.item_id == Item.id)
				& (Borrow.to_datetime == None)
			)
		)
		query = (Item
			.select(Item.id, Item.reference)
			.join(Borrow, JOIN.LEFT_OUTER, on=(Borrow.item_id == Item.id))
			.where(
				(Item.type == item_type)
				& (~fn.EXISTS(subq))
				& (Item.usage_counter < ITEM_USAGE_MAX)
				& (Item.is_servicing == False)
				& (Item.is_trashed == False)
			)
			.order_by(Item.reference)
		)
		last_states = get_items_last_state(item_type)
		return tuple(sorted([(i.id, i.reference) for i in set(i for i in query) if all(last_states.get(i.id, (True, )))], key=lambda t: t[1]))
	else:
		query = (Item
			.select(Item.id, Item.reference)
			.where(
				(Item.type == item_type)
			)
			.order_by(Item.reference)
		)
		return tuple([(row.id, row.reference) for row in query])


def get_item_id(item_type, reference):
	try:
		return Item.get_or_none(type=item_type, reference=reference, is_trashed=False).id
	except AttributeError:
		return None


def get_item_type(item_id):
	return Item.get_by_id(item_id).type


def get_item_reference(item_id):
	return Item.get_by_id(item_id).reference


def get_item_type_and_reference(item_id):
	item = Item.get_or_none(id=item_id)
	return f"{Item.type.lut[item.type]} {item.reference}"


def get_regulators(is_auxiliary=False):
	columns = (Item.type, Item.reference, Item.brand, Item.model, Item.serial_nb)
	header = tuple(str(getattr(col, 'i18n')) for col in columns)
	translatable_columns = ("type", "reference")

	first_stages_ids = (Item
		.select(Item.id)
		.where(Item.type == ("first_stage_auxiliary" if is_auxiliary else "first_stage"))
		.order_by(Item.reference)
	)

	regulators = []
	children_with_parent = []
	for first_stage_id in first_stages_ids:
		first_stage = (Item
			.select(Item.id, *columns)
			.where(Item.id == first_stage_id)
			.dicts()
		)[0]

		ALIAS = IsComposedOf.alias()
		parts = (IsComposedOf
			.select(ALIAS.parent_id, ALIAS.child_id)
			.join(ALIAS, JOIN.LEFT_OUTER, on=(IsComposedOf.child_id == ALIAS.child_id))
			.where(IsComposedOf.parent_id == first_stage_id)
			.order_by(ALIAS.at_date)
			.tuples()
		)

		children = set()
		for parent_id, child_id in parts:
			if parent_id == first_stage_id.id:
				children.add(child_id)
			else:
				try:
					children.remove(child_id)
				except:
					pass
		children = sorted(list(children))
		children_with_parent.extend(children)

		parts = []
		for part_id in children:
			part = (Item
				.select(Item.id, *columns)
				.where(Item.id == part_id)
				.tuples()
			)[0]
			parts.append(translate_row(part, model_fields=(Item.id, *columns), internationalizable_fields=translatable_columns)) #(part[0], ) + translate_row(part[1:]))

		first_stage['children'] = tuple(parts)
		Row = namedtuple("Row", ("id", "type", "reference", "brand", "model", "serial_nb", "children"))
		row = Row(**first_stage)
		regulators.append(row)

	subq = IsComposedOf.select().where(IsComposedOf.child_id == Item.id)
	regulator_parts = (Item
		.select(Item.id)
		.where(
			(Item.type.in_(['second_stage', 'octopus', 'manometer']))
			& (~fn.EXISTS(subq))
		)
	)
	regulator_parts = set([row.id for row in regulator_parts])
	orphans_ids = regulator_parts - set(children_with_parent)

	orphans = (Item
		.select(Item.id, *columns)
		.where(Item.id.in_(orphans_ids))
		.tuples()
	)

	return {
		'header': header,
		'rows': tuple(regulators),
		'orphans': tuple([(i[0], *translate_row(i[1:])) for i in orphans])
	}


def delete_item(item_id):
	query = Item.delete().where(Item.id == item_id)
	if query.execute() != 1:
		raise DatabaseException("Could not delete item '%s'" % item_id)


def trash_item(item_id):
	query = Item.update({Item.is_trashed: True}).where(Item.id == item_id)
	if query.execute() != 1:
		raise DatabaseException("Could not trash item '%s'" % item_id)


def untrash_item(item_id):
	item_type = get_item_type(item_id)
	item_reference = get_item_reference(item_id)
	_LOGGER.info(f"Untrashing item '{item_id}' of type '{item_type}' and reference '{item_reference}'")
	if get_item_id(item_type, item_reference) is not None:
		raise IntegrityError(f"An item of the type '{item_type}' already exists with the same reference")
	query = Item.update({Item.is_trashed: False}).where(Item.id == item_id)
	if query.execute() != 1:
		raise DatabaseException("Could not untrash item '%s'" % item_id)




########################################################################################################################
################################################## Members #############################################################
########################################################################################################################
def get_member(row_id):
	query = (Member
		.select()
		.where(Member.id == row_id)
		.dicts()
	)
	return query[0]


def get_member_id(license_nb):
	try:
		return Member.get(Member.license_nb == license_nb).id
	except DoesNotExist:
		return None


def get_members_fullnames(with_guarantee_only=False):
	if with_guarantee_only:
		where_filter = lambda: Member.has_guarantee == True
	else:
		where_filter = lambda: True == True

	query = (Member
		.select(Member.id, Member.last_name, Member.first_name)
		.where(where_filter())
		.order_by(Member.last_name)
	)
	return tuple([(m.id, "%s %s" % (m.last_name, m.first_name)) for m in query])


def delete_all_members():
	members_count = Member.select().count()
	_LOGGER.warning("Will delete the %d members...", members_count)
	query = Member.delete()
	if query.execute() != members_count:
		raise DatabaseException("Could not flush members table")




########################################################################################################################
#################################################### Loans #############################################################
########################################################################################################################
def borrow_item(item_id, user_id, member_id, at_datetime=None, usage_counter=0):
	if is_item_borrowed(item_id):
		raise IntegrityError("Item already borrowed")
	Borrow.create(item=item_id, user=user_id, member=member_id, from_datetime=at_datetime, usage_counter=usage_counter)
	current_counter = Item.select(Item.usage_counter).where(Item.id == item_id)[0].usage_counter
	query = Item.update({Item.usage_counter: current_counter + usage_counter}).where(Item.id == item_id)
	if query.execute() != 1:
		raise DatabaseException("Could not update usage_counter for item '%s'" % item_id)


def is_item_borrowed(item_id):
	query = (Borrow
		.select()
		.where((Borrow.item_id == item_id) & (Borrow.to_datetime == None))
	)
	return any([True for row in query])


def get_borrowed_items():
	query = (Item
		.select(Borrow.item_id, Item.type, Item.reference, Borrow.usage_counter)
		.join(Borrow)
		.where(Borrow.to_datetime == None)
		.order_by(Item.type)
		.tuples()
	)
	return tuple([(row[0], " ".join((str(Item.type.lut[row[1]]), str(row[2])))) for row in query])


def give_back_item(item_id, at_datetime, usage_counter=0):
	update_dict = {
		Borrow.user_id: None,
		Borrow.member_id: None,
		Borrow.to_datetime: at_datetime,
	}
	if usage_counter:
		update_dict[Borrow.usage_counter] = usage_counter
	query = Borrow.update(update_dict).where((Borrow.item_id == item_id) & (Borrow.to_datetime == None))
	if query.execute() != 1:
		raise DatabaseException("Could not give back item '%s'" % item_id)


def get_loans():
	columns = (Borrow.from_datetime, User.last_name, Member.last_name, Item.type, Item.reference)
	user = User.first_name.concat(" ").concat(User.last_name)
	member = Member.first_name.concat(" ").concat(Member.last_name)
	query = (Borrow
		.select(Borrow.id, Borrow.from_datetime, user, member, Item.type, Item.reference)
		.join(User)
		.switch(Borrow)
		.join(Member)
		.switch(Borrow)
		.join(Item)
		.order_by(Member.last_name)
		.tuples()
	)
	return TableRequestResult(columns, query)


def get_every_loans():
	columns = (Item.type, Item.reference, Borrow.from_datetime, Borrow.to_datetime, Borrow.usage_counter)
	query = (Borrow
		.select(Borrow.id, *columns)
		.join(Item)
		.where(Borrow.to_datetime > date(MINYEAR, 1, 1))
		.order_by(Item.type, Item.reference, Borrow.from_datetime)
		.tuples()
	)
	return TableRequestResult(columns, query)


def get_type_and_id(qrcode):
	reference = "".join(dropwhile(lambda c: c.isalpha(), qrcode))
	prefix = "".join(takewhile(lambda c: c.isalpha(), qrcode))
	item_type = [t for t, p in CONFIG_REF_PREFIXES.items() if p == prefix][0]

	query = (Item
		.select(Item.id)
		.where(
			(Item.type == item_type)
			& (Item.reference == reference)
		)
	)

	item_type = item_type

	return (item_type, query[0].id)




########################################################################################################################
################################################## Servicing ###########################################################
########################################################################################################################
def get_items_to_service(usage_max=ITEM_USAGE_MAX):
	query = (Item
		.select(Item.id, Item.usage_counter, Item.type, Item.reference)
		.where(
			(Item.usage_counter > usage_max - (usage_max / 5))
			& (Item.is_servicing == False)
		)
	)
	return tuple([(
			row.id,
			" ".join((_(row.type), str(row.reference))),
			usage_max - row.usage_counter,
		) for row in query])


def get_items_in_servicing():
	query = (Item
		.select(Item.id, Item.type, Item.reference)
		.where(Item.is_servicing)
		.tuples()
	)
	return tuple([(row[0], " ".join((_(row[1]), str(row[2])))) for row in query])


def service(items_ids):
	query = Item.update({Item.is_servicing: True}).where(Item.id.in_(items_ids))
	if query.execute() != len(items_ids):
		raise DatabaseException("Could not update is_servicing for items '%s'" % items_ids)


def unservice(item_id):
	query = Item.update({Item.is_servicing: False, Item.usage_counter: 0}).where(Item.id == item_id)
	if query.execute() != 1:
		raise DatabaseException("Could not set is_servicing to False for item '%s'" % item_id)


def get_servicing_files():
	query = (Servicing
		.select(Servicing.report_file, Servicing.date, Item.type, Item.reference)
		.join(Item)
		.dicts()
	)
	return tuple([(row['report_file'], f"{Item.type.lut[row['type']]}_{row['reference']}_{row['date']}{splitext(row['report_file'])[1]}") for row in query])




########################################################################################################################
################################################## Estimation ##########################################################
########################################################################################################################
def get_items_estimations(inventory_date):
	query = (ItemState
		.select(fn.SUM(ItemState.price))
		.where(ItemState.date == inventory_date)
		.tuples()
	)
	return query[0][0]


def get_items_estimations_table(inventory_date):
	query = (ItemState
		.select(Item.type, fn.SUM(ItemState.price))
		.join(Item)
		.where(ItemState.date == inventory_date)
		.group_by(Item.type)
		.tuples()
	)
	return [(translate_field(row[0], model_field=Item.type, is_internationalizable=True), row[1]) for row in query]


def get_items_count_table(inventory_date):
	query = (ItemState
		.select(Item.type, fn.COUNT(Item.type))
		.join(Item)
		.where((ItemState.date == inventory_date) & (ItemState.is_present))
		.group_by(Item.type)
		.tuples()
	)
	return [(translate_field(row[0], model_field=Item.type, is_internationalizable=True), row[1]) for row in query]


def get_item_states_dates():
	query = (ItemState
		.select(ItemState.date)
		.distinct()
		.order_by(ItemState.date.desc())
	)
	return tuple([row.date for row in query])


def get_items_last_state(item_type):
	query = (ItemState
		.select(ItemState.date, ItemState.is_present, ItemState.is_usable, Item.id)
		.join(Item)
		.where(Item.type == item_type)
		.dicts()
	)
	min_date = date(MINYEAR, 1, 1)
	ret = {}
	for row in query:
		if ret.get('date', min_date) < row['date']:
			ret[row['id']] = (row['is_present'], row['is_usable'])
	return ret


SERVICING_PERIODICITY = timedelta(days=365)

def get_serviced_items(item_type):
	valid_if_after = datetime.now() - SERVICING_PERIODICITY
	query = (Item
		.select(Item.id, Servicing.date)
		.join(Servicing)
		.where(
			(Item.type == item_type)
			& (Servicing.date > valid_if_after)
		)
	)
	return set(row.id for row in query)




########################################################################################################################
################################################## Inventory ###########################################################
########################################################################################################################
def create_inventory(**kwargs):
	if get_running_inventory_date():
		raise InventoryException("Can not create an inventory when there already is a running one")
	Inventory.create(**kwargs)


def get_inventories():
	columns = (Inventory.date, Inventory.in_progress)
	query = (Inventory
		.select(Inventory.id, *columns)
		.order_by(Inventory.date.desc())
		.tuples()
	)
	return TableRequestResult(columns, query)


def get_latest_inventory_date():
	return Inventory.select(fn.MAX(Inventory.date))[0].max or date.min


def get_inventory(date):
	return Inventory.get_or_none(date=date)


def get_inventory_date(inventory_id):
	return Inventory.get_or_none(id=inventory_id).date


def get_running_inventory_date():
	try:
		return Inventory.get(in_progress=True).date
	except (DoesNotExist, ProgrammingError):
		return None


def stop_inventory_campaign():
	query = Inventory.update({Inventory.in_progress: False}).where(Inventory.in_progress == True)
	if query.execute() != 1:
		raise DatabaseException("Error while stopping current inventory campaign")


def restart_inventory_campaign(inventory_id):
	query = Inventory.update({Inventory.in_progress: True}).where(Inventory.id == inventory_id)
	if query.execute() != 1:
		raise DatabaseException("Error while restarting inventory campaign id '%s'", inventory_id)


def get_inventory_items_select_list(date, selected_item_type=""):
	sorting_func = Case(Item.type, (
		(selected_item_type, ""),
	), Item.type)

	subq = (ItemState
		.select()
		.where(
			(Item.id == ItemState.item_id)
			& (ItemState.date == date)

		)
	)
	query = (Item
		.select(Item.type, fn.COUNT(Item.type), sorting_func.alias('sorting_func'))
		.where(
			(~fn.EXISTS(subq))
			& (Item.type != ITEM_TYPE_MANOMETER)
			& (Item.type != ITEM_TYPE_SECOND_STAGE)
			& (Item.type != ITEM_TYPE_OCTOPUS)
		)
		.group_by(Item.type)
		.order_by(SQL('sorting_func'))
		.namedtuples()
	)
	return query


def get_current_inventory_remaining_items(item_type):
	"""
	List of the items references of the type **item_type** that still have to be inventoried during the current inventory.

	"""
	running_inventory_date = get_running_inventory_date()
	_LOGGER.info("running_inventory_date=%s", running_inventory_date)
	columns = (Item.reference, )
	if item_type is None:
		return TableRequestResult(columns, ())
	subq = (ItemState
		.select()
		.where(
			(Item.id == ItemState.item_id)
			& (ItemState.date == running_inventory_date)
		))

	query = (Item
		.select(Item.id, *columns)
		.join(ItemState, JOIN.LEFT_OUTER, on=(ItemState.item_id == Item.id))
		.where(
			(Item.type == item_type)
			& (Item.is_trashed == False)
			& (~fn.EXISTS(subq))
		)
		.order_by(Item.reference)
		.distinct()
		.tuples()
	)
	return TableRequestResult(columns, query)


def get_inventory_missing_items(at_date):
	query = (Item
		.select(Item.id)
		.join(ItemState)
		.where(
			(ItemState.date == at_date)
			& (~ItemState.is_present)
		)
		.order_by(Item.type, Item.reference)
		.namedtuples()
	)
	return tuple([get_item_type_and_reference(row.id) for row in query])


def get_inventory_unusable_items(at_date):
	query = (Item
		.select(Item.id)
		.join(ItemState)
		.where(
			(ItemState.date == at_date)
			& (~ItemState.is_usable)
		)
		.order_by(Item.type, Item.reference)
		.namedtuples()
	)
	return tuple([get_item_type_and_reference(row.id) for row in query])


def get_uninventoried_items(at_date):
	subq = (ItemState.select().where(
			(Item.id == ItemState.item_id)
			& (ItemState.date == at_date)
		))

	query = (Item
		.select(Item.id, Item.type, Item.reference)
		.join(ItemState, JOIN.LEFT_OUTER)
		.where(
			(~fn.EXISTS(subq))
		)
		.order_by(Item.type, Item.reference)
		.distinct()
		.namedtuples()
	)
	return tuple([get_item_type_and_reference(row.id) for row in query])
