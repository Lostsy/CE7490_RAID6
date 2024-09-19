#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    : test_recover_compare_file_size.py
@Time    : 2024/09/19
@Version : 0.1
@License : TOADD
@Desc    : NONE
'''

import src
import pytest
import os
import time
import random
import logging
from test_save_load import calculate_md5

random.seed(42)

def build_raid6(block_size=256*1024):
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

def test_recover_data_data(filepath, corrupt_disk_num=1, total_size=64*1024*1024):
    '''
    Test the recover data from the RAID6 system
    '''
    raid6 = build_raid6()
    img_path = filepath # xxx/xxx/sample_2E20
    output_path = f"{filepath}_recover"
    # raid6.save_data(img_path, name="cockatoo")
    file_size = os.path.getsize(img_path)
    read_num = total_size // file_size

    for i in range(read_num):
        raid6.save_data(img_path, name=f"sample_{i}")
    
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

    md5src = calculate_md5(img_path)
    flag = True
    for i in range(read_num):
        raid6.load_data(f"sample_{i}", out_path=f"{filepath}_recover", verify=True)
        tgt_path = f"{filepath}_recover"
        md5tgt = calculate_md5(tgt_path)
        flag = flag and ( md5src == md5tgt )
    return duration, flag


def test_by_parameters():
    logger = logging.getLogger("RecoveryExp")
    logger.setLevel(logging.DEBUG)
    filehandler = logging.FileHandler("test/exp_results/compare_recovery_w_file_size.log")
    logger.addHandler(filehandler)


    file_list = [os.path.join("data/sample_data_pieces", f"sample_2E{i}") for i in range(17,21)]
    print(file_list)
    corrupt_disk_nums = [1, 2]
    for file in file_list:
        for corrupt_disk_num in corrupt_disk_nums:
            duration, flag = test_recover_data_data(file, corrupt_disk_num=corrupt_disk_num)
            # print(f"Block size: {block_size}, Corrupt disk number: {corrupt_disk_num}, Duration: {duration}, Flag: {flag}")
            logger.debug(f"File: {file}, Corrupt disk number: {corrupt_disk_num}, Duration: {duration}, Flag: {flag}")
    # block_sizes = [2**10, 2**12, 2**14, 2**16, 2**18, 2**20]
    # corrupt_disk_nums = [1, 2]
    # for block_size in block_sizes:
    #     for corrupt_disk_num in corrupt_disk_nums:
    #         duration, flag = test_recover_data_data(block_size=block_size, corrupt_disk_num=corrupt_disk_num)
    #         # print(f"Block size: {block_size}, Corrupt disk number: {corrupt_disk_num}, Duration: {duration}, Flag: {flag}")
    #         logger.debug(f"Block size: {block_size}, Corrupt disk number: {corrupt_disk_num}, Duration: {duration}, Flag: {flag}")
