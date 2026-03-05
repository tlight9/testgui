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

	# check for jog increments
	parent.jog_increments = parent.inifile.find('DISPLAY', 'INCREMENTS') or False

	# check for default file to open
	parent.open_file = parent.inifile.find('DISPLAY', 'OPEN_FILE') or False

	# get file extensions
	parent.extensions = ['.ngc'] # used by the touch file selector
	extensions = parent.inifile.find('DISPLAY', 'EXTENSIONS') or False
	if extensions: # add any extensions from the ini to ngc
		for ext in extensions.split(','):
			parent.extensions.append(ext.strip())
		extensions = extensions.split(',')
		extensions = ' '.join(extensions).strip()
		parent.ext_filter = f'G code Files ({extensions});;All Files (*)'
	else:
		parent.ext_filter = 'G code Files (*.ngc *.NGC);;All Files (*)'

	# set the nc code directory to some valid directory
	directory = parent.inifile.find('DISPLAY', 'PROGRAM_PREFIX') or False
	ini_dir = False
	if directory: # expand directory if needed
		ini_dir = True
		if directory.startswith('./'): # in this directory
			directory = os.path.join(parent.config_path, directory[2:])
		elif directory.startswith('../'): # up one directory
			directory = os.path.join(os.path.dirname(parent.config_path), directory[3:])
		elif directory.startswith('~'): # users home directory
			directory = os.path.expanduser(directory)

	if os.path.isdir(directory):
		parent.nc_code_dir = directory
	else: # try and find a directory
		if os.path.isdir(os.path.expanduser('~/linuxcnc/nc_files')):
			parent.nc_code_dir = os.path.expanduser('~/linuxcnc/nc_files')
		else:
			parent.nc_code_dir = os.path.expanduser('~/')
		if ini_dir: # a nc code directory was in the ini file but is not valid
			msg = (f'The path {directory}\n'
				'does not exist. Check the\n'
				'PROGRAM_PREFIX key in the\n'
				'[DISPLAY] section of the\n'
				'INI file for a valid path.\n'
				f'{parent.nc_code_dir} will be used.')
			dialogs.warn_msg_ok(parent, msg, 'Configuration Error')

	# nc code editor
	parent.editor = parent.inifile.find('DISPLAY', 'EDITOR') or False

	# tool file editor
	parent.tool_editor = parent.inifile.find('DISPLAY', 'TOOL_EDITOR') or False


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



