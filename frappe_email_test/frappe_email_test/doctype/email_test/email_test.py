# Copyright (c) 2026, Harish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmailTest(Document):
	def before_insert(self):
		if not self.recipient:
			settings = frappe.get_single("Email Tester Settings")
			if settings.default_recipient:
				self.recipient = settings.default_recipient

		if not self.status:
			self.status = "Draft"
