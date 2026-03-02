import os

from functools import partial

from PyQt6.QtWidgets import QWidget, QPushButton, QMenu, QListView
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtGui import QAction

import hal

from libtestgui import actions
from libtestgui import commands
from libtestgui import dialogs
from libtestgui import utilities

AXES = ['x', 'y', 'z', 'a', 'b', 'c', 'u', 'v', 'w']

def find_children(parent): # get the object names of all widgets
	#print('finding the buggers')
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

	#for name in parent.child_names:
	#	print(name)

def setup_vars(parent):
	parent.program_units = False
	parent.g_codes = ()

def setup_enables(parent):

	# enable and disable lists
	parent.state_estop_disabled = [] # everything but estop_pb
	parent.state_estop_reset_disabled = []
	parent.state_estop_reset_enabled = []
	parent.state_on_enabled = []
	parent.homed_enabled = []

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
		if f'home_pb_{i}' in parent.child_names:
			parent.state_on_enabled.append(f'home_pb_{i}')

def setup_status(parent):
	# Actual Position labels no offsets
	parent.status_position = {} # create an empty dictionary
	for i, axis in enumerate(AXES):
		label = f'actual_lb_{axis}'
		if label in parent.child_names:
			p = getattr(parent, label).property('precision')
			p = p if p is not None else parent.default_precision
			parent.status_position[f'{label}'] = [i, p] # label , joint & precision

	#for key, value in parent.status_position.items():
	#	print(type(value[0]))

	# G5x Offset Labels
	parent.status_g5x_offset = {} # create an empty dictionary
	for i, axis in enumerate(AXES):
		label = f'g5x_lb_{axis}'
		if label in parent.child_names:
			#print(label)
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

	#for key, value in parent.status_dro.items(): # key is label value list position & precision
	#print(f'Machine Position {parent.status.position}')
	#print(f'G5x Offset X {parent.status.g5x_offset}')
	#print(f'G92 Offset X {parent.status.g92_offset}')

def setup_buttons(parent): # connect buttons to functions
	if 'estop_pb' in parent.child_names:
		parent.estop_pb.toggled.connect(partial(actions.action_estop, parent))
		parent.estop_pb.setCheckable(True)

	if 'power_pb' in parent.child_names:
		parent.power_pb.toggled.connect(partial(actions.action_power, parent))
		parent.power_pb.setCheckable(True)

	if 'quit_pb' in parent.child_names:
		parent.quit_pb.clicked.connect(partial(actions.action_quit, parent))

	for i in range(9):
		if f'home_pb_{i}' in parent.child_names:
			getattr(parent, f'home_pb_{i}').clicked.connect(partial(commands.home, parent))
			parent.state_estop_disabled.append(f'home_pb_{i}')
		if f'unhome_pb_{i}' in parent.child_names:
			getattr(parent, f'unhome_pb_{i}').clicked.connect(partial(commands.unhome, parent))
			parent.state_estop_disabled.append(f'unhome_pb_{i}')

def setup_actions(parent): # setup menu actions
	actions_dict = {
		'actionShow_HAL': 'action_show_hal'
	}

	# if an action is found connect it to the function
	for key, value in actions_dict.items():
		if key in parent.child_names:
			getattr(parent, f'{key}').triggered.connect(partial(getattr(actions, f'{value}'), parent))

def setup_mdi(parent):
	# mdi_command_le is required to run mdi commands
	# run_mdi_pb and mdi_history_lw are optional
	#if set(['mdi_command_le', 'run_mdi_pb']).issubset(set(parent.child_names)):

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
				parent.state_estop_disabled.append(name)
				parent.homed_enabled.append(name)

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
		from libflexgui import flexplot
		parent.plotter = flexplot.emc_plot(parent)
		layout = QVBoxLayout(parent.plot_widget)
		layout.addWidget(parent.plotter)

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
			if isinstance(child, QLabel):
				hal_labels.append(child)

	##### HAL LABEL #####
	if len(hal_labels) > 0:
		valid_types = ['HAL_BIT', 'HAL_FLOAT', 'HAL_S32', 'HAL_U32']
		for label in hal_labels:
			label_name = label.objectName()
			pin_name = label.property('pin_name')
			hal_type = label.property('hal_type')
			true_text = label.property('true_text')
			false_text = label.property('false_text')
			#print(true_text, false_text)
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
			#print(f'pin_name {pin_name} hal type {hal_type}')
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

	#for key, value in parent.hal_readers.items():
	#	print(key, value)

def setup_tools(parent):
	pass


