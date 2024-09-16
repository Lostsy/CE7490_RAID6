module_path = '/Users/shiyumeng/Codes/CE7490_RAID6/src'
import sys
import time
sys.path.append(module_path)

from clib.galois_field import cal_parity, cal_parity_8, cal_parity_p, cal_parity_q, cal_parity_q_8
from clib.galois_field import q_recover_data, recover_data_data
import random
import numpy as np

def test_recover_data_data(block_size=1):
    data1 = bytearray(random.getrandbits(8) for _ in range(block_size))
    data2 = bytearray(random.getrandbits(8) for _ in range(block_size))
    data3 = bytearray(random.getrandbits(8) for _ in range(block_size))
    data4 = bytearray(random.getrandbits(8) for _ in range(block_size))
    print(np.array(data1, dtype=np.uint8))
    print(np.array(data2, dtype=np.uint8))
    print(np.array(data3, dtype=np.uint8))
    print(np.array(data4, dtype=np.uint8))

    q = bytearray(block_size)
    p = bytearray(block_size)
    # new_data = bytearray(random.getrandbits(8) for _ in range(block_size * 4))
    new_data = data1 + data2 + data3 + data4
    cal_parity_q(q, new_data, [0, 1, 2, 3])
    print(np.array(q, dtype=np.uint8))

    # Test recover_data_data
    data_corrupted = data1 + data2 + data4
    idxs = [0, 1, 3]
    inter_q = bytearray(block_size)
    cal_parity_q(inter_q, data_corrupted, idxs)
    print(np.array(inter_q, dtype=np.uint8))
    
    new_data = bytearray(block_size)
    q_recover_data(new_data, q, inter_q, 2)

    print(data3 == new_data)

if __name__ == '__main__':
    test_recover_data_data()
    exit(0)