

class SeaCatError(IOError):

	def __init__(self, rc):
		super(SeaCatError, self).__init__()
		self.rc = rc
		self.message = "rc={}".format(rc)

	def __str__(self):
		return self.message
