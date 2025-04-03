#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from logging import DEBUG
from os.path import dirname, join

from weblib.utils import get_config, log_init

log_init(__name__, level=DEBUG, directory=None)

_LOGGER = logging.getLogger(__name__)


CONFIG_FILEPATH = join(dirname(__file__), "..", "config.ini")
CONFIG_SECRETS = get_config(filepath=CONFIG_FILEPATH, section="secrets")
CONFIG_CUSTOMIZATION = get_config(filepath=CONFIG_FILEPATH, section="customization")

# app specific
CONFIG_REF_PREFIXES = get_config(filepath=CONFIG_FILEPATH, section="ref_prefixes")
CONFIG_QRCODE = get_config(filepath=CONFIG_FILEPATH, section="qrcode")


class InconsistentConfig(Exception):
	pass


if len(CONFIG_REF_PREFIXES) != len(set(CONFIG_REF_PREFIXES.values())):
	_LOGGER.error("Found duplicated ref_prefixes")
	raise InconsistentConfig()

