
class State(object):

	def __init__(self, state):
		self.state = state[0:].decode('ascii')

	def __str__(self):
		return "<{} {}>".format(self.__class__.__name__, self.state)

	def char_at(self, n):
		return self.state[n]

	def isAnonymous(self):
		return self.state[4] == 'A'

	def isReady(self):
		return (self.state[3] == 'Y') and (self.state[4] == 'N') and (self.state[0] != 'f')
