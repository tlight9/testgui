
import linuxcnc as emc

from libtestgui import dialogs

def home(parent):
	parent.status.poll()
	joint = int(parent.sender().objectName()[-1])
	if parent.status.homed[joint] == 0: # not homed
		if parent.status.task_mode != emc.MODE_MANUAL:
			parent.command.mode(emc.MODE_MANUAL)
			parent.command.wait_complete()
		if parent.status.motion_mode != emc.TRAJ_MODE_FREE:
			parent.command.teleop_enable(False)
			parent.command.wait_complete()
		parent.command.home(joint)
		parent.sender().setEnabled(False)
		if f'unhome_pb_{joint}' in parent.child_names:
			getattr(parent, f'unhome_pb_{joint}').setEnabled(True)

def unhome(parent):
	parent.status.poll()
	joint = int(parent.sender().objectName()[-1])
	if parent.status.homed[joint] == 1: # joint is homed so unhome it
		if parent.status.task_mode != emc.MODE_MANUAL:
			parent.command.mode(emc.MODE_MANUAL)
			parent.command.wait_complete()
		if parent.status.motion_mode != emc.TRAJ_MODE_FREE:
			parent.command.teleop_enable(False)
			parent.command.wait_complete()
		parent.command.unhome(joint)
		parent.sender().setEnabled(False)
		if f'home_pb_{joint}' in parent.child_names:
			getattr(parent, f'home_pb_{joint}').setEnabled(True)


def mdi_button(parent):
	mdi_command = parent.sender().property('command')
	print(f'*** MDI Command *** {mdi_command}')
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
	#print(f'jog_command {jog_command}')
	joint = int(jog_command[-1])
	#print(f'joint {joint}')
	increment = parent.jog_modes_cb.currentData()
	#print(f'increment {increment}')
	joint_jog_mode = True if parent.motion_mode == emc.TRAJ_MODE_FREE else False
	#print(f'joint_jog_mode {joint_jog_mode}')
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





