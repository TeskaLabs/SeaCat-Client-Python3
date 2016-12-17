import struct
from .spdy import *
from .vle import spdy_add_vle_string, spdy_read_vle_string

def build_syn_stream_frame(frame, stream_id, host, method, path):

	hdr_len = struct.calcsize('!HH4BIIBB')
	assert((frame.position + hdr_len) <= frame.capacity)

	struct.pack_into('!HH4BIIBB', frame.data, frame.position, 
		CNTL_FRAME_VERSION_ALX1, CNTL_FRAME_TYPE_SYN_STREAM, 
		0, # Flags
		0xFF, 0xFE, 0xFD, # Placeholder for real length
		stream_id,
		0, 
		0b00100000, # Priority
		0 # Slot
	)

	frame.position += hdr_len

	spdy_add_vle_string(frame, host)
	spdy_add_vle_string(frame, method)
	spdy_add_vle_string(frame, path)

	# Calculate length
	lenb = struct.pack('!I', frame.position - SPDY_HEADER_SIZE)
	frame.data[5:8] = lenb[1:]
	frame.data[4] = SPDY_FLAG_FIN


def parse_rst_stream_frame(frame):
	'''returns (stream_id, status_code) '''
	assert(frame.limit == SPDY_HEADER_SIZE + 8)
	return struct.unpack_from("!II", frame.data, frame.position + SPDY_HEADER_SIZE)


def parse_alx1_syn_reply_frame(frame):
	stream_id, status_code, _ = struct.unpack_from("!Ihh", frame.data, frame.position + SPDY_HEADER_SIZE)

	kv = []
	frame.position = frame.position + SPDY_HEADER_SIZE + 8
	while frame.position < frame.limit:
		hname = spdy_read_vle_string(frame)
		vname = spdy_read_vle_string(frame)
		kv.append((hname.decode('utf-8'), vname.decode('utf-8')))

	return stream_id, status_code, kv
