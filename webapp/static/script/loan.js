//
// Copyright 2021-2026, Johann Saunier
// SPDX-License-Identifier: AGPL-3.0-or-later
//
define(['lib', 'qrcodeReader'], function(lib, qrcodeReader) {

	function sendForm(scannedText) {
		let data = new FormData(document.querySelector("form"));
		data.append("scanned_text", scannedText ? scannedText : "");
		console.log("[loan] sendForm data:");
		console.log(data);

		lib.fetchPost(window.location.pathname + "/collect.json", data, (data) => {
			console.log("[loan] sendForm received data:");
			console.log(data);
			let qrcodeReaderElt = document.getElementById("barcode-reader-field");

			let item_reference = document.querySelector("[name=item_reference]");
			console.log(item_reference);
			let submitor = document.querySelector("[type=submit]");;
			if (submitor) {
				submitor.classList.add("hidden");
				submitor.classList.remove("shown");
			}
			if (! item_reference) {
				qrcodeReaderElt.classList.remove("shown");
				qrcodeReaderElt.classList.add("hidden");
				submitor = document.getElementById("barcode-reader-field");
			}

			let popupElt = document.getElementById("borrow-popup");
			popupElt.innerHTML = data.message;
			popupElt.classList.remove("alert-success");
			popupElt.classList.remove("alert-danger");
			popupElt.classList.add(data.success ? "alert-success" : "alert-danger");
			popupElt.classList.remove("hidden");
			popupElt.classList.add("shown");

			setTimeout(() => {
				if (qrcodeReaderElt == undefined) {
					window.location = "/loan/collection";
				} else {
					popupElt.innerHTML = "";
					popupElt.classList.remove("shown");
					popupElt.classList.add("hidden");

					qrcodeReaderElt.classList.remove("hidden");
					qrcodeReaderElt.classList.add("shown");

					if (submitor) {
						submitor.classList.remove("hidden");
						submitor.classList.add("shown");
					}
				}
			}, data.timeout * 1000);
		});
	}

	function onSubmit(event) {
		event.preventDefault();
		sendForm();
	}

	function onDegradedModeToggled(event) {
		window.location = "/loan/collection?use_scanner=toggle";
	}

	function start() {
		console.log("[loan] start");

		let memberElt = document.getElementsByName("member")[0]
		if (memberElt) {
			memberElt.addEventListener('change', (evt) => {
				console.log("Trigger QR code reading...");
				qrcodeReader.startQrcodeScan("barcode-reader-field", (decodedText) => {
					console.log(`QR Code read: ${decodedText}`);
					sendForm(decodedText);
				});
			});
		}

		if (document.getElementById("degraded-mode-btn")) {
			const button = document.getElementById('loan-submit');
			try {
				document.querySelector("[type=submit]").addEventListener('click', onSubmit);
				console.log("Binding click event of loan-submit");
			} catch {
				console.log("No loan-submit element");
			}
			document.getElementById("degraded-mode-btn").addEventListener('click', onDegradedModeToggled);
			for (let btn of document.querySelectorAll(".fake-qrcode-btn")) {
				btn.addEventListener('click', (event) => {sendForm(btn.innerHTML); });
			}
		}

	}

	return {
		start: start,
		sendForm: sendForm,
	}

});
