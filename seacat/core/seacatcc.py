import os, ctypes, logging
from ..exception import SeaCatError

###

L = logging.getLogger("seacat.core.seacatcc")

###

RC_OK = 0

###

seacatclcc = ctypes.cdll.LoadLibrary(os.path.join(os.path.dirname(__file__), "libseacatcc.so"))

hook_seacatcc_hook_type = ctypes.CFUNCTYPE(None)
seacatclcc.seacatcc_hook_register.argtypes = [ctypes.c_char, hook_seacatcc_hook_type]

###

# Configure logging

hook_seacatcc_log_fnct_type = ctypes.CFUNCTYPE(None, ctypes.c_char, ctypes.c_char_p)
seacatclcc.seacatcc_log_setfnct.argtypes = [hook_seacatcc_log_fnct_type]

def seacatcc_log_fnct(level, message):
	message = message.decode('utf-8')
	if level == b'I':
		L.info(message)
	elif level == b'D':
		L.debug(message)
	elif level == b'W':
		L.warn(message)
	elif level == b'E':
		L.error(message)
	elif level == b'F':
		L.fatal(message)
	else:
		L.error("(? unknown level {}): {}".format(level. message))

seacatcc_log_fnct = hook_seacatcc_log_fnct_type(seacatcc_log_fnct)
seacatclcc.seacatcc_log_setfnct(seacatcc_log_fnct)

###

hook_write_ready_type = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint16))
hook_read_ready_type = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint16))
hook_frame_received_type = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint16)
hook_frame_return_type = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
hook_worker_request_type = ctypes.CFUNCTYPE(None, ctypes.c_char)
hook_evloop_heartbeat_type = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_char)

seacatclcc.seacatcc_init.argtypes = [
	ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
	hook_write_ready_type,
	hook_read_ready_type,
	hook_frame_received_type,
	hook_frame_return_type,
	hook_worker_request_type,
	hook_evloop_heartbeat_type,
	ctypes.c_char_p
]

def init(reactor, appid, appid_suffix, platform, var_directory, openssl_engine_ppk):

	hook_write_ready = hook_write_ready_type(reactor._hook_write_ready)
	hook_read_ready = hook_read_ready_type(reactor._hook_read_ready)
	hook_frame_received = hook_frame_received_type(reactor._hook_frame_received)
	hook_frame_return = hook_frame_return_type(reactor._hook_frame_return)
	hook_worker_request = hook_worker_request_type(reactor._hook_worker_request)
	hook_evloop_heartbeat = hook_evloop_heartbeat_type(reactor._hook_evloop_heartbeat)

	seacatclcc.seacatcc_log_set_mask(1);

	# Initialize SeaCat client
	rc = seacatclcc.seacatcc_init(
		appid.encode('ascii'),
		appid_suffix.encode('ascii') if appid_suffix is not None else None,
		platform.encode('ascii'),
		var_directory.encode('ascii') if var_directory is not None else None,
		hook_write_ready,
		hook_read_ready,
		hook_frame_received,
		hook_frame_return,
		hook_worker_request,
		hook_evloop_heartbeat,
		openssl_engine_ppk.encode('ascii') if openssl_engine_ppk is not None else None,
	)
	if (rc != RC_OK): raise SeaCatError(rc)

	reactor.refs.append(hook_write_ready)
	reactor.refs.append(hook_read_ready)
	reactor.refs.append(hook_frame_received)
	reactor.refs.append(hook_frame_return)
	reactor.refs.append(hook_worker_request)
	reactor.refs.append(hook_evloop_heartbeat)

###

seacatclcc.seacatcc_run.argtypes = []

def run():
	return seacatclcc.seacatcc_run()

###

seacatclcc.seacatcc_shutdown.argtypes = []

def shutdown():
	rc = seacatclcc.seacatcc_shutdown()
	if (rc != RC_OK): raise SeaCatError(rc)

###

seacatclcc.seacatcc_state.argtypes = [ctypes.c_char_p]

def read_state(statebuf):
	seacatclcc.seacatcc_state(statebuf)

###

seacatclcc.seacatcc_yield.argtypes = [ctypes.c_char]

def yield_cmd(cmd):
	rc = seacatclcc.seacatcc_yield(ord(cmd))
	if (rc != RC_OK): raise SeaCatError(rc)

##

seacatclcc.seacatcc_gwconn_cert.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint16)]

def gwconn_cert():

	cert_buf_len = 4096
	cert_buf = ctypes.create_string_buffer(cert_buf_len)

	cert_buf_len_ctypes = ctypes.c_uint16(cert_buf_len)
	p = ctypes.addressof(cert_buf_len_ctypes)

	rc = seacatclcc.seacatcc_gwconn_cert(cert_buf, ctypes.cast(p, ctypes.POINTER(ctypes.c_uint16)))
	if (rc != RC_OK): raise SeaCatError(rc)

	return cert_buf[:cert_buf_len_ctypes.value]

##

seacatclcc.seacatcc_time.argtypes = []
seacatclcc.seacatcc_time.restype = ctypes.c_double

def time():
	return seacatclcc.seacatcc_time()

##

seacatclcc.seacatcc_characteristics_store.argtypes = [ctypes.POINTER(ctypes.c_char_p)]

def characteristics_store(characteristics):
	characteristics_l = ["{}\037{}".format(k, v).encode("utf-8") for k, v in characteristics.items()]
	characteristics_l.append(None)

	characteristics_arr = (ctypes.c_char_p * len(characteristics_l))(*characteristics_l)
	rc = seacatclcc.seacatcc_characteristics_store(characteristics_arr)
	if (rc != RC_OK): raise SeaCatError(rc)

##

seacatclcc.seacatcc_socket_configure_worker.argtypes = [ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_char_p, ctypes.c_char_p];

def socket_configure_worker(port, af_domain, af_type, af_protocol, peer_address, peer_port):
	rc = seacatclcc.seacatcc_socket_configure_worker(
		port,
		af_domain, af_type, af_protocol,
		peer_address.encode('utf-8'), peer_port.encode('utf-8')
	)
	if (rc != RC_OK): raise SeaCatError(rc)

###

seacatclcc.seacatcc_set_discover_domain.argtypes = [ctypes.c_char_p]

def set_discover_domain(domain):
	seacatclcc.seacatcc_set_discover_domain(domain.encode('utf-8'))


###

seacatclcc.seacatcc_derive_key.argtypes = [ctypes.c_char_p, ctypes.c_uint16, ctypes.c_char_p]

def derive_key(key_id, length):
	keybuf = ctypes.create_string_buffer(length)
	rc = seacatclcc.seacatcc_derive_key("{}".format(key_id).encode('utf-8'), length, keybuf)
	if (rc != RC_OK): raise SeaCatError(rc)
	return keybuf.raw
