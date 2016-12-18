import logging, itertools
from .. import spdy
from ..spdy import alx1_http

###

L = logging.getLogger("seacat.core.streamfactory")

###

class StreamFactory(object):

	def __init__(self):
		self.stream_id_seq = itertools.count(start=1, step=2)
		self.streams = dict()
		

	def register_stream(self, stream):
		streamid = next(self.stream_id_seq)
		self.streams[streamid] = stream
		return streamid


	def received_ALX1_SYN_REPLY(self, frame, length, flags):
		stream_id, status_code, kv = alx1_http.parse_alx1_syn_reply_frame(frame)
		stream = self.streams.get(stream_id, None)
		if (stream is None):
			L.warn("SYN_REPLY for unknown stream {}".format(stream_id))
			#TODO: Send RST_STREAM
			return True

		stream.syn_reply(status_code, kv, flags)
		return True


	def received_SPD3_RST_STREAM(self, frame, length, flags):
		stream_id, status_code = alx1_http.parse_rst_stream_frame(frame)
		stream = self.streams.pop(stream_id, None)
		if (stream is None):
			L.warn("RST_STREAM for unknown stream {}".format(stream_id))
			return True

		stream.reset_stream(status_code, flags)
		return True


	def received_cntl_frame(self, frame, version, ftype, length, flags):
		if ((version == spdy.CNTL_FRAME_VERSION_ALX1) and (ftype == spdy.CNTL_FRAME_TYPE_SYN_REPLY)):
			return self.received_ALX1_SYN_REPLY(frame, length, flags)

		elif ((version == spdy.CNTL_FRAME_VERSION_SPD3) and (ftype == spdy.CNTL_FRAME_TYPE_RST_STREAM)):
			return self.received_SPD3_RST_STREAM(frame, length, flags)

		L.warn("Unknown Control frame received: {} {} {} {}", version, ftype, flags, length)
		return True


