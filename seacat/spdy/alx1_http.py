import struct
from .spdy import *
from .vle import spdy_add_vle_string, spdy_read_vle_string

forbidden_fields = frozenset([
	"Host",
	"Connection"
])

def build_syn_stream_frame(frame, stream_id, host, method, path, headers, fin_flag):

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

	for hdr, value in headers.items():
		if (hdr in forbidden_fields): continue
		spdy_add_vle_string(frame, hdr)
		spdy_add_vle_string(frame, value)

	# Calculate length
	lenb = struct.pack('!I', frame.position - SPDY_HEADER_SIZE)
	frame.data[5:8] = lenb[1:]
	frame.data[4] = SPDY_FLAG_FIN if fin_flag else 0


def build_data_frame(frame, stream_id, data, fin_flag):
	data_len = len(data)

	frame_len = struct.calcsize('!II') + data_len
	assert((frame.position + frame_len) <= frame.capacity)

	struct.pack_into('!II', frame.data, frame.position, 
		stream_id,
		((SPDY_FLAG_FIN if fin_flag else 0) << 24 ) | data_len
	)

	# Not sure how this line is efficient
	frame.data[SPDY_HEADER_SIZE:SPDY_HEADER_SIZE+data_len] = data[0:data_len]

	frame.position += frame_len


def parse_rst_stream_frame(frame):
	'''returns (stream_id, status_code) '''
	assert(frame.limit == frame.position + 8)
	return struct.unpack_from("!II", frame.data, frame.position)
	frame.position += 8


def parse_alx1_syn_reply_frame(frame):
	assert(frame.limit >= frame.position + 8)
	stream_id, status_code, _ = struct.unpack_from("!Ihh", frame.data, frame.position)
	frame.position += 8

	kv = []
	while frame.position < frame.limit:
		hname = spdy_read_vle_string(frame)
		vname = spdy_read_vle_string(frame)
		kv.append((hname.decode('utf-8'), vname.decode('utf-8')))

	return stream_id, status_code, kv
