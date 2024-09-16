module_path = '/Users/shiyumeng/Codes/CE7490_RAID6/src'
import sys
import time
sys.path.append(module_path)

from clib.galois_field import cal_parity, cal_parity_8, cal_parity_p, cal_parity_q, cal_parity_q_8
from clib.galois_field import cal_parity_p_rm8, cal_parity_p_rmunrolling, cal_parity_q_rmunrolling, cal_parity_q_8_rmunrolling
from galois_field_old import cal_parity_p_py, cal_parity_q_py
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


def test_optimization_for_cal_p(block_size=1024, times=10):
    data = bytearray(random.getrandbits(8) for _ in range(block_size * 6))
    p = bytearray(block_size)

    # original python version
    start1 = time.time()
    for i in range(times):
        cal_parity_p_py(p, data)
    end1 = time.time()

    # c++ version
    start2 = time.time()
    for i in range(times):
        cal_parity_p_rm8(p, data)
    end2 = time.time()

    # c++ + 8 parallel version
    start3 = time.time()
    for i in range(times):
        cal_parity_p_rmunrolling(p, data)
    end3 = time.time()

    # c++ + 8 parallel + 8 unrolling version
    start4 = time.time()
    for i in range(times):
        cal_parity_p(p, data)
    end4 = time.time()

    print('cal_parity_p_py time: ', (end1 - start1) / times)
    print('cal_parity_p_rm8 time: ', (end2 - start2) / times)
    print('cal_parity_p_rmunrolling time: ', (end3 - start3) / times)
    print('cal_parity_p time: ', (end4 - start4) / times)


def test_optimization_for_cal_q(block_size=1024, times=10):
    data = bytearray(random.getrandbits(8) for _ in range(block_size * 6))
    q = bytearray(block_size)

    # original python version
    start1 = time.time()
    for i in range(times):
        cal_parity_q_py(q, data)
    end1 = time.time()

    # c++ version
    start2 = time.time()
    for i in range(times):
        cal_parity_q_rmunrolling(q, data, range(6))
    end2 = time.time()

    # c++ + unrolling version
    start3 = time.time()
    for i in range(times):
        cal_parity_q(q, data, range(6))
    end3 = time.time()

    # c++ 8 parallel version
    start4 = time.time()
    for i in range(times):
        cal_parity_q_8_rmunrolling(q, data)
    end4 = time.time()

    # c++ 8 parallel + unrolling version
    start5 = time.time()
    for i in range(times):
        cal_parity_q_8(q, data)
    end5 = time.time()

    print('cal_parity_q_py time: ', (end1 - start1) / times)
    print('cal_parity_q_rmunrolling time: ', (end2 - start2) / times)
    print('cal_parity_q time: ', (end3 - start3) / times)
    print('cal_parity_q_8_rmunrolling time: ', (end4 - start4) / times)
    print('cal_parity_q_8 time: ', (end5 - start5) / times)


if __name__ == '__main__':
    test_optimization_for_cal_q(2**20, 10)
    exit(0)