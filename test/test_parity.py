module_path = '/Users/shiyumeng/Codes/CE7490_RAID6/src'
import sys
import time
sys.path.append(module_path)

from clib.galois_field import cal_parity, cal_parity_8, cal_parity_p, cal_parity_q, cal_parity_q_8
import random
import numpy as np

def test_cal_parity(block_size=8):
    # block_size is multiple of 8
    data = bytearray(random.getrandbits(8) for _ in range(block_size * 4))
    p = bytearray(block_size)
    q = bytearray(block_size)

    p_8 = bytearray(block_size)
    q_8 = bytearray(block_size)
    
    start1 = time.time()
    cal_parity(p, q, data)
    print(np.array(p, dtype=np.uint8))
    end1 = time.time()

    start2 = time.time()
    cal_parity_8(p_8, q_8, data)
    print(np.array(p_8, dtype=np.uint8))
    end2 = time.time()
    
    print(q == q_8)
    print('cal_parity time: ', end1 - start1)
    print('cal_parity_8 time: ', end2 - start2)

if __name__ == '__main__':
    test_cal_parity()
    exit(0)