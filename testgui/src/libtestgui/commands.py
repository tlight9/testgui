
import linuxcnc as emc

from libtestgui import dialogs
from libtestgui import utilities

def set_task_mode(parent, mode):
	parent.status.poll()
	if parent.status.task_mode != mode:
		parent.command.mode(mode)
		parent.command.wait_complete()

def set_motion_mode(parent, mode):
	parent.status.poll()
	if parent.status.motion_mode != mode:
		parent.command.mode(mode)
		parent.command.wait_complete()

def home(parent):
	joint = int(parent.sender().objectName()[-1])
	if parent.status.homed[joint] == 0: # not homed
		set_task_mode(parent, emc.MODE_MANUAL)
		parent.command.teleop_enable(False)
		parent.command.wait_complete()
		parent.command.home(joint)

def home_all(parent):
	set_task_mode(parent, emc.MODE_MANUAL)
	parent.command.teleop_enable(False)
	parent.command.wait_complete()
	parent.command.home(-1)

def unhome(parent):
	parent.status.poll()
	joint = int(parent.sender().objectName()[-1])
	if parent.status.homed[joint] == 1: # joint is homed so unhome it
		set_task_mode(parent, emc.MODE_MANUAL)
		if parent.status.motion_mode != emc.TRAJ_MODE_FREE:
			parent.command.teleop_enable(False)
			parent.command.wait_complete()
		parent.command.unhome(joint)

def unhome_all(parent):
	set_task_mode(parent, emc.MODE_MANUAL)
	parent.command.teleop_enable(False)
	parent.command.wait_complete()
	parent.command.unhome(-1)

def run_mdi(parent):
	mdi_command = parent.mdi_command_le.text()
	if mdi_command:
		if parent.status.task_state == emc.STATE_ON:
			if parent.status.task_mode == emc.MODE_MANUAL:
				parent.command.mode(emc.MODE_MDI)
				parent.command.wait_complete()
				parent.command.mdi(mdi_command)

def add_mdi(parent): # when you click on the mdi history list widget
	parent.mdi_command_le.setText(f'{parent.mdi_history_lw.currentItem().text()}')

def mdi_button(parent):
	mdi_command = parent.sender().property('command')
	parent.status.poll()
	if parent.status.task_state == emc.STATE_ON:
		if parent.status.task_mode == emc.MODE_MANUAL:
			parent.command.mode(emc.MODE_MDI)
			parent.command.wait_complete()
			parent.command.mdi(mdi_command)

def jog_check(parent):
	if 'jog_vel_sl' in parent.child_names:
		if parent.jog_vel_sl.value() > 0.0:
			return True
		else:
			msg = ('Can not jog at Zero Velocity!')
			dialogs.warn_msg_ok(parent, msg, 'Error')
			return False
	else:
		msg = ('Can not jog without a\njog velocity slider.')
		dialogs.warn_msg_ok(msg, 'Error')
		return False

def set_jog_override(parent):
	if 'override_limits_cb' in parent.child_names:
		parent.override_limits_cb.setChecked(False)
		parent.override_limits_cb.setEnabled(False)

def jog(parent): # only do jog check if button is down
	jog_command = parent.sender().objectName().split('_')
	joint = int(jog_command[-1])
	increment = parent.jog_modes_cb.currentData()
	joint_jog_mode = True if parent.motion_mode == emc.TRAJ_MODE_FREE else False
	vel = parent.jog_vel_sl.value() / 60
	if 'minus' in jog_command:
		vel = -vel
	if parent.sender().isDown():
		if jog_check(parent):
			if increment:
				parent.command.jog(emc.JOG_INCREMENT, joint_jog_mode, joint, vel, increment)
			else:
				parent.command.jog(emc.JOG_CONTINUOUS, joint_jog_mode, joint, vel)
	else:
		parent.command.jog(emc.JOG_STOP, joint_jog_mode, joint)
		#set_jog_override(parent)





