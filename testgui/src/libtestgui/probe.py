
'''
You have to be homed and power on to be here
'''
def toggle(parent):
	if parent.probing_enable_pb.isChecked():
		parent.probing = True
		for item in parent.run_controls:
			getattr(parent, item).setEnabled(False)
		for item in parent.file_load_controls:
			getattr(parent, item).setEnabled(False)
		for item in parent.mdi_controls:
			getattr(parent, item).setEnabled(False)
		for item in parent.probe_controls:
			getattr(parent, item).setEnabled(True)

	else:
		parent.probing = False
		for item in parent.run_controls:
			getattr(parent, item).setEnabled(True)
		for item in parent.file_load_controls:
			getattr(parent, item).setEnabled(True)
		for item in parent.mdi_controls:
			getattr(parent, item).setEnabled(True)
		for item in parent.probe_controls:
			getattr(parent, item).setEnabled(False)



