import subprocess, os

from PyQt6.QtWidgets import QMenu

import linuxcnc as emc

from libtestgui import utilities

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
		if 'file_lb' in parent.child_names:
			base = os.path.basename(nc_code_file)
			parent.file_lb.setText(base)

		# update controls
		for item in parent.file_edit_items:
			getattr(parent, item).setEnabled(True)
		if 'start_line_lb' in parent.child_names:
			parent.start_line_lb.setText('0')

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



def action_estop(parent): # actionEstop
	if parent.status.task_state == emc.STATE_ESTOP:
		parent.command.state(emc.STATE_ESTOP_RESET)
	else:
		parent.command.state(emc.STATE_ESTOP)

def action_power(parent): # actionPower
	if parent.status.task_state == emc.STATE_ESTOP_RESET:
		if 'override_limits_cb' in parent.child_names:
			if parent.override_limits_cb.isChecked():
				parent.command. override_limits()
		parent.command.state(emc.STATE_ON)
	else:
		parent.command.state(emc.STATE_OFF)

def action_run (parent):
	pass

def action_run_from_line (parent):
	pass

def action_step (parent):
	pass

def action_pause (parent):
	pass

def action_resume (parent):
	pass

def action_stop (parent):
	pass

def action_edit (parent):
	pass

def action_reload (parent):
	pass

def action_save (parent):
	pass

def action_save_as (parent):
	pass

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

def action_hal_meter (parent):
	pass

def action_hal_scope (parent):
	pass

def action_about (parent):
	pass

def action_quick_reference (parent):
	pass


def action_show_hal(parent): # actionShow_HAL
	subprocess.Popen('halshow', cwd=parent.config_path)




