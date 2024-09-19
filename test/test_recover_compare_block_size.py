#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    : test_recover_compare_blcok_size.py
@Time    : 2024/09/19
@Version : 0.1
@License : TOADD
@Desc    : NONE
'''

import src
import pytest
import time
import random
import logging
from test_save_load import calculate_md5

random.seed(42)

def build_raid6(block_size=1024*1024):
    from src.utils import RAID6Config
    from src.raid6 import RAID6

    config = RAID6Config(
        data_disks=6, 
        parity_disks=2, 
        block_size=block_size, 
        disk_size=64*1024*1024
        )
    
    raid6 = RAID6(config)
    return raid6

def test_recover_data_data(block_size=1024*1024, corrupt_disk_num=1):
    '''
    Test the recover data from the RAID6 system
    '''
    raid6 = build_raid6(block_size=block_size)
    img_path = "data/sample.png"
    output_path = "data/cockatoo.png"
    raid6.save_data(img_path, name="cockatoo")
    
    # Randomly corrupt corrupt_disk_num disks
    assert corrupt_disk_num <=2, "The number of corrupted disks should be no more than 2" 
    corrupt_id = random.sample(range(raid6.data_disks), corrupt_disk_num)
    # print(f"Corrupt disk {corrupt_id}")
    for i in range(len(raid6.status)):
        for j in corrupt_id:
            raid6.status[i][j] = False
    # raid6.check_disks_status()
    # raid6.check_disks_status()
    start = time.time()
    raid6.recover_disks()
    end = time.time()
    duration = end - start
    raid6.load_data("cockatoo", out_path=output_path, verify=True)

    # compare md5 checksum
    print(f"MD5 of {img_path}: {calculate_md5(img_path)}")
    print(f"MD5 of {output_path}: {calculate_md5(output_path)}")
    flag = calculate_md5(img_path) == calculate_md5(output_path)
    return duration, flag


def test_by_parameters():
    logger = logging.getLogger("RecoveryExp")
    logger.setLevel(logging.DEBUG)
    filehandler = logging.FileHandler("test/exp_results/compare_recovery_w_block_size.log")
    logger.addHandler(filehandler)


    block_sizes = [2**10, 2**12, 2**14, 2**16, 2**18, 2**20]
    corrupt_disk_nums = [1, 2]
    for block_size in block_sizes:
        for corrupt_disk_num in corrupt_disk_nums:
            duration, flag = test_recover_data_data(block_size=block_size, corrupt_disk_num=corrupt_disk_num)
            # print(f"Block size: {block_size}, Corrupt disk number: {corrupt_disk_num}, Duration: {duration}, Flag: {flag}")
            logger.debug(f"Block size: {block_size}, Corrupt disk number: {corrupt_disk_num}, Duration: {duration}, Flag: {flag}")
