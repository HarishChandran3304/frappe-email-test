// Copyright (c) 2026, Harish and contributors
// For license information, please see license.txt

frappe.ui.form.on("Email Test", {
	refresh(frm) {
		frm._adding_buttons = true;
		add_form_buttons(frm);
		frm._adding_buttons = false;
	},

	email_template(frm) {
		if (frm.doc.email_template) {
			extract_variables(frm);
		}
	},
});

function add_form_buttons(frm) {
	// Extract Variables (Tools menu)
	if (frm.doc.email_template) {
		frm.add_custom_button(__("Extract Variables"), () => extract_variables(frm), __("Tools"));

		// Fill with AI (Tools menu)
		frm.add_custom_button(__("Fill with AI"), () => fill_with_ai(frm), __("Tools"));
	}

	// Send Test Email (top bar, primary) — Draft only
	if (!frm.is_new() && frm.doc.status === "Draft") {
		frm.add_custom_button(__("Send Test Email"), () => send_email(frm)).addClass(
			"btn-primary"
		);
	}

	// Resend (top bar, warning) — Failed only
	if (!frm.is_new() && frm.doc.status === "Failed") {
		frm.add_custom_button(__("Resend"), () => resend_email(frm)).addClass("btn-warning");
	}
}

function extract_variables(frm) {
	frappe.call({
		method: "frappe_email_test.frappe_email_test.api.extract_template_variables",
		args: { template_name: frm.doc.email_template },
		callback(r) {
			if (r.message) {
				frm.set_value("template_args", JSON.stringify(r.message, null, 2));
			}
		},
	});
}

function fill_with_ai(frm) {
	frappe.call({
		method: "frappe_email_test.frappe_email_test.api.generate_ai_args",
		args: {
			template_name: frm.doc.email_template,
			current_args: frm.doc.template_args || "{}",
		},
		freeze: true,
		freeze_message: __("Generating with AI..."),
		callback(r) {
			if (r.message && r.message.success) {
				frm.set_value("template_args", JSON.stringify(r.message.args, null, 2));
			} else if (r.message && !r.message.success) {
				frappe.msgprint({
					title: __("AI Error"),
					message: r.message.error,
					indicator: "red",
				});
			}
		},
	});
}

function do_send(frm) {
	frappe.call({
		method: "frappe_email_test.frappe_email_test.api.send_test_email",
		args: { doc_name: frm.doc.name },
		freeze: true,
		freeze_message: __("Sending email..."),
		callback(r) {
			if (r.message && r.message.success) {
				frappe.show_alert(
					{ message: __("Email sent successfully!"), indicator: "green" },
					5
				);
				frm.reload_doc();
			} else if (r.message && !r.message.success) {
				frappe.msgprint({
					title: __("Send Failed"),
					message: r.message.error,
					indicator: "red",
				});
				frm.reload_doc();
			}
		},
	});
}

function send_email(frm) {
	frappe.confirm(__("Send test email to <b>{0}</b>?", [frm.doc.recipient]), () => {
		if (frm.is_dirty()) {
			frm.save().then(() => do_send(frm));
		} else {
			do_send(frm);
		}
	});
}

function resend_email(frm) {
	frappe.confirm(__("Resend test email to <b>{0}</b>?", [frm.doc.recipient]), () => {
		frappe.call({
			method: "frappe_email_test.frappe_email_test.api.reset_and_resend",
			args: { doc_name: frm.doc.name },
			freeze: true,
			freeze_message: __("Resending email..."),
			callback(r) {
				if (r.message && r.message.success) {
					frappe.show_alert(
						{ message: __("Email resent successfully!"), indicator: "green" },
						5
					);
					frm.reload_doc();
				} else if (r.message && !r.message.success) {
					frappe.msgprint({
						title: __("Resend Failed"),
						message: r.message.error,
						indicator: "red",
					});
					frm.reload_doc();
				}
			},
		});
	});
}
