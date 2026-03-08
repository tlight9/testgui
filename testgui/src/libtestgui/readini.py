import os, subprocess

from PyQt6.QtCore import QSettings

from libtestgui import utilities
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
	if parent.editor:
		try:
			# Use subprocess.run with check=True to raise an exception on error
			# We can capture stderr to avoid printing output to the console
			subprocess.run(["dpkg", "-s", parent.editor], check=True, capture_output=True)
		except subprocess.CalledProcessError:
			# A non-zero exit code means the package is not installed or dpkg failed
			parent.editor = False
		except FileNotFoundError:
			# Handle the case where the 'dpkg' command itself isn't found (highly unlikely on Debian)
			print("Error: dpkg command not found.")

	# tool file editor
	parent.tool_editor = parent.inifile.find('DISPLAY', 'TOOL_EDITOR') or False

	# ***** [FLEXGUI] Section *****

	# check for CYCLE_TIME
	parent.cycle_time = parent.inifile.find('FLEXGUI', 'CYCLE_TIME') or 100
	if isinstance(parent.cycle_time, str): # the ini file had a setting
		if utilities.is_int(parent.cycle_time):
			parent.cycle_time = int(parent.cycle_time)

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

	# check for auto dro units
	parent.auto_dro_units = parent.inifile.find('FLEXGUI', 'DRO_UNITS') or False

	# check for plotter dro font size
	parent.dro_font_size = parent.inifile.find('FLEXGUI', 'DRO_FONT_SIZE') or '12'
	if not utilities.is_int(parent.dro_font_size): # not an int
		msg = (f'The FLEXGUI DRO_FONT_SIZE did not\n'
			'evaluate to an integer value.\n'
			'The DRO_FONT_SIZE will be set to 12.')
		dialogs.warn_msg_ok(parent, msg, 'INI Configuration ERROR!')
	else:
		parent.dro_font_size =  int(parent.dro_font_size)

	# plotter background color
	color_string = parent.inifile.find('FLEXGUI', 'PLOT_BACKGROUND_COLOR') or False
	if color_string:
		components = [c.strip() for c in color_string.split(',')]
		if len(components) == 3:
			for comp in components:
				value = float(comp)
				if not (0.0 <= value <= 1.0):
					parent.plot_background_color = False
					msg = ('The PLOT_BACKGROUND_COLOR in the\n'
					f'FLEXGUI section {color_string} is not valid.\n'
					'The plot background color will be black')
					dialogs.error_msg_ok(parent, msg, 'Configuration Error')
					break
				parent.plot_background_color = tuple(map(float, color_string.split(',')))
	else:
		parent.plot_background_color = False

	# set the default plotter view
	if parent.inifile.find('DISPLAY', 'LATHE') is not None:
		parent.default_view = 'y'
	elif parent.inifile.find('FLEXGUI', 'PLOT_VIEW') is not None:
		parent.default_view = parent.inifile.find('FLEXGUI', 'PLOT_VIEW')
	else:
		parent.default_view = 'p'

	# plotter units follow current program units
	parent.auto_plot_units = parent.inifile.find('FLEXGUI', 'PLOT_UNITS') or False


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



