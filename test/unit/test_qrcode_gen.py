#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from unittest.mock import Mock

import pytest

from webapp.qrcode_gen import ConverterException, Page, PageFullException, Point


def test01a():
	""" check default page sizes """
	page = Page()
	assert page._page.width == 2480
	assert page._page.height == 3508
	assert page._coord_min == Point(118, 118)
	assert page._coord_max == Point(2362, 3390)


def test02a():
	""" add some images to the page """
	mock_image_factory = Mock()
	mock_page = Mock()
	mock_image_factory.new = Mock(return_value=mock_page)
	mock_image = Mock(width=410, height=410)
	page = Page(image_factory=mock_image_factory)
	mock_image_factory.new.assert_called_with("RGB", (2480, 3508), (255, 255, 255))
	page.add_image(mock_image)
	page.add_image(mock_image)
	assert page._current_coord.x == 118 + 2 * 410
	assert page._current_coord.y == 118
	assert page._next_row_start == 118 + 410
	page.add_image(mock_image)
	page.add_image(mock_image)
	page.add_image(mock_image)
	page.add_image(mock_image)
	assert page._current_coord.x == 118 + 1 * 410
	assert page._current_coord.y == 118 + 410
	assert page._next_row_start == 118 + 410 + 410


def test02c():
	""" too much images for one page """
	mock_image_factory = Mock()
	mock_page = Mock()
	mock_image_factory.new = Mock(return_value=mock_page)
	mock_image = Mock(width=410, height=410)
	page = Page(image_factory=mock_image_factory)
	mock_image_factory.new.assert_called_with("RGB", (2480, 3508), (255, 255, 255))
	for i in range(35):
		page.add_image(mock_image)
	with pytest.raises(PageFullException):
		page.add_image(mock_image)


def test03a():
	""" add an image too wide to fit on the page (first one)"""
	mock_image_factory = Mock()
	mock_page = Mock()
	mock_image_factory.new = Mock(return_value=mock_page)
	mock_image = Mock(width=2300, height=410)
	page = Page(image_factory=mock_image_factory)
	with pytest.raises(ConverterException):
		page.add_image(mock_image)


def test03b():
	""" add an image too wide to fit on the page (not the first one)"""
	mock_image_factory = Mock()
	mock_page = Mock()
	mock_image_factory.new = Mock(return_value=mock_page)
	mock_image1 = Mock(width=410, height=410)
	mock_image2 = Mock(width=2300, height=410)
	page = Page(image_factory=mock_image_factory)
	page.add_image(mock_image1)
	with pytest.raises(ConverterException):
		page.add_image(mock_image2)


def test04a():
	""" add an image too high to fit on the page (first one)"""
	mock_image_factory = Mock()
	mock_page = Mock()
	mock_image_factory.new = Mock(return_value=mock_page)
	mock_image = Mock(width=410, height=3300)
	page = Page(image_factory=mock_image_factory)
	with pytest.raises(ConverterException):
		page.add_image(mock_image)


def test04b():
	""" add an image too high to fit on the page (not the first one)"""
	mock_image_factory = Mock()
	mock_page = Mock()
	mock_image_factory.new = Mock(return_value=mock_page)
	mock_image1 = Mock(width=410, height=410)
	mock_image2 = Mock(width=410, height=3300)
	page = Page(image_factory=mock_image_factory)
	page.add_image(mock_image1)
	with pytest.raises(ConverterException):
		page.add_image(mock_image2)
