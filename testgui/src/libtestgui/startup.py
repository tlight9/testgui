
from functools import partial

from PyQt6.QtWidgets import QWidget, QPushButton, QMenu, QListView
from PyQt6.QtGui import QAction

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
	print(parent.joints)
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


def setup_tools(parent):
	pass


