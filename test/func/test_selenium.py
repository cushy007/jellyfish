# coding: utf-8
#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import datetime as dt
import logging
from copy import copy
from datetime import date, timedelta
from logging import WARNING
from os import environ
from time import sleep

import pytest
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from weblib.models import WEBLIB_MODELS
from weblib.test.utils import SeleniumFixtures

from webapp import requests
from webapp.items import GEAR
from webapp.models import MODELS, Member
from webapp.requests import create_item
from webapp.roles import ROLE_LENDER

from .data import ITEMS, MANY_ITEMS, MEMBERS

for logger in ("urllib3", "werkzeug", "peewee", "selenium.webdriver.remote"):
	logging.getLogger(logger).setLevel(WARNING)


_LOGGER = logging.getLogger(__name__)

class ItemReferenceException(Exception):
	pass


class JellyfishMacrosMixin:

	def add_member(self, form_dict):
		self.switch_to_tab("member")
		self.click_element_by_id("btn-add-member")
		self.fill_form(form_dict)

	def add_item(self, path):
		self.switch_to_tab("gear", path[0], path[1])
		self.click_element_by_id("btn-add-item")
		self.fill_form(ITEMS[path], select_visible_text=False)

	def click_gear_table_row_by_item_ref(self, reference, in_trashcan=False):
		self.wait_for_document_ready()
		ref_tds = self.driver.find_elements(By.CSS_SELECTOR, 'table[name="%s"] td:nth-child(1)' % ("trashed_gear" if in_trashcan else "gear"))
		for td in ref_tds:
			if td.text == str(reference):
				td.click()
				return
		raise ItemReferenceException(f"Reference '{reference}' not found")

	def add_item_state(self, item_group, item_type, reference, date=None, is_present=True, is_usable=True, price=0, comment=""):
		self.switch_to_tab("gear", item_group, item_type)
		self.click_gear_table_row_by_item_ref(reference)
		self.click_modal_button("state")
		self.fill_form({
			'date': date,
			'is_present': is_present,
			'is_usable': is_usable,
			'price': price,
			'comment': comment,
		})

	def add_item_servicing(self, item_group, item_type, reference, date=None, filename=""):
		self.switch_to_tab("gear", item_group, item_type)
		self.click_gear_table_row_by_item_ref(reference)
		self.click_modal_button("servicing")
		self.fill_form({
			'date': date,
			'report_file': f"/home/seluser/resources/{filename}",
		})

	def assert_bcd1_available(self):
		self.switch_to_tab("gear", "stabilization", "bcd")
		assert len(self.driver.find_elements(By.CSS_SELECTOR, '.unavailable')) == 0
		self.switch_to_tab("loan", "collection")
		if not self._is_loan_in_degraded_mode:
			self.click_element_by_id("degraded-mode-btn")
		self._is_loan_in_degraded_mode = True
		sleep(1)
		self.select("reason", "4")
		self.select("member", visible_text="Morrison Jim")
		self.select("item_reference-parent", "bcd")
		self.select("item_reference", visible_text="1")
		sleep(.5)
		self.submit()
		self.click_element_by_id("title")
		self.switch_to_tab("loan", "reintegration")
		sleep(.5)
		self.select('item', value=6)
		self.submit()
		self.click_element_by_id("title")

	def assert_bcd1_unavailable(self):
		self.switch_to_tab("gear", "stabilization", "bcd")
		tr = self.driver.find_elements(By.CSS_SELECTOR, '.unavailable')[0]
		assert tr.find_elements(By.CSS_SELECTOR, 'td')[0].text == "1"
		self.switch_to_tab("loan", "collection")
		if not self._is_loan_in_degraded_mode:
			self.click_element_by_id("degraded-mode-btn")
		self._is_loan_in_degraded_mode = True
		sleep(1)
		self.select("reason", "4")
		self.select("member", visible_text="Morrison Jim")
		self.select("item_reference-parent", "bcd")
		with pytest.raises(NoSuchElementException):
			self.select("item_reference", visible_text="1")
		self.click_element_by_id("title")


class JellyfishFixtures(SeleniumFixtures, JellyfishMacrosMixin):
	IS_FULLY_PRIVATE_SITE = True

	@pytest.fixture(scope='function')
	def members(self):
		with self.database.bind_ctx(MODELS + WEBLIB_MODELS):
			for member in MEMBERS.values():
				Member.create(**member)

	def __populate_items(self, items_dict):
		with self.database.bind_ctx(MODELS + WEBLIB_MODELS):
			for key, val in items_dict.items():
				item_type = key[1]
				d = copy(val)
				d['type'] = item_type
				d['owner_club'] = "The Club"
				d['entry_date'] = "28/02/2022"
				create_item(**d)

	@pytest.fixture(scope='function')
	def items(self):
		self.__populate_items(ITEMS)

	@pytest.fixture(scope='function')
	def many_items(self):
		self.__populate_items(MANY_ITEMS)


class TestMembers(JellyfishFixtures):

	def test01a(self, start_app, users, members, items, start_driver):
		""" Check table content """
		self.login_as("gilmour")
		self.switch_to_tab("member")
		self.check_table("member", (3, 4),
			header=("NOM", "N° DE LICENCE", "CAUTION"),
			rows=(
				("Brown", "123456", "Oui"),
				("Mercury", "658798", "Oui"),
				("Morrison", "789123", "Oui"),
			)
		)

	def test02a(self, start_app, users, members, items, start_driver):
		""" Create a member with a guarantee and another one with a license"""
		self.login_as("gilmour")
		self.switch_to_tab("member")
		self.click_element_by_id("btn-create-member")
		self.fill_form({
			'first_name': "John",
			'last_name': "Rambo",
			'has_guarantee': True,
		}, submit_btn_text=_("Create"))
		assert self.get_table_field("member", 4, 3) == ""
		assert self.get_table_field("member", 4, 4) == "Oui"

		self.click_element_by_id("btn-create-member")
		self.fill_form({
			'first_name': "Chuck",
			'last_name': "Norris",
			'license_nb': "121212",
		}, submit_btn_text=_("Create"))
		assert self.get_table_field("member", 4, 3) == "121212"
		assert self.get_table_field("member", 4, 4) == "Non"

	def test03a(self, start_app, users, members, items, start_driver):
		""" Delete a member with confirmation """
		self.login_as("gilmour")
		self.switch_to_tab("member")
		self.click_table_row("member", 2)
		self.click_modal_button("del", with_confirmation=True)
		sleep(1)
		self.check_table("member", (2, 4),
			header=("NOM", "N° DE LICENCE", "CAUTION"),
			rows=(
				("Brown", "123456", "Oui"),
				("Morrison", "789123", "Oui"),
			)
		)

	def test04a(self, start_app, treasurer, items, start_driver):
		""" CRUD for a treasurer """
		self.login_as("treasurer")
		self.switch_to_tab("member")
		self.click_element_by_id("btn-create-member")
		self.fill_form({
			'first_name': "John",
			'last_name': "Rambo",
			'has_guarantee': True,
		}, submit_btn_text=_("Create"))
		assert self.get_table_field("member", 1, 3) == ""
		assert self.get_table_field("member", 1, 4) == "Oui"

		self.click_table_row("member", 1)
		self.click_modal_button("update")
		sleep(1)
		self.fill_form({
			'has_guarantee': False,
		}, submit_btn_text=_("Update"))
		assert self.get_table_field("member", 1, 4) == "Non"

		self.click_table_row("member", 1)
		self.click_modal_button("del", with_confirmation=True)
		sleep(1)
		assert self.get_table_header("member", 2) == "VIDE"

	def test05a(self, start_app, treasurer, items, start_driver):
		""" A treasurer can only access the member's tab """
		self.login_as("treasurer")
		self.switch_to_tab("gear")
		self.is_forbidden()
		self.switch_to_tab("loan")
		self.is_forbidden()
		self.switch_to_tab("inventory")
		self.is_forbidden()

	def test06a(self, start_app, treasurer, items, start_driver):
		""" Can't add a duplicated member's name and firstname (strip trailing spaces) """
		self.login_as("treasurer")
		self.switch_to_tab("member")
		self.click_element_by_id("btn-create-member")
		self.fill_form({
			'first_name': "John",
			'last_name': "Rambo",
		}, submit_btn_text=_("Create"))

		sleep(.2)
		self.click_element_by_id("btn-create-member")
		self.fill_form({
			'first_name': " John ",
			'last_name': "Rambo ",
		}, submit_btn_text=_("Create"))
		assert "dupliquée" in self.driver.find_element(By.CSS_SELECTOR, 'body p').text  # TODO use self.is_server_error()

	def test06b(self, start_app, treasurer, items, start_driver):
		""" Member's name and firstname can't collide on modification """
		self.login_as("treasurer")
		self.switch_to_tab("member")
		self.click_element_by_id("btn-create-member")
		self.fill_form({
			'first_name': "John",
			'last_name': "Rambo",
		}, submit_btn_text=_("Create"))

		sleep(.2)
		self.click_element_by_id("btn-create-member")
		self.fill_form({
			'first_name': "John2",
			'last_name': "Rambo",
		}, submit_btn_text=_("Create"))

		sleep(.3)
		self.click_table_row("member", 2)
		self.click_modal_button("update")
		self.fill_form({
			'first_name': "John",
			'last_name': "Rambo",
		})
		assert "dupliquée" in self.driver.find_element(By.CSS_SELECTOR, 'body p').text  # TODO use self.is_server_error()


class TestLoans(JellyfishFixtures):

	def test01a(self, start_app, users, members, items, start_driver):
		""" Borrowing an item does not reset the current reason and member """
		self.login_as('gilmour')
		self.switch_to_tab("loan", "collection")
		self.click_element_by_id("degraded-mode-btn")
		sleep(1)
		self.select("reason", "4")  # TODO verify this when servicing will be ready
		self.select("member", visible_text="Morrison Jim")
		self.select("item_reference-parent", "suit")
		self.select("item_reference", visible_text="2")
		sleep(.5)
		self.submit()
		sleep(5)
		self.submit()  # second one with the default item type and item reference selected
		sleep(.5)
		self.click_element_by_id("title")
		assert self.get_table_field("loans", 1, 3) == "Jim Morrison"
		assert self.get_table_field("loans", 1, 4) == "Combinaison"
		assert self.get_table_field("loans", 1, 5) == "2"
		assert self.get_table_field("loans", 2, 3) == "Jim Morrison"
		assert self.get_table_field("loans", 2, 4) == "Détendeur principal"
		assert self.get_table_field("loans", 2, 5) == "1"

	def test01b(self, start_app, users, members, items, start_driver):
		""" A borrowed item does not appear again in the lending list """
		self.login_as('gilmour')
		self.switch_to_tab("loan", "collection")
		self.click_element_by_id("degraded-mode-btn")
		sleep(1)
		self.select("reason", "4")
		self.select("member", visible_text="Morrison Jim")
		self.select("item_reference-parent", "suit")
		self.select("item_reference", visible_text="1")
		sleep(.5)
		self.submit()
		sleep(5)
		self.select("item_reference-parent", "suit")
		sleep(1)  # wait for child sync
		with pytest.raises(NoSuchElementException):
			self.select("item_reference", visible_text="1")

	def test01c(self, start_app, users, members, items, start_driver):
		""" A user must be in the ROLE_LENDER group for being allowed to lend an item """
		# Create a lender user...
		self.login_as('gilmour')
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-users")
		self.click_element_by_id("btn-create-users")
		self.fill_form({
			'username': "scubadiver",
			'last_name': "Scuba",
			'first_name': "Diver",
			'password': "1234",
			'password_confirmation': "1234",
			'roles': ROLE_LENDER,
		})
		# he's able to lend
		self.logout()
		self.login_as('scubadiver', passwd="1234")
		self.switch_to_tab("loan", "collection")
		self.click_element_by_id("degraded-mode-btn")
		sleep(1)
		self.select("reason", "4")  # TODO verify this when servicing will be ready
		self.select("member", visible_text="Morrison Jim")
		self.select("item_reference-parent", "suit")
		self.select("item_reference", visible_text="2")
		sleep(.5)
		self.submit()
		sleep(5)
		self.submit()  # second one with the default item type and item reference selected
		sleep(.5)
		self.click_element_by_id("title")
		assert self.get_table_field("loans", 1, 3) == "Jim Morrison"
		assert self.get_table_field("loans", 1, 4) == "Combinaison"
		assert self.get_table_field("loans", 1, 5) == "2"
		assert self.get_table_field("loans", 2, 3) == "Jim Morrison"
		assert self.get_table_field("loans", 2, 4) == "Détendeur principal"
		assert self.get_table_field("loans", 2, 5) == "1"

		# Remove the lender role to this user...
		self.logout()
		self.login_as('gilmour')
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-users")
		self.click_table_row("users", 3)
		self.click_modal_button("modify_roles")
		self.select('roles', visible_text="user")
		self.deselect('roles', visible_text="lender")
		self.submit()

		# He's not able to lend anymore
		self.logout()
		self.login_as('scubadiver', passwd="1234")
		self.switch_to_tab("loan")
		self.is_forbidden()

	def test02a(self, start_app, users, members, items, start_driver):
		""" A member whith no guarantee can not borrow an item """
		self.login_as('gilmour')
		self.switch_to_tab("member")
		self.click_table_row("member", 3)
		self.click_modal_button("update")
		self.checkbox("has_guarantee", False)
		self.submit()
		assert self.get_table_field("member", 1, 1) == "Brown"
		assert self.get_table_field("member", 1, 4) == "Oui"
		assert self.get_table_field("member", 3, 1) == "Morrison"
		assert self.get_table_field("member", 3, 4) == "Non"
		self.switch_to_tab("loan", "collection")
		assert "Brown James" in self.get_select_choices("[name=member]")
		assert len(self.get_select_choices("[name=member]")) == 3  # 2 plus the empty default user

	def test03a(self, start_app, users, members, items, start_driver):
		""" Borrowed items appear in overview """
		self.login_as('gilmour')
		self.switch_to_tab("loan", "collection")
		self.click_element_by_id("degraded-mode-btn")
		sleep(1)
		self.select("reason", "2")
		self.select("member", visible_text="Brown James")
		sleep(.5)
		self.submit()
		sleep(.5)
		self.click_element_by_id("title")
		assert self.get_table_field("loans", 1, 1) == date.today().strftime("%d/%m/%Y")
		assert self.get_table_field("loans", 1, 2) == "David Gilmour"
		assert self.get_table_field("loans", 1, 3) == "James Brown"
		assert self.get_table_field("loans", 1, 4) == "Détendeur principal"
		assert self.get_table_field("loans", 1, 5) == "1"

	def Xtest04a(self, start_app, users, members, items, start_driver):
		""" The items' information page displays the loans history """
		self.login_as('gilmour')
		self.switch_to_tab("loan", "collection")
		self.select("reason", "2")
		self.select("member", visible_text="James Brown")
		sleep(.5)
		self.submit()
		self.switch_to_tab("loan", "reintegration")
		sleep(.5)
		self.submit()
		self.switch_to_tab("gear", "regulator", "first_stage")
		self.click_gear_table_row_by_item_ref(1)
		self.click_modal_button("info")
		# TODO...


class TestItems(JellyfishFixtures):

	def test01a(self, start_app, users, start_driver):
		""" Add some items """
		self.login_as('gilmour')
		for item in ITEMS:
			self.add_item(item)
		assert self.get_table_field("gear", 1, 6) == ""
		assert self.get_table_field("gear", 1, 7) == "M"

	def test01b(self, start_app, users, start_driver):
		""" Add all item types """
		self.login_as('gilmour')
		for group in GEAR.groups:
			for item in group.items:
				self.switch_to_tab("gear", group.name, item.type)
				self.click_element_by_id("btn-add-item")
				self.fill_form({'reference': "77"}, select_visible_text=False)

	def test01c(self, start_app, users, items, start_driver):
		""" Modify items """
		self.login_as('gilmour')

		# modify a BCD
		self.switch_to_tab("gear", "stabilization", "bcd")
		self.click_gear_table_row_by_item_ref(1)
		self.click_modal_button("modify")
		self.input_text("serial_nb", 1234)
		self.input_text("size_letter_min", "L")
		self.submit()
		assert self.get_table_field("gear", 1, 6) == "1234"
		assert self.get_table_field("gear", 1, 7) == "L"

		# modify a suit
		self.switch_to_tab("gear", "wear", "suit")
		self.click_gear_table_row_by_item_ref(1)
		self.click_modal_button("modify")
		# Leave all the values as they are and submit
		self.submit()
		assert self.get_table_field("gear", 1, 7) == ""  # thickness
		assert self.get_table_field("gear", 1, 10) == "" # size_number_min
		assert self.get_table_field("gear", 1, 11) == "" # size_number_max

	def test01d(self, start_app, users, items, start_driver):
		""" Delete items """
		self.login_as('gilmour')
		# Delete a suit that has never been used (TODO remove it from DB)
		self.switch_to_tab("gear", "wear", "suit")
		self.click_gear_table_row_by_item_ref(2)
		self.click_modal_button("delete", with_confirmation=True)
		assert self.get_table_field("gear", 2, 5) == "Medas"

		# Delete a BCD that has already been used -> to recycle bin
		self.add_item_state("stabilization", "bcd", 1, price=200, comment="En bon état :)")
		self.switch_to_tab("gear", "stabilization", "bcd")
		self.click_gear_table_row_by_item_ref(1)
		self.click_modal_button("delete", with_confirmation=True)
		assert self.get_table_field("trashed_gear", 1, 5) == "Black Diamond"

	def test01e(self, start_app, users, items, start_driver):
		""" Untrash an item """
		self.login_as('gilmour')
		# Delete a BCD that has already been used -> to recycle bin
		self.add_item_state("stabilization", "bcd", 1, price=200, comment="En bon état :)")
		self.switch_to_tab("gear", "stabilization", "bcd")
		self.click_gear_table_row_by_item_ref(1)
		self.click_modal_button("delete", with_confirmation=True)
		assert self.get_table_field("trashed_gear", 1, 5) == "Black Diamond"

		# Untrash it
		self.switch_to_tab("gear", "stabilization", "bcd")
		with pytest.raises(ItemReferenceException):
			self.click_gear_table_row_by_item_ref(1)
		self.click_gear_table_row_by_item_ref(1, in_trashcan=True)
		self.click_modal_button("untrash")
		self.switch_to_tab("gear", "stabilization", "bcd")
		self.click_gear_table_row_by_item_ref(1)

	def test01f(self, start_app, users, items, start_driver):
		""" Untrash of an item is forbidden if an item with the same reference has been created """
		self.login_as('gilmour')
		# Delete a BCD that has already been used -> to trash
		self.add_item_state("stabilization", "bcd", 1, price=200, comment="En bon état :)")
		self.switch_to_tab("gear", "stabilization", "bcd")
		self.click_gear_table_row_by_item_ref(1)
		self.click_modal_button("delete", with_confirmation=True)
		assert self.get_table_field("trashed_gear", 1, 5) == "Black Diamond"

		# Create a new one with the same reference
		self.add_item(("stabilization", "bcd", 1))

		# Can not untrash it
		self.switch_to_tab("gear", "stabilization", "bcd")
		self.click_gear_table_row_by_item_ref(1, in_trashcan=True)
		# with pytest.raises(peewee.IntegrityError):  TODO
			# self.click_modal_button("untrash")

	def Xtest01z(self, start_app, users, items, start_driver):
		""" ??? """
		#...
		self.switch_to_tab("gear", "regulator")
		assert self.get_table_field("gear", 1, 6) == "AK47"
		# self.switch_to_tab("gear", "regulator", "second_stage")
		# assert self.get_table_field("gear", 0, 6) == "AK48"

	def test10a(self, start_app, users, items, start_driver):
		""" Check translations... """
		self.login_as('gilmour')
		self.switch_to_tab("gear", "regulator")
		assert self.driver.find_element(By.ID, "tab-l3-first_stage").text == "Détendeurs principaux"
		""" ... for auxiliary """
		assert self.driver.find_element(By.ID, "tab-l3-first_stage_auxiliary").text == "Octopus"
		""" ... for fields """
		assert self.get_table_field("gear", 1, 9) == "Étrier"

	def test11a(self, start_app, users, items, start_driver):
		""" Check table content """
		self.login_as('gilmour')
		self.switch_to_tab("gear", "wear", "suit")
		self.check_table("gear", (3, 14),
			header=("RÉFÉRENCE", "TAILLE AMÉRICAINE MINI", "AVEC SHORTY"),
			rows=(
				("1", "M", ""),
				("2", "M", "Oui"),
				("3", "S", ""),
			),
			# has_checkboxes=True,
		)

	def test12a(self, start_app, users, items, start_driver):
		""" Items references constraints """
		# Can't have duplicated references for each item type
		self.login_as('gilmour')
		self.switch_to_tab("gear", "wear", "suit")
		self.click_element_by_id("btn-add-item")
		self.fill_form({'reference': 1})
		sleep(1)
		self.assert_wtf_error("reference")

		# Can't modify the reference of  an item
		self.switch_to_tab("gear", "wear", "suit")
		self.click_gear_table_row_by_item_ref(1)
		self.click_modal_button("modify")
		self.fill_form({'reference': 7})
		assert self.get_table_field("gear", 1, 1) == "1"


class TestItemState(JellyfishFixtures):

	def test01a(self, start_app, users, items, start_driver):
		""" Add, modify and delete an item state """
		self.login_as('gilmour')
		self.add_item_state("stabilization", "bcd", 2, price=200, comment="En bon état :)")
		self.add_item_state("stabilization", "bcd", 2, price=300, comment="ooops, can't have two states on the same day")
		self.is_server_error()

		self.switch_to_tab("gear", "stabilization", "bcd")
		self.click_gear_table_row_by_item_ref(2)
		self.click_modal_button("info")
		sleep(2)  # FIXME use selenium-ready
		assert len(self.driver.find_elements(By.CSS_SELECTOR, 'table[name="state"] tbody tr')) == 1
		assert self.get_table_field("state", 1, 2) == "Oui"
		assert self.get_table_field("state", 1, 4) == "200.00"
		assert self.get_table_field("state", 1, 5) == "En bon état :)"

		self.click_table_row("state", 1)
		self.click_modal_button("update")
		self.checkbox("is_present", False)
		self.submit()
		assert self.get_table_field("state", 1, 2) == "Non"

		self.click_table_row("state", 1)
		self.click_modal_button("del", with_confirmation=True)
		sleep(2)
		assert len(self.driver.find_elements(By.CSS_SELECTOR, 'table[name="state"] tbody tr')) == 0


class TestServicing(JellyfishFixtures):

	def test01a(self, start_app, users, items, start_driver, tmp_path):

		""" Add, modify and delete an item servicing """
		environ['UPLOAD_DIR'] = str(tmp_path)
		self.login_as('gilmour')
		self.add_item_servicing("stabilization", "bcd", 2, filename="polop.pdf")
		self.add_item_servicing("stabilization", "bcd", 2, filename="polop.png")
		#self.is_server_error()... for now on allow users to upload more than one file for each servicing

		self.switch_to_tab("gear", "stabilization", "bcd")
		self.click_gear_table_row_by_item_ref(2)
		self.click_modal_button("info")
		sleep(2)  # FIXME use selenium-ready
		assert len(self.driver.find_elements(By.CSS_SELECTOR, 'table[name="servicing"] tbody tr')) == 2
		assert self.get_table_field("servicing", 1, 1) == date.today().strftime("%d/%m/%Y")
		field = self.get_table_field_raw("servicing", 1, 2)
		anchor = field.find_element(By.CSS_SELECTOR, "a")
		assert "fa-solid fa-file-pdf" in anchor.get_attribute("class")
		assert "upload/185b5b433e47391824dc9a6599edb8041c984b43ee31a28a5e4fd4d4e2f0b42f" in anchor.get_attribute("href")

		self.click_table_row("servicing", 1)
		self.click_modal_button("update")
		self.input_text("report_file", "/home/seluser/resources/polop.txt")
		self.submit()
		field = self.get_table_field_raw("servicing", 1, 2)
		anchor = field.find_element(By.CSS_SELECTOR, "a")
		assert "fa-solid fa-file" in anchor.get_attribute("class")
		assert "upload/ff3f012667b82adcebaad526b513f1ef87616baf249522e1d9858d4746a188ef" in anchor.get_attribute("href")
		#assert hashlib.sha256(requests.get(anchor.get_attribute("href")).content).hexdigest() == "ff3f012667b82adcebaad526b513f1ef87616baf249522e1d9858d4746a188ef"  # TODO must be logged in

		self.click_table_row("servicing", 1)
		self.click_modal_button("del", with_confirmation=True)
		sleep(2)
		assert len(self.driver.find_elements(By.CSS_SELECTOR, 'table[name="servicing"] tbody tr')) == 1

	def test02a(self, start_app, users, items, start_driver, tmp_path):
		""" Servicind status is displayed in the item tables"""
		self.login_as('gilmour')
		self.switch_to_tab("gear", "stabilization", "bcd")
		assert self.get_table_field("gear", 2, 10) == "Non"
		self.add_item_servicing("stabilization", "bcd", 2, date=(dt.datetime.now() - requests.SERVICING_PERIODICITY), filename="polop.pdf")
		assert self.get_table_field("gear", 2, 10) == "Non"
		self.add_item_servicing("stabilization", "bcd", 2, date=(dt.datetime.now() - requests.SERVICING_PERIODICITY + timedelta(days=3)), filename="polop.png")
		assert self.get_table_field("gear", 2, 10) == "Oui"


class TestInventory(JellyfishFixtures):

	def test01a(self, start_app, users, many_items, start_driver):
		""" Do a first inventory campaign """
		self.login_as('gilmour')
		self.switch_to_tab("inventory")

		self.click_element_by_id("btn-start-campaign")

		# Another user will see that the inventory is started
		self.switch_to_browser_2()
		self.login_as('gilmour')
		self.switch_to_tab("inventory")
		# sleep(5)
		with pytest.raises(NoSuchElementException):
			self.click_element_by_id("btn-start-campaign")
		self.switch_to_browser_1()

		# Children items like second stages should not be offered
		assert self.get_select_choices('[name="remaining_items"') == [
			"Stab (2)",
			"Détendeur principal (1)",
			"Octopus (1)",
			"Combinaison (3)",
		]

		# BCDs are selected first
		assert self.get_table_field("current_remaining_items", 1, 1) == "1"
		assert self.get_table_field("current_remaining_items", 2, 1) == "2"
		with pytest.raises(IndexError):
			self.get_table_field("current_remaining_items", 3, 1)

		# Inventory the first BCD
		self.click_table_row("current_remaining_items", 1)
		self.fill_form({
			'is_present': True,
			'is_usable': False,
			'price': 37,
			'comment': "Fait",
		})
		sleep(3) # This is unstable
		assert self.get_select_choices('[name="remaining_items"')[0] == "Stab (1)"

		# Go to the regulators because I'm curious and come back to BCDs
		self.select("remaining_items", visible_text="Détendeur principal (1)")
		sleep(1)
		assert self.get_table_field("current_remaining_items", 1, 1) == "1"
		self.select("remaining_items", visible_text="Stab (1)")

		# Another user inventories the last BCD
		self.switch_to_browser_2()
		# He has to update the inventory page because it has been started by the first user in between
		self.switch_to_tab("inventory")
		assert self.get_table_field("current_remaining_items", 1, 1) == "2"
		self.click_table_row("current_remaining_items", 1)
		self.fill_form({
			'is_present': True,
			'is_usable': True,
			'price': 73,
			'comment': "Terminé pour les stabs :)",
		})

		# No more BCD to inventory -> next item type is auto selected
		sleep(1)
		assert self.get_select_choices('[name="remaining_items"')[0] == "Détendeur principal (1)"
		sleep(1)
		assert self.get_table_field("current_remaining_items", 1, 1) == "1"

		self.switch_to_browser_1()

		# Stop the campaign
		self.click_element_by_id("btn-stop-campaign")
		assert self.get_table_field("inventories", 1, 1) == date.today().strftime("%d/%m/%Y")

		# The "Start a new campaign" button should not be displayed because there is already one that has been opened today
		with pytest.raises(NoSuchElementException):
			self.click_element_by_id("btn-start-campaign")

		# Watch the state of today's campaign
		self.click_table_row("inventories", 1)
		self.click_modal_button("info")
		assert self.get_table_field("unusable_items", 1, 1) == "Stab 1"
		self.switch_to_tab("inventory")
		# sleep(20)

		# Restart today's campaign by the contextual menu
		self.click_table_row("inventories", 1)
		self.click_modal_button("restart", with_confirmation=True)

		# No more BCD to inventory -> next item type is auto selected again
		assert self.get_select_choices('[name="remaining_items"')[0] == "Détendeur principal (1)"
		sleep(1)
		assert self.get_table_field("current_remaining_items", 1, 1) == "1"
		# self.click_table_row("current_remaining_items", 1)

		# sleep(60)

	def test02a(self, start_app, users, many_items, start_driver):
		""" Redirection after editing item states """
		self.login_as('gilmour')
		self.switch_to_tab("inventory")

		# redirected to inventory tab when an inventory is being done
		self.click_element_by_id("btn-start-campaign")
		self.add_item_state("stabilization", "bcd", 1)
		assert self.get_table_field("current_remaining_items", 1, 1) == "2"

		# redirected to gear tab when no inventory running
		self.click_element_by_id("btn-stop-campaign")
		self.add_item_state("stabilization", "bcd", 2)
		assert self.get_table_field("gear", 1, 1) == "1"

	def test03a(self, start_app, users, members, many_items, start_driver):
		""" States lifecycle """
		self._is_loan_in_degraded_mode = False
		self.login_as('gilmour')
		self.assert_bcd1_available()

		# The item was unusable yesterday
		self.add_item_state("stabilization", "bcd", 1, is_usable=False, date=dt.datetime.now() - timedelta(days=1))
		self.assert_bcd1_unavailable()

		# Do an inventory, the item is now available
		self.switch_to_tab("inventory")
		self.click_element_by_id("btn-start-campaign")
		self.add_item_state("stabilization", "bcd", 1)
		sleep(1)
		assert self.get_table_field("current_remaining_items", 1, 1) == "2"
		self.click_element_by_id("btn-stop-campaign")
		self.assert_bcd1_available()

		# The item becomes unavailable after the inventory
		self.add_item_state("stabilization", "bcd", 1, is_usable=False, date=dt.datetime.now() + timedelta(days=1))
		assert self.get_table_field("gear", 1, 1) == "1"
		self.assert_bcd1_unavailable()


class TestStatistics(JellyfishFixtures):

	def borrow_items(self, items):
		self.login_as('gilmour')
		self.switch_to_tab("loan", "collection")
		self.click_element_by_id("degraded-mode-btn")
		sleep(1)
		self.select("reason", "4")
		self.select("member", visible_text="Morrison Jim")
		for item_type, nb in items:
			self.select("item_reference-parent", item_type)
			sleep(1)  # wait for child sync
			self.select("item_reference", visible_text=str(nb))
			sleep(.5)
			self.submit()
			sleep(5)

	def test01a(self, start_app, users, members, items, start_driver):
		""" Every loans table: currently borrowed items do not appear in the list """
		self.borrow_items((("suit", 1), ("bcd", 1), ("bcd", 2)))
		self.click_element_by_id("title")
		self.switch_to_tab("statistics")
		with pytest.raises(IndexError):
			self.get_table_field("loans", 1, 1)
		self.switch_to_tab("loan", "reintegration")
		sleep(.5)
		self.select('item', value=6)
		self.submit()
		sleep(1)
		self.click_element_by_id("title")
		self.switch_to_tab("statistics")
		assert self.get_table_field("loans", 1, 1) == "Stab"
		assert self.get_table_field("loans", 1, 2) == "1"
		assert self.get_table_field("loans", 1, 5) == "4"


class TestAdmin(JellyfishFixtures):

	def test01a(self, start_app, users, items, start_driver):
		""" Go to admin tools """
		self.login_as('gilmour')
		self.switch_to_tab("admin", "tools")


class TestWholeSite(JellyfishFixtures):

	def Xtest(self, start_app, users, start_driver):
		assert self.title == "La Méduse"

		self.login_as('gilmour')
		for member in MEMBERS.values():
			self.add_member(member)

		for item in ITEMS:
			self.add_item(item)

		self.switch_to_tab("gear", "stabilization", "bcd")
		self.click_gear_table_row_by_item_ref(1)
		self.click_modal_button("modify")
		self.input_text("serial_nb", 1234)
		self.input_text("size_letter_min", "L")
		self.submit()

		self.switch_to_tab("gear", "regulator")
		assert self.get_table_field("gear", 1, 6) == "AK47"
		# self.switch_to_tab("gear", "regulator", "second_stage")
		# assert self.get_table_field("gear", 0, 6) == "AK48"
