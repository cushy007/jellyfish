#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import datetime as dt
import logging
from datetime import date, datetime, timedelta
from logging import INFO
from os import environ

import pytest
import time_machine
from flask import Flask
from peewee import DoesNotExist, IntegrityError
from weblib.models import WEBLIB_MODELS, User, flask_db
from weblib.requests import create_user, get_user, get_users
from weblib.table import Table

from webapp.items import ITEM_TYPE_BCD, ITEM_TYPE_FIRST_STAGE, ITEM_TYPE_SECOND_STAGE, ITEM_TYPE_SUIT, ITEM_USAGE_MAX
from webapp.models import (
	ITEM_FASTENING_DIN, ITEM_FASTENING_YOKE, ITEM_GENDER_MALE, MODELS, Borrow, IsComposedOf, Item, ItemState, Member
)
from webapp.requests import (
	InventoryException, borrow_item, create_inventory, create_item, create_item_state, create_servicing,
	get_borrowed_items, get_current_inventory_remaining_items, get_inventory_items_select_list, get_item, get_item_id,
	get_item_references, get_item_states_dates, get_item_type, get_items, get_items_estimations,
	get_items_estimations_table, get_items_in_servicing, get_items_last_state, get_items_to_service,
	get_latest_inventory_date, get_loans, get_member, get_member_id, get_members_fullnames, get_regulators,
	get_running_inventory_date, get_servicing_files, get_type_and_id, give_back_item, is_item_borrowed, service,
	stop_inventory_campaign, trash_item, untrash_item
)

for module in ("peewee", "passlib"):
	logging.getLogger(module).setLevel(INFO)


@pytest.fixture(scope='function')
def populate_db():
	app = Flask(__name__)

	app.config['SECRET_KEY'] = environ.get("SECRET_KEY", 'pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw')
	app.config['DATABASE'] = {
		'host': "localhost",
		'name': "%s_test" % environ['DATABASE_NAME'],
		'engine': 'playhouse.pool.PooledPostgresqlDatabase',
		'user': environ.get('USER', ""),
	}

	flask_db.init_app(app)

	for model in WEBLIB_MODELS + MODELS:
		model.drop_table(safe=True, cascade=True)
		model.create_table(safe=True)

	Item.create(type=ITEM_TYPE_BCD, reference=1, serial_nb="s1", owner_club="Club", brand="Mares", size_letter_min="L", entry_date="24/10/06")
	Item.create(type=ITEM_TYPE_BCD, reference=2, serial_nb="s2", owner_club="Club", brand="Cressi", model="Stab", size_letter_min="M")
	Item.create(type=ITEM_TYPE_BCD, reference=3, serial_nb="s3", owner_club="Club", brand="Aqualung", model="Hudson", size_letter_min="S", entry_date="02/07/15")
	Item.create(type=ITEM_TYPE_BCD, reference=10, serial_nb="s10", owner_club="Club", brand="Scubapro", model="One Flex", size_letter_min="XS", entry_date="16/04/17")

	first_stage = Item.create(type="first_stage", reference=1, owner_club="Club", brand="Aqualung", model="Titan LX Suprème", serial_nb="7056701", is_cold_water=True, entry_date="01/06/07", fastening=ITEM_FASTENING_YOKE)
	second_stage = Item.create(type="second_stage", reference=1, owner_club="Club", brand="Aqualung", model="Titan LX Suprème", serial_nb="7056702", is_cold_water=True, entry_date="01/06/07")
	octopus_stage = Item.create(type="octopus", reference=1, owner_club="Club", brand="Aqualung", model="Titan LX Octopus", serial_nb="7056703", is_cold_water=True, entry_date="01/06/07")
	manometer = Item.create(type="manometer", reference=1, owner_club="Club", brand="Aqualung", model="Manometer 200 bars", serial_nb="7056704", entry_date="01/06/07")
	IsComposedOf.create(parent=first_stage.id, child=second_stage.id, at_date="01/06/07")
	IsComposedOf.create(parent=first_stage.id, child=octopus_stage.id, at_date="01/06/07")
	IsComposedOf.create(parent=first_stage.id, child=manometer.id, at_date="01/06/07")

	first_stage = Item.create(type="first_stage_auxiliary", reference=1, owner_club="Club", brand="Scubapro", model="MK2", serial_nb="7056801", is_cold_water=True, entry_date="01/06/07", fastening=ITEM_FASTENING_YOKE)
	octopus_stage = Item.create(type="octopus", reference=2, owner_club="Club", brand="Scubapro", model="MK2 Octopus", serial_nb="7056802", is_cold_water=True, entry_date="01/06/07")
	manometer = Item.create(type="manometer", reference=2, owner_club="Club", brand="Scubapro", model="Manometer 300 bars", serial_nb="7056803", entry_date="01/06/07")
	IsComposedOf.create(parent=first_stage.id, child=octopus_stage.id, at_date="01/06/07")
	IsComposedOf.create(parent=first_stage.id, child=manometer.id, at_date="01/06/07")

	orphand_octopus_stage = Item.create(type="octopus", reference=3, owner_club="Club", brand="Scubapro", model="MK2 Octopus", serial_nb="7056803", is_cold_water=True, entry_date="01/06/07")

	Member.create(last_name="Rambo", first_name="John", license_nb="A-5678")
	Member.create(last_name="Gilmour", first_name="David", license_nb="A-1234", has_guarantee=True)

	Item.create(type=ITEM_TYPE_SUIT, reference="1", owner_club="Club", brand="Cressi", model="Ice", gender=ITEM_GENDER_MALE, thickness=7, size_letter_min="M", size_letter_max="M", size_number_min=0, size_number_max=0, entry_date="2021/09/15")

	for model in (User, ):
		model.drop_table(safe=True, cascade=True)
		model.create_table(safe=True)
	with app.app_context():
		user = create_user(username="mknopfler", last_name="Knopfler", first_name="Mark", password="1234")
		user = create_user(username="jbeck", last_name="Beck", first_name="Jeff", password="1234")

	flask_db.database.close()


def test00a(populate_db):
	""" Get all BCDs """
	table = Table("items").build_from_request(get_items(ITEM_TYPE_BCD))
	assert table.dict['header'] == (
		{'name': 'reference'       , 'i18n': "Reference", 'values': ()},
		{'name': 'owner_club'      , 'i18n': "Owner club", 'values': ()},
		{'name': 'entry_date'      , 'i18n': "Entry date", 'values': ()},
		{'name': 'brand'           , 'i18n': "Brand", 'values': ()},
		{'name': 'model'           , 'i18n': "Model", 'values': ()},
		{'name': 'serial_nb'       , 'i18n': "Serial number", 'values': ()},
		{'name': 'size_letter_min' , 'i18n': "Minimum American size", 'values': ()},
		{'name': 'is_present'      , 'i18n': "Is present", 'values': ()},
		{'name': 'is_usable'       , 'i18n': "Is usable", 'values': ()},
		{'name': 'is_serviced'     , 'i18n': "Is serviced", 'values': ()},
	)
	assert table.dict['rows'] == (
		{'id': 1, 'class': () , 'title': "Chose an action", 'fields':  ("1", "Club", "24/10/2006", "Mares", "", "s1", "L", "Yes", "Yes", "No")},
		{'id': 2, 'class': () , 'title': "Chose an action", 'fields':  ("2", "Club", "", "Cressi", "Stab", "s2", "M", "Yes", "Yes", "No")},
		{'id': 3, 'class': () , 'title': "Chose an action", 'fields':  ("3", "Club", "02/07/2015", "Aqualung", "Hudson", "s3", "S", "Yes", "Yes", "No")},
		{'id': 4, 'class': () , 'title': "Chose an action", 'fields':  ("10", "Club", "16/04/2017", "Scubapro", "One Flex", "s10", "XS", "Yes", "Yes", "No")},
	)


def test00b(populate_db):
	""" Get all suits """
	table = Table("items").build_from_request(get_items(ITEM_TYPE_SUIT))
	assert table.dict['header'] == (
		{'name': 'reference'          , 'i18n': "Reference", 'values': ()},
		{'name': 'owner_club'         , 'i18n': "Owner club", 'values': ()},
		{'name': 'entry_date'         , 'i18n': "Entry date", 'values': ()},
		{'name': 'brand'              , 'i18n': "Brand", 'values': ()},
		{'name': 'model'              , 'i18n': "Model", 'values': ()},
		{'name': 'gender'             , 'i18n': "Gender", 'values': ()},
		{'name': 'thickness'          , 'i18n': "Thickness", 'values': ()},
		{'name': 'size_letter_min'    , 'i18n': "Minimum American size", 'values': ()},
		{'name': 'size_letter_max'    , 'i18n': "Maximum American size", 'values': ()},
		{'name': 'size_number_min'    , 'i18n': "Minimum size", 'values': ()},
		{'name': 'size_number_max'    , 'i18n': "Maximum size", 'values': ()},
		{'name': 'is_semi_dry'        , 'i18n': "Semi-dry", 'values': ()},
		{'name': 'is_split_bottom_up' , 'i18n': "Split bottom / up", 'values': ()},
		{'name': 'is_with_shorty'     , 'i18n': "With shorty", 'values': ()},
		{'name': 'is_present'         , 'i18n': "Is present", 'values': ()},
		{'name': 'is_usable'          , 'i18n': "Is usable", 'values': ()},
		{'name': 'is_serviced'     , 'i18n': "Is serviced", 'values': ()},
	)
	assert table.dict['rows'] == (
		{'id': 13, 'class': () , 'title': "Chose an action" , 'fields':  ("1", "Club", "15/09/2021", "Cressi", "Ice", "Man", "7.0", "M", "M", "0", "0", "", "", "", "Yes", "Yes", "No")},
	)


def test00c(populate_db):
	""" Get all BCDs when at least one inventory exists"""
	ItemState.create(item_id=1, date="2019-09-09", is_present=False, is_usable=True)
	create_inventory(date=date(2020, 9, 9))
	ItemState.create(item_id=2, date="2020-09-09", is_present=True, is_usable=True)
	ItemState.create(item_id=3, date="2020-09-09", is_present=False, is_usable=True)
	ItemState.create(item_id=4, date="2020-09-09", is_present=True, is_usable=False)
	create_item(type=ITEM_TYPE_BCD, reference=33, serial_nb="s33", owner_club="Club")

	table = Table("items").build_from_request(get_items(ITEM_TYPE_BCD))
	assert table.dict['header'] == (
		{'name': 'reference'       , 'i18n': "Reference", 'values': ()},
		{'name': 'owner_club'      , 'i18n': "Owner club", 'values': ()},
		{'name': 'entry_date'      , 'i18n': "Entry date", 'values': ()},
		{'name': 'brand'           , 'i18n': "Brand", 'values': ()},
		{'name': 'model'           , 'i18n': "Model", 'values': ()},
		{'name': 'serial_nb'       , 'i18n': "Serial number", 'values': ()},
		{'name': 'size_letter_min' , 'i18n': "Minimum American size", 'values': ()},
		{'name': 'is_present'      , 'i18n': "Is present", 'values': ()},
		{'name': 'is_usable'       , 'i18n': "Is usable", 'values': ()},
		{'name': 'is_serviced'     , 'i18n': "Is serviced", 'values': ()},
)
	assert table.dict['rows'] == (
		{'id': 1  , 'class': () , 'title': "Chose an action", 'fields':  ("1", "Club", "24/10/2006", "Mares", "", "s1", "L", "No", "Yes", "No")},
		{'id': 2  , 'class': () , 'title': "Chose an action", 'fields':  ("2", "Club", "", "Cressi", "Stab", "s2", "M", "Yes", "Yes", "No")},
		{'id': 3  , 'class': () , 'title': "Chose an action", 'fields':  ("3", "Club", "02/07/2015", "Aqualung", "Hudson", "s3", "S", "No", "Yes", "No")},
		{'id': 4  , 'class': () , 'title': "Chose an action", 'fields':  ("10", "Club", "16/04/2017", "Scubapro", "One Flex", "s10", "XS", "Yes", "No", "No")},
		{'id': 14 , 'class': () , 'title': "Chose an action", 'fields':  ("33", "Club", "", "", "", "s33", "", "Yes", "Yes", "No")},
	)


def test00d(populate_db):
	""" Get all usable BCDs when no inventory exists"""
	ItemState.create(item_id=1, date="2019-09-09", is_present=False, is_usable=True)
	ItemState.create(item_id=2, date="2020-09-09", is_present=True, is_usable=True)
	ItemState.create(item_id=3, date="2020-09-09", is_present=False, is_usable=True)
	ItemState.create(item_id=4, date="2020-09-09", is_present=True, is_usable=False)
	create_item(type=ITEM_TYPE_BCD, reference=33, serial_nb="s33", owner_club="Club")

	def class_builder(fields_dict):
		return () if (fields_dict.get('is_present', False) and fields_dict.get('is_usable', False)) else ("unavailable", )

	table = Table("items").build_from_request(get_items(ITEM_TYPE_BCD, usable_only=True), class_builder=class_builder)
	assert table.dict['header'] == (
		{'name': 'reference'       , 'i18n': "Reference", 'values': ()},
		{'name': 'owner_club'      , 'i18n': "Owner club", 'values': ()},
		{'name': 'entry_date'      , 'i18n': "Entry date", 'values': ()},
		{'name': 'brand'           , 'i18n': "Brand", 'values': ()},
		{'name': 'model'           , 'i18n': "Model", 'values': ()},
		{'name': 'serial_nb'       , 'i18n': "Serial number", 'values': ()},
		{'name': 'size_letter_min' , 'i18n': "Minimum American size", 'values': ()},
		{'name': 'is_present'      , 'i18n': "Is present", 'values': ()},
		{'name': 'is_usable'       , 'i18n': "Is usable", 'values': ()},
		{'name': 'is_serviced'     , 'i18n': "Is serviced", 'values': ()},
	)
	assert table.dict['rows'] == (
		{'id': 1  , 'class': ('unavailable', ) , 'title': "Chose an action", 'fields':  ("1", "Club", "24/10/2006", "Mares", "", "s1", "L", "No", "Yes", "No")},
		{'id': 2  , 'class': ()                , 'title': "Chose an action", 'fields':  ("2", "Club", "", "Cressi", "Stab", "s2", "M", "Yes", "Yes", "No")},
		{'id': 3  , 'class': ('unavailable', ) , 'title': "Chose an action", 'fields':  ("3", "Club", "02/07/2015", "Aqualung", "Hudson", "s3", "S", "No", "Yes", "No")},
		{'id': 4  , 'class': ('unavailable', ) , 'title': "Chose an action", 'fields':  ("10", "Club", "16/04/2017", "Scubapro", "One Flex", "s10", "XS", "Yes", "No", "No")},
		{'id': 14 , 'class': ()                , 'title': "Chose an action", 'fields':  ("33", "Club", "", "", "", "s33", "", "Yes", "Yes", "No")},
	)


def test00j(populate_db):
	""" Get characteristics of an item by id """
	assert get_item(3) == {
		'reference': 3,
		'owner_club': "Club",
		'entry_date': date(2015, 7, 2),
		'brand': "Aqualung",
		'model': "Hudson",
		'serial_nb': "s3",
		'size_letter_min': "S",
	}


def test01b(populate_db):
	""" Get all the references of an item type """
	assert get_item_references(ITEM_TYPE_BCD) == (
		(1, 1),
		(2, 2),
		(3, 3),
		(4, 10),
	)


def test01c(populate_db):
	""" Get all the references for available items only (borrowed) """
	borrow_item(2, 1, 1, datetime(2021, 9, 15), 1)
	assert get_item_references(ITEM_TYPE_BCD, available_items_only=True) == (
		(1, 1),
		(3, 3),
		(4, 10),
	)


def test01d(populate_db):
	""" Get all the references for available items only (does not include borrowed, need servicing/repairing...) """
	borrow_item(2, 1, 1, datetime(2021, 9, 15), 1)
	borrow_item(4, 1, 1, datetime(2021, 9, 15), 1)
	give_back_item(4, datetime(2021, 9, 16))
	borrow_item(4, 1, 1, datetime(2021, 9, 17), 1)
	give_back_item(4, datetime(2021, 9, 18))
	assert get_item_references(ITEM_TYPE_BCD, available_items_only=True) == (
		(1, 1),
		(3, 3),
		(4, 10),
	)


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test01e(populate_db):
	""" Get all the references for available items only (does not include missing or unusable) """
	create_item_state(item_id=1, is_present=True, is_usable=True, date=(datetime.now() - timedelta(days=7)))
	create_item_state(item_id=1, is_present=False, is_usable=True, date=(datetime.now() - timedelta(days=3)))
	create_item_state(item_id=2, is_present=True, is_usable=True, date=(datetime.now() - timedelta(days=7)))
	create_item_state(item_id=2, is_present=True, is_usable=False, date=(datetime.now() - timedelta(days=3)))
	assert get_item_references(ITEM_TYPE_BCD, available_items_only=True) == (
		(3, 3),
		(4, 10),
	)


def test01z(populate_db):
	""" Get all the references for composite items """
	assert get_item_references(ITEM_TYPE_FIRST_STAGE) == (
		(5, 1),
	)


def test02a(populate_db):
	""" Get the type of an item by its id """
	assert get_item_type(1) == ITEM_TYPE_BCD
	assert get_item_type(5) == ITEM_TYPE_FIRST_STAGE
	with pytest.raises(DoesNotExist):
		get_item_type(999)


def test02b(populate_db):
	""" Get the id of an item by its type/reference """
	assert get_item_id(ITEM_TYPE_BCD, 1) ==  1
	assert get_item_id(ITEM_TYPE_SECOND_STAGE, 1) ==  6


def test03a(populate_db):
	""" Get all main regulators """
	regulators = get_regulators()
	assert regulators['header'] == ("Type", "Reference", "Brand", "Model", "Serial number")
	assert regulators['rows'][0].id == 5
	assert regulators['rows'][0].type == "first_stage"
	assert regulators['rows'][0].brand == "Aqualung"
	assert regulators['rows'][0] == (5, "first_stage", 1, "Aqualung", "Titan LX Suprème", "7056701", (
			("6", "Second stage", "1", "Aqualung", "Titan LX Suprème", "7056702"),
			("7", "Octopus", "1", "Aqualung", "Titan LX Octopus", "7056703"),
			("8", "Manometer", "1", "Aqualung", "Manometer 200 bars", "7056704"),
		)
	)
	assert regulators['orphans'] == (
		(12, "octopus", "3", "Scubapro", "MK2 Octopus", "7056803"),
	)


def test03b(populate_db):
	""" Get all auxiliary regulators """
	regulators = get_regulators(is_auxiliary=True)
	assert regulators['header'] == ("Type", "Reference", "Brand", "Model", "Serial number")
	assert regulators['rows'][0].id == 9
	assert regulators['rows'][0].type == "first_stage_auxiliary"
	assert regulators['rows'][0].brand == "Scubapro"
	assert regulators['rows'][0] == (9, "first_stage_auxiliary", 1, "Scubapro", "MK2", "7056801", (
			("10", "Octopus", "2", "Scubapro", "MK2 Octopus", "7056802"),
			("11", "Manometer", "2", "Scubapro", "Manometer 300 bars", "7056803"),
		)
	)
	assert regulators['orphans'] == (
		(12, "octopus", "3", "Scubapro", "MK2 Octopus", "7056803"),
	)


def test03c(populate_db):
	""" Move the manometer to another regulator """
	first_stage = Item.create(type="first_stage", reference=2, owner_club="Club", brand="Aqualung", model="Titan LX Suprème", serial_nb="701", is_cold_water=True, entry_date="01/06/07", fastening=ITEM_FASTENING_DIN)
	second_stage = Item.create(type="second_stage", reference=2, owner_club="Club", brand="Aqualung", model="Titan LX Suprème", serial_nb="702", is_cold_water=True, entry_date="01/06/07")
	octopus_stage = Item.create(type="octopus", reference=4, owner_club="Club", brand="Aqualung", model="Titan LX Octopus", serial_nb="704", is_cold_water=True, entry_date="01/06/07")
	IsComposedOf.create(parent=first_stage.id, child=second_stage.id, at_date="01/06/07")
	IsComposedOf.create(parent=first_stage.id, child=octopus_stage.id, at_date="01/06/07")

	IsComposedOf.create(parent=first_stage.id, child=8, at_date="02/06/07")

	regulators = get_regulators()
	assert regulators['header'] == ("Type", "Reference", "Brand", "Model", "Serial number")
	assert tuple(regulators['rows'][0]) == (5, "first_stage", 1, "Aqualung", "Titan LX Suprème", "7056701", (
			("6", "Second stage", "1", "Aqualung", "Titan LX Suprème", "7056702"),
			("7", "Octopus", "1", "Aqualung", "Titan LX Octopus", "7056703"),
		))
	assert tuple(regulators['rows'][1]) == (14, "first_stage", 2, "Aqualung", "Titan LX Suprème", "701", (
			("8", "Manometer", "1", "Aqualung", "Manometer 200 bars", "7056704"),
			("15", "Second stage", "2", "Aqualung", "Titan LX Suprème", "702"),
			("16", "Octopus", "4", "Aqualung", "Titan LX Octopus", "704"),
		))
	assert regulators['orphans'] == (
		(12, "octopus", "3", "Scubapro", "MK2 Octopus", "7056803"),
	)


def test04b(populate_db):
	""" Get the fullnames of the members """
	assert get_members_fullnames() ==  (
		(2, "Gilmour David"),
		(1, "Rambo John"),
	)


def test04bb(populate_db):
	""" Get the fullnames of the members (but only those who gave their guarantee)"""
	assert get_members_fullnames(with_guarantee_only=True) ==  (
		(2, "Gilmour David"),
	)


def test04e(populate_db):
	""" Get a specific member """
	assert get_member(2)['last_name'] =="Gilmour"


def test04f(populate_db):
	""" Get a member's id given it's license number """
	assert get_member_id("A-5678") == 1
	assert get_member_id("unknown-license-number") is None


def test05a(populate_db):
	""" An item can not be borrowed more than one time """
	assert Item.get(Item.id == 1).usage_counter == 0
	borrow_item(1, 1, 2, datetime(2021, 9, 15), 7)
	with pytest.raises(IntegrityError):
		borrow_item(1, 1, 1, datetime(2021, 9, 15), 3)


def test05b(populate_db):
	""" Borrowing an item increases its usage counter """
	assert Item.get(Item.id == 1).usage_counter == 0
	borrow_item(1, 1, 2, datetime(2021, 9, 15), 7)
	assert Borrow.get(Borrow.item == 1).member_id == 2
	assert Item.get(Item.id == 1).usage_counter == 7
	give_back_item(1, datetime.now())
	borrow_item(1, 1, 2, datetime(2021, 9, 15), 3)
	assert Item.get(Item.id == 1).usage_counter == 10


def test06a(populate_db):
	""" Get borrowed items """
	borrow_item(1, 1, 2, datetime(2021, 9, 15), 7)
	assert get_borrowed_items() == (
		(1, "Bcd 1"),
	)


def test06b(populate_db):
	""" Test if items are borrowed """
	borrow_item(1, 1, 2, datetime(2021, 9, 15), 7)
	borrow_item(2, 1, 2, datetime(2021, 9, 15), 3)
	give_back_item(2, datetime.now())
	assert is_item_borrowed(1)
	assert not is_item_borrowed(2)
	assert get_borrowed_items() == (
		(1, "Bcd 1"),
	)


def test07a(populate_db):
	""" Get loans """
	borrow_item(1, 1, 2, datetime(2021, 9, 15), 3)
	assert [t for t in get_loans().query] == [
		(1, datetime(2021, 9, 15), 'Mark Knopfler', 'David Gilmour', 'bcd', 1),
	]


def test07b(populate_db):
	""" Get loans. Items borrowed in the past are not shown """
	borrow_item(1, 1, 2, datetime(2021, 9, 15), 3)
	borrow_item(2, 1, 1, datetime(2021, 9, 15), 3)
	give_back_item(2, datetime.now())
	assert [t for t in get_loans().query] == [
		(1, datetime(2021, 9, 15), 'Mark Knopfler', 'David Gilmour', 'bcd', 1),
	]


def test08a(populate_db):
	""" Get items that are close or need servicing """
	borrow_item(1, 1, 2, datetime(2021, 9, 15), ITEM_USAGE_MAX - 5)
	borrow_item(2, 1, 2, datetime(2021, 9, 15), ITEM_USAGE_MAX)
	assert get_items_to_service() == (
		(1, "bcd 1", 5),
		(2, "bcd 2", 0),
	)


def test08b(populate_db):
	""" Items that are in servicing do not need service anymore """
	borrow_item(1, 1, 2, datetime(2021, 9, 15), ITEM_USAGE_MAX - 5)
	borrow_item(2, 1, 2, datetime(2021, 9, 15), ITEM_USAGE_MAX)
	service((2, ))
	assert get_items_to_service() == (
		(1, "bcd 1", 5),
	)


def test09a(populate_db):
	""" Put some items to servicing """
	service((2, 3))
	assert get_item_references(ITEM_TYPE_BCD, available_items_only=True) == (
		(1, 1),
		(4, 10),
	)


def test10a(populate_db):
	""" Get items in servicing """
	service((2, 3))
	assert get_items_in_servicing() == (
		(2, "bcd 2"),
		(3, "bcd 3"),
	)


def test10h(populate_db):
	""" Get servicing files (for export) """
	create_servicing(item_id=1, date=date(2024, 10, 9), report_file="185b42f.pdf")
	create_servicing(item_id=1, date=date(2024, 10, 3), report_file="185b42g.pdf")
	create_servicing(item_id=2, date=date(2024, 10, 9), report_file="185b42h.pdf")
	create_servicing(item_id=2, date=date(2024, 11, 7), report_file="185b42i.pdf")
	assert get_servicing_files() == (
		("185b42f.pdf", "Bcd_1_2024-10-09.pdf"),
		("185b42g.pdf", "Bcd_1_2024-10-03.pdf"),
		("185b42h.pdf", "Bcd_2_2024-10-09.pdf"),
		("185b42i.pdf", "Bcd_2_2024-11-07.pdf"),
	)


def test11b(populate_db):
	""" Get item states dates (no existing state)"""
	assert get_item_states_dates() == ()


def test11c(populate_db):
	""" Get inventories dates """
	ItemState.create(item_id=3, date="2021-09-09", is_present=True, is_usable=True, price="7", comment="")
	ItemState.create(item_id=3, date="2022-09-03", is_present=True, is_usable=True, price="7", comment="")
	assert get_item_states_dates() == (date(2022, 9, 3), date(2021, 9, 9))


def test12a(populate_db):
	""" Get the users list """
	assert [t for t in get_users().query] == [
		[2, "Beck", "Jeff", "jbeck", ""],
		[1, "Knopfler", "Mark", "mknopfler", ""],
	]


def test12b(populate_db):
	""" Get a specific user """
	assert get_user(2).last_name == "Beck"


def test14a(populate_db):
	""" Return the type and id of an item given it's QRcode reference """
	assert get_type_and_id("S1") == ("bcd", 1)
	assert get_type_and_id("D1") == ("first_stage", 5)


def test15a(populate_db):
	""" Trash an item """
	trashed_id = get_item_id(ITEM_TYPE_FIRST_STAGE, 1)
	trash_item(trashed_id)
	assert get_item(trashed_id) == {}
	assert get_item(trashed_id, include_trashed=True)['reference'] == 1
	assert len(Table("items").build_from_request(get_items(ITEM_TYPE_FIRST_STAGE)).dict['rows']) == 0
	assert len(Table("items").build_from_request(get_items(ITEM_TYPE_FIRST_STAGE, include_trashed=True)).dict['rows']) == 1
	assert len(get_item_references(ITEM_TYPE_FIRST_STAGE)) == 1
	assert len(get_item_references(ITEM_TYPE_FIRST_STAGE, available_items_only=True)) == 0


def test15b(populate_db):
	""" Work with trashed items """
	# Trash BCD 2
	trashed_id = get_item_id(ITEM_TYPE_BCD, 2)
	trash_item(trashed_id)
	assert len(Table("items").build_from_request(get_items(ITEM_TYPE_BCD)).dict['rows']) == 3
	assert Table("items").build_from_request(get_items(ITEM_TYPE_BCD, trashed_only=True)).dict['rows'][0]['id'] == 2
	# Create a new BCD 2
	create_item(type=ITEM_TYPE_BCD, reference=2, serial_nb="s22", owner_club="Club")
	# Can no untrash the BCD 2 because a new one has been created
	with pytest.raises(IntegrityError):
		untrash_item(trashed_id)


def test15c(populate_db):
	""" Can not create two items with the same reference (unless the same reference is in the trashcan) """
	with pytest.raises(IntegrityError):
		create_item(type=ITEM_TYPE_BCD, reference=2, serial_nb="s22", owner_club="Club")


def test20a(populate_db):
	""" Inventory: create a new one """
	create_inventory(date=datetime.now())


def test20b(populate_db):
	""" Inventory: create a new one while there already is a running one """
	create_inventory(date=datetime.now())
	with pytest.raises(InventoryException):
		create_inventory(date=datetime.now() + timedelta(days=1))


def test20c(populate_db):
	""" Inventory: create a new one with the same date as an already existing one """
	create_inventory(date=datetime.now())
	stop_inventory_campaign()
	with pytest.raises(IntegrityError):
		create_inventory(date=datetime.now())


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test20d(populate_db):
	""" Inventory: get the date of the current inventory campaign """
	create_inventory(date=datetime.now())
	assert get_running_inventory_date() == dt.date(2023, 2, 7)




@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test21a(populate_db):
	""" Inventory: get_inventory_items_select_list, no item state at all """
	assert [(t, v) for t, v, _ in get_inventory_items_select_list(datetime.now())] == [
		('bcd', 4),
		('first_stage', 1),
		('first_stage_auxiliary', 1),
		('suit', 1),
	]


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test21b(populate_db):
	""" Inventory: get_inventory_items_select_list, one item as a state that is not part of this inventory date """
	create_item_state(item_id=1, is_present=True, is_usable=True, date=datetime.now() - timedelta(days=3))
	assert [(t, v) for t, v, _ in get_inventory_items_select_list(datetime.now())] == [
		('bcd', 4),
		('first_stage', 1),
		('first_stage_auxiliary', 1),
		('suit', 1),
	]


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test21c(populate_db):
	""" Inventory: get_inventory_items_select_list, one item as a state that is part of this inventory date """
	create_item_state(item_id=1, is_present=True, is_usable=True, date=datetime.now())
	assert [(t, v) for t, v, _ in get_inventory_items_select_list(datetime.now())] == [
		('bcd', 3),
		('first_stage', 1),
		('first_stage_auxiliary', 1),
		('suit', 1),
	]


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test21d(populate_db):
	""" Inventory: get_inventory_items_select_list, suits first """
	assert [(t, v) for t, v, _ in get_inventory_items_select_list(datetime.now(), "suit")] == [
		('suit', 1),
		('bcd', 4),
		('first_stage', 1),
		('first_stage_auxiliary', 1),
	]


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test21e(populate_db):
	""" Inventory: get_inventory_items_select_list, one item as more than one state but none that is part of this inventory date """
	create_item_state(item_id=1, is_present=True, is_usable=True, date=(datetime.now() - timedelta(days=7)))
	create_item_state(item_id=1, is_present=True, is_usable=True, date=(datetime.now() - timedelta(days=3)))
	assert [(t, v) for t, v, _ in get_inventory_items_select_list(datetime.now())] == [
		('bcd', 4),
		('first_stage', 1),
		('first_stage_auxiliary', 1),
		('suit', 1),
	]


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test22a(populate_db):
	""" Inventory: get_current_inventory_remaining_items """
	create_inventory(date=datetime.now())
	assert [t[1] for t in get_current_inventory_remaining_items(ITEM_TYPE_BCD).query] == [1, 2, 3, 10]


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test22b(populate_db):
	""" Inventory: get_current_inventory_remaining_items, one item has been inventoried during the current campaign"""
	create_inventory(date=datetime.now())
	create_item_state(item_id=3, is_present=True, is_usable=True, date=datetime.now())
	assert [t[1] for t in get_current_inventory_remaining_items(ITEM_TYPE_BCD).query] == [1, 2, 10]


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test22c(populate_db):
	""" Inventory: get_current_inventory_remaining_items, one item has already been inventoried more than one time on the fly"""
	create_item_state(item_id=3, is_present=True, is_usable=True, date=datetime(2022, 9, 3))
	create_item_state(item_id=3, is_present=True, is_usable=True, date=datetime(2022, 10, 11))
	create_inventory(date=datetime.now())
	assert [t[1] for t in get_current_inventory_remaining_items(ITEM_TYPE_BCD).query] == [1, 2, 3, 10]


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test22d(populate_db):
	""" Inventory: get_current_inventory_remaining_items, no item type chosen """
	create_item_state(item_id=3, is_present=True, is_usable=True, date=datetime(2022, 9, 3))
	create_inventory(date=datetime.now())
	create_item_state(item_id=3, is_present=True, is_usable=True, date=datetime.now())
	assert get_current_inventory_remaining_items(None).query == ()


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test22e(populate_db):
	""" Inventory: get_current_inventory_remaining_items, do not display trashed items """
	create_item_state(item_id=get_item_id(ITEM_TYPE_BCD, 3), is_present=True, is_usable=True, date=datetime(2022, 9, 3))
	trash_item(3)
	create_item(type=ITEM_TYPE_BCD, reference=3, serial_nb="s33", owner_club="Club")
	create_inventory(date=datetime.now())
	assert [t[1] for t in get_current_inventory_remaining_items(ITEM_TYPE_BCD).query] == [1, 2, 3, 10]
	create_item_state(item_id=get_item_id(ITEM_TYPE_BCD, 3), is_present=True, is_usable=True, date=datetime.now())
	assert [t[1] for t in get_current_inventory_remaining_items(ITEM_TYPE_BCD).query] == [1, 2, 10]


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test23a(populate_db):
	""" Inventory: get_latest_inventory_date """
	latest_inventory_date = (datetime.now() - timedelta(days=1)).date()
	create_inventory(date=latest_inventory_date)
	assert get_latest_inventory_date() == latest_inventory_date


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test23b(populate_db):
	""" Inventory: get_latest_inventory_date, no inventory yet """
	assert get_latest_inventory_date() == date.min


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test24a(populate_db):
	""" Inventory: get_items_estimations, only the item's estimations at the given date are taken into account """
	create_item_state(item_id=2, is_present=True, is_usable=True, price=37, date=(datetime.now() + timedelta(days=-1)))
	create_item_state(item_id=3, is_present=True, is_usable=True, price=3, date=datetime.now())
	create_item_state(item_id=4, is_present=True, is_usable=True, price=7, date=(datetime.now() + timedelta(days=1)))
	assert get_items_estimations(datetime.now()) == 3


@time_machine.travel(dt.datetime(2023, 2, 7, 14, 38))
def test25a(populate_db):
	""" Inventory: get_items_estimations_table """
	# BCDs
	create_item_state(item_id=1, is_present=True, is_usable=True, price=1, date=(datetime.now()))
	create_item_state(item_id=2, is_present=True, is_usable=False, price=120, date=(datetime.now() + timedelta(days=-1)))
	create_item_state(item_id=2, is_present=True, is_usable=False, price=2, date=(datetime.now()))
	# Regulators
	create_item_state(item_id=5, is_present=True, is_usable=False, price=3, date=datetime.now())
	create_item_state(item_id=5, is_present=True, is_usable=True, price=730, date=(datetime.now() + timedelta(days=1)))
	# Auxiliary regulators
	create_item_state(item_id=9, is_present=True, is_usable=True, price=4, date=(datetime.now()))
	assert get_items_estimations_table(datetime.now()) == [
		("Bcd", 3),
		("Main regulator", 3),
		("Auxiliary regulator", 4),
	]


@time_machine.travel(dt.datetime(2021, 10, 1))
def test26a(populate_db):
	""" Get items last state, no state in the DB """
	assert get_items_last_state("bcd") == {}


@time_machine.travel(dt.datetime(2021, 10, 1))
def test26b(populate_db):
	""" Get items last state, one state in the DB """
	ItemState.create(item_id=3, date="2021-09-09", is_present=True, is_usable=True)
	assert get_items_last_state("bcd") == {
		3: (True, True),
	}


@time_machine.travel(dt.datetime(2021, 10, 1))
def test26c(populate_db):
	""" Get items last state, several states in the DB for this item """
	ItemState.create(item_id=3, date="2021-09-09", is_present=True, is_usable=True)
	ItemState.create(item_id=3, date="2021-09-10", is_present=True, is_usable=True)
	ItemState.create(item_id=3, date="2021-09-11", is_present=False, is_usable=True)
	assert get_items_last_state("bcd") == {
		3: (False, True),
	}


@time_machine.travel(dt.datetime(2021, 10, 1))
def test26d(populate_db):
	""" Get items last state, multiple items of the same type have states """
	ItemState.create(item_id=3, date="2021-09-09", is_present=True, is_usable=True)
	ItemState.create(item_id=3, date="2021-09-11", is_present=False, is_usable=True)
	ItemState.create(item_id=1, date="2021-08-01", is_present=False, is_usable=False)
	ItemState.create(item_id=1, date="2021-09-09", is_present=True, is_usable=False)
	assert get_items_last_state("bcd") == {
		1: (True, False),
		3: (False, True),
	}


@time_machine.travel(dt.datetime(2021, 10, 1))
def test26e(populate_db):
	""" Get items last state, several items of different types have states """
	ItemState.create(item_id=3, date="2021-09-09", is_present=True, is_usable=True)
	ItemState.create(item_id=3, date="2021-09-10", is_present=True, is_usable=True)
	ItemState.create(item_id=3, date="2021-09-11", is_present=False, is_usable=True)
	ItemState.create(item_id=5, date="2021-09-12", is_present=True, is_usable=True)
	assert get_items_last_state("bcd") == {
		3: (False, True),
	}

