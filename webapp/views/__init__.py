#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from webapp.views.admin import admin_views
from webapp.views.gear import gear_views
from webapp.views.inventory import inventory_views
from webapp.views.loan import loan_views
from webapp.views.main import main_views
from webapp.views.member import member_views

all_views = (main_views, gear_views, inventory_views, loan_views, member_views, admin_views)
