import urllib.request
from .connection import SeaCatHTTPConnection

class SeaCatHttpHandler(urllib.request.AbstractHTTPHandler):

	handler_order = 499

	def __init__(self, reactor):
		super(urllib.request.AbstractHTTPHandler, self).__init__()
		self._debuglevel = 0
		self.reactor = reactor

	def http_open(self, req):
		return self.do_open(SeaCatHTTPConnection, req, reactor=self.reactor)

	def https_open(self, req):
		return self.do_open(SeaCatHTTPConnection, req, reactor=self.reactor)


	http_request = urllib.request.AbstractHTTPHandler.do_request_
	https_request = urllib.request.AbstractHTTPHandler.do_request_
