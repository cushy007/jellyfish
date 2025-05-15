#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging

from flask_babel import lazy_gettext as _l
from peewee import (
	SQL, BooleanField, CharField, DateField, DateTimeField, DecimalField, ForeignKeyField, IntegerField, TextField
)
from weblib.database import AbstractMigrator
from weblib.models import BaseModel, FileField, MigratorException, PriceField, User, flask_db

from webapp.items import (
	ITEM_TYPE_BACKPACK, ITEM_TYPE_BCD, ITEM_TYPE_BOOT, ITEM_TYPE_COMPUTER, ITEM_TYPE_FIN, ITEM_TYPE_FIRST_STAGE,
	ITEM_TYPE_FIRST_STAGE_AUXILIARY, ITEM_TYPE_FRISBEE, ITEM_TYPE_GLOVE, ITEM_TYPE_HOOD, ITEM_TYPE_LAMP,
	ITEM_TYPE_MANOMETER, ITEM_TYPE_MASK, ITEM_TYPE_MONOFIN, ITEM_TYPE_OCTOPUS, ITEM_TYPE_OXYMETER, ITEM_TYPE_PREMISES_KEY,
	ITEM_TYPE_RING, ITEM_TYPE_SECOND_STAGE, ITEM_TYPE_SNORKLE, ITEM_TYPE_SOCK, ITEM_TYPE_SUCKER, ITEM_TYPE_SUIT,
	ITEM_TYPE_TANK, ITEM_TYPE_WEIGHT
)

_LOGGER = logging.getLogger(__name__)

ITEM_FASTENING_YOKE = "yoke"
ITEM_FASTENING_DIN = "din"

ITEM_GENDER_MALE = "m"
ITEM_GENDER_FEMALE = "f"

ITEM_SIZE_AGE_ADULT = "adult"
ITEM_SIZE_AGE_CHILD = "child"


class Item(BaseModel):
	type = TextField()
	type.i18n = _l("Type")
	type.lut = {
		ITEM_TYPE_FIRST_STAGE: _l("Main regulator"),
		ITEM_TYPE_FIRST_STAGE_AUXILIARY: _l("Auxiliary regulator"),
		ITEM_TYPE_SECOND_STAGE: _l("Second stage"),
		ITEM_TYPE_OCTOPUS: _l("Octopus"),
		ITEM_TYPE_MANOMETER: _l("Manometer"),
		ITEM_TYPE_TANK: _l("Tank"),
		ITEM_TYPE_BCD: _l("Bcd"),
		ITEM_TYPE_BACKPACK: _l("Backpack"),
		ITEM_TYPE_SUIT: _l("Suit"),
		ITEM_TYPE_HOOD: _l("Hood"),
		ITEM_TYPE_BOOT: _l("Boot"),
		ITEM_TYPE_SOCK: _l("Sock"),
		ITEM_TYPE_GLOVE: _l("Glove"),
		ITEM_TYPE_FIN: _l("Fin"),
		ITEM_TYPE_MONOFIN: _l("Monofin"),
		ITEM_TYPE_MASK: _l("Mask"),
		ITEM_TYPE_SNORKLE: _l("Snorkle"),
		ITEM_TYPE_COMPUTER: _l("Computer"),
		ITEM_TYPE_LAMP: _l("Lamp"),
		ITEM_TYPE_WEIGHT: _l("Weight"),
		ITEM_TYPE_SUCKER: _l("Sucker"),
		ITEM_TYPE_RING: _l("Ring"),
		ITEM_TYPE_FRISBEE: _l("Frisbee"),
		ITEM_TYPE_OXYMETER: _l("Oxymeter"),
		ITEM_TYPE_PREMISES_KEY: _l("Premises key"),
	}

	is_auxiliary = BooleanField(default=False)  # TODO remove totally
	is_auxiliary.i18n = _l("Auxiliary")

	reference = IntegerField()
	reference.i18n = _l("Reference")

	owner_club = TextField()
	owner_club.i18n = _l("Owner club")

	entry_date = DateField(null=True)
	entry_date.i18n = _l("Entry date")

	brand = TextField(null=True)
	brand.i18n = _l("Brand")

	model = TextField(null=True)
	model.i18n = _l("Model")

	serial_nb = TextField(null=True)
	serial_nb.i18n = _l("Serial number")

	gender = CharField(null=True)
	gender.i18n = _l("Gender")
	gender.lut = {
		ITEM_GENDER_MALE: _l("Man"),
		ITEM_GENDER_FEMALE: _l("Woman"),
	}

	size_number_min = IntegerField(null=True)
	size_number_min.i18n = _l("Minimum size")
	size_number_max = IntegerField(null=True)
	size_number_max.i18n = _l("Maximum size")
	size_letter_min = TextField(null=True)
	size_letter_min.i18n = _l("Minimum American size")
	size_letter_max = TextField(null=True)
	size_letter_max.i18n = _l("Maximum American size")
	size_age = TextField(null=True)
	size_age.i18n = _l("Size")
	size_age.lut = {
		ITEM_SIZE_AGE_ADULT: _l("Adult"),
		ITEM_SIZE_AGE_CHILD: _l("Child"),
	}

	is_cold_water = BooleanField(null=True)
	is_cold_water.i18n = _l("Cold water compliant")

	is_nitrox = BooleanField(null=True)
	is_nitrox.i18n = _l("Nitrox compliant")

	fastening = TextField(null=True)  # DIN / etrier...
	fastening.i18n = _l("Fastening")
	fastening.lut = {
		ITEM_FASTENING_YOKE: _l("Yoke"),
		ITEM_FASTENING_DIN: _l("DIN"),
	}

	is_apnea = BooleanField(null=True)
	is_apnea.i18n = _l("For apnea")

	material = TextField(null=True)
	material.i18n = _l("Material")
	weight = IntegerField(null=True)  # g
	weight.i18n = _l("Weight")
	thickness = DecimalField(null=True, decimal_places=1)  # mm
	thickness.i18n = _l("Thickness")
	pressure = IntegerField(null=True)  # Bar
	pressure.i18n = _l("Pressure")

	is_semi_dry = BooleanField(null=True)
	is_semi_dry.i18n = _l("Semi-dry")
	is_split_bottom_up = BooleanField(null=True)
	is_split_bottom_up.i18n = _l("Split bottom / up")
	is_with_shorty = BooleanField(null=True)
	is_with_shorty.i18n = _l("With shorty")

	usage_counter = IntegerField(default=0)
	is_servicing = BooleanField(default=False)
	is_repairing = BooleanField(default=False)
	is_trashed = BooleanField(default=False)

	class Meta:
		constraints = [SQL('UNIQUE (type, reference, serial_nb)')]


class IsComposedOf(BaseModel):
	parent = ForeignKeyField(Item)
	child = ForeignKeyField(Item)
	at_date = DateField()


class Inventory(BaseModel):
	date = DateField(unique=True)
	date.i18n = _l("Date")
	in_progress = BooleanField(default=True)
	in_progress.i18n = _l("In progress")


class Club(BaseModel):
	name = TextField()


class BelongToClub(BaseModel):
	item = ForeignKeyField(Item, backref="items")
	club = ForeignKeyField(Club, backref="clubs")
	at_date = DateField()


class Member(BaseModel):
	last_name = TextField()
	last_name.i18n = _l("Last name")
	first_name = TextField()
	first_name.i18n = _l("First name")
	license_nb = TextField(null=True)
	license_nb.i18n = _l("License number")
	has_guarantee = BooleanField(default=False)
	has_guarantee.i18n = _l("Guarantee")
	guarantee_end_date = DateField(null=True)
	guarantee_end_date.i18n = _l("Valid until")

	class Meta:
		constraints = [SQL('UNIQUE (last_name, first_name)')]


class Servicing(BaseModel):
	item_id = ForeignKeyField(Item, backref="items")
	date = DateField(null=False)
	date.i18n = _l("Servicing date")
	report_file = FileField(null=False)
	report_file.i18n = _l("Report file")


class ItemState(BaseModel):
	item_id = ForeignKeyField(Item, backref="items")
	date = DateField()
	date.i18n = _l("Date")
	is_present = BooleanField()
	is_present.i18n = _l("Is present")
	is_usable = BooleanField()
	is_usable.i18n = _l("Is usable")
	price =  PriceField(null=True)
	price.i18n = _l("Price")
	comment = TextField(null=True)
	comment.i18n = _l("Comment")

	class Meta:
		constraints = [SQL('UNIQUE (item_id, date)')]


class Borrow(BaseModel):
	item = ForeignKeyField(Item, backref="items")
	user = ForeignKeyField(User, backref="users", null=True)
	member = ForeignKeyField(Member, backref="members", null=True)
	from_datetime = DateTimeField()
	from_datetime.i18n = _l("From date")
	from_datetime.display_date_only = True
	to_datetime = DateTimeField(null=True)
	to_datetime.i18n = _l("To date")
	to_datetime.display_date_only = True
	usage_counter = IntegerField(null=True)
	usage_counter.i18n = _l("Usage counter")


# ~class BelongToMember(BaseModel):
	# ~item = ForeignKeyField(Item, backref="items")
	# ~member = ForeignKeyField(Member, backref="members")
	# ~at_date = DateField()


# ~class Location(BaseModel):
	# ~place = TextField()


# ~class LocatedAt(BaseModel):
	# ~item = ForeignKeyField(Item, backref="items")
	# ~location = ForeignKeyField(Location, backref="locations")
	# ~at_date = DateField()


# ~class Repairs(BaseModel):
	# ~item = ForeignKeyField(Item, backref="items")
	# ~member = ForeignKeyField(Member, backref="members")
	# ~date = DateField()
	# ~comment = TextField()


MODELS = [
	Item,
	IsComposedOf,
	Inventory,
	Club,
	BelongToClub,
	Member,
	# ~BelongToMember,
	Borrow,
	# ~Location,
	# ~LocatedAt,
	ItemState,
	Servicing,
	# ~Repairs,
]


VERSION = 12

class Migrator(AbstractMigrator):
	"""
	https://docs.peewee-orm.com/en/latest/peewee/playhouse.html#migrate

	"""

	def migrate_to_version_2(self):
		_LOGGER.warning("Will migrate items types of auxiliary first stages")
		query = Item.update(type=ITEM_TYPE_FIRST_STAGE_AUXILIARY).where(
				(Item.type == ITEM_TYPE_FIRST_STAGE)
				& (Item.is_auxiliary == True)
			)
		query.execute()
		user = User(id=1)
		user.roles = "admin,user"
		user.save()

	def migrate_to_version_3(self):
		self._migrate(
			self._migrator.drop_index('borrow', 'borrow_item_id'),
			self._migrator.add_index('borrow', ('item_id', )),
			self._migrator.drop_not_null('borrow', 'user_id'),
			self._migrator.drop_not_null('borrow', 'member_id'),
			self._migrator.rename_column('borrow', 'at_date', 'from_datetime'),
			self._migrator.alter_column_type('borrow', 'from_datetime', DateTimeField()),
			self._migrator.add_column('borrow', 'to_datetime', DateTimeField(null=True)),
		)

	def migrate_to_version_4(self):
		self._migrate(
			self._migrator.add_column('borrow', 'usage_counter', IntegerField(null=True)),
		)

	def migrate_to_version_5(self):
		self._migrate(
			self._migrator.add_column('item', 'is_trashed', BooleanField(default=False)),
			self._migrator.drop_constraint('item', 'item_type_reference_is_auxiliary_key'),
			self._migrator.add_constraint('item', 'item_type_reference_serial_nb_key', SQL('UNIQUE (type, reference, serial_nb)')),
		)

	def migrate_to_version_6(self):
		self._migrate(
			self._migrator.rename_table('inventory', 'itemstate'),
			self._migrator.add_constraint('itemstate', 'itemstate_item_id_date_key', SQL('UNIQUE (item_id, date)')),
		)

	def migrate_to_version_7(self):
		self._db.create_tables((Inventory, ))

	def migrate_to_version_8(self):
		self._migrate(
			self._migrator.add_column('member', 'guarantee_end_date', DateField(null=True)),
		)

	def migrate_to_version_9(self):
		self._migrate(
			self._migrator.drop_column('servicing', 'member_id'),
			self._migrator.drop_column('servicing', 'comment'),
			self._migrator.add_column('servicing', 'report_file', TextField(null=False, default="")),
		)

	def migrate_to_version_10(self):
		self._migrate(
			self._migrator.drop_column('item', 'price'),
			self._migrator.alter_column_type('itemstate', 'price', DecimalField(null=True, decimal_places=2)),
		)
		for itemstate in ItemState.select():
			if itemstate.price:
				decimal_price = itemstate.price / 100
				_LOGGER.info("Migrating item state price value '%s' -> '%s'", itemstate.price, decimal_price)
				query = ItemState.update({'price': decimal_price}).where(ItemState.id == itemstate.id)
				if query.execute() != 1:
					raise MigratorException("Could not upgrade item state's price")

	def migrate_to_version_11(self):
		for itemstate in ItemState.select():
			if itemstate.price:
				decimal_price = itemstate.price * 100
				_LOGGER.info("Migrating item state price value '%s' -> '%s'", itemstate.price, decimal_price)
				query = ItemState.update({'price': decimal_price}).where(ItemState.id == itemstate.id)
				if query.execute() != 1:
					raise MigratorException("Could not upgrade item state's price")

	def migrate_to_version_12(self):
		self._migrate(
			self._migrator.add_constraint('member', 'member_last_name_first_name_key', SQL('UNIQUE (last_name, first_name)')),
		)
