#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from copy import copy

from flask_babel import lazy_gettext as _l

ITEM_USAGE_MAX = 99999

ITEM_TYPE_FIRST_STAGE = "first_stage"
ITEM_TYPE_FIRST_STAGE_AUXILIARY = "first_stage_auxiliary"
ITEM_TYPE_SECOND_STAGE = "second_stage"
ITEM_TYPE_OCTOPUS = "octopus"
ITEM_TYPE_MANOMETER = "manometer"
ITEM_TYPE_TANK = "tank"
ITEM_TYPE_BCD = "bcd"
ITEM_TYPE_BACKPACK = "backpack"
ITEM_TYPE_SUIT = "suit"
ITEM_TYPE_HOOD = "hood"
ITEM_TYPE_BOOT = "boot"
ITEM_TYPE_SOCK = "sock"
ITEM_TYPE_GLOVE = "glove"
ITEM_TYPE_FIN = "fin"
ITEM_TYPE_MONOFIN = "monofin"
ITEM_TYPE_MASK = "mask"
ITEM_TYPE_SNORKLE = "snorkle"
ITEM_TYPE_COMPUTER = "computer"
ITEM_TYPE_LAMP = "lamp"
ITEM_TYPE_WEIGHT = "weight"
ITEM_TYPE_SUCKER = "sucker"
ITEM_TYPE_RING = "ring"
ITEM_TYPE_FRISBEE = "frisbee"
ITEM_TYPE_OXYMETER = "oxymeter"
ITEM_TYPE_PREMISES_KEY = "premises_key"


class GearStruct:

	def __init__(self, *groups):
		self.groups = groups

	def __getitem__(self, key):
		try:
			return [g for g in self.groups if g.name == key][0]
		except IndexError:
			raise KeyError("Unknown group '%s'" % key)

	def get_item_group(self, item_type):
		for group in self.groups:
			for item in group.items:
				if item.type == item_type:
					return group

	@property
	def borrowable_items(self):
		borrowable_items = []
		for group in self.groups:
			borrowable_items.extend(group.borrowable_items)
		return borrowable_items


class Group:

	def __init__(self, name, i18n, items):
		self.name = name
		self.i18n = i18n
		self.items = []
		for i in items:
			i.is_auxiliary = False
			self.items.append(i)
			if i.has_auxiliary:
				aux = copy(i)
				aux.is_auxiliary = True
				self.items.append(aux)

	def __getitem__(self, key):
		try:
			return [i for i in self.items if i.type == key][0]
		except IndexError:
			raise KeyError("Unknown item '%s'" % key)

	@property
	def borrowable_items(self):
		borrowable_items = []
		for item in self.items:
			if item.is_borrowable:
				borrowable_items.append(item)
		return borrowable_items

	def __str__(self):
		return ", ".join([str(i.tab_name) for i in self.items])

	def __repr__(self):
		return self.__str__()


class ItemStruct:

	def __init__(self, type, i18n, tab_name, is_composite=False, is_borrowable=True, has_auxiliary=False):
		self.type = type
		self.i18n = i18n
		self.tab_name = tab_name
		self.is_composite = is_composite
		self.is_borrowable = is_borrowable
		self.has_auxiliary = has_auxiliary


GEAR = GearStruct(
	Group('regulator', _l("Regulators"), (
		ItemStruct(ITEM_TYPE_FIRST_STAGE            , _l("Main regulator")      , _l("Main regulators")      , is_borrowable=True, has_auxiliary=False),
		ItemStruct(ITEM_TYPE_FIRST_STAGE_AUXILIARY  , _l("Auxiliary regulator") , _l("Auxiliary regulators") , is_borrowable=True, has_auxiliary=False),
		# ItemStruct(ITEM_TYPE_SECOND_STAGE        , _l("Second stage")        , _l("Second stages")        , is_borrowable=False, has_auxiliary=True),
		# ItemStruct(ITEM_TYPE_OCTOPUS             , _l("Octopus")             , _l("Octopus")              , is_borrowable=False, has_auxiliary=True),
		# ItemStruct(ITEM_TYPE_MANOMETER           , _l("Manometer")           , _l("Manometers")           , is_borrowable=False),
		# ~ ItemStruct(ITEM_TYPE_MAIN_REGULATOR      , _l("Main regulator")      , _l("Main regulators")      , is_composite=True),
		# ~ ItemStruct(ITEM_TYPE_AUXILIARY_REGULATOR , _l("Auxiliary regulator") , _l("Auxiliary regulators") , is_composite=True),
	)),
	Group('air_source', _l("Air source"), (
		ItemStruct(ITEM_TYPE_TANK           , _l("Tank")      , _l("Tanks")),
	)),
	Group('stabilization', _l("Stabilization"), (
		ItemStruct(ITEM_TYPE_BCD           , _l("BCD")      , _l("BCDs")),
		ItemStruct(ITEM_TYPE_BACKPACK      , _l("Backpack") , _l("Backpacks")),
	)),
	Group('wear', _l("Wear"), (
		ItemStruct(ITEM_TYPE_SUIT  , _l("Suit")  , _l("Suits")),
		ItemStruct(ITEM_TYPE_HOOD  , _l("Hood")  , _l("Hoods")),
		ItemStruct(ITEM_TYPE_GLOVE , _l("Glove") , _l("Gloves")),
		ItemStruct(ITEM_TYPE_BOOT  , _l("Boot")  , _l("Boots")),
		ItemStruct(ITEM_TYPE_SOCK  , _l("Sock")  , _l("Socks")),
	)),
	Group('snorkeling', _l("Snorkeling"), (
		ItemStruct(ITEM_TYPE_FIN           , _l("Fins")     , _l("Fins")),
		ItemStruct(ITEM_TYPE_MONOFIN       , _l("Monfins")  , _l("Monofins")),
		ItemStruct(ITEM_TYPE_MASK          , _l("Mask")     , _l("Masks")),
		ItemStruct(ITEM_TYPE_SNORKLE       , _l("Snorkle")  , _l("Snorkles")),
	)),
	Group('measure', _l("Measure"), (
		ItemStruct(ITEM_TYPE_COMPUTER      , _l("Computer") , _l("Computers")),
		ItemStruct(ITEM_TYPE_OXYMETER      , _l("Oxymeter") , _l("Oxymeters")),
	)),
	Group('accessory', _l("Accessories"), (
		ItemStruct(ITEM_TYPE_LAMP          , _l("Lamp")     , _l("Lamps")),
		ItemStruct(ITEM_TYPE_WEIGHT        , _l("Weight")   , _l("Weights")),
		ItemStruct(ITEM_TYPE_SUCKER        , _l("Sucker")   , _l("Suckers")),
		ItemStruct(ITEM_TYPE_RING          , _l("Ring")     , _l("Rings")),
		ItemStruct(ITEM_TYPE_FRISBEE       , _l("Frisbee")  , _l("Frisbees")),
		ItemStruct(ITEM_TYPE_PREMISES_KEY  , _l("Premises key")   , _l("Premises keys")),
	)),
)
