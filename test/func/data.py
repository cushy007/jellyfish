#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from copy import copy

MEMBERS = {
	'mercury': {
		'last_name': "Mercury",
		'first_name': "Freddie",
		'license_nb': "658798",
		'has_guarantee': True,
	},
	'morisson': {
		'last_name': "Morrison",
		'first_name': "Jim",
		'license_nb': "789123",
		'has_guarantee': True,
	},
	'brown': {
		'last_name': "Brown",
		'first_name': "James",
		'license_nb': "123456",
		'has_guarantee': True,
	},
}


ITEMS = {
	("regulator", "first_stage", 1): {
		'reference': "1",
		'brand': "Aqualung",
		'model': "Legend",
		'is_cold_water': True,
		'serial_nb': "AK47",
		'fastening': "yoke",
	},

	("regulator", "first_stage_auxiliary", 1): {
		'reference': "1",
		'brand': "Aqualung",
		'model': "Titan LX",
		'is_cold_water': True,
		'serial_nb': "M16",
		'fastening': "din",
	},

	("wear", "suit", 1): {
		'reference': "1",
		'brand': "Cressi",
		'model': "Ice",
		# 'thickness': 7,
		'size_letter_min': "M",
		'size_letter_max': "M",
	},

	("wear", "suit", 2): {
		'reference': "2",
		'brand': "Mares",
		'model': "Pioneer",
		'gender': "f",
		'thickness': 5,
		'size_letter_min': "M",
		'size_letter_max': "M",
		'size_number_min': 3,
		'is_with_shorty': True,
	},

	("wear", "suit", 3): {
		'reference': "3",
		'brand': "Cressi",
		'model': "Medas",
		'gender': "f",
		'thickness': 5,
		'size_letter_min': "S",
		'size_letter_max': "M",
		'is_split_bottom_up': True,
	},

	("stabilization", "bcd", 1): {
		'reference': "1",
		'brand': "Aqualung",
		'model': "Black Diamond",
		'size_letter_min': "M",
	},

	("stabilization", "bcd", 2): {
		'reference': "2",
		'brand': "Mares",
		'model': "Quantum",
		'size_letter_min': "L",
	},
}

MANY_ITEMS = copy(ITEMS)
MANY_ITEMS.update({
	("regulator", "second_stage", 1): {
		'reference': "1",
		'brand': "Aqualung",
		'model': "Legend",
		'is_cold_water': True,
		'serial_nb': "AK48",
	},
	("regulator", "octopus", 1): {
		'reference': "1",
		'brand': "Aqualung",
		'model': "Legend OC",
		'is_cold_water': True,
		'serial_nb': "AK49",
	},
	("regulator", "manometer", 1): {
		'reference': "1",
		'brand': "Aqualung",
		'model': "AL50",
		'serial_nb': "AK50",
	},

	("regulator", "second_stage", 2): {
		'reference': "2",
		'brand': "Aqualung",
		'model': "Titan LX",
		'is_cold_water': True,
		'serial_nb': "M17",
	},
	("regulator", "octopus", 2): {
		'reference': "2",
		'brand': "Aqualung",
		'model': "Titan OC",
		'is_cold_water': True,
		'serial_nb': "M18",
	},
	("regulator", "manometer", 2): {
		'reference': "2",
		'brand': "Aqualung",
		'model': "AL50",
		'serial_nb': "M19",
	},

})
