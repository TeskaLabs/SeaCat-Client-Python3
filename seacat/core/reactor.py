import ctypes, threading, logging, queue
from . import seacatcc, framepool, state
from ..exception import SeaCatError
from .. import spdy
from ..ping.ping_factory import PingFactory
from .streamfactory import StreamFactory

###

L = logging.getLogger("seacat.core.reactor")

###

class Reactor(object):

	def __init__(self, appid, appid_suffix, platform, var_directory):
		self.refs = []
		self.write_frame = None
		self.read_frame = None

		self.state_buffer = ctypes.create_string_buffer(32)

		self.on_csr_needed = None
		self.on_state_changed = None
		self.on_ready = None

		self.is_ready_event = threading.Event()
		self.is_connected_event = threading.Event()
		self.is_disconnected_event = threading.Event()
		self.is_disconnected_event.set()

		self.frame_pool = framepool.FramePool()
		self.reactor_thread = threading.Thread(target=self._run, name="SeaCatReactorThread", daemon=True)
		self.active_workers = list()

		self.frame_providers = queue.Queue()

		if platform is None:
			platform = "py3"
		seacatcc.init(self, appid, appid_suffix, platform, var_directory)

		seacatcc.read_state(self.state_buffer)
		self.state = state.State(self.state_buffer)

		self.hook_register('S', self._hook_on_state_changed)

		# Factories
		self.ping_factory = PingFactory()
		self.stream_factory = StreamFactory()

		# Frame consumers
		self.cntl_frame_consumers = dict()
		self.cntl_frame_consumers[(spdy.CNTL_FRAME_VERSION_SPD3 << 16) | spdy.CNTL_FRAME_TYPE_PING] = self.ping_factory;
		self.cntl_frame_consumers[(spdy.CNTL_FRAME_VERSION_ALX1 << 16) | spdy.CNTL_FRAME_TYPE_SYN_REPLY] = self.stream_factory;
		self.cntl_frame_consumers[(spdy.CNTL_FRAME_VERSION_SPD3 << 16) | spdy.CNTL_FRAME_TYPE_RST_STREAM] = self.stream_factory;


	###


	def start(self):
		self.reactor_thread.start()

	def isAlive(self):
		if self.reactor_thread is None: return False
		return self.reactor_thread.is_alive()		

	def join(self, timeout=None):
		if self.reactor_thread is None: return None
		return self.reactor_thread.join(timeout)

	def shutdown(self, timeout=None):
		seacatcc.shutdown()
		self.join()

	def _run(self):
		rc = seacatcc.run()
		if rc != seacatcc.RC_OK:
			L.error("SeaCat C-Code return code {}".format(rc))
		
		self.reactor_thread = None
		self.refs = []


	def hook_register(self, code, callback):
		h = seacatcc.hook_seacatcc_hook_type(callback)
		seacatcc.seacatclcc.seacatcc_hook_register(ord(code), h)	
		self.refs.append(h)

	###

	def register_frame_provider(self, provider, single):
		#TODO: if single and (provider in self.frame_providers): return
		self.frame_providers.put(provider)

		seacatcc.yield_cmd('W')

	###

	def _received_cntl_frame(self, frame):
		version, ftype, flags, length = spdy.parse_cntl_frame(frame)

		consumer = self.cntl_frame_consumers.get((version << 16 ) | ftype)
		if consumer is None:
			L.warn("Unidentified Control frame received: {} {} {} {}", version, ftype, flags, length)
			return True

		return consumer.received_cntl_frame(frame, version, ftype, length, flags)


	def _hook_frame_received(self, data, data_len):
		assert(self.read_frame is not None)
		assert(ctypes.addressof(self.read_frame.data) == data)

		frame = self.read_frame
		self.read_frame = None

		frame.position = 0
		frame.limit = data_len

		fb = ord(frame.data[0])
		give_back = True

		try:
			if (fb & 0x80) != 0:
				give_back = self._received_cntl_frame(frame)

			else:
				#TODO: This...
				print("Received data frame:", frame, fb)

		except:
			L.exception("Error when processing incoming frame")
			give_back = True

		finally:
			if give_back:
				self.frame_pool.putback(frame)


	def _hook_write_ready(self, data, data_len):
		assert(self.write_frame is None)

		try:
			provider = self.frame_providers.get_nowait()
		except queue.Empty:
			return

		frame, keep = provider.build_frame(self)
		if keep:
			self.frame_providers.put(provider)

		data[0] = ctypes.addressof(frame.data)
		data_len[0] = frame.limit
		self.write_frame = frame


	def _hook_read_ready(self, data, data_len):
		assert(self.read_frame is None)

		self.read_frame = self.frame_pool.borrow()
		data[0] = ctypes.addressof(self.read_frame.data)
		data_len[0] = self.read_frame.capacity


	def _hook_frame_return(self, frame):
		if (self.read_frame is not None) and (ctypes.addressof(self.read_frame.data) == frame):
			self.frame_pool.putback(self.read_frame)
			self.read_frame = None
			return

		if (self.write_frame is not None) and (ctypes.addressof(self.write_frame.data) == frame):
			self.frame_pool.putback(self.write_frame)
			self.write_frame = None
			return

		L.error("Frame returned {:X} - UNKNOWN FRAME".format(frame))


	def _hook_worker_request(self, worker_code):
		if worker_code == b'P':
			w = threading.Thread(name="SeaCatPPKWorkerThread", target=seacatcc.seacatclcc.seacatcc_ppkgen_worker)
			w.start()
			self.active_workers.append(w)

		elif worker_code == b'C':
			w = threading.Thread(name="SeaCatCSRWorkerThread", target=self._hook_csr_worker)
			w.start()
			self.active_workers.append(w)

		else:
			L.error("Unknown worker requested: '{}'".format(worker_code.decode('utf-8')))


	def _hook_evloop_heartbeat(self, now):
		a = self.active_workers
		self.active_workers = []
		for w in a:
			w.join(0.0)
			if w.is_alive():
				self.active_workers.append(w)
		return 5.0


	def _hook_csr_worker(self):
		if self.on_csr_needed is not None:
			csr_params = self.on_csr_needed()
		else:
			csr_params = {}
		arr = (ctypes.c_char_p * (len(csr_params) * 2 + 1))()
		for x in enumerate(csr_params.items()):
			i = x[0] * 2			
			arr[i] = x[1][0].encode('utf-8')
			arr[i+1] = x[1][1].encode('utf-8')
		arr[len(csr_params) * 2] = None

		rc = seacatcc.seacatclcc.seacatcc_csrgen_worker(arr)
		if (rc != seacatcc.RC_OK): raise SeaCatError(rc)

	#

	def _hook_on_state_changed(self):
		seacatcc.read_state(self.state_buffer)
		self.state = state.State(self.state_buffer)

		if self.state.char_at(0) == 'E':
			self.is_disconnected_event.clear()
			self.is_connected_event.set()
		else:
			self.is_connected_event.clear()
			self.is_disconnected_event.set()

		if self.on_state_changed is not None:
			self.on_state_changed(s)
		
		if self.state.isReady():
			self.is_ready_event.set()
			if self.on_ready is not None:
				self.on_ready()
				self.on_ready = None # Call only once
		else:
			self.is_ready_event.clear()
