app_name = "omnexa_hr"
app_title = "ErpGenEx — HR"
app_publisher = "ErpGenEx"
app_description = "HR management free core app"
app_email = "dev@erpgenex.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["omnexa_core", "omnexa_accounting"]

add_to_apps_screen = [
	{
		"name": "omnexa_hr",
		"logo": "/assets/omnexa_hr/logo.png",
		"title": "HR",
		"route": "/app/hr-workcenter",
		"has_permission": "omnexa_hr.omnexa_hr.api.permission.has_app_permission",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	"/assets/omnexa_hr/css/employee_directory.css",
	"/assets/omnexa_hr/css/hr_desk.css",
]
app_include_js = "/assets/omnexa_hr/js/employee_list.js"

# include js, css files in header of web template
# web_include_css = "/assets/omnexa_hr/css/omnexa_hr.css"
# web_include_js = "/assets/omnexa_hr/js/omnexa_hr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "omnexa_hr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_list_js = {"Employee": "public/js/employee_list.js"}
doctype_js = {
	"HR Leave Application": "public/js/hr_leave_application.js",
	"HR Biometric Device": "public/js/hr_biometric_device.js",
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "omnexa_hr/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "omnexa_hr.utils.jinja_methods",
# 	"filters": "omnexa_hr.utils.jinja_filters"
# }

# Installation
# ------------

before_install = "omnexa_hr.install.enforce_supported_frappe_version"
before_migrate = "omnexa_hr.install.enforce_supported_frappe_version"
after_migrate = "omnexa_hr.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "omnexa_hr.uninstall.before_uninstall"
# after_uninstall = "omnexa_hr.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "omnexa_hr.utils.before_app_install"
# after_app_install = "omnexa_hr.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "omnexa_hr.utils.before_app_uninstall"
# after_app_uninstall = "omnexa_hr.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "omnexa_hr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"HR Leave Application": "omnexa_hr.permissions.hr_leave_application_query",
	"HR Attendance": "omnexa_hr.permissions.hr_attendance_query",
	"HR Salary Slip": "omnexa_hr.permissions.hr_salary_slip_query",
	"HR Training Record": "omnexa_hr.permissions.hr_training_record_query",
	"HR Employee Appraisal": "omnexa_hr.permissions.hr_employee_appraisal_query",
}

has_permission = {
	"HR Leave Application": "omnexa_hr.permissions.has_hr_employee_permission",
	"HR Attendance": "omnexa_hr.permissions.has_hr_employee_permission",
	"HR Salary Slip": "omnexa_hr.permissions.has_hr_employee_permission",
	"HR Training Record": "omnexa_hr.permissions.has_hr_employee_permission",
	"HR Employee Appraisal": "omnexa_hr.permissions.has_hr_employee_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Employee": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc",
	},
	"HR Attendance": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc"
	},
	"HR Payroll Entry": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc"
	},
	"HR Payroll Company Settings": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context"
	},
	"HR Salary Slip": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc"
	},
	"HR Payroll Run": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc"
	},
	"HR Salary Advance": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc"
	},
	"HR End of Service Settlement": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc"
	},
	"HR Recruitment Request": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context"
	},
	"HR Interview": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context"
	},
	"HR Training Record": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context"
	},
	"HR Leave Type": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context"
	},
	"HR Leave Application": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": [
			"omnexa_hr.permissions.enforce_branch_access_for_doc",
			"omnexa_hr.permissions.validate_leave_application_permissions",
		],
	},
	"HR Biometric Device": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc",
	},
	"HR Biometric Punch Log": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
	},
	"HR Leave Balance": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc",
	},
	"HR Department": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc",
	},
	"HR Shift Type": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc",
	},
	"HR Job Applicant": {
		"before_validate": "omnexa_hr.permissions.populate_company_branch_from_user_context",
		"validate": "omnexa_hr.permissions.enforce_branch_access_for_doc",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"omnexa_hr.omnexa_hr.api.biometric.sync_all_devices",
	],
}

# Testing
# -------

# before_tests = "omnexa_hr.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "omnexa_hr.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "omnexa_hr.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["omnexa_hr.utils.before_request"]
# after_request = ["omnexa_hr.utils.after_request"]

# Job Events
# ----------
# before_job = ["omnexa_hr.utils.before_job"]
# after_job = ["omnexa_hr.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{}",
# 		"filter_by": "{}",
# 		"redact_fields": ["{}", "{}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{}",
# 		"filter_by": "{}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"omnexa_hr.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

