#
# Copyright 2021-2026, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from webapp.views.loan import get_scanned_code_content

CONFIG_QRCODE = {
	'item': r"https://gear.jellyfish.org/%s",
	'license': "https://l.ffessm.fr/c.asp?id=%%s_85648D",
}


def test01a():
	""" Found item """
	assert get_scanned_code_content("https://gear.jellyfish.org/M3", config_dict=CONFIG_QRCODE) == {
		'item_type': "mask",
		'item_reference': "3",
	}


def test01b():
	""" Found item (confusing) """
	assert get_scanned_code_content("https://gear.jellyfish.org/CG3", config_dict=CONFIG_QRCODE) == {
		'item_type': "hood",
		'item_reference': "3",
	}


def test02a():
	""" Found license """
	assert get_scanned_code_content("https://l.ffessm.fr/c.asp?id=1234567_85648D") == {
		'license_nb': "1234567",
	}
