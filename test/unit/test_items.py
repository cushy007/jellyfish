#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import pytest

from webapp.items import GEAR, ITEM_TYPE_FIRST_STAGE, ITEM_TYPE_SUIT, Group


def test01a():
	""" Get the 'regulator' group of the gear """
	assert isinstance(GEAR['regulator'], Group)
	assert GEAR['regulator'].name == "regulator"
	assert GEAR['regulator'].i18n == "Regulators"


def test01b():
	""" Try to get an unknown group """
	with pytest.raises(KeyError):
		GEAR['polop']


def test01c():
	""" Get all groups """
	assert GEAR.groups[0].name == 'regulator'
	assert GEAR.groups[-1].name == 'accessory'


def test02a():
	""" Get an item of the group 'regulator' """
	assert GEAR['regulator'][ITEM_TYPE_FIRST_STAGE].i18n == "Main regulator"


def test02b():
	""" Get all items of the group 'regulator' """
	assert GEAR['regulator'].items[0].type == ITEM_TYPE_FIRST_STAGE
	assert GEAR['regulator'].items[-1].i18n == "Auxiliary regulator"


def test03a():
	""" Get the group of the item type 'first_stage' """
	assert GEAR.get_item_group('first_stage').name == 'regulator'


def test03b():
	""" Get the group of a non existing item type """
	assert GEAR.get_item_group('polop') == None


def test04a():
	""" Get borrowable items """
	assert GEAR.borrowable_items[0].type == ITEM_TYPE_FIRST_STAGE
	assert GEAR.borrowable_items[5].type == ITEM_TYPE_SUIT
