import struct
from .spdy import *

def parse_cntl_frame(frame):
	version, ftype, length = struct.unpack_from("!HHI", frame.data)

	flags = length >> 24;
	length &= 0xffffff;

	if length + SPDY_HEADER_SIZE != frame.limit:
		raise RuntimeError("Parsing error.")

	return version, ftype, flags, length
