import struct

def spdy_add_vle_string(frame, string):
	buf = bytes(string, 'utf-8')
	buf_len = len(buf)

	if buf_len >= 0xFA:
		struct.pack_into('!BH', frame.data, frame.position, 0xFF, buf_len)
		frame.position += struct.calcsize('!BH')

	else:
		struct.pack_into('!B', frame.data, frame.position, buf_len)
		frame.position += struct.calcsize('!B')

	struct.pack_into('!{}s'.format(buf_len), frame.data, frame.position, buf)
	frame.position += buf_len


def spdy_read_vle_string(frame):
	len, = struct.unpack_from("!B", frame.data, frame.position)
	frame.position += struct.calcsize('!B')
	if (len == 0xFF):
		len, = struct.unpack_from("!H", frame.data, frame.position)
		frame.position += struct.calcsize('!H')

	data, = struct.unpack_from("!{}s".format(len), frame.data, frame.position)
	frame.position += struct.calcsize("!{}s".format(len))

	return data
