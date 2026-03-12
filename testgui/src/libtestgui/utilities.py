import re, os

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QTextFormat
from PyQt6.QtWidgets import QFileDialog, QTextEdit

import linuxcnc as emc

from libtestgui import dialogs

def is_float(string):
	try:
		float(string)
		return True
	except ValueError:
		return False

def is_int(string):
	try:
		int(string)
		return True
	except ValueError:
		return False

def is_number(string):
	try:
		int(string)
		return True
	except ValueError:
		try:
			float(string)
			return True
		except ValueError:
			return False

def conv_units(value, suffix, units):
	if units == 'INCH':
		if suffix == 'in' or suffix == 'inch':
			return float(value)
		elif suffix == 'mil':
			return float(value) * 0.001
		elif suffix == 'cm':
			return float(value) / 2.54
		elif suffix == 'mm':
			return float(value) / 25.4
		elif suffix == 'um':
			return float(value) / 25400

	elif units == 'MM':
		if suffix == 'in' or suffix == 'inch':
			return float(value) * 25.4
		elif suffix == 'mil':
			return float(value) * 0.0254
		elif suffix == 'cm':
			return float(value) * 10
		elif suffix == 'mm':
			return float(value)
		elif suffix == 'um':
			return float(value) / 1000

def convert_fraction(item):
	# strip trailing non digits
	for i in range(len(item) - 1, -1, -1):
		if item[i].isdigit():
			fraction_string = item[:i+1]
			break
	suffix = item[i+1:].strip() if len(item[i+1:].strip()) > 0 else False

	if len(fraction_string.split('/')) == 2: # might be a good number
		match = re.match(r'(\d+)?\s*(\d+)/(\d+)', fraction_string)
		if match:
			whole_number = int(match.group(1)) if match.group(1) else 0
			numerator = int(match.group(2))
			denominator = int(match.group(3))
			# return the decimal number plus suffix
			return whole_number + (numerator / denominator), suffix
	else:
		return False, False

def is_valid_increment(parent, item): # need to return text ,data and suffix
	if is_number(item): # there is no suffix and it's a valid number
		return f'{item} {parent.units.lower()}', item, parent.units

	if '/' in item: # it might be a fraction
		#for character in item:
		fraction, suffix = convert_fraction(item)
		if fraction and suffix:
			return f'{item}', fraction, 'inch'
		elif fraction and not suffix:
			return f'{item} inch', fraction, 'inch'
		else:
			return False, False, False

	units = ['mm', 'cm', 'um', 'in', 'inch', 'mil']
	if item.endswith(tuple(units)): # test to see if it matches any units
		for suffix in units:
			if item.endswith(suffix):
				increment = item.removesuffix(suffix).strip()
				if is_number(increment):
					return item, increment, suffix
				else:
					return False, False, False
	else: # not a valid increment
		return False, False, False

def file_chooser(parent, caption, dialog_type, nc_code_dir=None):
	if nc_code_dir is None:
		nc_code_dir = parent.nc_code_dir
	options = QFileDialog.Option.DontUseNativeDialog
	file_path = False
	file_dialog = QFileDialog()
	file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
	file_dialog.setOptions(QFileDialog.Option.DontUseNativeDialog)
	file_dialog.setWindowTitle('Open File')
	file_dialog.setStyleSheet('') # this does  nothing
	file_dialog.setGeometry(10, 10, 800, 600) # this does  nothing
	if dialog_type == 'open':
		file_path, file_type = file_dialog.getOpenFileName(None,
		caption=caption, directory=parent.nc_code_dir,
		filter=parent.ext_filter, options=options)
	elif dialog == 'save':
		file_path, file_type = file_dialog.getSaveFileName(None,
		caption=caption, directory=parent.nc_code_dir,
		filter=parent.ext_filter, options=options)
	if file_path:
		return file_path
	else:
		return False

def update_mdi(parent):
	if 'mdi_history_lw' in parent.child_names:
		rows = parent.mdi_history_lw.count()
		if rows > 0:
			last_item = parent.mdi_history_lw.item(rows - 1).text().strip()
		else:
			last_item = ''
		if last_item != parent.mdi_command_le.text():
			parent.mdi_history_lw.addItem(parent.mdi_command_le.text())
			path = os.path.dirname(parent.status.ini_filename)
			mdi_file = os.path.join(path, 'mdi_history.txt')
			mdi_codes = []
			for index in range(parent.mdi_history_lw.count()):
				mdi_codes.append(parent.mdi_history_lw.item(index).text())
			with open(mdi_file, 'w') as f:
				f.write('\n'.join(mdi_codes))
		parent.mdi_command_le.setText('')

def home_all_check(parent):
	parent.status.poll()
	for i in range(parent.status.joints):
		if parent.inifile.find(f'JOINT_{i}', 'HOME_SEQUENCE') is None:
			return False
	return True

def update_home_controls(parent):
	parent.status.poll()
	if parent.status.task_state == emc.STATE_ON:
		for joint in range(parent.joints):
			if parent.status.joint[joint]['homed']:
				if f'home_pb_{joint}' in parent.child_names:
					getattr(parent, f'home_pb_{joint}').setEnabled(False)
				if f'unhome_pb_{joint}' in parent.child_names:
					getattr(parent, f'unhome_pb_{joint}').setEnabled(True)
			elif not parent.status.joint[joint]['homed']:
				if f'home_pb_{joint}' in parent.child_names:
					getattr(parent, f'home_pb_{joint}').setEnabled(True)
				if f'unhome_pb_{joint}' in parent.child_names:
					getattr(parent, f'unhome_pb_{joint}').setEnabled(False)

		# all joints homed
		if all(parent.status.homed[:parent.joints]):
			if 'home_all_pb' in parent.child_names:
				parent.home_all_pb.setEnabled(False)
			if 'unhome_all_pb' in parent.child_names:
				parent.unhome_all_pb.setEnabled(True)
			for item in parent.homed_enabled:
				getattr(parent, item).setEnabled(True)

		# not all joints homed
		if not any(parent.status.homed[:parent.joints]):
			if 'home_all_pb' in parent.child_names and home_all_check(parent):
				parent.home_all_pb.setEnabled(True)
			if 'unhome_all_pb' in parent.child_names:
				parent.unhome_all_pb.setEnabled(False)
			for item in parent.homed_enabled:
				getattr(parent, item).setEnabled(False)

def update_run_controls(parent):
	parent.status.poll()
	if parent.status.task_mode == emc.MODE_MANUAL:
		if not parent.probing:
			for item in parent.file_load_controls:
				getattr(parent, item).setEnabled(True)
			if (all(parent.status.homed[:parent.joints])
				and parent.status.task_state == emc.STATE_ON):
				for item in parent.mdi_controls:
					getattr(parent, item).setEnabled(True)
				if parent.status.file != '':
					for item in parent.run_controls:
						getattr(parent, item).setEnabled(True)

	elif parent.status.task_mode == emc.MODE_AUTO:
		for item in parent.file_load_controls:
			getattr(parent, item).setEnabled(False)
		for item in parent.run_controls:
			getattr(parent, item).setEnabled(False)
		for item in parent.mdi_controls:
			getattr(parent, item).setEnabled(False)

def set_hal_enables(parent, obj):
	obj_name = obj.objectName()
	if obj_name == 'probing_enable_pb':
		return
	always_on = obj.property('always_on')
	state_on = obj.property('state_on')
	all_homed = obj.property('all_homed')

	match (always_on, state_on, all_homed):
		case (True, None, None): # always on
			return
		case (None, True, None): # power on
			parent.state_estop_disabled.append(obj_name)
			parent.state_estop_reset_disabled.append(obj_name)
			parent.state_on_enabled.append(obj_name)
		case (None, None, True): # all homed
			parent.state_estop_disabled.append(obj_name)
			parent.state_estop_reset_disabled.append(obj_name)
			parent.homed_enabled.append(obj_name)
		case _: # normal enable/disable
			parent.state_estop_disabled.append(obj_name)
			parent.state_estop_reset_enabled.append(obj_name)

def hal_confirm(parent):
	sender = parent.sender()
	text = sender.text()
	checked_state = sender.isChecked()
	pin = sender.property('pin_name')
	#getattr(parent, f'{pin_name}')
	msg = (f'The HAL object "{text}" requests\n'
	'confirmation before changing the HAL\n'
	f'state of the {pin} pin.')
	result = dialogs.confirm_msg_ok_cancel(parent, msg, 'HAL')
	#print(f'result {result}') self.hal_test['out'] = True
	if result:
		setattr(parent.halcomp, pin, checked_state)
	else: # reset the checked state
		sender.blockSignals(True)
		sender.setChecked(not checked_state)
		sender.blockSignals(False)

def io_watch(parent):
	for key, value in parent.hal_io_check.items():
		checked_state = getattr(parent, key).isChecked()
		hal_state = getattr(parent.halcomp, value)
		if checked_state != hal_state:
			getattr(parent, key).setChecked(hal_state)

	for key, value in parent.hal_io_int.items():
		int_value = getattr(parent, key).value()
		hal_value = getattr(parent.halcomp, value)
		if int_value != hal_value:
			getattr(parent, key).setValue(hal_value)

	for key, value in parent.hal_io_float.items():
		float_value = getattr(parent, key).value()
		hal_value = getattr(parent.halcomp, value)
		if float_value != hal_value:
			getattr(parent, key).setValue(hal_value)

def update_hal_io(parent, value):
	setattr(parent.halcomp, parent.sender().property('pin_name'), value)

def update_hal_spinbox(parent, value):
	setattr(parent.halcomp, parent.sender().property('pin_name'), value)

def update_hal_slider(parent, value):
	setattr(parent.halcomp, parent.sender().property('pin_name'), value)

def var_value_changed(parent, value):
	variable = parent.sender().property('variable')
	parent.cmd = f'#{variable}={value}'
	QTimer.singleShot(500, lambda: sync_var_file(parent))

def sync_var_file(parent): # only update var file if in manual mode and homed
	if (parent.status.task_state == emc.STATE_ON
		and parent.status.task_mode == emc.MODE_MANUAL
		and parent.status.motion_mode == emc.TRAJ_MODE_TELEOP
		and parent.status.interp_state == emc.INTERP_IDLE):
		if parent.status.task_mode != emc.MODE_MDI:
			parent.command.mode(emc.MODE_MDI)
			parent.command.wait_complete()
		parent.command.mdi(parent.cmd)
		parent.command.wait_complete()
		parent.command.task_plan_synch()
		parent.command.mode(emc.MODE_MANUAL)
		parent.command.wait_complete()

def var_file_watch(parent):
	parent.status.poll()
	if parent.status.task_mode == emc.MODE_MANUAL:
		var_current_time = os.stat(os.path.join(parent.config_path, parent.var_file)).st_mtime
		if parent.var_mod_time != var_current_time:
			var_file = os.path.join(parent.config_path, parent.var_file)
			with open(var_file, 'r') as f:
				var_list = f.readlines()
			for key, value in parent.watch_var.items():
				for line in var_list:
					if line.startswith(value[0]):
						getattr(parent, key).setText(f'{float(line.split()[1]):.{value[1]}f}')
			for key, value in parent.set_var.items():
				for line in var_list:
					if line.split()[0] == value:
						getattr(parent, key).setValue(float(line.split()[1]))
			parent.var_mod_time = var_current_time

def change_page(parent):
	object_name = parent.sender().property('change_page')
	index = int(parent.sender().property('index'))
	getattr(parent, object_name).setCurrentIndex(index)

def update_qcode_pte(parent):
	extraSelections = []
	if not parent.gcode_pte.isReadOnly():
		selection = QTextEdit.ExtraSelection()
		lineColor = QColor('yellow').lighter(160)
		selection.format.setBackground(lineColor)
		selection.format.setForeground(QColor('black'))
		selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
		selection.cursor = parent.gcode_pte.textCursor()
		selection.cursor.clearSelection()
		extraSelections.append(selection)
	parent.gcode_pte.setExtraSelections(extraSelections)
	if 'start_line_lb' in parent.child_names:
		cursor = parent.gcode_pte.textCursor()
		selected_block = cursor.blockNumber() # get current block number
		parent.start_line_lb.setText(f'{selected_block}')




