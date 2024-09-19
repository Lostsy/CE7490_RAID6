module_path = '/Users/shiyumeng/Codes/CE7490_RAID6/src'
import sys
import time
sys.path.append(module_path)

from raid6 import RAID6
from utils import RAID6Config
import logging

def test_block_size(block_size, path, name):
    config = RAID6Config(data_disks=6, block_size=block_size)
    print(config)
    raid6 = RAID6(config)

    # Save data to the RAID6 system
    fp = path
    raid6.save_data(fp, name=name)

if __name__ == "__main__":
    path = "../data/data.bin"
    name = "data.bin"
    logger = logging.getLogger("RAID6")
    # logger.setLevel(logging.DEBUG)
    for i in range(5):
        test_block_size(2**10, path, name)
    for i in range(5):
        test_block_size(2**15, path, name)
    for i in range(5):
        test_block_size(2**20, path, name)
    for i in range(5):
        test_block_size(2**25, path, name)
    for i in range(5):
        test_block_size(2**30, path, name)