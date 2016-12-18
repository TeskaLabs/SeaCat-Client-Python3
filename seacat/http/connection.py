import logging, threading, http.client, io, os
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

		#TODO: os.pipe can be replaced by in-memory queue
		self.resp_fp = None


	def send(self, method, path, body=None, headers={}):
		assert(self.stream_id is None)
		assert(self.method is None)

		self.method = method
		self.path = path
		self.body = body # Can be a 'bytes' for fixed Content-Length transfers or file-like object for Transfer-Encoding: chunked
		self.headers = headers # Dictionary

		self.send_syn_frame = True
		self.reactor.register_frame_provider(self, False)


	def wait(self):
		with self.response_ready_cv:
			while not self.response_ready:
				self.response_ready_cv.wait()


	def build_frame(self, reactor):
		'''Interface to reactor'''

		if self.send_syn_frame:
			# Send SYN FRAME
			assert(self.stream_id is None)
			self.stream_id = reactor.stream_factory.register_stream(self)		

			#TODO: If self.body has fixed and known length, add Content-Length attribute
			if self.body is not None:
				if hasattr(self.body, "read"):
					pass #TODO: Set Transfer-Encoding: chunked
				else:
					self.headers['Content-Length'] = "{}".format(len(self.body))

			fin_flag = (self.body is None)
			self.send_syn_frame = False
			frame = reactor.frame_pool.borrow()
			alx1_http.build_syn_stream_frame(frame, self.stream_id, self.host, self.method, self.path, self.headers, fin_flag)
			frame.flip()

		# Send DATA packets
		elif hasattr(self.body, "read"):
			#TODO: this ...
			raise RuntimeError("Not implemented yet")

		else:
			# Byte-buffer like data to be sent
			body_len = len(self.body)
			if (body_len < 8192): # 8k frame size
				fin_flag = True
				
				frame = reactor.frame_pool.borrow()
				alx1_http.build_data_frame(frame, self.stream_id, self.body, fin_flag)
				frame.flip()
			
			else:
				body = self.body[:8192]
				self.body = self.body[8192:]

				fin_flag = len(self.body) == 0
				
				frame = reactor.frame_pool.borrow()
				alx1_http.build_data_frame(frame, self.stream_id, body, fin_flag)
				frame.flip()


		return frame, not fin_flag


	def reset_stream(self, status_code, flags):
		'''Stream factory'''
		with self.response_ready_cv:
			self.reset_status_code = status_code
			if not self.response_ready:
				self.response_ready = True
				self.response_ready_cv.notify_all()


	def syn_reply(self, status_code, kv, flags):
		'''Stream factory'''
		with self.response_ready_cv:
			self.http_status_code = status_code
			self.http_headers = kv

			r, w = os.pipe()
			self.resp_fp = (io.open(r, mode="rb", closefd=True), io.open(w, mode="wb", closefd=True))

			if not self.response_ready:
				self.response_ready = True
				self.response_ready_cv.notify_all()		


	def data(self, frame, flags, fin_flag, length):
		'''Stream factory'''
		self.resp_fp[1].write(frame.data[frame.position:frame.limit])
		if fin_flag:
			self.resp_fp[1].close()
		return True


	def get_response_headers(self):
		assert(self.http_headers is not None)
		#TODO: Transform into http.client.HTTPMessage
		# Python uses for that email.parser.Parser (wierd but true)
		return self.http_headers

###

class SeaCatHTTPResponse(object):

	def __init__(self, stream):
		self.stream = stream

		self.reason = "AAAA"
		self.code = 200

		self.headers = None

		# TODO: implement timeout
		while True:
			self.stream.wait()

			if self.stream.reset_status_code is not None:
				# We received a RST_STREAM
				self.code = 501
				self.reason = "SPDY Error {}".format(self.stream.reset_status_code)
				break

			if self.stream.http_status_code is not None:
				self.code = self.stream.http_status_code
				self.reason = http.client.responses.get(self.code, "REASON MISSING")
				self.headers = self.stream.get_response_headers()
				break


	def read(self, amt=None):
		return self.stream.resp_fp[0].read(amt)

	def close(self):
		return "xxx - close"

	###

	def getheader(self, name, default=None):
		if self.headers is None:
			raise http.client.ResponseNotReady()

		headers = self.headers.get_all(name) or default
		if isinstance(headers, str) or not hasattr(headers, '__iter__'):
			return headers
		else:
			return ', '.join(headers)

	def getheaders(self):
		"""Return list of (header, value) tuples."""
		if self.headers is None:
			raise http.client.ResponseNotReady()
		return list(self.headers.items())

	# For compatibility with old-style urllib responses.

	def info(self):
		return self.headers

	def geturl(self):
		#TODO: This ...
		return self.url

	def getcode(self):
		return self.code

###

class SeaCatHTTPConnection(object):

	def __init__(self, host, reactor, port=None, timeout=30, source_address=None):
		super(SeaCatHTTPConnection, self).__init__()
		self.sock = None
		self.stream = SeaCatHTTPStream(reactor, host)
		self.response = None


	def request(self, method, url, body=None, headers=None):
		self.stream.send(method, url, body, headers if not None else {})

	def getresponse(self):
		if self.response is not None:
			return self.response

		self.response = SeaCatHTTPResponse(self.stream)
		return self.response


	def close(self):
		print("Close")
