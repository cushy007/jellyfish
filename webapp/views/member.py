#
# Copyright 2021-2026, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging

from flask import Blueprint
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_login import login_required
from weblib.roles import ROLE_USER, roles_required
from weblib.views import crud_page

from webapp.forms import MemberForm
from webapp.models import Member
from webapp.roles import ROLE_TREASURER

_LOGGER = logging.getLogger(__name__)


member_views = Blueprint('_views', __name__)


@member_views.before_request
@login_required
@roles_required(ROLE_USER, ROLE_TREASURER)
def before_request():
	pass


@member_views.route('/member')
@member_views.route('/member/<table_name>.table', methods=['GET'])
@member_views.route('/member/<table_name>/<crud_step>', methods=['GET', 'POST'])
def member(table_name=None, crud_step="read"):
	return crud_page(table_name, crud_step,
		page_title= _("Members"),
		tables={
			'member': {
				'model_factory': Member,
				'columns': (Member.last_name, Member.first_name, Member.license_nb, Member.has_guarantee, Member.guarantee_end_date),
				'order_by': Member.last_name,
				'form_factory': MemberForm,
				'row_title_builder': lambda row: f"{row[2]} {row[1]}",
			},
		}
	)

