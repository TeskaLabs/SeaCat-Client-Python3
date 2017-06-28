import sys
from ..core import seacatcc

def commit_characteristics(characteristics=None):
	characteristics_sys = {
		"pln": sys.implementation.name,
		"pli": sys.api_version,
		"plv": sys.version,
		"plb": sys.platform
	}

	if characteristics is None:
		characteristics = characteristics_sys
	else:
		characteristics = characteristics.copy()
		characteristics.update(characteristics_sys)

	seacatcc.characteristics_store(characteristics)
