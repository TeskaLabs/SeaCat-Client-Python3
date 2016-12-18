# SeaCat-Client-Python3
TeskaLabs SeaCat client for Python3

## Quick setup guide

1. Place a `libseacat.so` into `./seacat/core` directory.
2. `import seacat`

## HTTP client example

	import seacat

	# Install HTTP handler into urllib chain
	handler = seacat.getHTTPHandler()
	opener = urllib.request.build_opener(handler)
	urllib.request.install_opener(opener)
	
	# Use urllib in the normal fashion
	response = urllib.request.urlopen('http://example.com/')
	body = response.read()
	print(body)
	

