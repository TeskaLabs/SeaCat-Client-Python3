import queue
from .frame import Frame

class FramePool(object):


	def __init__(self, frame_count=20, frame_capacity=16*1024):
		self.q = queue.Queue()

		self.write_ref = None
		self.read_ref = None

		for _ in range(frame_count):
			frame = Frame(frame_capacity)
			self.q.put(frame)

	def borrow(self):
		frame = self.q.get()
		frame.reset()
		return frame

	def putback(self, frame):
		self.q.put(frame)
