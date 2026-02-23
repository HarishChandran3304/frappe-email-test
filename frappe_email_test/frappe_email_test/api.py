# Copyright (c) 2026, Harish and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def extract_template_variables(template_name):
	"""Extract undeclared Jinja2 variables from an Email Template."""
	from jinja2 import Environment, meta

	template_doc = frappe.get_doc("Email Template", template_name)
	env = Environment()

	variables = set()
	for attr in ("subject", "response_html", "response"):
		text = getattr(template_doc, attr, None) or ""
		if text:
			try:
				ast = env.parse(text)
				variables |= meta.find_undeclared_variables(ast)
			except Exception:
				pass

	return {var: "" for var in sorted(variables)}


@frappe.whitelist()
def generate_ai_args(template_name, current_args):
	"""Use OpenRouter to generate realistic placeholder values for template variables."""
	import requests

	settings = frappe.get_single("Email Tester Settings")
	api_key = settings.get_password("openrouter_api_key") if settings.openrouter_api_key else None

	if not api_key:
		return {"success": False, "error": _("OpenRouter API key not configured in Email Tester Settings.")}

	model = settings.ai_model or "openai/gpt-4o-mini"

	try:
		template_doc = frappe.get_doc("Email Template", template_name)
		subject = template_doc.subject or ""
		body = template_doc.response_html or template_doc.response or ""

		try:
			args_dict = json.loads(current_args) if current_args else {}
		except json.JSONDecodeError:
			args_dict = {}

		variable_names = list(args_dict.keys())

		prompt = f"""You are helping a developer test a Jinja2 email template.

--- SUBJECT TEMPLATE ---
{subject}

--- BODY TEMPLATE ---
{body}

--- VARIABLES TO FILL ---
{json.dumps(variable_names)}

Read the full template above carefully, then return a JSON object with realistic placeholder values for every variable.
Rules:
- Use the correct JSON type inferred from how the variable is used (e.g. if the template does `var > 0`, the value must be a number, not a string).
- Values should be realistic for the context (names, amounts, dates, etc.).
- Return ONLY the raw JSON object — no explanation, no markdown, no code fences."""

		response = requests.post(
			"https://openrouter.ai/api/v1/chat/completions",
			headers={
				"Authorization": f"Bearer {api_key}",
				"Content-Type": "application/json",
			},
			json={
				"model": model,
				"max_tokens": 1024,
				"messages": [{"role": "user", "content": prompt}],
			},
			timeout=30,
		)
		response.raise_for_status()

		raw = response.json()["choices"][0]["message"]["content"].strip()
		# Strip markdown code fences if present
		if raw.startswith("```"):
			raw = raw.split("```")[1]
			if raw.startswith("json"):
				raw = raw[4:]
		raw = raw.strip()

		ai_args = json.loads(raw)

		# Backfill any missing keys from the original args dict
		for key in args_dict:
			if key not in ai_args:
				ai_args[key] = args_dict[key]

		return {"success": True, "args": ai_args}

	except json.JSONDecodeError as e:
		return {"success": False, "error": _("AI returned invalid JSON: {0}").format(str(e))}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Email Tester: AI Fill Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_test_email(doc_name):
	"""Render and send the test email via the configured Email Account."""
	try:
		doc = frappe.get_doc("Email Test", doc_name)
		settings = frappe.get_single("Email Tester Settings")

		try:
			args_dict = json.loads(doc.template_args) if doc.template_args else {}
		except json.JSONDecodeError:
			args_dict = {}

		template_doc = frappe.get_doc("Email Template", doc.email_template)
		rendered = template_doc.get_formatted_email(args_dict)
		subject = rendered.get("subject", "")
		message = rendered.get("message", "")

		sender = None
		if settings.email_account:
			email_account = frappe.get_doc("Email Account", settings.email_account)
			sender = email_account.email_id

		frappe.sendmail(
			recipients=[doc.recipient],
			sender=sender,
			subject=subject,
			message=message,
			now=True,
			reference_doctype="Email Test",
			reference_name=doc_name,
		)

		doc.db_set({"status": "Sent", "sent_at": now_datetime()})

		return {"success": True}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Email Tester: Send Error")
		try:
			frappe.db.set_value("Email Test", doc_name, "status", "Failed")
		except Exception:
			pass
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def reset_and_resend(doc_name):
	"""Reset a Failed email back to Draft and resend it."""
	try:
		frappe.db.set_value("Email Test", doc_name, "status", "Draft")
		return send_test_email(doc_name)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Email Tester: Resend Error")
		return {"success": False, "error": str(e)}
