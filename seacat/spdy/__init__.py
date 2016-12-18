import struct
from .spdy import *

def parse_cntl_frame(frame):
	if (frame.position + SPDY_HEADER_SIZE) > frame.limit:
		raise RuntimeError("Parsing error")

	version, ftype, length = struct.unpack_from("!HHI", frame.data, frame.position)

	flags = length >> 24;
	length &= 0xffffff;

	frame.position += struct.calcsize("!HHI")

	if (frame.position + length) > frame.limit:
		raise RuntimeError("Parsing error")

	return version, ftype, flags, length


def parse_data_frame(frame):
	if (frame.position + SPDY_HEADER_SIZE) > frame.limit:
		raise RuntimeError("Parsing error")

	stream_id, length = struct.unpack_from("!II", frame.data, frame.position)
	flags = (length & 0xFF000000) >> 24
	length &= 0x00FFFFFF

	frame.position += struct.calcsize("!II")

	if (frame.position + length) > frame.limit:
		raise RuntimeError("Parsing error")

	fin_flag = (flags & SPDY_FLAG_FIN) == SPDY_FLAG_FIN

	return stream_id, flags, fin_flag, length
