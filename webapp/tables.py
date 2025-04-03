#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from webapp.items import (
	ITEM_TYPE_BACKPACK, ITEM_TYPE_BCD, ITEM_TYPE_BOOT, ITEM_TYPE_COMPUTER, ITEM_TYPE_FIN, ITEM_TYPE_FIRST_STAGE,
	ITEM_TYPE_FIRST_STAGE_AUXILIARY, ITEM_TYPE_FRISBEE, ITEM_TYPE_GLOVE, ITEM_TYPE_HOOD, ITEM_TYPE_LAMP,
	ITEM_TYPE_MANOMETER, ITEM_TYPE_MASK, ITEM_TYPE_MONOFIN, ITEM_TYPE_OCTOPUS, ITEM_TYPE_OXYMETER, ITEM_TYPE_PREMISES_KEY,
	ITEM_TYPE_RING, ITEM_TYPE_SECOND_STAGE, ITEM_TYPE_SNORKLE, ITEM_TYPE_SOCK, ITEM_TYPE_SUCKER, ITEM_TYPE_SUIT,
	ITEM_TYPE_TANK, ITEM_TYPE_WEIGHT
)
from webapp.models import Item

MANDATORY_ITEMS_COLUMNS = (Item.reference, Item.owner_club, Item.entry_date)
ITEMS_COLUMNS = {
	ITEM_TYPE_FIRST_STAGE            : (Item.brand, Item.model, Item.serial_nb, Item.is_cold_water, Item.is_nitrox, Item.fastening),
	ITEM_TYPE_FIRST_STAGE_AUXILIARY  : (Item.brand, Item.model, Item.serial_nb, Item.is_cold_water, Item.is_nitrox, Item.fastening),
	ITEM_TYPE_SECOND_STAGE           : (Item.brand, Item.model, Item.serial_nb, Item.is_cold_water, Item.is_nitrox),
	ITEM_TYPE_OCTOPUS                : (Item.brand, Item.model, Item.serial_nb, Item.is_cold_water, Item.is_nitrox),
	ITEM_TYPE_MANOMETER              : (Item.brand, Item.model, Item.serial_nb, Item.is_nitrox),
	ITEM_TYPE_TANK                   : (),
	ITEM_TYPE_BCD                    : (Item.brand, Item.model, Item.serial_nb, Item.size_letter_min),
	ITEM_TYPE_BACKPACK               : (),
	ITEM_TYPE_SUIT                   : (Item.brand, Item.model, Item.gender, Item.thickness, Item.size_letter_min, Item.size_letter_max, Item.size_number_min, Item.size_number_max, Item.is_semi_dry, Item.is_split_bottom_up, Item.is_with_shorty),
	ITEM_TYPE_HOOD                   : (Item.brand, Item.thickness, Item.size_letter_min),
	ITEM_TYPE_BOOT                   : (Item.brand, Item.thickness, Item.size_letter_min, Item.size_letter_max, Item.size_number_min, Item.size_number_max),
	ITEM_TYPE_SOCK                   : (Item.brand, Item.thickness, Item.size_letter_min, Item.size_letter_max, Item.size_number_min, Item.size_number_max),
	ITEM_TYPE_GLOVE                  : (Item.brand, Item.thickness, Item.size_letter_min),
	ITEM_TYPE_FIN                    : (Item.brand, Item.is_apnea, Item.size_letter_min, Item.size_letter_max, Item.size_number_min, Item.size_number_max),
	ITEM_TYPE_MONOFIN                : (Item.brand, Item.size_letter_min, Item.size_letter_max, Item.size_number_min, Item.size_number_max),
	ITEM_TYPE_MASK                   : (Item.brand, Item.size_age),
	ITEM_TYPE_SNORKLE                : (Item.brand, ),
	ITEM_TYPE_COMPUTER               : (Item.brand, Item.model, Item.serial_nb),
	ITEM_TYPE_LAMP                   : (Item.brand, Item.model),
	ITEM_TYPE_WEIGHT                 : (Item.weight, ),
	ITEM_TYPE_SUCKER                 : (),
	ITEM_TYPE_RING                   : (),
	ITEM_TYPE_FRISBEE                : (),
	ITEM_TYPE_OXYMETER               : (Item.brand, Item.model),
	ITEM_TYPE_PREMISES_KEY           : (),
}
