import logging, threading
from ..spdy import alx1_http

###

L = logging.getLogger("seacat.http.connection")

###

class SeaCatHTTPStream(object):

	def __init__(self, reactor, host):
		self.response_ready_cv = threading.Condition()
		self.response_ready = False

		self.stream_id = None
		self.reactor = reactor
		self.host = host

		self.method = None

		self.reset_status_code = None
		self.http_status_code = None
		self.http_headers = None


	def send(self, method, path, body=None, headers={}):
		assert(self.stream_id is None)
		assert(self.method is None)

		self.method = method
		self.path = path
		self.body = body
		self.headers = headers

		self.reactor.register_frame_provider(self, False)


	def wait(self):
		with self.response_ready_cv:
			while not self.response_ready:
				self.response_ready_cv.wait()


	def build_frame(self, reactor):
		'''Interface to reactor'''
		assert(self.stream_id is None)
		self.stream_id = reactor.stream_factory.register_stream(self)

		frame = reactor.frame_pool.borrow()
		alx1_http.build_syn_stream_frame(frame, self.stream_id, self.host, self.method, self.path)
		frame.flip()

		return frame, False


	def reset_stream(self, status_code, flags):
		with self.response_ready_cv:
			self.reset_status_code = status_code
			if not self.response_ready:
				self.response_ready = True
				self.response_ready_cv.notify_all()


	def syn_reply(self, status_code, kv, flags):
		with self.response_ready_cv:
			self.http_status_code = status_code
			self.http_headers = kv
			if not self.response_ready:
				self.response_ready = True
				self.response_ready_cv.notify_all()		

###

class SeaCatHTTPResponse(object):

	def __init__(self, stream):
		self.stream = stream

		self.reason = "AAAA"
		self.code = 200

		# TODO: implement timeout
		while True:

			self.stream.wait()

			if self.stream.reset_status_code is not None:
				# We received a RST_STREAM
				self.code = 501
				self.reason = "SPDY Error {}".format(self.stream.reset_status_code)
				break;

			if self.stream.http_status_code is not None:
				self.code = self.stream.http_status_code
				self.reason = "REASON MISSING" #TODO: Lookup reasons
				break;


	def info(self):
		return "xxx - info"

	def read(self):
		return "xxx - read"

	def close(self):
		return "xxx - close"

###

class SeaCatHTTPConnection(object):

	def __init__(self, host, reactor, port=None, timeout=30, source_address=None):
		super(SeaCatHTTPConnection, self).__init__()
		self.sock = None
		self.stream = SeaCatHTTPStream(reactor, host)
		self.response = None


	def request(self, method, url, body=None, headers={}):
		self.stream.send(method, url, body, headers)

	def getresponse(self):
		if self.response is not None:
			return self.response

		self.response = SeaCatHTTPResponse(self.stream)
		return self.response


	def close(self):
		print("Close")
