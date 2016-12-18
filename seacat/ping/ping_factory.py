import queue, itertools, logging
from .ping import Ping
from ..spdy import spd3_ping

###

L = logging.getLogger("seacat.ping")

###

class PingFactory(object):

	def __init__(self):
		self.id_seq = itertools.count(start=1, step=2)
		self.outbound_ping_q = queue.Queue()
		self.watinig_pings = dict()

	#TODO: Reset when gw connection is disconnected
	#TODO: Heartbeat and timeout

	def ping(self, reactor, on_pong):
		p = Ping(on_pong)
		self.outbound_ping_q.put(p)
		reactor.register_frame_provider(self, True)
		return p


	def build_frame(self, reactor):
		try:
			p = self.outbound_ping_q.get_nowait()
		except queue.Empty:
			p = None
		if p is None: return None, False

		p.ping_id = next(self.id_seq)
		self.watinig_pings[p.ping_id] = p

		frame = reactor.frame_pool.borrow()
		spd3_ping.build_ping_frame(frame, p.ping_id)

		frame.flip()
		return frame, not self.outbound_ping_q.empty()


	def received_cntl_frame(self, frame, version, ftype, length, flags):
		ping_id, = spd3_ping.parse_ping_frame(frame)

		if (ping_id % 2) == 1:
			ping = self.watinig_pings.pop(ping_id)
			if ping is None:
				L.warn("Unknown ping received: {}".format(ping_id))
			else:
				ping.pong()
			return True

		else:
			#TODO: Send pong to server ...
			pass

		return True
