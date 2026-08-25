const DEFAULT_AVATAR = "/assets/omnexa_hr/images/default-avatar.svg";

frappe.listview_settings["Employee"] = {
	add_fields: ["employee_photo", "employee_code", "department", "designation", "branch"],
	formatters: {
		employee_name(value, df, doc) {
			const src = doc.employee_photo
				? frappe.utils.get_file_link(doc.employee_photo)
				: DEFAULT_AVATAR;
			return `<img class="emp-list-avatar" src="${src}" alt="" style="width:28px;height:28px;border-radius:50%;object-fit:cover;margin-right:8px;vertical-align:middle;"> ${frappe.utils.escape_html(value || "")}`;
		},
	},
};
