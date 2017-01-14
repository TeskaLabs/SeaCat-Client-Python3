import sys
from ..core import seacatcc

def commit_capabilities(caps=None):
	caps_sys = {
		"pln": sys.implementation.name,
		"pli": sys.api_version,
		"plv": sys.version,
		"plb": sys.platform
	}

	if caps is None:
		caps = caps_sys
	else:
		caps = caps.copy()
		caps.update(caps_sys)

	seacatcc.capabilities_store(caps)
