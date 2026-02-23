import frappe


def after_install():
	if not frappe.db.exists("Email Tester Settings", "Email Tester Settings"):
		doc = frappe.new_doc("Email Tester Settings")
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
