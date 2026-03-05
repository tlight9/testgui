import math, statistics

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QLCDNumber

import linuxcnc as emc
import hal

from libtestgui import utilities

EXEC_STATES = {1: 'EXEC_ERROR', 2: 'EXEC_DONE', 3: 'EXEC_WAITING_FOR_MOTION',
	4: 'EXEC_WAITING_FOR_MOTION_QUEUE', 5: 'EXEC_WAITING_FOR_IO',
	7: 'EXEC_WAITING_FOR_MOTION_AND_IO', 8: 'EXEC_WAITING_FOR_DELAY',
	9: 'EXEC_WAITING_FOR_SYSTEM_CMD', 10: 'EXEC_WAITING_FOR_SPINDLE_ORIENTED', }

INTERP_STATES = {1: 'INTERP_IDLE', 2: 'INTERP_READING', 3: 'INTERP_PAUSED',
	4: 'INTERP_WAITING'}

INTERPRETER_ERRCODES = {0: 'INTERP_OK', 1: 'INTERP_EXIT',
	2: 'INTERP_EXECUTE_FINISH', 3 :'INTERP_ENDFILE', 4 :'INTERP_FILE_NOT_OPEN',
	5 :'INTERP_ERROR'}

MOTION_MODES = {1: 'TRAJ_MODE_FREE', 2: 'TRAJ_MODE_COORD', 3: 'TRAJ_MODE_TELEOP'}

MOTION_TYPES = {0: 'MOTION_TYPE_NONE', 1: 'MOTION_TYPE_TRAVERSE',
	2: 'MOTION_TYPE_FEED', 3: 'MOTION_TYPE_ARC', 4: 'MOTION_TYPE_TOOLCHANGE',
	5: 'MOTION_TYPE_PROBING', 6: 'MOTION_TYPE_INDEXROTARY'}

STATES = {1: 'RCS_DONE', 2: 'RCS_EXEC', 3: 'RCS_ERROR'}

TASK_MODES = {1: 'MODE_MANUAL', 2: 'MODE_AUTO', 3: 'MODE_MDI'}

TASK_STATES = {1: 'STATE_ESTOP', 2: 'STATE_ESTOP_RESET', 3: 'STATE_OFF',
	4: 'STATE_ON'}

def update(parent):
	changed = False
	parent.status.poll()

	# **** EXEC STATE ****
	#exec_state EXEC_ERROR, EXEC_DONE, EXEC_WAITING_FOR_MOTION,
	#EXEC_WAITING_FOR_MOTION_QUEUE, EXEC_WAITING_FOR_IO,
	#EXEC_WAITING_FOR_MOTION_AND_IO, EXEC_WAITING_FOR_DELAY,
	#EXEC_WAITING_FOR_SYSTEM_CMD, EXEC_WAITING_FOR_SPINDLE_ORIENTED.
	if parent.exec_state != parent.status.exec_state:
		#print(f'EXEC STATE: {EXEC_STATES[parent.status.exec_state]}')
		if 'exec_state_lb' in parent.child_names: # update the label
			parent.exec_state_lb.setText(EXEC_STATES[parent.status.exec_state])
		changed = True
		# FIXME is this needed here?
		#if parent.status.state == emc.RCS_DONE and parent.status.task_mode == emc.MODE_MDI:
		#	parent.command.mode(emc.MODE_MANUAL)

		#if parent.status.exec_state == emc.EXEC_DONE and parent.status.task_mode == emc.MODE_AUTO:
		#	parent.command.mode(emc.MODE_MANUAL)

		parent.exec_state = parent.status.exec_state

	# **** INTERP STATE ****
	# interp_state INTERP_IDLE, INTERP_READING, INTERP_PAUSED, INTERP_WAITING
	if parent.interp_state != parent.status.interp_state:
		#print(f'INTERP STATE: {INTERP_STATES[parent.status.interp_state]}')
		if 'interp_state_lb' in parent.child_names: # update the label
			parent.interp_state_lb.setText(INTERP_STATES[parent.status.interp_state])

		if parent.status.interp_state == emc.INTERP_IDLE:
			utilities.update_run_controls(parent)



		parent.interp_state = parent.status.interp_state

	# **** INTERPRETER ERRCODE ****
	if parent.interpreter_errcode != parent.status.interpreter_errcode:
		#print(f'INTERPRETER ERRCODE: {INTERPRETER_ERRCODES[parent.status.interpreter_errcode]}')
		if 'interpreter_errcode_lb' in parent.child_names: # update the label
			parent.interpreter_errcode_lb.setText(INTERPRETER_ERRCODES[parent.status.interpreter_errcode])
		changed = True

		parent.interpreter_errcode = parent.status.interpreter_errcode

	# **** MOTION MODE ****
	# motion_mode TRAJ_MODE_COORD, TRAJ_MODE_FREE, TRAJ_MODE_TELEOP
	if parent.motion_mode != parent.status.motion_mode:
		#print(f'MOTION MODE: {MOTION_MODES[parent.status.motion_mode]}')
		if 'motion_mode_lb' in parent.child_names: # update the label
			parent.motion_mode_lb.setText(MOTION_MODES[parent.status.motion_mode])

		parent.motion_mode = parent.status.motion_mode

	# **** MOTION TYPE ****
	if parent.motion_type != parent.status.motion_type:
		#print(f'MOTION TYPE: {MOTION_TYPES[parent.status.motion_type]}')
		if 'motion_type_lb' in parent.child_names: # update the label
			parent.motion_type_lb.setText(MOTION_TYPES[parent.status.motion_type])

		parent.motion_type = parent.status.motion_type

	# **** STATE ****
	# state RCS_DONE, RCS_EXEC, RCS_ERROR
	if parent.state != parent.status.state:
		#print(f'STATE: {STATES[parent.status.state]}')
		if 'state_lb' in parent.child_names: # update the label
			parent.state_lb.setText(STATES[parent.status.state])

		# this is needed for MDI commands that use motion
		if parent.status.state == emc.RCS_DONE:
			if parent.status.task_mode == emc.MODE_MDI:
				utilities.update_mdi(parent)
			parent.command.mode(emc.MODE_MANUAL)

		parent.state = parent.status.state

	# **** TASK MODE ****
	# task_mode MODE_MDI, MODE_AUTO, MODE_MANUAL
	if parent.task_mode != parent.status.task_mode:
		#print(f'TASK MODE: {TASK_MODES[parent.status.task_mode]}')
		if 'task_mode_lb' in parent.child_names: # update the label
			parent.task_mode_lb.setText(TASK_MODES[parent.status.task_mode])

		# this is needed for MDI commands that do not use motion
		if parent.status.state == emc.RCS_DONE and parent.status.task_mode == emc.MODE_MDI:
			parent.command.mode(emc.MODE_MANUAL)
			utilities.update_mdi(parent)

		utilities.update_run_controls(parent)

		parent.task_mode = parent.status.task_mode

	# **** TASK STATE ****
	# task_state STATE_ESTOP, STATE_ESTOP_RESET, STATE_ON, STATE_OFF < never seen
	if parent.task_state != parent.status.task_state:
		#print(f'TASK STATE: {TASK_STATES[parent.status.task_state]}')
		if 'task_state_lb' in parent.child_names: # update the label
			parent.task_state_lb.setText(TASK_STATES[parent.status.task_state])

		# estop open
		if parent.status.task_state == emc.STATE_ESTOP:
			#print('status update STATE_ESTOP')
			for item in parent.state_estop_disabled:
				getattr(parent, item).setEnabled(False)
			for item in parent.state_on_enabled:
				getattr(parent, item).setEnabled(False)

		# estop closed power off
		if parent.status.task_state == emc.STATE_ESTOP_RESET:
			#print('status update STATE_ESTOP_RESET')
			for item in parent.state_estop_reset_disabled:
				getattr(parent, item).setEnabled(False)
			for item in parent.state_on_enabled:
				getattr(parent, item).setEnabled(False)
			for item in parent.state_estop_reset_enabled:
				getattr(parent, item).setEnabled(True)

		# estop closed power on
		if parent.status.task_state == emc.STATE_ON:
			#print('status update STATE_ON')
			for item in parent.state_on_enabled:
				getattr(parent, item).setEnabled(True)

		utilities.update_run_controls(parent)

		parent.task_state = parent.status.task_state

	# **** FILE CHANGE ****
	if parent.file != parent.status.file:
		#print('File Changed')
		utilities.update_run_controls(parent)

		parent.file = parent.status.file


	# **** HOMED CHANGE **** FIXME may not need to test for state on
	if parent.homed != parent.status.homed:
		if parent.status.task_state == emc.STATE_ON:
			utilities.update_home_controls(parent)
		utilities.update_run_controls(parent)

		'''
		if all(parent.status.homed[:parent.joints]):
			for item in parent.homed_enabled:
				getattr(parent, item).setEnabled(True)
		else:
			for item in parent.homed_enabled:
				getattr(parent, item).setEnabled(False)
		'''

		parent.homed = parent.status.homed

	# axis position no offsets
	for key, value in parent.status_position.items(): # key is label value precision
		getattr(parent, f'{key}').setText(f'{parent.status.position[value[0]]:.{value[1]}f}')

	# axis g5x offset
	for key, value in parent.status_g5x_offset.items(): # key is label value tuple position & precision
		getattr(parent, f'{key}').setText(f'{parent.status.g5x_offset[value[0]]:.{value[1]}f}')

	# axis g92 offset
	for key, value in parent.status_g92.items(): # key is label value tuple position & precision
		getattr(parent, f'{key}').setText(f'{parent.status.g92_offset[value[0]]:.{value[1]}f}')

	# calculate DRO positions
	positions = parent.status.position
	positions = [(i-j) for i, j in zip(positions, parent.status.tool_offset)]
	positions = [(i-j) for i, j in zip(positions, parent.status.g5x_offset)]
	t = -parent.status.rotation_xy
	t = math.radians(t)
	_x = positions[0]
	_y = positions[1]
	positions[0] = _x * math.cos(t) - _y * math.sin(t)
	positions[1] = _x * math.sin(t) + _y * math.cos(t)
	positions = [(i-j) for i, j in zip(positions, parent.status.g92_offset)]


	# axis position with offsets
	for key, value in parent.status_dro.items(): # key is label value tuple position & precision
		position = positions[value[0]]
		# metric linear units with inch program units
		if parent.status.linear_units == 1 and parent.program_units == 'INCH' and parent.auto_dro_units:
			getattr(parent, f'{key}').setText(f'{position * 0.03937007874015748:.4f}')
		# inch linear units with metric program units
		elif parent.status.linear_units != 1 and parent.program_units == 'MM' and parent.auto_dro_units:
			getattr(parent, f'{key}').setText(f'{position * 25.4:.3f}')
		# linear units and program units are the same
		else:
			getattr(parent, f'{key}').setText(f'{position:.{value[1]}f}')

		#position = parent.status.position[value[0]]
		#g5x_offset = parent.status.g5x_offset[value[0]]
		#g92_offset = parent.status.g92_offset[value[0]]
		#dro = position + g5x_offset + g92_offset
		#getattr(parent, f'{key}').setText(f'{dro:.{value[1]}f}')

	# G codes only update when they change
	if parent.g_codes != parent.status.gcodes:
		g_codes = []
		for i in parent.status.gcodes[1:]:
			if i == -1: continue
			if i % 10 == 0:
				g_codes.append(f'G{(i/10):.0f}')
			else:
				g_codes.append(f'G{(i/10):.0f}.{i%10}')

		if 'gcodes_lb' in parent.child_names:
			parent.gcodes_lb.setText(f'{" ".join(g_codes)}')

		if 'G20' in g_codes:
			parent.program_units = 'INCH'
		else:
			parent.program_units = 'MM'

	#### HAL ####
	# update hal labels key is label name and value[0] is pin name value[1] is digits
	for key, value in parent.hal_readers.items():
		state = hal.get_value(f'flexhal.{value[0]}')
		if value[1] is not None:
			state = f"{state:0{value[1]}d}"
		if isinstance(getattr(parent, key), QLCDNumber):
			getattr(parent, key).display(f'{state}')
		else: # it's a HAL Label
			getattr(parent, key).setText(f'{state}')

	# update hal float labels
	for key, value in parent.hal_floats.items():
		# label [status item, precision]
		hal_value = hal.get_value(f'flexhal.{value[0]}')
		if isinstance(getattr(parent, key), QLCDNumber):
			getattr(parent, key).display(f'{hal_value:.{value[1]}f}')
		else:
			getattr(parent, key).setText(f'{hal_value:.{value[1]}f}')

	# update hal bool labels
	# key is label name, value[0] is pin name, value[1] is true text, value[2] is false text
	for key, value in parent.hal_bool_labels.items():
		state = hal.get_value(f'flexhal.{value[0]}')
		if state:
			getattr(parent, key).setText(value[1])
		else:
			getattr(parent, key).setText(value[2])

	# update hal average float labels key is label name and value is pin name
	# [pin_name, deque([0], maxlen=samples), p, _round]
	for key, value in parent.hal_avr_float.items():
		cur_val = hal.get_value(f'flexhal.{value[0]}')
		value[1].append(cur_val)
		stat = statistics.fmean(value[1])
		rounding = value[3]
		getattr(parent, key).setText(f'{round(stat, rounding):.{value[2]}f}')

	# update multi state labels
	# key is label name and value[0] is the pin name
	for key, value in parent.hal_ms_labels.items():
		state = hal.get_value(f'flexhal.{value[0]}')
		if state < len(value[1]):
			getattr(parent, key).setText(f'{value[1][state]}')
		else:
			getattr(parent, key).setText('Value Error')

	# update hal progressbars key is the progressbar name and value is the pin name
	for key, value in parent.hal_progressbars.items():
		value = hal.get_value(f'flexhal.{value}')
		getattr(parent, key).setValue(int(value))


	# handle errors
	error = parent.error.poll()
	if error:
		kind, text = error
		if kind in (emc.NML_ERROR, emc.OPERATOR_ERROR):
			error_type = 'Error'
		else:
			error_type = 'Info'
		if 'override_limits_cb' in parent.child_names:
			if 'limit switch error' in text:
				parent.override_limits_cb.setEnabled(True)
		if error_type == 'Info':
			if 'info_pte' in parent.child_names:
				parent.info_pte.appendPlainText(error_type)
				parent.info_pte.appendPlainText(text)
				# Get the text cursor
				cursor = parent.info_pte.textCursor()
				# Move the cursor to the end of the document
				cursor.movePosition(QTextCursor.MoveOperation.End)
				# Set the modified cursor back to the editor
				parent.info_pte.setTextCursor(cursor)
				# Ensure the cursor is visible (this performs the scroll)
				parent.info_pte.ensureCursorVisible()
			elif 'errors_pte' in parent.child_names:
				parent.errors_pte.appendPlainText(error_type)
				parent.errors_pte.appendPlainText(text)
				parent.errors_pte.setFocus()
				# Get the text cursor
				cursor = parent.errors_pte.textCursor()
				# Move the cursor to the end of the document
				cursor.movePosition(QTextCursor.MoveOperation.End)
				# Set the modified cursor back to the editor
				parent.errors_pte.setTextCursor(cursor)
				# Ensure the cursor is visible (this performs the scroll)
				parent.errors_pte.ensureCursorVisible()

		elif error_type == 'Error':
			if 'errors_pte' in parent.child_names:
				parent.errors_pte.appendPlainText(error_type)
				parent.errors_pte.appendPlainText(text)
				parent.errors_pte.setFocus()
				# Get the text cursor
				cursor = parent.errors_pte.textCursor()
				# Move the cursor to the end of the document
				cursor.movePosition(QTextCursor.MoveOperation.End)
				# Set the modified cursor back to the editor
				parent.errors_pte.setTextCursor(cursor)
				# Ensure the cursor is visible (this performs the scroll)
				parent.errors_pte.ensureCursorVisible()

		if 'statusbar' in parent.child_names:
			parent.statusbar.showMessage('Error')




