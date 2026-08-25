frappe.ui.form.on("HR Leave Application", {
	setup(frm) {
		if (!frm.is_new()) return;
		if (!frappe.user_roles.includes("HR Employee")) return;
		frappe.call({
			method: "omnexa_hr.omnexa_hr.api.leave_workflow.get_my_employee",
			callback(r) {
				if (r.message) {
					frm.set_value("employee", r.message);
				}
			},
		});
	},
	refresh(frm) {
		if (frm.is_new()) return;

		if (frm.doc.status === "Draft" || frm.doc.status === "") {
			frm.add_custom_button(__("Submit"), () => {
				frappe.call({
					method: "omnexa_hr.omnexa_hr.api.leave_workflow.submit_leave",
					args: { name: frm.doc.name },
					callback() {
						frm.reload_doc();
					},
				});
			});
		}

		if (frm.doc.status === "Submitted") {
			const canApprove = ["HR Manager", "HR User", "System Manager", "Company Admin"].some((r) =>
				frappe.user_roles.includes(r)
			);
			if (!canApprove) return;
			frm.add_custom_button(__("Approve"), () => {
				frappe.call({
					method: "omnexa_hr.omnexa_hr.api.leave_workflow.approve_leave",
					args: { name: frm.doc.name },
					callback() {
						frm.reload_doc();
					},
				});
			}, __("Actions"));

			frm.add_custom_button(__("Reject"), () => {
				frappe.prompt(
					[{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 }],
					(values) => {
						frappe.call({
							method: "omnexa_hr.omnexa_hr.api.leave_workflow.reject_leave",
							args: { name: frm.doc.name, reason: values.reason },
							callback() {
								frm.reload_doc();
							},
						});
					},
					__("Reject Leave"),
					__("Reject")
				);
			}, __("Actions"));
		}
	},
});
