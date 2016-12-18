import struct
from .spdy import *

def build_ping_frame(frame, ping_id):
	frame_len = struct.calcsize('!HHII')
	assert((frame.position + frame_len) <= frame.capacity)
	struct.pack_into('!HHII', frame.data, frame.position, 
		CNTL_FRAME_VERSION_SPD3, CNTL_FRAME_TYPE_PING, 
		(frame_len - SPDY_HEADER_SIZE) & 0x00FFFFFF,
		ping_id
	)

	frame.limit += frame_len
	frame.position += frame_len

	return frame


def parse_ping_frame(frame):
	assert(frame.limit == frame.position + 4)
	return struct.unpack_from("!I", frame.data, frame.position)
	frame.position += 4
