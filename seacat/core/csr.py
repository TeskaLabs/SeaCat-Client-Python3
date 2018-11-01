import ctypes

from ..exception import SeaCatError
from . import seacatcc

def submitCSR(csr_params:dict):
	arr = (ctypes.c_char_p * (len(csr_params) * 2 + 1))()
	for x in enumerate(csr_params.items()):
		i = x[0] * 2			
		arr[i] = x[1][0].encode('utf-8')
		arr[i+1] = x[1][1].encode('utf-8')
	arr[len(csr_params) * 2] = None

	rc = seacatcc.seacatclcc.seacatcc_csrgen_worker(arr)
	if (rc != seacatcc.RC_OK): raise SeaCatError(rc)

