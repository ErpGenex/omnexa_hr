frappe.ui.form.on("HR Biometric Device", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Sync Now"), () => {
			frappe.call({
				method: "omnexa_hr.omnexa_hr.api.biometric.sync_single_device",
				args: { device: frm.doc.name },
				freeze: true,
				callback(r) {
					const msg = r.message || {};
					frappe.msgprint(
						__("Imported: {0}, Attendance processed: {1}", [
							msg.imported || 0,
							msg.attendance_processed || 0,
						])
					);
					frm.reload_doc();
				},
			});
		});
	},
});
