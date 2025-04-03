//
// Copyright 2021-2025, Johann Saunier
// SPDX-License-Identifier: AGPL-3.0-or-later
//
require.config({
	paths: {
		bootstrap:    "/static/weblib/script/external/bootstrap.bundle",
		domReady:     "/static/weblib/script/external/domReady",
		html5Qrcode:  "/static/weblib/script/external/html5-qrcode",
		log:          "/static/weblib/script/log",
		lib:          "/static/weblib/script/lib",
		dyn_table:    "/static/weblib/script/dyn_table",
		qrcodeReader: "/static/weblib/script/qrcode-reader",
		qrcode:       "/static/script/qrcode",
		loan:         "/static/script/loan"
	}
});


requirejs(['domReady', 'lib', 'dyn_table', 'loan'], function(domReady, lib, dyn_table, loan) {

	require(['domReady'], function(domReady) {
		domReady(function () {
			console.log("Document ready");
			lib.init();
			dyn_table.init();

			// Business logic
			loan.start();

			const elt = document.getElementsByName("remaining_items")[0];
			if (elt) {
				elt.addEventListener('change', (evt) => {
					const table = document.querySelector("table[name='current_remaining_items']");
					console.log("evt.target.value=" + evt.target.value);
					dyn_table.fetchDynTable("/inventory/current_remaining_items.table?item_type=" + evt.target.value, table);
				});
			}

		});
	});

});
