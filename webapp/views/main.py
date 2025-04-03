#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from datetime import datetime

from flask import Blueprint, jsonify, redirect, request, url_for
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_login import login_required
from weblib.roles import ROLE_USER, roles_required
from weblib.table import Table
from weblib.views import Tab, site

from webapp.forms import ServicingForm
from webapp.requests import (
	create_servicing, get_every_loans, get_items_in_servicing, get_items_to_service, get_loans, get_members_fullnames,
	unservice
)

_LOGGER = logging.getLogger(__name__)


main_views = Blueprint('main_views', __name__, template_folder="templates", static_folder="static")


@main_views.before_request
@login_required
def before_request():
	pass


TABS = {
	'overview': Tab('overview', _l("Overview")),
	'gear': Tab('gear', _l("Gear")),
	'loan': Tab('loan', _l("Loans"), {
		'collection': Tab('collection', _l("Collect")),
		'reintegration': Tab('reintegration', _l("Reintegrate")),
	}),
	'inventory': Tab('inventory', _l("Inventories"), {
	}),
	'member': Tab('member', _l("Members")),
	'statistics': Tab('statistics', _l("Statistics")),
	'admin': Tab('admin', _l("Admin"), {
		'tools': Tab('tools', _l("Tools")),
		'qrcode': Tab('qrcode', _l("QRCodes")),
	}),
}


site.set_tabs(TABS)


@main_views.route('/')
def index():
	return redirect(url_for(".overview"))


@main_views.route('/overview')
def overview():
	return site.render_page(
		items_to_service=get_items_to_service(),
		in_servicing=get_items_in_servicing(),
	)


@main_views.route('/overview/loans.table')
def overview_loans_table():
	table = Table("loans")
	table.build_from_request(get_loans())
	return jsonify(table.dict)


@main_views.route('/statistics')
def statistics():
	return site.render_page()


@main_views.route('/statistics/loans.table')
def statistics_loans_table():
	table = Table("loans", title=_l("Every loans"))
	table.build_from_request(get_every_loans())
	return jsonify(table.dict)


@main_views.route('/servicing/add', methods=['GET', 'POST'])
@roles_required(ROLE_USER)
def servicing_add():
	form = ServicingForm()
	form.member.choices = get_members_fullnames()
	if request.method == 'POST':
		if form.validate():
			_LOGGER.info("Add a servicing for item '%s' to the database", form.item_id.data)
			create_servicing(
				item=form.item_id.data,
				member=form.member.data,
				date=form.date.data,
				comment=form.comment.data,
			)
			unservice(form.item_id.data)
			return redirect(url_for('.overview'))
	else:
		form.item_id.data = request.args['id']
		form.date.data = datetime.now()
		return site.render_page(html_template="servicing_form.html",
			active_tab='overview',
			form=form,
		)
