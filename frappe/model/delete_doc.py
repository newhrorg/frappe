# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import frappe
import frappe.model.meta
import frappe.defaults
from frappe.utils.file_manager import remove_all
from frappe import _

def delete_doc(doctype=None, name=None, force=0, ignore_doctypes=None, for_reload=False, ignore_permissions=False):
	"""
		Deletes a doc(dt, dn) and validates if it is not submitted and not linked in a live record
	"""
	if not ignore_doctypes: ignore_doctypes = []

	# get from form
	if not doctype:
		doctype = frappe.form_dict.get('dt')
		name = frappe.form_dict.get('dn')

	if not doctype:
		frappe.msgprint(_('Nothing to delete'), raise_exception =1)

	# already deleted..?
	if not frappe.db.exists(doctype, name):
		return

	if doctype=="DocType":
		if not for_reload:
			frappe.db.sql("delete from `tabCustom Field` where dt = %s", name)
			frappe.db.sql("delete from `tabCustom Script` where dt = %s", name)
			frappe.db.sql("delete from `tabProperty Setter` where doc_type = %s", name)
			frappe.db.sql("delete from `tabReport` where ref_doctype=%s", name)

		delete_from_table(doctype, name, ignore_doctypes, None)

	else:
		doc = frappe.get_doc(doctype, name)

		if not for_reload:
			check_permission_and_not_submitted(doc, ignore_permissions)
			doc.run_method("on_trash")
			# check if links exist
			if not force:
				check_if_doc_is_linked(doc)

		delete_from_table(doctype, name, ignore_doctypes, doc)

	# delete attachments
	remove_all(doctype, name)

	# delete user_permissions
	frappe.defaults.clear_default(parenttype="User Permission", key=doctype, value=name)

	return 'okay'

def delete_from_table(doctype, name, ignore_doctypes, doc):
	if doctype!="DocType" and doctype==name:
		frappe.db.sql("delete from `tabSingles` where doctype=%s", name)
	else:
		frappe.db.sql("delete from `tab%s` where name=%s" % (doctype, "%s"), (name,))

	# get child tables
	if doc:
		tables = [d.options for d in doc.meta.get_table_fields()]

	else:
		def get_table_fields(field_doctype):
			return frappe.db.sql_list("""select options from `tab{}` where fieldtype='Table'
				and parent=%s""".format(field_doctype), doctype)

		tables = get_table_fields("DocField") + get_table_fields("Custom Field")

	# delete from child tables
	for t in tables:
		if t not in ignore_doctypes:
			frappe.db.sql("delete from `tab%s` where parent = %s" % (t, '%s'), (name,))

def check_permission_and_not_submitted(doc, ignore_permissions=False):
	# permission
	if not ignore_permissions and frappe.session.user!="Administrator" and not doc.has_permission("delete"):
		frappe.msgprint(_("User not allowed to delete."), raise_exception=True)

	# check if submitted
	if doc.docstatus == 1:
		frappe.msgprint(_("Submitted Record cannot be deleted")+": "+doc.name+"("+doc.doctype+")",
			raise_exception=True)

def check_if_doc_is_linked(doc, method="Delete"):
	"""
		Raises excption if the given doc(dt, dn) is linked in another record.
	"""
	from frappe.model.rename_doc import get_link_fields
	link_fields = get_link_fields(doc.doctype)
	link_fields = [[lf['parent'], lf['fieldname'], lf['issingle']] for lf in link_fields]

	for link_dt, link_field, issingle in link_fields:
		if not issingle:
			item = frappe.db.get_value(link_dt, {link_field:doc.name},
				["name", "parent", "parenttype", "docstatus"], as_dict=True)

			if item and item.parent != doc.name and ((method=="Delete" and item.docstatus<2) or
					(method=="Cancel" and item.docstatus==1)):
				frappe.throw(_("Cannot delete or cancel because {0} {1} is linked with {2} {3}").format(doc.doctype,
					doc.name, item.parent or item.name, item.parenttype if item.parent else link_dt),
					frappe.LinkExistsError)
