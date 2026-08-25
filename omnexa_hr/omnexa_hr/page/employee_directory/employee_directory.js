frappe.pages["employee-directory"].on_page_load = function (wrapper) {
	egx.desk.boot_modern_page(
		{
			pageRoute: "employee-directory",
			wrapper: wrapper,
			css: ["/assets/omnexa_hr/css/employee_directory.css"],
		},
		() => init_employee_directory_page(wrapper)
	);
};

function init_employee_directory_page(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Employee Directory"),
		single_column: true,
	});

	const STORAGE_KEY = "omnexa_emp_dir_view";
	const FETCH_LIMIT = 500;

	const state = {
		allEmployees: [],
		meta: {},
		viewMode: localStorage.getItem(STORAGE_KEY) || "list",
		search: "",
		filters: {
			department: "",
			designation: "",
			branch: "",
			company: "",
			status: "",
			employment_type: "",
		},
		sortBy: "name_asc",
		groupBy: "",
		page: 1,
		pageSize: 10,
		selected: new Set(),
	};

	const $root = $(`
		<div class="egx-page-shell employee-directory-page" role="main" aria-label="${__("Employee Directory")}">
			<header class="ed-hero">
				<div class="ed-hero__text">
					<h1>${__("Employee Directory")}</h1>
					<p>${__("Manage employees across your organization.")}</p>
				</div>
				<div class="ed-hero__actions">
					<button type="button" class="ed-btn ed-btn--primary ed-add-employee">
						+ ${__("Add Employee")}
					</button>
					<button type="button" class="ed-btn ed-import">${__("Import")}</button>
					<button type="button" class="ed-btn ed-export">${__("Export")}</button>
					<button type="button" class="ed-btn ed-btn--icon ed-refresh" title="${__("Refresh")}" aria-label="${__("Refresh")}">↻</button>
				</div>
			</header>

			<div class="ed-kpi-row" aria-live="polite"></div>

			<div class="ed-toolbar">
				<div class="ed-search-row">
					<div class="ed-search-wrap">
						<span class="fa fa-search" aria-hidden="true"></span>
						<input type="search" class="ed-search-input" placeholder="${__("Search by ID, name, department, designation, branch, company…")}" aria-label="${__("Search employees")}">
					</div>
					<div class="ed-view-switch" role="group" aria-label="${__("Display mode")}">
						<button type="button" class="ed-view-list" title="${__("List View")}" aria-label="${__("List View")}">☰</button>
						<button type="button" class="ed-view-cards" title="${__("Card View")}" aria-label="${__("Card View")}">▦</button>
					</div>
				</div>
				<div class="ed-filters"></div>
			</div>

			<div class="ed-content" aria-live="polite"></div>
		</div>

		<div class="ed-drawer-overlay" tabindex="-1"></div>
		<aside class="ed-drawer" role="dialog" aria-modal="true" aria-labelledby="ed-drawer-title">
			<div class="ed-drawer__head">
				<strong id="ed-drawer-title">${__("Employee Preview")}</strong>
				<button type="button" class="ed-btn ed-btn--icon ed-drawer-close" aria-label="${__("Close")}">×</button>
			</div>
			<div class="ed-drawer__body"></div>
			<div class="ed-drawer__foot"></div>
		</aside>
	`);

	$(page.main).empty().append($root);

	const $kpi = $root.find(".ed-kpi-row");
	const $filters = $root.find(".ed-filters");
	const $content = $root.find(".ed-content");
	const $drawer = $(".ed-drawer");
	const $overlay = $(".ed-drawer-overlay");

	// ——— Utilities ———

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function format_date(d) {
		if (!d) return "—";
		return frappe.datetime.str_to_user(d);
	}

	function get_initials(name) {
		if (!name) return "?";
		const parts = String(name).trim().split(/\s+/).filter(Boolean);
		if (parts.length >= 2) {
			return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
		}
		return parts[0].substring(0, 2).toUpperCase();
	}

	function photo_url(path) {
		if (!path) return "";
		return frappe.utils.get_file_link(path);
	}

	function badge_class(status) {
		const s = (status || "Active").toLowerCase();
		if (s === "on leave") return "ed-badge--leave";
		if (s === "resigned") return "ed-badge--resigned";
		if (s === "inactive") return "ed-badge--inactive";
		return "ed-badge--active";
	}

	function dot_class(status) {
		const s = (status || "Active").toLowerCase();
		if (s === "on leave") return "ed-card__dot--leave";
		if (s === "resigned") return "ed-card__dot--resigned";
		return "";
	}

	function status_badge(status) {
		const s = status || "Active";
		return `<span class="ed-badge ${badge_class(s)}">${esc(s)}</span>`;
	}

	function avatar_html(emp, sizeClass) {
		const name = emp.employee_name || emp.name || "";
		const url = photo_url(emp.employee_photo);
		if (url) {
			return `<img class="ed-avatar ${sizeClass}" src="${esc(url)}" alt="" loading="lazy" data-fallback-initials="${esc(get_initials(name))}">`;
		}
		return `<span class="ed-avatar ed-avatar--initials ${sizeClass}" aria-hidden="true">${esc(get_initials(name))}</span>`;
	}

	function fix_broken_avatars($scope) {
		$scope.find("img.ed-avatar[data-fallback-initials]").each(function () {
			const img = this;
			img.onerror = function () {
				const initials = img.getAttribute("data-fallback-initials") || "?";
				const span = document.createElement("span");
				span.className = img.className + " ed-avatar--initials";
				span.textContent = initials;
				img.replaceWith(span);
			};
		});
	}

	function unique_values(key) {
		const set = new Set();
		state.allEmployees.forEach((e) => {
			const v = e[key];
			if (v) set.add(v);
		});
		return Array.from(set).sort((a, b) => String(a).localeCompare(String(b)));
	}

	function is_new_this_month(d) {
		if (!d) return false;
		const dt = frappe.datetime.str_to_obj(d);
		const now = frappe.datetime.now_datetime(true);
		return dt.getFullYear() === now.getFullYear() && dt.getMonth() === now.getMonth();
	}

	// ——— Data pipeline ———

	function get_filtered_employees() {
		let rows = state.allEmployees.slice();
		const q = state.search.trim().toLowerCase();

		if (q) {
			rows = rows.filter((e) => {
				const hay = [
					e.name,
					e.employee_name,
					e.employee_code,
					e.department,
					e.designation,
					e.company,
					e.branch,
					e.status,
					e.employment_type,
				]
					.filter(Boolean)
					.join(" ")
					.toLowerCase();
				return hay.includes(q);
			});
		}

		Object.keys(state.filters).forEach((key) => {
			const val = state.filters[key];
			if (val) rows = rows.filter((e) => (e[key] || "") === val);
		});

		rows.sort((a, b) => {
			switch (state.sortBy) {
				case "name_desc":
					return String(b.employee_name || "").localeCompare(String(a.employee_name || ""));
				case "dept_asc":
					return String(a.department || "").localeCompare(String(b.department || ""));
				case "join_desc":
					return String(b.date_of_joining || "").localeCompare(String(a.date_of_joining || ""));
				case "join_asc":
					return String(a.date_of_joining || "").localeCompare(String(b.date_of_joining || ""));
				default:
					return String(a.employee_name || "").localeCompare(String(b.employee_name || ""));
			}
		});

		return rows;
	}

	function paginate(rows) {
		const start = (state.page - 1) * state.pageSize;
		return rows.slice(start, start + state.pageSize);
	}

	// ——— Actions ———

	function open_employee(name) {
		if (name) frappe.set_route("Form", "Employee", name);
	}

	function open_drawer(emp) {
		const name = emp.employee_name || emp.name;
		$drawer.find(".ed-drawer__body").html(`
			<div class="ed-drawer__profile">
				${avatar_html(emp, "ed-avatar--drawer")}
				<h3 style="margin:12px 0 4px;font-size:18px;">${esc(name)}</h3>
				<div>${status_badge(emp.status)}</div>
			</div>
			<div class="ed-drawer__field"><span>${__("Employee ID")}</span><span>${esc(emp.employee_code || emp.name)}</span></div>
			<div class="ed-drawer__field"><span>${__("Designation")}</span><span>${esc(emp.designation || "—")}</span></div>
			<div class="ed-drawer__field"><span>${__("Department")}</span><span>${esc(emp.department || "—")}</span></div>
			<div class="ed-drawer__field"><span>${__("Branch")}</span><span>${esc(emp.branch || "—")}</span></div>
			<div class="ed-drawer__field"><span>${__("Company")}</span><span>${esc(emp.company || "—")}</span></div>
			<div class="ed-drawer__field"><span>${__("Employment Type")}</span><span>${esc(emp.employment_type || "—")}</span></div>
			<div class="ed-drawer__field"><span>${__("Joining Date")}</span><span>${format_date(emp.date_of_joining)}</span></div>
		`);
		$drawer.find(".ed-drawer__foot").html(`
			<button type="button" class="ed-btn ed-btn--primary ed-drawer-open-full">${__("Open Full Profile")}</button>
			<button type="button" class="ed-btn ed-drawer-edit">${__("Edit")}</button>
		`);
		$drawer.find(".ed-drawer-open-full, .ed-drawer-edit").data("name", emp.name);
		fix_broken_avatars($drawer);
		$overlay.addClass("open");
		$drawer.addClass("open");
	}

	function close_drawer() {
		$overlay.removeClass("open");
		$drawer.removeClass("open");
	}

	function route_list(doctype, employee) {
		frappe.set_route("List", doctype, { employee });
	}

	function can_delete_employee() {
		return frappe.model.can_delete("Employee");
	}

	function show_actions_menu(emp, $anchor) {
		const items = [
			{ label: __("View"), action: () => open_drawer(emp) },
			{ label: __("Edit"), action: () => open_employee(emp.name) },
			{ label: __("Attendance"), action: () => route_list("Attendance", emp.name) },
			{ label: __("Leave"), action: () => route_list("Leave Application", emp.name) },
			{ label: __("Payroll"), action: () => route_list("Salary Slip", emp.name) },
			{ label: __("Performance"), action: () => route_list("Appraisal", emp.name) },
		];
		if (can_delete_employee()) {
			items.push({
				label: __("Delete"),
				action: () => {
					frappe.confirm(__("Delete employee {0}?", [emp.employee_name || emp.name]), () => {
						frappe.call({
							method: "frappe.client.delete",
							args: { doctype: "Employee", name: emp.name },
							callback() {
								frappe.show_alert({ message: __("Deleted"), indicator: "green" });
								fetch_employees(true);
							},
						});
					});
				},
			});
		}

		const menu = items
			.map(
				(item, i) =>
					`<button type="button" class="dropdown-item ed-action-item" data-idx="${i}">${esc(item.label)}</button>`
			)
			.join("");

		const $menu = $(`
			<div class="dropdown-menu show ed-actions-menu" style="position:absolute;z-index:1060;">
				${menu}
			</div>
		`);

		$("body").append($menu);
		const offset = $anchor.offset();
		$menu.css({ top: offset.top + $anchor.outerHeight(), left: offset.left - 120 });

		$menu.find(".ed-action-item").on("click", function () {
			const idx = cint($(this).data("idx"));
			items[idx].action();
			$menu.remove();
		});

		$(document).one("click", () => $menu.remove());
	}

	function export_csv(rows, filename) {
		const headers = [
			"Employee ID",
			"Name",
			"Designation",
			"Department",
			"Company",
			"Branch",
			"Status",
			"Employment Type",
			"Joining Date",
		];
		const lines = [headers.join(",")];
		rows.forEach((e) => {
			lines.push(
				[
					e.employee_code || e.name,
					e.employee_name,
					e.designation,
					e.department,
					e.company,
					e.branch,
					e.status,
					e.employment_type,
					e.date_of_joining,
				]
					.map((v) => `"${String(v || "").replace(/"/g, '""')}"`)
					.join(",")
			);
		});
		const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
		const link = document.createElement("a");
		link.href = URL.createObjectURL(blob);
		link.download = filename || "employees.csv";
		link.click();
	}

	// ——— Render ———

	function render_kpis(rows) {
		const active = rows.filter((e) => (e.status || "Active") === "Active").length;
		const onLeave = rows.filter((e) => e.status === "On Leave").length;
		const resigned = rows.filter((e) => e.status === "Resigned").length;
		const newMonth = rows.filter((e) => is_new_this_month(e.date_of_joining)).length;

		$kpi.html(`
			<div class="ed-kpi"><div class="ed-kpi__label">${__("Total")}</div><div class="ed-kpi__value">${rows.length}</div></div>
			<div class="ed-kpi ed-kpi--active"><div class="ed-kpi__label">${__("Active")}</div><div class="ed-kpi__value">${active}</div></div>
			<div class="ed-kpi ed-kpi--leave"><div class="ed-kpi__label">${__("On Leave")}</div><div class="ed-kpi__value">${onLeave}</div></div>
			<div class="ed-kpi"><div class="ed-kpi__label">${__("Resigned")}</div><div class="ed-kpi__value">${resigned}</div></div>
			<div class="ed-kpi"><div class="ed-kpi__label">${__("New This Month")}</div><div class="ed-kpi__value">${newMonth}</div></div>
		`);
	}

	function render_filters() {
		const defs = [
			{ key: "department", label: __("Department") },
			{ key: "designation", label: __("Designation") },
			{ key: "branch", label: __("Branch") },
			{ key: "company", label: __("Company") },
			{ key: "status", label: __("Status") },
			{ key: "employment_type", label: __("Employment Type") },
		];

		const selects = defs
			.map(({ key, label }) => {
				const opts = unique_values(key)
					.map((v) => `<option value="${esc(v)}" ${state.filters[key] === v ? "selected" : ""}>${esc(v)}</option>`)
					.join("");
				return `
					<select class="ed-filter-select" data-filter="${key}" aria-label="${esc(label)}">
						<option value="">${esc(label)}</option>
						${opts}
					</select>`;
			})
			.join("");

		$filters.html(`
			${selects}
			<select class="ed-filter-select ed-sort" aria-label="${__("Sort")}">
				<option value="name_asc" ${state.sortBy === "name_asc" ? "selected" : ""}>${__("Name A–Z")}</option>
				<option value="name_desc" ${state.sortBy === "name_desc" ? "selected" : ""}>${__("Name Z–A")}</option>
				<option value="dept_asc" ${state.sortBy === "dept_asc" ? "selected" : ""}>${__("Department")}</option>
				<option value="join_desc" ${state.sortBy === "join_desc" ? "selected" : ""}>${__("Join Date (newest)")}</option>
				<option value="join_asc" ${state.sortBy === "join_asc" ? "selected" : ""}>${__("Join Date (oldest)")}</option>
			</select>
			<select class="ed-filter-select ed-group" aria-label="${__("Group By")}">
				<option value="" ${!state.groupBy ? "selected" : ""}>${__("Group By")}</option>
				<option value="department" ${state.groupBy === "department" ? "selected" : ""}>${__("Department")}</option>
				<option value="branch" ${state.groupBy === "branch" ? "selected" : ""}>${__("Branch")}</option>
				<option value="status" ${state.groupBy === "status" ? "selected" : ""}>${__("Status")}</option>
			</select>
			<button type="button" class="ed-filter-clear">${__("Clear Filters")}</button>
		`);
	}

	function render_skeleton() {
		$content.html(`
			<div class="ed-skeleton-grid">
				${Array(8).fill('<div class="ed-skeleton-card"></div>').join("")}
			</div>
		`);
	}

	function render_empty(meta) {
		const msg = meta.empty_reason || __("No employees found for the current scope.");
		let actions = "";
		if (meta.suggest_view_all && meta.company) {
			actions = `
				<button type="button" class="ed-btn ed-btn--primary ed-view-all-branches" style="margin-top:16px;">
					${__("View all branches in {0}", [meta.company])}
				</button>`;
		} else {
			actions = `
				<button type="button" class="ed-btn ed-btn--primary ed-add-employee" style="margin-top:16px;">
					+ ${__("Create Employee")}
				</button>`;
		}
		return `
			<div class="ed-empty">
				<div class="ed-empty__icon">👥</div>
				<div class="ed-empty__title">${__("No Employees Found")}</div>
				<p class="text-muted">${esc(msg)}</p>
				${actions}
			</div>`;
	}

	function render_pagination(total) {
		const pages = Math.max(1, Math.ceil(total / state.pageSize));
		if (state.page > pages) state.page = pages;

		const btns = [];
		for (let i = 1; i <= pages && i <= 7; i++) {
			btns.push(`<button type="button" class="ed-page-btn ${i === state.page ? "active" : ""}" data-page="${i}">${i}</button>`);
		}

		return `
			<div class="ed-pagination">
				<div>
					<label>${__("Show")}
						<select class="ed-page-size">
							${[10, 25, 50, 100].map((n) => `<option value="${n}" ${state.pageSize === n ? "selected" : ""}>${n}</option>`).join("")}
						</select>
					</label>
					<span style="margin-left:8px;color:var(--ed-muted);">${__("{0} employees", [total])}</span>
				</div>
				<div class="ed-page-btns">
					<button type="button" class="ed-page-prev" ${state.page <= 1 ? "disabled" : ""}>‹</button>
					${btns.join("")}
					<button type="button" class="ed-page-next" ${state.page >= pages ? "disabled" : ""}>›</button>
				</div>
			</div>`;
	}

	function actions_btn(emp) {
		return `<button type="button" class="ed-actions-btn" data-name="${esc(emp.name)}" aria-label="${__("Actions")}">⋮</button>`;
	}

	function render_list_rows(rows) {
		return rows
			.map((emp) => {
				const checked = state.selected.has(emp.name) ? "checked" : "";
				return `
					<tr data-name="${esc(emp.name)}" class="${state.selected.has(emp.name) ? "ed-row-selected" : ""}">
						<td><input type="checkbox" class="ed-row-check" data-name="${esc(emp.name)}" ${checked} aria-label="${__("Select")}"></td>
						<td>${esc(emp.employee_code || emp.name)}</td>
						<td>
							<div class="ed-emp-cell">
								${avatar_html(emp, "ed-avatar--list")}
								<div class="ed-emp-cell__info">
									<div class="name">${esc(emp.employee_name || "")}</div>
									<div class="sub">${esc(emp.designation || "—")}</div>
									<div class="sub">${esc(emp.department || "—")}</div>
								</div>
							</div>
						</td>
						<td>${esc(emp.designation || "—")}</td>
						<td>${esc(emp.department || "—")}</td>
						<td>${esc(emp.company || "—")}</td>
						<td>${esc(emp.branch || "—")}</td>
						<td class="text-muted">—</td>
						<td class="text-muted">—</td>
						<td>${format_date(emp.date_of_joining)}</td>
						<td>${status_badge(emp.status)}</td>
						<td>${actions_btn(emp)}</td>
					</tr>`;
			})
			.join("");
	}

	function render_list(allFiltered) {
		if (!allFiltered.length && !state.allEmployees.length) {
			$content.html(render_empty(state.meta));
			bind_static_actions();
			return;
		}
		if (!allFiltered.length) {
			$content.html(render_empty({ empty_reason: __("No employees match your search or filters.") }));
			bind_static_actions();
			return;
		}

		const pageRows = paginate(allFiltered);
		const exportSel =
			state.selected.size > 0
				? `<button type="button" class="ed-btn ed-export-selected">${__("Export selected ({0})", [state.selected.size])}</button>`
				: "";

		$content.html(`
			<div class="ed-list-panel">
				<div style="padding:12px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--ed-border);">
					<strong>${__("List View")}</strong>
					${exportSel}
				</div>
				<div class="ed-table-wrap">
					<table class="ed-table">
						<thead>
							<tr>
								<th><input type="checkbox" class="ed-select-all" aria-label="${__("Select all")}"></th>
								<th>${__("Employee ID")}</th>
								<th>${__("Employee")}</th>
								<th>${__("Designation")}</th>
								<th>${__("Department")}</th>
								<th>${__("Company")}</th>
								<th>${__("Branch")}</th>
								<th>${__("Email")}</th>
								<th>${__("Mobile")}</th>
								<th>${__("Joining Date")}</th>
								<th>${__("Status")}</th>
								<th>${__("Actions")}</th>
							</tr>
						</thead>
						<tbody>${render_list_rows(pageRows)}</tbody>
					</table>
				</div>
				${render_pagination(allFiltered.length)}
			</div>
		`);
		fix_broken_avatars($content);
		bind_list_actions(allFiltered);
	}

	function render_card(emp) {
		return `
			<article class="ed-card" data-name="${esc(emp.name)}" tabindex="0">
				<span class="ed-card__dot ${dot_class(emp.status)}" title="${esc(emp.status || "Active")}"></span>
				<div class="ed-card__menu">${actions_btn(emp)}</div>
				<div class="ed-card__photo">${avatar_html(emp, "ed-avatar--card")}</div>
				<div class="ed-card__name" title="${esc(emp.employee_name)}">${esc(emp.employee_name || "")}</div>
				<div class="ed-card__code">${esc(emp.employee_code || emp.name)}</div>
				<div class="ed-card__designation">${esc(emp.designation || "—")}</div>
				<div class="ed-card__department">${esc(emp.department || "—")}</div>
				<div class="ed-card__lines"><span>${esc(emp.company || "—")}</span></div>
				<div class="ed-card__lines"><span>${esc(emp.branch || "—")}</span></div>
				<div class="ed-card__contact"><span class="fa fa-envelope-o" aria-hidden="true"></span><span>—</span></div>
				<div class="ed-card__contact"><span class="fa fa-phone" aria-hidden="true"></span><span>—</span></div>
				<div style="margin-top:8px;">${status_badge(emp.status)}</div>
				<div class="ed-card__quick">
					<button type="button" class="ed-quick-btn ed-quick-view" data-name="${esc(emp.name)}">${__("View")}</button>
					<button type="button" class="ed-quick-btn ed-quick-attendance" data-name="${esc(emp.name)}">${__("Attendance")}</button>
					<button type="button" class="ed-quick-btn ed-quick-leave" data-name="${esc(emp.name)}">${__("Leave")}</button>
				</div>
				<div class="ed-card__footer">
					<span>${esc(emp.employee_code || emp.name)}</span>
					<span>${format_date(emp.date_of_joining)}</span>
				</div>
			</article>`;
	}

	function render_cards(allFiltered) {
		if (!allFiltered.length && !state.allEmployees.length) {
			$content.html(render_empty(state.meta));
			bind_static_actions();
			return;
		}
		if (!allFiltered.length) {
			$content.html(render_empty({ empty_reason: __("No employees match your search or filters.") }));
			bind_static_actions();
			return;
		}

		const pageRows = paginate(allFiltered);
		let html = `<div class="ed-card-grid">${pageRows.map(render_card).join("")}</div>`;

		if (state.groupBy) {
			const groups = {};
			allFiltered.forEach((e) => {
				const g = e[state.groupBy] || __("Unassigned");
				if (!groups[g]) groups[g] = [];
				groups[g].push(e);
			});
			html = Object.keys(groups)
				.sort()
				.map(
					(g) => `
						<h4 style="margin:16px 0 12px;font-size:14px;color:var(--ed-muted);">${esc(g)} (${groups[g].length})</h4>
						<div class="ed-card-grid">${groups[g].map(render_card).join("")}</div>`
				)
				.join("");
			$content.html(html);
		} else {
			$content.html(html + render_pagination(allFiltered.length));
		}
		fix_broken_avatars($content);
		bind_card_actions(allFiltered);
	}

	function render_all() {
		render_filters();
		const filtered = get_filtered_employees();
		render_kpis(filtered);
		if (state.viewMode === "cards") render_cards(filtered);
		else render_list(filtered);
		update_view_switcher();
	}

	function update_view_switcher() {
		$root.find(".ed-view-list").toggleClass("active", state.viewMode === "list");
		$root.find(".ed-view-cards").toggleClass("active", state.viewMode === "cards");
	}

	// ——— Event binding ———

	function get_emp_by_name(name) {
		return state.allEmployees.find((e) => e.name === name);
	}

	function bind_static_actions() {
		$root.find(".ed-add-employee").off("click").on("click", () => frappe.new_doc("Employee"));
		$root.find(".ed-view-all-branches").off("click").on("click", view_all_branches);
	}

	function bind_list_actions(allFiltered) {
		bind_static_actions();

		$content.find(".ed-row-check").on("change", function () {
			const name = $(this).data("name");
			if (this.checked) state.selected.add(name);
			else state.selected.delete(name);
			$(this).closest("tr").toggleClass("ed-row-selected", this.checked);
		});

		$content.find(".ed-select-all").on("change", function () {
			const checked = this.checked;
			paginate(allFiltered).forEach((e) => {
				if (checked) state.selected.add(e.name);
				else state.selected.delete(e.name);
			});
			render_all();
		});

		$content.find("tbody tr").on("click", function (e) {
			if ($(e.target).closest("input, .ed-actions-btn, button").length) return;
			const name = $(this).data("name");
			const emp = get_emp_by_name(name);
			if (emp) open_drawer(emp);
		});

		$content.find(".ed-actions-btn").on("click", function (e) {
			e.stopPropagation();
			const emp = get_emp_by_name($(this).data("name"));
			if (emp) show_actions_menu(emp, $(this));
		});

		bind_pagination(allFiltered);
		bind_export_selected();
	}

	function bind_card_actions(allFiltered) {
		bind_static_actions();

		$content.find(".ed-card").on("click", function (e) {
			if ($(e.target).closest(".ed-actions-btn, .ed-quick-btn").length) return;
			const emp = get_emp_by_name($(this).data("name"));
			if (emp) open_drawer(emp);
		});

		$content.find(".ed-quick-view").on("click", function (e) {
			e.stopPropagation();
			open_employee($(this).data("name"));
		});

		$content.find(".ed-quick-attendance").on("click", function (e) {
			e.stopPropagation();
			route_list("Attendance", $(this).data("name"));
		});

		$content.find(".ed-quick-leave").on("click", function (e) {
			e.stopPropagation();
			route_list("Leave Application", $(this).data("name"));
		});

		$content.find(".ed-actions-btn").on("click", function (e) {
			e.stopPropagation();
			const emp = get_emp_by_name($(this).closest("[data-name]").data("name") || $(this).data("name"));
			if (emp) show_actions_menu(emp, $(this));
		});

		bind_pagination(allFiltered);
	}

	function bind_pagination(allFiltered) {
		$content.find(".ed-page-size").on("change", function () {
			state.pageSize = cint($(this).val()) || 10;
			state.page = 1;
			render_all();
		});

		$content.find(".ed-page-btn").on("click", function () {
			state.page = cint($(this).data("page"));
			render_all();
		});

		$content.find(".ed-page-prev").on("click", function () {
			if (state.page > 1) {
				state.page -= 1;
				render_all();
			}
		});

		$content.find(".ed-page-next").on("click", function () {
			const pages = Math.ceil(allFiltered.length / state.pageSize);
			if (state.page < pages) {
				state.page += 1;
				render_all();
			}
		});
	}

	function bind_export_selected() {
		$content.find(".ed-export-selected").on("click", function () {
			const rows = state.allEmployees.filter((e) => state.selected.has(e.name));
			export_csv(rows, "employees-selected.csv");
		});
	}

	function view_all_branches() {
		const company = state.meta.company;
		if (!company) return;
		frappe.call({
			method: "omnexa_core.omnexa_core.session_context.set_desk_view_context",
			type: "POST",
			args: { company, branch: null, view_all_branches: 1 },
			freeze: true,
			callback() {
				fetch_employees(true);
			},
		});
	}

	// ——— Fetch ———

	function fetch_employees(force) {
		render_skeleton();
		frappe.call({
			method: "omnexa_hr.omnexa_hr.api.employee_directory.get_employees",
			args: { search: "", limit: FETCH_LIMIT },
			callback(r) {
				const meta = r.message || {};
				state.meta = meta;
				state.allEmployees = meta.employees || [];
				if (force) {
					state.page = 1;
					state.selected.clear();
				}
				render_all();
			},
			error() {
				$content.html(render_empty({ empty_reason: __("Could not load employees. Check permissions and try Refresh.") }));
				bind_static_actions();
			},
		});
	}

	// ——— Global events ———

	let searchTimer = null;

	$root.find(".ed-search-input").on("input", function () {
		state.search = $(this).val() || "";
		state.page = 1;
		clearTimeout(searchTimer);
		searchTimer = setTimeout(render_all, 150);
	});

	$root.on("change", ".ed-filter-select[data-filter]", function () {
		const key = $(this).data("filter");
		state.filters[key] = $(this).val() || "";
		state.page = 1;
		render_all();
	});

	$root.on("change", ".ed-sort", function () {
		state.sortBy = $(this).val();
		render_all();
	});

	$root.on("change", ".ed-group", function () {
		state.groupBy = $(this).val();
		state.page = 1;
		render_all();
	});

	$root.on("click", ".ed-filter-clear", function () {
		Object.keys(state.filters).forEach((k) => (state.filters[k] = ""));
		state.search = "";
		state.groupBy = "";
		state.sortBy = "name_asc";
		state.page = 1;
		$root.find(".ed-search-input").val("");
		render_all();
	});

	$root.find(".ed-view-list").on("click", function () {
		state.viewMode = "list";
		localStorage.setItem(STORAGE_KEY, "list");
		state.page = 1;
		render_all();
	});

	$root.find(".ed-view-cards").on("click", function () {
		state.viewMode = "cards";
		localStorage.setItem(STORAGE_KEY, "cards");
		state.page = 1;
		render_all();
	});

	$root.find(".ed-refresh").on("click", () => fetch_employees(true));

	$root.find(".ed-export").on("click", function () {
		export_csv(get_filtered_employees(), "employee-directory.csv");
	});

	$root.find(".ed-import").on("click", function () {
		frappe.set_route("List", "Data Import", { reference_doctype: "Employee" });
	});

	$root.find(".ed-add-employee").on("click", () => frappe.new_doc("Employee"));

	$overlay.on("click", close_drawer);
	$drawer.find(".ed-drawer-close").on("click", close_drawer);

	$drawer.on("click", ".ed-drawer-open-full, .ed-drawer-edit", function () {
		open_employee($(this).data("name"));
		close_drawer();
	});

	$(document).on("keydown.emp_dir", function (e) {
		if (e.key === "Escape") close_drawer();
	});

	fetch_employees(false);
}
