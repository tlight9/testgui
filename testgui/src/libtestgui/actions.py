import subprocess, os, shutil

from PyQt6.QtWidgets import QFileDialog, QMenu

import linuxcnc as emc

from libtestgui import utilities
from libtestgui import dialogs

def load_file(parent, nc_code_file=None):
	# File load buttons don't pass a file name it has to be read from the property
	load_file_btn = False
	if not nc_code_file: # function called by a file load button
		if parent.sender() is not None:
			if parent.sender().property('function') == 'load_file':
				if parent.sender().property('filename'):
					nc_code_file = parent.sender().property('filename')
					load_file_btn = True
				else:
					msg = ('The property filename\n'
					'was not found. Loading aborted!')
					dialogs.warn_msg_ok(parent, msg, 'Configuration Error')

	if '~' in nc_code_file:
		nc_code_file = os.path.expanduser(nc_code_file)
	elif not os.path.isfile(nc_code_file): # try adding the nc code dir path to the file name
		nc_code_file = os.path.join(parent.nc_code_dir, nc_code_file)
	if os.path.isfile(nc_code_file):
		parent.command.program_open(nc_code_file)
		parent.command.wait_complete()
		if 'plot_widget' in parent.child_names:
			parent.plotter.clear_live_plotter()

		if 'gcode_pte' in parent.child_names:
			text = open(nc_code_file).read()
			parent.gcode_pte.setPlainText(text)
			if 'actionSave' in parent.child_names:
				parent.actionSave.setEnabled(True)
			if 'actionSave_As' in parent.child_names:
				parent.actionSave_As.setEnabled(True)

		if 'file_lb' in parent.child_names:
			base = os.path.basename(nc_code_file)
			parent.file_lb.setText(base)

		# update controls
		for item in parent.file_edit_items:
			getattr(parent, item).setEnabled(True)
		if 'start_line_lb' in parent.child_names:
			parent.start_line_lb.setText('0')
		if 'reload_pb' in parent.child_names:
			parent.reload_pb.setEnabled(True)
		if 'actionReload' in parent.child_names:
			parent.actionReload.setEnabled(True)

		if not load_file_btn: # called by menu or file open button
			# get recent files from settings
			keys = parent.settings.allKeys()
			file_list = []
			for key in keys:
				if key.startswith('recent_files'):
					file_list.append(parent.settings.value(key))
			# if the g code file is in the list remove it
			if nc_code_file in file_list:
				file_list.remove(nc_code_file)
			# insert the g code file at the top of the list
			file_list.insert(0, nc_code_file)
			# trim the list to 10
			file_list = file_list[:10]

			# add files back into settings
			parent.settings.beginGroup('recent_files')
			parent.settings.remove('')
			for i, item in enumerate(file_list):
				parent.settings.setValue(str(i), item)
			parent.settings.endGroup()

			# clear recent menu
			if parent.findChild(QMenu, 'menuRecent'):
				parent.menuRecent.clear()
				# add the recent files from settings
				keys = parent.settings.allKeys()
				for key in keys:
					if key.startswith('recent_files'):
						path = parent.settings.value(key)
						name = os.path.basename(path)
						a = parent.menuRecent.addAction(name)
						a.triggered.connect(partial(load_file, parent, path))

		if 'save_pb' in parent.child_names:
			if hasattr(parent.save_pb, 'led'):
				parent.save_pb.led = False
		if 'reload_pb' in parent.child_names:
			if hasattr(parent.reload_pb, 'led'):
				parent.reload_pb.led = False

	else: # file not found
		msg = (f'{nc_code_file}\n'
		'was not found. Loading aborted!')
		dialogs.warn_msg_ok(parent, msg, 'File Missing')

def action_open(parent): # actionOpen
	nc_code_file = utilities.file_chooser(parent, 'Open File', 'open')
	if nc_code_file: load_file(parent, nc_code_file)

def action_edit(parent): # actionEdit
	parent.status.poll
	nc_code_file = parent.status.file or False
	if not nc_code_file:
		msg = ('No File is open.\nDo you want to open a file?')
		response = dialogs.warn_msg_yes_no(parent, msg, 'No File Loaded')
		if response:
			action_open(parent)
			return
		else:
			return

	if parent.editor:
		if shutil.which(parent.editor.lower()) is not None:
			subprocess.Popen([parent.editor, nc_code_file])
		else:
			select_editor(parent, nc_code_file)
	else:
		msg = ('No Editor was found\nin the ini Display section\n'
			'Do you want to select an Editor?')
		if dialogs.warn_msg_yes_no(parent, msg, 'No Editor Configured'):
			select_editor(parent, nc_code_file)

def action_estop(parent): # actionE_Stop
	if parent.status.task_state == emc.STATE_ESTOP:
		parent.command.state(emc.STATE_ESTOP_RESET)
		if parent.sender().objectName() == 'actionE_Stop':
			if 'estop_pb' in parent.child_names:
				parent.estop_pb.setChecked(True)
	else:
		parent.command.state(emc.STATE_ESTOP)
		if parent.sender().objectName() == 'actionE_Stop':
			if 'estop_pb' in parent.child_names:
				parent.estop_pb.setChecked(False)
		if 'power_pb' in parent.child_names:
			parent.power_pb.setChecked(False)

def action_power(parent): # actionPower
	if parent.status.task_state == emc.STATE_ESTOP_RESET:
		if 'override_limits_cb' in parent.child_names:
			if parent.override_limits_cb.isChecked():
				parent.command. override_limits()
		parent.command.state(emc.STATE_ON)
		if parent.sender().objectName() == 'actionPower':
			if 'power_pb' in parent.child_names:
				parent.power_pb.setChecked(True)
	else:
		parent.command.state(emc.STATE_OFF)
		if parent.sender().objectName() == 'actionPower':
			if 'power_pb' in parent.child_names:
				parent.power_pb.setChecked(False)

def action_run(parent, start=0): # actionRun
	if parent.status.task_mode != emc.MODE_AUTO:
		parent.command.mode(emc.MODE_AUTO)
		parent.command.wait_complete()
	parent.command.auto(emc.AUTO_RUN, start)

def action_run_from_line(parent): # actionRun_from_Line
	if 'gcode_pte' in parent.child_names:
		cursor = parent.gcode_pte.textCursor()
		selected_block = cursor.blockNumber() # get current block number
		action_run(parent, selected_block)

def action_step(parent): # actionStep
	if parent.status.task_state == emc.STATE_ON:
		if parent.status.task_mode != emc.MODE_AUTO:
			parent.command.mode(emc.MODE_AUTO)
			parent.command.wait_complete()
		parent.command.auto(emc.AUTO_STEP)

def action_pause(parent): # actionPause
	if parent.status.task_mode == emc.MODE_AUTO: # program is running
		parent.command.auto(emc.AUTO_PAUSE)

def action_resume(parent): # actionResume
	if parent.status.paused:
		parent.command.auto(emc.AUTO_RESUME)

def action_stop(parent): # actionStop
	parent.status.poll()
	if parent.status.interp_state != emc.INTERP_IDLE:
		parent.command.abort()

def action_reload(parent): # actionReload
	if parent.status.task_mode != emc.MODE_MANUAL:
		parent.command.mode(emc.MODE_MANUAL)
		parent.command.wait_complete()
	parent.command.program_open(parent.status.file)
	if 'plot_widget' in parent.child_names:
		parent.plotter.clear_live_plotter()
		parent.plotter.update()
		parent.plotter.load(parent.status.file)
	if 'gcode_pte' in parent.child_names:
		with open(parent.status.file) as f:
			parent.gcode_pte.setPlainText(f.read())

def action_save(parent): # actionSave
	text = parent.gcode_pte.toPlainText()
	nc_code = text.splitlines()
	with open(parent.status.file, 'w') as f:
		f.writelines(line + "\n" for line in nc_code)
	parent.statusBar().showMessage('Save Action completed!', 10000)

def action_save_as(parent): # actionSave_As
	if os.path.isdir(os.path.expanduser('~/linuxcnc/nc_files')):
		gcode_dir = os.path.expanduser('~/linuxcnc/nc_files')
	else:
		gcode_dir = os.path.expanduser('~/')
	new_nc_code_file, file_type = QFileDialog.getSaveFileName(None,
	caption="Save As", directory=gcode_dir,
	filter='G code Files (*.ngc *.NGC);;All Files (*)', options=QFileDialog.Option.DontUseNativeDialog,)
	if new_nc_code_file:
		with open(parent.status.file, 'r') as cf:
			gcode = cf.read()
		with open(new_nc_code_file, 'w') as f:
			f.write(gcode)
		load_file(parent, new_nc_code_file)

def action_edit_tool_table (parent):
	pass

def action_ladder_editor (parent):
	pass

def action_reload_tool_table (parent):
	pass

def action_quit (parent): # actionQuit
	parent.close()

def action_clear_mdi (parent):
	pass

def action_copy_mdi (parent):
	pass

def action_save_mdi (parent):
	pass

def action_show_hal (parent): # actionShow_HAL
	subprocess.Popen('halshow', cwd=parent.config_path)

def action_hal_meter(parent): # actionHal_Meter
	subprocess.Popen('halmeter', cwd=parent.config_path)

def action_hal_scope(parent): # actionHal_Scope
	subprocess.Popen('halscope', cwd=parent.config_path)

def action_about (parent):
	pass

def action_quick_reference (parent):
	pass

def action_toggle_dro (parent, checked):
	if checked:
		parent.plotter.enable_dro = True
		parent.settings.setValue('Plot_Settings/show_dro', 'True')
	else:
		parent.plotter.enable_dro = False
		parent.settings.setValue('Plot_Settings/show_dro', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_limits (parent, checked):
	if checked:
		parent.plotter.show_limits = True
		parent.settings.setValue('Plot_Settings/show_limits', 'True')
	else:
		parent.plotter.show_limits = False
		parent.settings.setValue('Plot_Settings/show_limits', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_extents_option (parent, checked):
	if checked:
		parent.plotter.show_extents_option = True
		parent.settings.setValue('Plot_Settings/show_extents_option', 'True')
	else:
		parent.plotter.show_extents_option = False
		parent.settings.setValue('Plot_Settings/show_extents_option', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_live_plot (parent, checked):
	if checked:
		parent.plotter.show_live_plot = True
		parent.settings.setValue('Plot_Settings/show_live_plot', 'True')
	else:
		parent.plotter.show_live_plot = False
		parent.settings.setValue('Plot_Settings/show_live_plot', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_velocity (parent, checked):
	if checked:
		parent.plotter.show_velocity = True
		parent.settings.setValue('Plot_Settings/show_velocity', 'True')
	else:
		parent.plotter.show_velocity = False
		parent.settings.setValue('Plot_Settings/show_velocity', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_metric_units (parent, checked):
	if not parent.auto_plot_units:
		if checked:
			parent.plotter.metric_units = True
			parent.settings.setValue('Plot_Settings/metric_units', 'True')
		else:
			parent.plotter.metric_units = False
			parent.settings.setValue('Plot_Settings/metric_units', 'False')
		parent.plotter.update()
	parent.settings.sync()

def action_toggle_program (parent, checked):
	if checked:
		parent.plotter.show_program = True
		parent.settings.setValue('Plot_Settings/show_program', 'True')
	else:
		parent.plotter.show_program = False
		parent.settings.setValue('Plot_Settings/show_program', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_rapids (parent, checked):
	if checked:
		parent.plotter.show_rapids = True
		parent.settings.setValue('Plot_Settings/show_rapids', 'True')
	else:
		parent.plotter.show_rapids = False
		parent.settings.setValue('Plot_Settings/show_rapids', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_tool (parent, checked):
	if checked:
		parent.plotter.show_tool = True
		parent.settings.setValue('Plot_Settings/show_tool', 'True')
	else:
		parent.plotter.show_tool = False
		parent.settings.setValue('Plot_Settings/show_tool', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_lathe_radius (parent, checked):
	if checked:
		parent.plotter.show_lathe_radius = True
		parent.settings.setValue('Plot_Settings/show_lathe_radius', 'True')
	else:
		parent.plotter.show_lathe_radius = False
		parent.settings.setValue('Plot_Settings/show_lathe_radius', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_dtg (parent, checked):
	if checked:
		parent.plotter.show_dtg = True
		parent.settings.setValue('Plot_Settings/show_dtg', 'True')
	else:
		parent.plotter.show_dtg = False
		parent.settings.setValue('Plot_Settings/show_dtg', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_offsets (parent, checked):
	if checked:
		parent.plotter.show_offsets = True
		parent.settings.setValue('Plot_Settings/show_offsets', 'True')
	else:
		parent.plotter.show_offsets = False
		parent.settings.setValue('Plot_Settings/show_offsets', 'False')
	parent.plotter.update()
	parent.settings.sync()

def action_toggle_overlay (parent, checked):
	if checked:
		parent.plotter.show_overlay = False
		parent.settings.setValue('Plot_Settings/show_overlay', 'True')
	else:
		parent.plotter.show_overlay = True
		parent.settings.setValue('Plot_Settings/show_overlay', 'False')
	parent.plotter.update()
	parent.settings.sync()





