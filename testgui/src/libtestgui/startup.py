import os

from functools import partial
from collections import deque

from PyQt6.QtWidgets import QWidget, QPushButton, QMenu, QListView
from PyQt6.QtWidgets import QLabel, QSpinBox, QDoubleSpinBox, QSlider
from PyQt6.QtWidgets import QAbstractButton, QCheckBox, QProgressBar
from PyQt6.QtWidgets import QVBoxLayout, QLCDNumber, QRadioButton
from PyQt6.QtGui import QAction

import hal

from libtestgui import actions
from libtestgui import commands
from libtestgui import dialogs
from libtestgui import probe
from libtestgui import utilities

AXES = ['x', 'y', 'z', 'a', 'b', 'c', 'u', 'v', 'w']

def find_children(parent): # get the object names of all widgets
	parent.child_names = []
	children = parent.findChildren(QWidget)
	for child in children:
		if child.objectName():
			parent.child_names.append(child.objectName())
	parent.actions = parent.findChildren(QAction)
	for action in parent.actions:
		if action.objectName():
			parent.child_names.append(action.objectName())
			if 'toolBar' in parent.child_names:
				widget_name = f'flex_{action.objectName()[6:].replace(" ", "_")}'
				# make sure the action is in the tool bar
				if parent.toolBar.widgetForAction(action) is not None:
					parent.toolBar.widgetForAction(action).setObjectName(widget_name)
					setattr(parent, widget_name, parent.toolBar.widgetForAction(action))
					parent.child_names.append(widget_name)
	menus = parent.findChildren(QMenu)
	for menu in menus:
		if menu.objectName():
			parent.child_names.append(menu.objectName())

def setup_vars(parent):
	parent.program_units = False
	parent.g_codes = ()
	parent.homed = parent.status.homed
	parent.program_paused = False
	parent.motion_line = -1
	parent.plot_units = False
	parent.probing = False

def setup_enables(parent):

	# enable and disable lists
	parent.state_estop_disabled = [] # everything but estop_pb
	parent.state_estop_reset_disabled = []
	parent.state_estop_reset_enabled = []
	parent.state_on_enabled = []
	parent.homed_enabled = []
	parent.program_running_disabled = []
	parent.run_controls = [] # enabled when homed, manual, file loaded
	parent.file_load_controls = [] # disable when a program or mdi is running
	parent.mdi_controls = []
	parent.probe_controls = []

	# STATE_ESTOP everything is disabled except the estop and file open save etc.
	state_estop_items = ['power_pb', 'run_pb', 'run_from_line_pb',
	'step_pb', 'pause_pb', 'resume_pb', 'jog_selected_plus', 'jog_selected_minus',
	'home_all_pb', 'unhome_all_pb', 'run_mdi_pb', 'mdi_s_pb', 'spindle_start_pb',
	'spindle_fwd_pb', 'spindle_rev_pb', 'spindle_stop_pb', 'spindle_plus_pb',
	'spindle_minus_pb', 'flood_pb', 'mist_pb', 'actionPower', 'actionRun',
	'actionRun_From_Line', 'actionStep', 'actionPause', 'actionResume',
	'tool_change_pb', 'touchoff_selected_pb', 'touchoff_selected_tool_pb']

	for i in range(9):
		state_estop_items.append(f'home_pb_{i}')
		state_estop_items.append(f'unhome_pb_{i}')
		state_estop_items.append(f'jog_plus_pb_{i}')
		state_estop_items.append(f'jog_minus_pb_{i}')

	for axis in AXES:
		state_estop_items.append(f'touchoff_pb_{axis}')
		state_estop_items.append(f'tool_touchoff_{axis}')
		state_estop_items.append(f'zero_{axis}_pb')

	for i in range(100):
		state_estop_items.append(f'tool_change_pb_{i}')

	for i in range(1, 10):
		state_estop_items.append(f'change_cs_{i}')

	for name in state_estop_items:
		if name in parent.child_names:
			parent.state_estop_disabled.append(name)

	# STATE_ESTOP_RESET everything is disabled except power_pb
	state_estop_reset_disabled_items = ['run_pb', 'run_from_line_pb', 'step_pb',
		'pause_pb', 'resume_pb', 'jog_selected_plus', 'jog_selected_minus',
		'home_all_pb', 'unhome_all_pb', 'run_mdi_pb', 'mdi_s_pb',
		'spindle_start_pb', 'spindle_fwd_pb', 'spindle_rev_pb', 'spindle_stop_pb',
		'spindle_plus_pb', 'spindle_minus_pb', 'flood_pb', 'mist_pb', 'actionPower',
		'actionRun', 'actionRun_From_Line', 'actionStep', 'actionPause',
		'actionResume', 'tool_change_pb', 'touchoff_selected_pb',
		'touchoff_selected_tool_pb']

	for i in range(9):
		state_estop_reset_disabled_items.append(f'home_pb_{i}')
		state_estop_reset_disabled_items.append(f'unhome_pb_{i}')
		state_estop_reset_disabled_items.append(f'jog_plus_pb_{i}')
		state_estop_reset_disabled_items.append(f'jog_minus_pb_{i}')

	for item in AXES:
		state_estop_reset_disabled_items.append(f'touchoff_pb_{item}')
		state_estop_reset_disabled_items.append(f'tool_touchoff_{item}')

	for i in range(100):
		state_estop_reset_disabled_items.append(f'tool_change_pb_{i}')

	for i in range(1, 10):
		state_estop_reset_disabled_items.append(f'change_cs_{i}')

	for name in state_estop_reset_disabled_items:
		if name in parent.child_names:
			parent.state_estop_reset_disabled.append(name)

	# the only things enabled when estop is reset
	for name in ['power_pb', 'actionPower']:
		if name in parent.child_names:
			parent.state_estop_reset_enabled.append(name)

	# STATE_ON enable jog and homing
	parent.state_on_enabled = []
	for i in range(9):
		if f'jog_plus_pb_{i}' in parent.child_names:
			parent.state_on_enabled.append(f'jog_plus_pb_{i}')
		if f'jog_minus_pb_{i}' in parent.child_names:
			parent.state_on_enabled.append(f'jog_minus_pb_{i}')

	parent.program_running_enable = []
	for item in ['pause_pb', 'actionPause']:
		if item in parent.child_names:
			parent.program_running_enable.append(item)

	parent.program_paused_enable = []
	for item in ['resume_pb', 'actionResume']:
		if item in parent.child_names:
			parent.program_paused_enable.append(item)

	# FIXME might need to remove run_from_line_pb and actionRun_From_Line if not configured correctly
	parent.program_running_disable = ['open_pb', 'reload_pb', 'run_pb',
	'run_from_line_pb', 'step_pb', 'jog_selected_plus', 'jog_selected_minus',
	'resume_pb', 'run_mdi_pb', 'home_all_pb', 'actionRun', 'actionOpen',
	'menuRecent', 'actionReload', 'actionRun_From_Line', 'actionStep',
	'actionResume', 'unhome_all_pb', 'tool_change_pb']

	for i in range(9):
		parent.program_running_disable.append(f'home_pb_{i}')
		parent.program_running_disable.append(f'unhome_pb_{i}')

	for i in range(100):
		parent.program_running_disable.append(f'tool_change_pb_{i}')

	for i in range(1, 10):
		parent.program_running_disable.append(f'change_cs_{i}')

	for item in AXES:
		parent.program_running_disable.append(f'touchoff_pb_{item}')
		parent.program_running_disable.append(f'tool_touchoff_{item}')

	parent.program_running_disable.append('mdi_s_pb')

	# remove any items not found in the gui
	for item in parent.program_running_disable:
		if item not in parent.child_names:
			parent.program_running_disable.remove(item)

def setup_status(parent):
	# Actual Position labels no offsets
	parent.status_position = {} # create an empty dictionary
	for i, axis in enumerate(AXES):
		label = f'actual_lb_{axis}'
		if label in parent.child_names:
			p = getattr(parent, label).property('precision')
			p = p if p is not None else parent.default_precision
			parent.status_position[f'{label}'] = [i, p] # label , joint & precision

	# G5x Offset Labels
	parent.status_g5x_offset = {} # create an empty dictionary
	for i, axis in enumerate(AXES):
		label = f'g5x_lb_{axis}'
		if label in parent.child_names:
			p = getattr(parent, label).property('precision')
			p = p if p is not None else parent.default_precision
			parent.status_g5x_offset[f'{label}'] = [i, p] # add the label, tuple position & precision

	# G92 Offset Labels
	parent.status_g92 = {} # create an empty dictionary
	for i, axis in enumerate(AXES):
		label = f'g92_lb_{axis}'
		if label in parent.child_names:
			p = getattr(parent, label).property('precision')
			p = p if p is not None else parent.default_precision
			parent.status_g92[f'{label}'] = [i, p] # add the label, tuple position & precision

	# DRO labels including offsets
	parent.status_dro = {} # create an empty dictionary
	for i, axis in enumerate(AXES):
		label = f'dro_lb_{axis}'
		if label in parent.child_names:
			p = getattr(parent, label).property('precision')
			p = p if p is not None else parent.default_precision
			parent.status_dro[f'{label}'] = [i, p] # add the label, tuple position & precision

def setup_run_controls(parent):
	file_run_items = ['run_pb', 'run_from_line_pb', 'step_pb', 'run_mdi_pb',
	'actionRun', 'actionRun_From_Line', 'actionStep', 'tool_change_pb']
	for item in file_run_items:
		if item in parent.child_names:
			parent.run_controls.append(item)
	for i in range(100):
		if f'tool_change_pb_{i}' in parent.child_names:
			parent.run_controls.append(item)
	for item in AXES:
		if f'tool_touchoff_{item}' in parent.child_names:
			parent.run_controls.append(f'tool_touchoff_{item}')
		if f'touchoff_pb_{item}' in parent.child_names:
			parent.run_controls.append(f'touchoff_pb_{item}')

def setup_buttons(parent): # connect buttons to functions
	if 'estop_pb' in parent.child_names:
		parent.estop_pb.toggled.connect(partial(actions.action_estop, parent))
		parent.estop_pb.setCheckable(True)

	if 'power_pb' in parent.child_names:
		parent.power_pb.toggled.connect(partial(actions.action_power, parent))
		parent.power_pb.setCheckable(True)

	# file items if not loaded disable
	file_items = ['edit_pb', 'reload_pb', 'save_as_pb', 'search_pb', 'actionEdit',
		'actionReload', 'actionSave_As']

	parent.file_edit_items = []
	for item in file_items:
		if item in parent.child_names:
			parent.file_edit_items.append(item)

	action_buttons = {
	'run_pb': 'action_run',
	'step_pb': 'action_step',
	'pause_pb': 'action_pause',
	'resume_pb': 'action_resume',
	'stop_pb': 'action_stop',
	'open_pb': 'action_open',
	'edit_pb': 'action_edit',
	'reload_pb': 'action_reload',
	'save_pb': 'action_save',
	'save_as_pb': 'action_save_as',
	'edit_tool_table_pb': 'action_edit_tool_table',
	'edit_ladder_pb': 'action_ladder_editor',
	'reload_tool_table_pb': 'action_reload_tool_table',
	'quit_pb': 'action_quit',
	'clear_mdi_history_pb': 'action_clear_mdi',
	'copy_mdi_history_pb': 'action_copy_mdi',
	'save_mdi_history_pb': 'action_save_mdi',
	'show_hal_pb': 'action_show_hal',
	'hal_meter_pb': 'action_hal_meter',
	'hal_scope_pb': 'action_hal_scope',
	'about_pb': 'action_about',
	'quick_reference_pb': 'action_quick_reference'
	}

	if 'run_from_line_pb' in parent.child_names:
		if 'gcode_pte' in parent.child_names:
			action_buttons['run_from_line_pb'] = 'action_run_from_line'
		else:
			parent.run_from_line_pb.setEnabled(False)
			parent.state_estop_disabled.remove('run_from_line_pb')
			parent.run_controls.remove('run_from_line_pb')
			msg = ('The Run From Line button can not\n'
			'function without the Code Viewer.\n'
			'The Run From Line button will be disabled.')
			dialogs.error_msg_ok(parent, msg, 'Configuration Error!')

	if 'edit_pb' in parent.child_names and not parent.editor:
		del action_buttons['edit_pb']
		parent.file_edit_items.remove('edit_pb')
		parent.edit_pb.setEnabled(False)
		msg = ('The Edit button was found but no\n'
		'editor was found in the ini file\n'
		'or the editor is not installed\n'
		'The Edit button will be disabled.')
		dialogs.error_msg_ok(parent, msg, 'Configuration Error')

	for key, value in action_buttons.items():
		if key in parent.child_names:
			getattr(parent, key).clicked.connect(partial(getattr(actions, value), parent))

	# disable home all if home sequence is not found
	if 'home_all_pb' in parent.child_names:
		if utilities.home_all_check(parent):
			parent.home_all_pb.clicked.connect(partial(commands.home_all, parent))
		else:
			parent.home_all_pb.setEnabled(False)
			msg = ('All joints must have the HOME_SEQUENCE set\n'
			'in order for the Home All button to function.\n'
			'The Home All button will be disabled.')
			dialogs.error_msg_ok(parent, msg, 'Configuration Error')
			if 'home_all_pb' in parent.state_estop_disabled:
				del parent.state_estop_disabled['home_all_pb']
			if 'home_all_pb' in parent.state_estop_reset_disabled:
				del parent.state_estop_reset_disabled['home_all_pb']

	if 'unhome_all_pb' in parent.child_names:
			parent.unhome_all_pb.clicked.connect(partial(commands.unhome_all, parent))

	for i in range(9):
		if f'home_pb_{i}' in parent.child_names:
			getattr(parent, f'home_pb_{i}').clicked.connect(partial(commands.home, parent))
			parent.state_estop_disabled.append(f'home_pb_{i}')
		if f'unhome_pb_{i}' in parent.child_names:
			getattr(parent, f'unhome_pb_{i}').clicked.connect(partial(commands.unhome, parent))
			parent.state_estop_disabled.append(f'unhome_pb_{i}')

	# file open buttons
	for child in parent.findChildren(QPushButton):
		if child.property('function') == 'load_file':
			child.clicked.connect(partial(actions.load_file, parent))
			parent.file_load_controls.append(child.objectName())

def setup_actions(parent): # setup menu actions
	actions_dict = {
		'actionOpen': 'action_open',
		'actionEdit': 'action_edit',
		'actionReload': 'action_reload',
		'actionSave': 'action_save',
		'actionSave_As': 'action_save_as',
		'actionEdit_Tool_Table': 'action_edit_tool_table',
		'actionReload_Tool_Table': 'action_reload_tool_table',
		'actionLadder_Editor': 'action_ladder_editor',
		'actionQuit': 'action_quit',
		'actionE_Stop': 'action_estop',
		'actionPower': 'action_power',
		'actionRun': 'action_run',
		'actionStep': 'action_step',
		'actionPause': 'action_pause',
		'actionResume': 'action_resume',
		'actionStop': 'action_stop',
		'actionClear_MDI_History': 'action_clear_mdi',
		'actionCopy_MDI_History': 'action_copy_mdi',
		'actionOverlay': 'action_toggle_overlay',
		'actionShow_HAL': 'action_show_hal',
		'actionHAL_Meter': 'action_hal_meter',
		'actionHAL_Scope': 'action_hal_scope',
		'actionAbout': 'action_about',
		'actionQuick_Reference': 'action_quick_reference',
		'actionClear_Live_Plot': 'action_clear_live_plot'}

	if 'actionRun_From_Line' in parent.child_names:
		if 'gcode_pte' in parent.child_names:
			actions_dict['actionRun_From_Line'] = 'action_run_from_line'
		else:
			parent.actionRun_From_Line.setEnabled(False)
			parent.state_estop_disabled.remove('actionRun_From_Line')
			parent.run_controls.remove('actionRun_From_Line')
			msg = ('The Run From Line Menu item can not\n'
			'function without the Code Viewer.\n'
			'The Run From Line Menu item will be disabled.')
			dialogs.error_msg_ok(parent, msg, 'Configuration Error!')

	if 'actionEdit' in parent.child_names and not parent.editor:
		del actions_dict['actionEdit']
		parent.file_edit_items.remove('actionEdit')
		parent.actionEdit.setEnabled(False)
		msg = ('The Edit Menu was found but no\n'
		'editor was found in the ini file.\n'
		'or the editor is not installed\n'
		'The Edit Menu will be disabled.')
		dialogs.error_msg_ok(parent, msg, 'Configuration Error')


	# if an action is found connect it to the function
	for key, value in actions_dict.items():
		if key in parent.child_names:
			getattr(parent, f'{key}').triggered.connect(partial(getattr(actions, f'{value}'), parent))

	# special check for the classicladder editor
	if not hal.component_exists("classicladder_rt"):
		if 'actionLadder_Editor' in parent.child_names:
			parent.actionLadder_Editor.setEnabled(False)
		if 'edit_ladder_pb' in parent.child_names:
			parent.edit_ladder_pb.setEnabled(False)

	# special check for MDI
	if 'mdi_history_lw' in parent.child_names:
		if 'actionClear_MDI_History' in parent.child_names:
			parent.actionClear_MDI_History.setEnabled(False)
		if 'actionCopy_MDI_History' in parent.child_names:
			parent.actionCopy_MDI_History.setEnabled(False)

def setup_mdi(parent):
	# mdi_command_le is required to run mdi commands
	# run_mdi_pb and mdi_history_lw are optional

	if 'mdi_command_le' in parent.child_names:
		parent.mdi_command_le.returnPressed.connect(partial(commands.run_mdi, parent))
	if 'run_mdi_pb' in parent.child_names:
		parent.run_mdi_pb.clicked.connect(partial(commands.run_mdi, parent))
		parent.homed_enabled.append('run_mdi_pb')

	if 'mdi_history_lw' in parent.child_names:
		path = os.path.dirname(parent.status.ini_filename)
		mdi_file = os.path.join(path, 'mdi_history.txt')
		if os.path.exists(mdi_file): # load mdi history
			with open(mdi_file, 'r') as f:
				history_list = f.readlines()
				for item in history_list:
					parent.mdi_history_lw.addItem(item.strip())
		parent.mdi_history_lw.itemSelectionChanged.connect(partial(commands.add_mdi, parent))

def setup_mdi_buttons(parent):
	for button in parent.findChildren(QPushButton):
		if button.property('function') == 'mdi':
			if button.property('command'):
				name = button.objectName()
				button.clicked.connect(partial(commands.mdi_button, parent))
				if not name.startswith('probe_'):
					parent.state_estop_disabled.append(name)
					parent.homed_enabled.append(name)
					parent.mdi_controls.append(name)

def setup_jog(parent):
	jog_buttons = []
	for i in range(parent.joints):
		if f'jog_plus_pb_{i}' in parent.child_names:
			jog_buttons.append(f'jog_plus_pb_{i}')
		if f'jog_minus_pb_{i}' in parent.child_names:
			jog_buttons.append(f'jog_minus_pb_{i}')

	if len(jog_buttons) > 0:
		for item in ['jog_vel_sl', 'jog_modes_cb']:
			# don't make the connection if all required widgets are not present
			if item not in parent.child_names:
				msg = (f'{item} is required to jog\n but was not found.\n'
					'Jog Buttons will be disabled.')
				dialogs.warn_msg_ok(parent, msg, 'Missing Item')
				for item in parent.jog_buttons:
					getattr(parent, item).setEnabled(False)
					if item in parent.state_estop_disabled:
						parent.state_estop_disabled.remove(item)
					if item in parent.state_estop_reset_disabled:
						parent.state_estop_reset_disabled.remove(item)
					if item in parent.state_on_enabled:
						parent.state_on_enabled.remove(item)
				return
		# ok to connect if we get this far
		for item in jog_buttons: # connect jog buttons
			getattr(parent, item).pressed.connect(partial(getattr(commands, 'jog'), parent))
			getattr(parent, item).released.connect(partial(getattr(commands, 'jog'), parent))

		parent.jog_modes_cb.setView(QListView())
		parent.jog_modes_cb.addItem('Continuous', False)

		# setup the jog increment combo box items
		if parent.jog_increments:
			for item in parent.jog_increments.split(','):
				item = item.strip()
				text, data, suffix = utilities.is_valid_increment(parent, item)
				if data:
					jog_distance = utilities.conv_units(data, suffix.lower(), parent.units)
					parent.jog_modes_cb.addItem(text, jog_distance)
				else:
					msg = ('The DISPLAY INCREMENTS entry in the ini\n'
					f'> {item} < is not a valid unit and will not\n'
					'be used. INCREMENTS must be comma seperated.')
					dialogs.error_msg_ok(parent, msg, 'Configuration Error')

def setup_plot(parent):
	if 'plot_widget' in parent.child_names:
		# add the plotter to the container
		from libtestgui import flexplot
		parent.plotter = flexplot.emc_plot(parent)
		layout = QVBoxLayout(parent.plot_widget)
		layout.addWidget(parent.plotter)

		# set the font size
		parent.plotter._font = f'monospace bold {parent.dro_font_size}'

		# set background color if specified
		if parent.plot_background_color:
			parent.plotter.background_color = parent.plot_background_color

		view_checkboxes = {
			'view_dro_cb': 'action_toggle_dro',
			'view_limits_cb': 'action_toggle_limits',
			'view_extents_option_cb': 'action_toggle_extents_option',
			'view_live_plot_cb': 'action_toggle_live_plot',
			'view_velocity_cb': 'action_toggle_velocity',
			'view_metric_units_cb': 'action_toggle_metric_units',
			'view_program_cb': 'action_toggle_program',
			'view_rapids_cb': 'action_toggle_rapids',
			'view_tool_cb': 'action_toggle_tool',
			'view_lathe_radius_cb': 'action_toggle_lathe_radius',
			'view_dtg_cb': 'action_toggle_dtg',
			'view_offsets_cb': 'action_toggle_offsets',
			'view_overlay_cb': 'action_toggle_overlay'
		}

		for key, value in view_checkboxes.items():
			if key in parent.child_names:
				getattr(parent, f'{key}').clicked.connect(partial(getattr(actions, f'{value}'), parent))

		if parent.auto_plot_units: # disable metric units
			if 'view_metric_units_cb' in parent.child_names:
				parent.view_metric_units_cb.setEnabled(False)

def setup_hal(parent):
	hal_labels = []
	hal_avr_float_labels = [] # average float labels
	hal_avr_int_labels = [] # average int labels
	hal_multi_state_labels = [] # multi state labels
	hal_buttons = []
	hal_spinboxes = []
	hal_dbl_spinboxes = []
	hal_sliders = []
	hal_lcds = []
	hal_leds = []
	hal_progressbar = []
	parent.hal_io_check = {}
	parent.hal_io_int = {}
	parent.hal_io_float = {}
	parent.hal_avr_float = {}
	parent.hal_avr_int = {}
	parent.hal_readers = {}
	parent.hal_ms_labels = {}
	parent.hal_bool_labels = {}
	parent.hal_progressbars = {}
	parent.hal_floats = {}

	for child in parent.findChildren(QWidget):
		if child.property('function') == 'hal_pin':
			if isinstance(child, QAbstractButton): # QCheckBox, QPushButton, QRadioButton, and QToolButton
				hal_buttons.append(child)
			elif isinstance(child, QSpinBox):
				hal_spinboxes.append(child)
			elif isinstance(child, QDoubleSpinBox):
				hal_dbl_spinboxes.append(child)
			elif isinstance(child, QSlider):
				hal_sliders.append(child)
			elif isinstance(child, QProgressBar):
				hal_progressbar.append(child)
			elif isinstance(child, QLCDNumber):
				hal_lcds.append(child)
			elif isinstance(child, QLabel):
				hal_labels.append(child)
		elif child.property('function') == 'hal_avr_f':
			if isinstance(child, QLabel):
				hal_avr_float_labels.append(child)
		elif child.property('function') == 'hal_msl':
			if isinstance(child, QLabel):
				hal_multi_state_labels.append(child)

	##### HAL BUTTON & CHECKBOX & RADIO BUTTON #####
	if len(hal_buttons) > 0:
		for button in hal_buttons:
			button_name = button.objectName()
			pin_name = button.property('pin_name')

			if isinstance(button, QPushButton) or isinstance(button, QCheckBox):
				confirm = button.property('confirm')
			else:
				confirm = False
			if confirm and not button.isCheckable():
				button.setEnabled(False)
				msg = (f'The HAL Button {button_name}\n'
				f'with the text {button.text()}\n'
				'has confirm set but is not checkable\n'
				f'The {button_name} button will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if pin_name in [None, '']:
				button.setEnabled(False)
				msg = (f'The HAL Button {button_name}\n'
				f'with the text {button.text()}\n'
				'pin name is blank or missing\n'
				'The HAL pin can not be created.\n'
				f'The {button_name} button will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if pin_name in dir(parent):
				button.setEnabled(False)
				msg = (f'HAL Button {button_name}\n'
				f'pin name {pin_name}\n'
				'is already used in Flex GUI\n'
				'The HAL pin can not be created.\n'
				f'The {button_name} button will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			hal_type = getattr(hal, 'HAL_BIT')
			hal_dir = getattr(hal, 'HAL_OUT')
			setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal_type, hal_dir))
			pin = getattr(parent, f'{pin_name}')

			if button.isCheckable() and not confirm:
				button.toggled.connect(lambda checked, pin=pin: (pin.set(checked)))
				# set the hal pin default
				setattr(parent.halcomp, pin_name, button.isChecked())
			elif button.isCheckable() and confirm:
				button.toggled.connect(partial(utilities.hal_confirm, parent))
			else:
				button.pressed.connect(lambda pin=pin: (pin.set(True)))
				button.released.connect(lambda pin=pin: (pin.set(False)))

			utilities.set_hal_enables(parent, button)

	##### HAL SPINBOX #####
	if len(hal_spinboxes) > 0:
		valid_types = ['HAL_S32', 'HAL_U32']
		for spinbox in hal_spinboxes:
			spinbox_name = spinbox.objectName()
			pin_name = spinbox.property('pin_name')

			if pin_name in [None, '']:
				spinbox.setEnabled(False)
				msg = (f'HAL SPINBOX {spinbox_name}\n'
				'pin name is blank or missing\n'
				'The HAL pin can not be created.\n'
				f'The {spinbox_name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if pin_name in dir(parent):
				spinbox.setEnabled(False)
				msg = (f'HAL Spinbox {spinbox_name}\n'
				f'pin name {pin_name}\n'
				'is already used in Flex GUI\n'
				'The HAL pin can not be created.\n'
				f'The {spinbox_name} spinbox will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			hal_type = spinbox.property('hal_type')
			if hal_type not in valid_types:
				spinbox.setEnabled(False)
				msg = (f'{hal_type} is not valid\n'
				'for a HAL spinbox, only\n'
				'HAL_S32 or HAL_U32\n'
				f'The {spinbox_name} spinbox will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error!')
				continue

			hal_type = getattr(hal, f'{hal_type}')
			hal_dir = getattr(hal, 'HAL_OUT')
			parent.halcomp.newpin(pin_name, hal_type, hal_dir)
			# set the default value of the spin box to the hal pin
			setattr(parent.halcomp, pin_name, spinbox.value())
			spinbox.valueChanged.connect(partial(utilities.update_hal_spinbox, parent))

			utilities.set_hal_enables(parent, spinbox)

			# FIXME look into this to see if it can be added to utilities.set_hal_enables
			#if parent.probe_controls: # make sure the probing_enable_pb is there
			#	if spinbox_name.startswith('probe_'): # don't enable it when power is on
			#		parent.probe_controls.append(spinbox_name)

	##### HAL Double Spinboxes #####
	if len(hal_dbl_spinboxes) > 0:
		for spinbox in hal_dbl_spinboxes:
			spinbox_name = spinbox.objectName()
			pin_name = spinbox.property('pin_name')

			if pin_name in [None, '']:
				spinbox.setEnabled(False)
				msg = (f'HAL SPINBOX {spinbox_name}\n'
				'pin name is blank or missing\n'
				'The HAL pin can not be created.\n'
				f'The {spinbox_name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if pin_name in dir(parent):
				spinbox.setEnabled(False)
				msg = (f'HAL Spinbox {spinbox_name}\n'
				f'pin name {pin_name}\n'
				'is already used in Flex GUI\n'
				'The HAL pin can not be created.\n'
				f'The {spinbox_name} spinbox will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			hal_type = getattr(hal, 'HAL_FLOAT')
			hal_dir = getattr(hal, 'HAL_OUT')
			parent.halcomp.newpin(pin_name, hal_type, hal_dir)
			# set the default value of the spin box to the hal pin
			setattr(parent.halcomp, pin_name, spinbox.value())
			spinbox.valueChanged.connect(partial(utilities.update_hal_spinbox, parent))

			utilities.set_hal_enables(parent, spinbox)

	##### HAL SLIDERS #####
	if len(hal_sliders) > 0:
		valid_types = ['HAL_S32', 'HAL_U32']
		for slider in hal_sliders:
			slider_name = slider.objectName()
			pin_name = slider.property('pin_name')

			if pin_name in [None, '']:
				slider.setEnabled(False)
				msg = (f'HAL SLIDER {slider_name}\n'
				'pin name is blank or missing\n'
				'The HAL pin can not be created.\n'
				f'The {slider_name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if pin_name in dir(parent):
				slider.setEnabled(False)
				msg = (f'HAL Slider {slider_name}\n'
				f'pin name {pin_name}\n'
				'is already used in Flex GUI\n'
				'The HAL pin can not be created.\n')
				f'The {slider_name} slider will be disabled.'
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			hal_type = slider.property('hal_type')
			if hal_type not in valid_types:
				slider.setEnabled(False)
				msg = (f'{hal_type} is not valid\n'
				'for a HAL slider, only\n'
				'HAL_S32 or HAL_U32 are valid\n'
				f'The {slider_name} slider will be disabled.\n')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error!')
				continue

			hal_type = getattr(hal, f'{hal_type}')
			hal_dir = getattr(hal, 'HAL_OUT')
			parent.halcomp.newpin(pin_name, hal_type, hal_dir)
			# set the default value of the spin box to the hal pin
			setattr(parent.halcomp, pin_name, slider.value())
			slider.valueChanged.connect(partial(utilities.update_hal_slider, parent))

			utilities.set_hal_enables(parent, slider)

			# FIXME look into this to see if it can be added to utilities.set_hal_enables
			#if parent.probe_controls: # make sure the probing_enable_pb is there
			#	if slider_name.startswith('probe_'): # don't enable it when power is on
			#		parent.probe_controls.append(slider_name)

	##### HAL PROGRESSBAR #####
	if len(hal_progressbar) > 0:
		valid_types = ['HAL_S32', 'HAL_U32']
		for progressbar in hal_progressbar:
			progressbar_name = progressbar.objectName()
			pin_name = progressbar.property('pin_name')

			if pin_name in [None, '']:
				progressbar.setEnabled(False)
				msg = (f'HAL PROGRESSBAR {progressbar_name}\n'
				'pin name is blank or missing\n'
				'The HAL pin can not be created.\n'
				f'The {progressbar_name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if pin_name in dir(parent):
				progressbar.setEnabled(False)
				msg = (f'HAL Label {progressbar_name}\n'
				f'pin name {pin_name}\n'
				'is already used in Flex GUI\n'
				'The HAL pin can not be created.\n'
				f'The {progressbar_name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			'''
			hal_type = progressbar.property('hal_type')
			if hal_type not in valid_types:
				progressbar.setEnabled(False)
				msg = (f'{hal_type} is not valid type for a HAL Progressbar\n'
				'only HAL_S32 or HAL_U32 can be used. \n'
				f'The {progressbar_name} progressbar will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error!')
				continue
			'''

			hal_type = getattr(hal, 'HAL_U32')
			hal_dir = getattr(hal, 'HAL_IN')
			setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal_type, hal_dir))
			# pin = getattr(parent, f'{pin_name}')
			parent.hal_progressbars[progressbar_name] = pin_name

	##### HAL_IO #####
	for child in parent.findChildren(QWidget):
		if child.property('function') == 'hal_io':
			child_name = child.objectName()
			pin_name = child.property('pin_name')

			if pin_name in [None, '']:
				child.setEnabled(False)
				msg = (f'The HAL I/O {child_name}\n'
				f'pin name is blank or missing\n'
				'The HAL pin can not be created.\n'
				f'The {child_name} button will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if isinstance(child, QCheckBox):
				setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal.HAL_BIT, hal.HAL_IO))
				child.stateChanged.connect(partial(utilities.update_hal_io, parent))
				parent.hal_io_check[child_name] = pin_name

			elif isinstance(child, QPushButton):
				if child.isCheckable():
					setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal.HAL_BIT, hal.HAL_IO))
					child.toggled.connect(partial(utilities.update_hal_io, parent))
					parent.hal_io_check[child_name] = pin_name
				else:
					child.setEnabled(False)
					msg = (f'The QPushButton {child_name} must be\n'
					'set to checkable to be a I/O button.\n'
					'The QPushButton will be disabled.')
					dialogs.error_msg_ok(parent, msg, 'Error')

			elif isinstance(child, QRadioButton):
				setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal.HAL_BIT, hal.HAL_IO))
				child.toggled.connect(partial(utilities.update_hal_io, parent))
				parent.hal_io_check[child_name] = pin_name

			elif isinstance(child, QSpinBox) or isinstance(child, QSlider):
				hal_type = child.property('hal_type')
				if hal_type in ['HAL_S32', 'HAL_U32']:
					hal_type = getattr(hal, f'{hal_type}')
					setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal_type, hal.HAL_IO))
					child.valueChanged.connect(partial(utilities.update_hal_io, parent))
					parent.hal_io_int[child_name] = pin_name
				else:
					child.setEnabled(False)
					msg = (f'The QSpinBox hal_type must be\n'
					'set to HAL_S32 or HAL_U32.\n'
					'The spinbox will be disabled')
					dialogs.error_msg_ok(parent, msg, 'Error')

			elif isinstance(child, QDoubleSpinBox):
				setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal.HAL_FLOAT, hal.HAL_IO))
				child.valueChanged.connect(partial(utilities.update_hal_io, parent))
				parent.hal_io_float[child_name] = pin_name

			utilities.set_hal_enables(parent, child)

	##### HAL LABEL #####
	if len(hal_labels) > 0:
		valid_types = ['HAL_BIT', 'HAL_FLOAT', 'HAL_S32', 'HAL_U32']
		for label in hal_labels:
			label_name = label.objectName()
			pin_name = label.property('pin_name')
			hal_type = label.property('hal_type')
			true_text = label.property('true_text')
			false_text = label.property('false_text')
			if any([true_text, false_text]):
				if not all([true_text, false_text]):
					label.setEnabled(False)
					msg = (f'HAL BOOL LABEL {label_name}\n'
					'the true text is blank or missing\n'
					'or the false text is blank or missing\n'
					'The HAL pin can not be created.\n'
					f'The {label_name} will be disabled.')
					dialogs.error_msg_ok(parent, msg, 'Configuration Error')
					continue
				elif all([true_text, false_text]):
					hal_type = 'HAL_BIT'

			if pin_name in [None, '']:
				label.setEnabled(False)
				msg = (f'HAL LABEL {label_name}\n'
				'pin name is blank or missing\n'
				'The HAL pin can not be created.\n'
				f'The {label_name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			# the pin_name can not be the same as a built in variable or object name
			if pin_name in parent.child_names:
				msg = (f'HAL Label {label_name}\n'
				f'pin name {pin_name}\n'
				'is already used in Flex GUI\n'
				'The HAL pin can not be created.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if hal_type not in valid_types:
				label.setEnabled(False)
				msg = (
				f'{hal_type} is not valid type for a\n'
				' HAL Label. Valid types are HAL_BIT, \n'
				'HAL_FLOAT, HAL_S32 or HAL_U32\n'
				f'The {label_name} label will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error!')
				continue

			hal_type = getattr(hal, f'{hal_type}')
			hal_dir = getattr(hal, 'HAL_IN')

			# Only create the pin if its not already created
			if pin_name in dir(parent):
				pin = getattr(parent, f'{pin_name}')
				if pin.get_type() != hal_type or pin.get_dir() != hal_dir:
					label.setEnabled(False)
					msg = (f'An existing HAL pin named {pin_name}\n'
						'exists, but has a different type or direction.\n'
						'The HAL object will not be created\n'
						'and the label will be disabled.')
					dialogs.critical_msg_ok(parent, msg, 'Configuration Error!')
					continue
			elif None not in [pin_name, hal_type, hal_dir]:
				setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal_type, hal_dir))

			# if hal type is float add it to hal_float with precision
			if hal_type == 2: # HAL_FLOAT
				p = label.property('precision')
				p = p if p is not None else parent.default_precision
				parent.hal_floats[f'{label_name}'] = [pin_name, p] # label ,status item, precision
			elif true_text and false_text:
				parent.hal_bool_labels[label_name] = [pin_name, true_text, false_text]
			else:
				integer_digits = label.property('integer_digits')
				parent.hal_readers[label_name] = [pin_name, integer_digits]

	##### HAL AVERAGE FLOAT LABEL #####
	if len(hal_avr_float_labels) > 0:
		#valid_types = ['HAL_FLOAT', 'HAL_S32', 'HAL_U32']
		for label in hal_avr_float_labels:
			label_name = label.objectName()
			pin_name = label.property('pin_name')
			s = label.property('samples') or 10
			r = label.property('rounding') or 0
			if r > 0:
				r = -r

			if pin_name in [None, '']:
				label.setEnabled(False)
				msg = (f'HAL Average Label {label_name}\n'
				'pin name is blank or missing\n'
				'The HAL pin can not be created.\n'
				f'The {label_name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if pin_name in dir(parent):
				label.setEnabled(False)
				msg = (f'HAL Average Label {label_name}\n'
				f'pin name {pin_name}\n'
				'is already used in Flex GUI\n'
				'The HAL pin can not be created.'
				f'The {label_name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			hal_type = getattr(hal, 'HAL_FLOAT')
			hal_dir = getattr(hal, 'HAL_IN')
			setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal_type, hal_dir))

			p = label.property('precision')
			p = p if p is not None else parent.default_precision

			parent.hal_avr_float[label_name] = [pin_name, deque([0], maxlen=s), p, r]

	# FIXME add hal_avr_i_labels
	##### HAL AVERAGE INT LABEL #####
	# parent.hal_avr_int = {}

	##### HAL MULTI STATE LABEL #####
	if len(hal_multi_state_labels) > 0:
		for label in hal_multi_state_labels:
			label_name = label.objectName()
			pin_name = label.property('pin_name')

			if pin_name in [None, '']:
				label.setEnabled(False)
				msg = (f'HAL MULTI STATE LABEL {name}\n'
				'pin name is blank or missing\n'
				'The HAL pin can not be created.\n'
				f'The {name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if pin_name in dir(parent):
				msg = (f'HAL Multi-State Label {label_name}\n'
				f'pin name {pin_name}\n'
				'is already used in Flex GUI\n'
				'The HAL pin can not be created.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			if label.property('text_0') == None:
				label.setEnabled(False)
				msg = (f'HAL MULTI STATE LABEL {label_name}\n'
				'text_0 Dynamic Property is blank or missing\n'
				'A HAL MULTI STATE LABEL requires at least\n'
				'one text message to display starting with\n'
				'text_0. The HAL pin can not be created.\n'
				f'The {name} will be disabled.')
				dialogs.error_msg_ok(parent, msg, 'Configuration Error')
				continue

			hal_type = getattr(hal, 'HAL_U32')
			hal_dir = getattr(hal, 'HAL_IN')
			setattr(parent, f'{pin_name}', parent.halcomp.newpin(pin_name, hal_type, hal_dir))
			#pin = getattr(parent, f'{pin_name}')
			text = ''
			text_list = []
			i = 0
			while text is not None:
				text = label.property(f'text_{i}')
				if text is not None:
					text_list.append(text)
				i += 1
			parent.hal_ms_labels[label_name] = [pin_name, text_list]

def setup_hal_io_state(parent): # this updates any hal i/o items at startup
	# key is the object name value is the hal pin name
	for key, value in parent.hal_io_check.items():
		checked_state = getattr(parent, key).isChecked()
		hal_state = getattr(parent.halcomp, value)
		if checked_state != hal_state:
			#getattr(parent, key).setChecked(hal_state)
			setattr(parent.halcomp, value, checked_state)

	for key, value in parent.hal_io_int.items():
		obj_value = getattr(parent, key).value()
		hal_value = getattr(parent.halcomp, value)
		if obj_value != hal_value:
			setattr(parent.halcomp, value, obj_value)

	for key, value in parent.hal_io_float.items():
		obj_value = getattr(parent, key).value()
		hal_value = getattr(parent.halcomp, value)
		if obj_value != hal_value:
			setattr(parent.halcomp, value, obj_value)


def setup_set_var(parent):
	# variables are floats so only put them in a QDoubleSpinBox
	var_file = os.path.join(parent.config_path, parent.var_file)
	with open(var_file, 'r') as f:
		var_list = f.readlines()

	parent.set_var = {}
	for child in parent.findChildren(QDoubleSpinBox):
		if child.property('function') == 'set_var':
			var = child.property('variable')
			found = False
			if var is not None:
				for line in var_list:
					if line.startswith(var):
						child.setValue(float(line.split()[1]))
						found = True
						child.valueChanged.connect(partial(utilities.var_value_changed, parent))
						parent.set_var[child.objectName()] = var
						parent.state_estop_disabled.append(child.objectName())
						parent.state_estop_reset_disabled.append(child.objectName())
						parent.homed_enabled.append(child.objectName())
						child.setEnabled(False)

						break
				if not found:
					child.setEnabled(False)
					msg = (f'The variable {var} was not found\n'
					f'in the variables file {parent.var_file}\n'
					f'the QDoubleSpinBox "{child.objectName()}"\n'
					'will not contain value from the\n'
					'parameters file and will be disabled')
					dialogs.warn_msg_ok(parent, msg, 'Error')

def setup_watch_var(parent):
	parent.watch_var = {}
	for child in parent.findChildren(QLabel):
		if child.property('function') == 'watch_var':
			var = child.property('variable')
			prec = child.property('precision')
			prec = prec if prec is not None else 6
			name = child.objectName()
			parent.watch_var[name] = [var, prec]

	if len(parent.watch_var) > 0: # update the labels
		var_file = os.path.join(parent.config_path, parent.var_file)
		with open(var_file, 'r') as f:
			var_list = f.readlines()
		for key, value in parent.watch_var.items():
			for line in var_list:
				if line.startswith(value[0]):
					getattr(parent, key).setText(f'{float(line.split()[1]):.{value[1]}f}')


def setup_plain_text_edits(parent):
	# for gcode_pte update
	parent.motion_line = -1
	if 'gcode_pte' in parent.child_names:
		parent.gcode_pte.setCenterOnScroll(True)
		parent.gcode_pte.ensureCursorVisible()
		parent.gcode_pte.viewport().installEventFilter(parent)
		parent.gcode_pte.cursorPositionChanged.connect(partial(utilities.update_qcode_pte, parent))
		parent.last_line = parent.status.motion_line

def setup_probing(parent):
	# any object name that starts with probe_ is disabled
	parent.probing = False
	for child in parent.child_names:
		if child.startswith('probe_'):
			getattr(parent, child).setEnabled(False)
			parent.probe_controls.append(child)

	if len(parent.probe_controls) > 0: # make sure the probe enable is present
		if 'probing_enable_pb' in parent.child_names:
			if not parent.probing_enable_pb.isCheckable():
				parent.probing_enable_pb.setCheckable(True)
			parent.probing_enable_pb.toggled.connect(partial(probe.toggle, parent))
			parent.state_estop_disabled.append('probing_enable_pb')
			parent.state_estop_reset_disabled.append('probing_enable_pb')
			parent.homed_enabled.append('probing_enable_pb')

def load_postgui(parent): # load post gui hal and tcl files if found
	if parent.postgui_halfiles:
		for f in parent.postgui_halfiles:
			if os.path.exists(os.path.join(parent.config_path, f)):
				if f.lower().endswith('.tcl'):
					res = os.spawnvp(os.P_WAIT, "haltcl", ["haltcl", "-i", parent.ini_path, f])
				else:
					res = os.spawnvp(os.P_WAIT, "halcmd", ["halcmd", "-i", parent.ini_path, "-f", f])
				if res: raise SystemExit(res)
			else:
				msg = (f'The POSTGUI_HALFILE\n'
				f'{os.path.join(parent.config_path, f)}\n'
				'was not found in the configuration directory.')
				dialogs.warn_msg_ok(parent, msg, 'Configuration Error')

def setup_defaults(parent):
	if parent.open_file and parent.open_file != '""':
		actions.load_file(parent, parent.open_file)
	else:
		if 'reload_pb' in parent.child_names:
			parent.reload_pb.setEnabled(False)
		if 'actionReload' in parent.child_names:
			parent.actionReload.setEnabled(False)
		if 'actionSave' in parent.child_names:
			parent.actionSave.setEnabled(False)
		if 'actionSave_As' in parent.child_names:
			parent.actionSave_As.setEnabled(False)

	# check to see if the PLOT group is in settings
	if 'plot_widget' in parent.child_names:
		groups = parent.settings.childGroups()
		if 'Plot_Settings' not in groups:
			parent.settings.beginGroup('Plot_Settings')
			parent.settings.setValue('show_dro', 'True')
			parent.settings.setValue('show_limits', 'True')
			parent.settings.setValue('show_live_plot', 'True')
			parent.settings.setValue('show_velocity', 'True')
			parent.settings.setValue('show_program', 'True')
			parent.settings.setValue('show_rapids', 'True')
			parent.settings.setValue('show_tool', 'True')
			parent.settings.endGroup()
			parent.settings.sync() # Ensure data is written to storage
			default_plot_cb = ['view_dro_cb', 'view_limits_cb', 'view_live_plot_cb',
			'view_velocity_cb', 'view_program_cb', 'view_rapids_cb', 'view_tool_cb']
			for item in default_plot_cb:
				if item in parent.child_names:
					getattr(parent, item).blockSignals(True)
					getattr(parent, item).setChecked(True)
					getattr(parent, item).blockSignals(False)
		else:
			view_checkboxes = {
				'view_dro_cb': ['action_toggle_dro', 'show_dro'],
				'view_limits_cb': ['action_toggle_limits', 'show_limits'],
				'view_extents_option_cb': ['action_toggle_extents_option', 'show_extents_option'],
				'view_live_plot_cb': ['action_toggle_live_plot', 'show_live_plot'],
				'view_velocity_cb': ['action_toggle_velocity', 'show_velocity'],
				'view_metric_units_cb': ['action_toggle_metric_units', 'metric_units'],
				'view_program_cb': ['action_toggle_program', 'show_program'],
				'view_rapids_cb': ['action_toggle_rapids', 'show_rapids'],
				'view_tool_cb': ['action_toggle_tool', 'show_tool'],
				'view_lathe_radius_cb': ['action_toggle_lathe_radius', 'show_lathe_radius'],
				'view_dtg_cb': ['action_toggle_dtg', 'show_dtg'],
				'view_offsets_cb': ['action_toggle_offsets', 'show_offsets'],
				'view_overlay_cb': ['action_toggle_overlay', 'show_overlay']
			}

			for key, value in view_checkboxes.items():
				if key in parent.child_names:
					if parent.settings.contains(f'Plot_Settings/{value[1]}'):
						checked_state = parent.settings.value(f'Plot_Settings/{value[1]}', type=bool)
						if checked_state:
							getattr(parent, key).setChecked(checked_state)
						else:
							getattr(actions, value[0])(parent, False)

def setup_tools(parent):
	pass


