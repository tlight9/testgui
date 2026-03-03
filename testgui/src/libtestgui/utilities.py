import re, os



def is_number(string):
	try:
		int(string)
		return True
	except ValueError:
		try:
			float(string)
			return True
		except ValueError:
			return False

def conv_units(value, suffix, units):
	if units == 'INCH':
		if suffix == 'in' or suffix == 'inch':
			return float(value)
		elif suffix == 'mil':
			return float(value) * 0.001
		elif suffix == 'cm':
			return float(value) / 2.54
		elif suffix == 'mm':
			return float(value) / 25.4
		elif suffix == 'um':
			return float(value) / 25400

	elif units == 'MM':
		if suffix == 'in' or suffix == 'inch':
			return float(value) * 25.4
		elif suffix == 'mil':
			return float(value) * 0.0254
		elif suffix == 'cm':
			return float(value) * 10
		elif suffix == 'mm':
			return float(value)
		elif suffix == 'um':
			return float(value) / 1000

def convert_fraction(item):
	# strip trailing non digits
	for i in range(len(item) - 1, -1, -1):
		if item[i].isdigit():
			fraction_string = item[:i+1]
			break
	suffix = item[i+1:].strip() if len(item[i+1:].strip()) > 0 else False

	if len(fraction_string.split('/')) == 2: # might be a good number
		match = re.match(r'(\d+)?\s*(\d+)/(\d+)', fraction_string)
		if match:
			whole_number = int(match.group(1)) if match.group(1) else 0
			numerator = int(match.group(2))
			denominator = int(match.group(3))
			# return the decimal number plus suffix
			return whole_number + (numerator / denominator), suffix
	else:
		return False, False

def is_valid_increment(parent, item): # need to return text ,data and suffix
	if is_number(item): # there is no suffix and it's a valid number
		return f'{item} {parent.units.lower()}', item, parent.units

	if '/' in item: # it might be a fraction
		#for character in item:
		fraction, suffix = convert_fraction(item)
		if fraction and suffix:
			return f'{item}', fraction, 'inch'
		elif fraction and not suffix:
			return f'{item} inch', fraction, 'inch'
		else:
			return False, False, False

	units = ['mm', 'cm', 'um', 'in', 'inch', 'mil']
	if item.endswith(tuple(units)): # test to see if it matches any units
		for suffix in units:
			if item.endswith(suffix):
				increment = item.removesuffix(suffix).strip()
				if is_number(increment):
					return item, increment, suffix
				else:
					return False, False, False
	else: # not a valid increment
		return False, False, False

def update_mdi(parent):
	if 'mdi_history_lw' in parent.child_names:
		rows = parent.mdi_history_lw.count()
		if rows > 0:
			last_item = parent.mdi_history_lw.item(rows - 1).text().strip()
		else:
			last_item = ''
		if last_item != parent.mdi_command_le.text():
			parent.mdi_history_lw.addItem(parent.mdi_command_le.text())
			path = os.path.dirname(parent.status.ini_filename)
			mdi_file = os.path.join(path, 'mdi_history.txt')
			mdi_codes = []
			for index in range(parent.mdi_history_lw.count()):
				mdi_codes.append(parent.mdi_history_lw.item(index).text())
			with open(mdi_file, 'w') as f:
				f.write('\n'.join(mdi_codes))
		parent.mdi_command_le.setText('')

def home_all_check(parent):
	parent.status.poll()
	for i in range(parent.status.joints):
		if parent.inifile.find(f'JOINT_{i}', 'HOME_SEQUENCE') is None:
			return False
	return True

def update_home_controls(parent):
	parent.status.poll()
	for joint in range(parent.joints):
		if parent.status.joint[joint]['homed']:
			if f'home_pb_{joint}' in parent.child_names:
				getattr(parent, f'home_pb_{joint}').setEnabled(False)
			if f'unhome_pb_{joint}' in parent.child_names:
				getattr(parent, f'unhome_pb_{joint}').setEnabled(True)
		elif not parent.status.joint[joint]['homed']:
			if f'home_pb_{joint}' in parent.child_names:
				getattr(parent, f'home_pb_{joint}').setEnabled(True)
			if f'unhome_pb_{joint}' in parent.child_names:
				getattr(parent, f'unhome_pb_{joint}').setEnabled(False)
	if all(parent.status.homed[:parent.joints]):
		parent.home_all_pb.setEnabled(False)
		if 'unhome_all_pb' in parent.child_names:
			parent.unhome_all_pb.setEnabled(True)
	if not any(parent.status.homed[:parent.joints]):
		if 'home_all_pb' in parent.child_names and home_all_check(parent):
			parent.home_all_pb.setEnabled(True)
		if 'unhome_all_pb' in parent.child_names:
			parent.unhome_all_pb.setEnabled(False)






