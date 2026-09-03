frappe.pages["hr-workcenter"].on_page_load = function (wrapper) {
	function mount() {
		if (window.omnexa_core && omnexa_core.vertical_portal && omnexa_core.vertical_portal.mountWorkcenter) {
			omnexa_core.vertical_portal.mountWorkcenter(wrapper, "omnexa_hr", {
				pageTitle: __("Human Resources Workcenter"),
			});
			return true;
		}
		return false;
	}
	if (mount()) return;
	frappe.require("/assets/omnexa_core/js/vertical-portal-desk.js", mount);
};
