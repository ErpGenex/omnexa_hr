frappe.pages["hr-employee-self-service"].on_page_load = function (wrapper) {
	egx.desk.boot_modern_page(
		{
			pageRoute: "hr-employee-self-service",
			wrapper: wrapper,
			css: ["/assets/omnexa_hr/css/hr_desk.css"],
			js: ["/assets/omnexa_core/js/egx_desk_dashboard.js"],
		},
		() => init_hr_ess(wrapper)
	);
};

function init_hr_ess(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Employee Self-Service"),
		single_column: true,
	});

	page.set_primary_action(__("Refresh"), () => load());

	function load() {
		$(page.main).html(`<p class="egx-muted padding">${__("Loading...")}</p>`);
		frappe.call({
			method: "omnexa_hr.omnexa_hr.api.leave_workflow.get_ess_dashboard",
			callback(r) {
				egx.desk.mountESS($(page.main), r.message || {}, { onRefresh: load });
			},
			error() {
				$(page.main).html(`<div class="egx-empty"><div class="egx-empty__title">${__("Could not load self-service")}</div></div>`);
			},
		});
	}

	load();
};
