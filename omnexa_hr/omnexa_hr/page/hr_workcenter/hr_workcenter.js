frappe.pages["hr-workcenter"].on_page_load = function (wrapper) {
	if (window.omnexa_core && omnexa_core.vertical_workcenter && omnexa_core.vertical_workcenter.mount) {
		omnexa_core.vertical_workcenter.mount(wrapper, "omnexa_hr");
		return;
	}
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Human Resources Workcenter"),
		single_column: true});
	$(page.body).html('<p class="text-muted">' + __("Load omnexa_core vertical workcenter kit") + "</p>");
};
