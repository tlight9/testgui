import re



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

