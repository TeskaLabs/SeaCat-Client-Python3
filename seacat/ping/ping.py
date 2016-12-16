import threading
from ..core import seacatcc

class Ping(object):


	def __init__(self, on_pong, deadline = 60.0):
		self.ping_id = -1
		self.sent_at = seacatcc.time()
		self.deadline =  self.sent_at + deadline
		self.on_pong = on_pong
		self.on_pong_event = threading.Event()
		self.pong_received = None


	def wait(self, timeout = None):
		self.on_pong_event.wait(timeout)
		return self.pong_received


	def pong(self):
		self.pong_received = True
		self.on_pong_event.set()
		if self.on_pong is not None: self.on_pong(self, True)


	def cancel(self):
		self.pong_received = False
		self.on_pong_event.set()
		if self.on_pong is not None: self.on_pong(self, False)
