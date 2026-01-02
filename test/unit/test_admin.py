#
# Copyright 2021-2026, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from unittest.mock import Mock

from webapp.items import ITEM_TYPE_COMPUTER
from webapp.views.admin import build_items_list


def test01a():
	""" build_items_list """
	available_refs = (1, 2, 3)
	mock_get_item_references = Mock(return_value=zip(available_refs, available_refs))
	assert build_items_list(ITEM_TYPE_COMPUTER, "1,2,3", get_item_references=mock_get_item_references) == (1, 2, 3)


def test02a():
	""" build_items_list with range """
	available_refs = range(1, 8)
	mock_get_item_references = Mock(return_value=zip(available_refs, available_refs))
	assert build_items_list(ITEM_TYPE_COMPUTER, "1,3-5,7", get_item_references=mock_get_item_references) == (1, 3, 4, 5, 7)


def test03a():
	""" build_items_list with wildcard """
	available_refs = (1, 2, 3, 7)
	mock_get_item_references = Mock(return_value=zip(available_refs, available_refs))
	assert build_items_list(ITEM_TYPE_COMPUTER, "*", get_item_references=mock_get_item_references) == (1, 2, 3, 7)
