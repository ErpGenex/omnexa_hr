frappe.pages["hr-dashboard"].on_page_load = function (wrapper) {
	egx.desk.boot_modern_page(
		{
			pageRoute: "hr-dashboard",
			wrapper: wrapper,
			css: ["/assets/omnexa_hr/css/hr_desk.css"],
			js: ["/assets/omnexa_core/js/egx_desk_dashboard.js"],
		},
		() => init_hr_dashboard(wrapper)
	);
};

function init_hr_dashboard(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("HR Dashboard"),
		single_column: true,
	});

	const $main = $(page.main);
	page.set_primary_action(__("Refresh"), () => load());

	function show_error(msg) {
		$main.html(
			`<div class="egx-empty egx-page-shell"><div class="egx-empty__title">${frappe.utils.escape_html(msg)}</div></div>`
		);
	}

	function load() {
		$main.html(
			`<div class="egx-skeleton-grid egx-page-shell" style="padding:16px">${Array(6)
				.fill('<div class="ed-skeleton-card" style="height:120px"></div>')
				.join("")}</div>`
		);

		frappe.call({
			method: "omnexa_hr.omnexa_hr.api.hr_dashboard.get_hr_dashboard_catalog",
			callback(r) {
				if (!window.egx || !egx.desk || typeof egx.desk.mountDashboard !== "function") {
					show_error(__("Dashboard renderer not loaded. Run bench build and clear cache."));
					return;
				}
				try {
					egx.desk.mountDashboard($main, r.message || {}, { onRefresh: load });
				} catch (err) {
					console.error("[hr-dashboard]", err);
					show_error(__("Could not render HR Dashboard"));
				}
			},
			error() {
				show_error(__("Could not load HR Dashboard"));
			},
		});
	}

	load();
}
