import ctypes

class Frame(object):

	def __init__(self, capacity):
		self.capacity = capacity
		self.position = 0
		self.limit = self.capacity
		self.data = ctypes.create_string_buffer(capacity)


	def flip(self):
		self.limit = self.position
		self.position = 0

