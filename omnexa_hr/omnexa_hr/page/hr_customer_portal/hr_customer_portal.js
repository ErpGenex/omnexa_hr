frappe.pages["hr-customer-portal"].on_page_load = function (wrapper) {
	function mount() {
		if (window.omnexa_core && omnexa_core.vertical_portal && omnexa_core.vertical_portal.mountRoleDesk) {
			omnexa_core.vertical_portal.mountRoleDesk(wrapper, "omnexa_hr", "customer-portal");
			return true;
		}
		return false;
	}
	if (mount()) return;
	frappe.require("/assets/omnexa_core/js/vertical-portal-desk.js", mount);
};
