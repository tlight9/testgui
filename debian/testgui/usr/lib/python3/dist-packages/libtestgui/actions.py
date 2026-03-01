import subprocess

import linuxcnc as emc

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

def action_quit(parent): # actionQuit
	parent.close()


def action_show_hal(parent): # actionShow_HAL
	subprocess.Popen('halshow', cwd=parent.config_path)




