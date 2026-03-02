import os

from PyQt6.QtCore import QSettings

from libtestgui import dialogs

def read(parent):

	# ***** [EMC] Section *****
	machine_name = parent.inifile.find('EMC', 'MACHINE') or False
	if machine_name: # FIXME rename back to Flex when done
		parent.settings = QSettings('Test_flex', machine_name)
	else:
		parent.settings = QSettings('Test_flex', 'unknown')

	# ***** [DISPLAY] Section *****

	parent.jog_increments = parent.inifile.find('DISPLAY', 'INCREMENTS') or False

	# ***** [FLEXGUI] Section *****

	# check for a RESOURCES file
	parent.resources_file = parent.inifile.find('FLEXGUI', 'RESOURCES') or False
	if parent.resources_file:
		if not os.path.exists(os.path.join(parent.config_path, parent.resources_file)):
			msg = (f'The RESOURCES file {parent.resources_file}\n'
				'Was not found. Resourses can not be imported')
			dialogs.warn_msg_ok(parent, msg, 'INI Configuration ERROR!')
			parent.resources_file = False

	# check for QSS file
	parent.qss_file = parent.inifile.find('FLEXGUI', 'QSS') or False
	if parent.qss_file:
		if not os.path.exists(os.path.join(parent.config_path, parent.qss_file)):
			msg = (f'The QSS file {parent.qss_file}\n'
				'Was not found. QSS can not be applied')
			dialogs.warn_msg_ok(parent, msg, 'INI Configuration ERROR!')
			parent.qss_file = False


	# ***** [KINS] Section *****
	# this ini file items will cause EMC to fail to load if missing
	parent.joints = parent.inifile.find('KINS', 'JOINTS') or False
	if parent.joints: # convert string to int
		parent.joints = int(parent.joints)

	# ***** [TRAJ] Section *****
	match parent.inifile.find('TRAJ', 'LINEAR_UNITS'):
		case 'inch':
			parent.default_precision = 4
			parent.units = 'INCH'
		case 'mm':
			parent.default_precision = 3
			parent.units = 'MM'



