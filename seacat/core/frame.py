import ctypes

class Frame(object):

	def __init__(self, capacity):
		self.capacity = capacity
		self.data = ctypes.create_string_buffer(capacity)
		self.reset()

	def reset(self):
		self.position = 0
		self.limit = self.capacity

	def flip(self):
		self.limit = self.position
		self.position = 0

	def save(self, fname):
		f = open(fname, 'wb')
		f.write(self.data[0:self.limit])
