import atexit, threading

from . import plugin
from .core import reactor, seacatcc
from .exception import SeaCatError

###

Reactor = None

###

def initialize(appid, appid_suffix = None, platform = None, var_directory = None,
		on_csr_needed = None,
		on_state_changed = None,
		on_ready = None,
		on_connected = None,
		on_disconnected = None,
	):

	global Reactor
	assert(Reactor is None)
	Reactor = reactor.Reactor(appid, appid_suffix, platform, var_directory)

	Reactor.on_csr_needed = on_csr_needed
	Reactor.on_state_changed = on_state_changed
	Reactor.on_ready = on_ready

	if on_connected is not None:
		Reactor.hook_register('c', on_connected)

	if on_disconnected is not None:
		Reactor.hook_register('R', on_disconnected)

	Reactor.start()

	atexit.register(__atexit)

	plugin.commit_capabilities()


def __atexit():
	global Reactor

	atexit.unregister(__atexit)

	if Reactor is not None:
		Reactor.shutdown()
		Reactor = None


def connect(wait_timeout = 0):
	global Reactor
	assert(Reactor is not None)
	seacatcc.yield_cmd('c')
	if wait_timeout is not 0:
		return Reactor.is_connected_event.wait(wait_timeout)


def disconnect(wait_timeout = 0):
	global Reactor
	assert(Reactor is not None)
	seacatcc.yield_cmd('d')
	if wait_timeout is not 0:
		return Reactor.is_disconnected_event.wait(wait_timeout)


def ping(on_pong = None):
	global Reactor
	if Reactor is None: return None
	return Reactor.ping_factory.ping(Reactor, on_pong)


def get_seacat_handler():
	global Reactor
	if Reactor is None: return None
	from .http.handler import SeaCatHttpHandler
	return SeaCatHttpHandler(Reactor)


def install_urllib_opener():
	import urllib.request
	handler = get_seacat_handler()
	opener = urllib.request.build_opener(handler)
	urllib.request.install_opener(opener)


def getState():
	global Reactor
	if Reactor is None: return None
	return Reactor.state

def getGWCert():
	return seacatcc.gwconn_cert()


def isReady(wait_timeout=0.0):
	'''
	wait_timeout = None -> wait forever
	'''
	return Reactor.is_ready_event.wait(wait_timeout)

def isAlive():
	global Reactor
	if (Reactor is None): return False
	return Reactor.isAlive()

def join(timeout=None):
	global Reactor
	if (Reactor is None): return None
	return Reactor.join(timeout)

def configureSocket(port, af_domain, af_type, af_protocol, peer_address, peer_port):
	seacatcc.socket_configure_worker(port, af_domain, af_type, af_protocol, peer_address, peer_port)

def setDiscoverDomain(domain):
	seacatcc.set_discover_domain(domain)

