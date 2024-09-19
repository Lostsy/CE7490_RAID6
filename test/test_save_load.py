#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    : test_save_load.py
@Time    : 2024/09/19
@Version : 0.1
@License : TOADD
@Desc    : Unit tests for the save and load of data from the raid6 database
'''

import src
import pytest
import hashlib


def build_raid6():
    from src.utils import RAID6Config
    from src.raid6 import RAID6

    config = RAID6Config(
        data_disks=6, 
        parity_disks=2, 
        block_size=1024*1024, 
        disk_size=1024*1024*1024
        )
    
    raid6 = RAID6(config)
    return raid6

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def test_raid6_basic():
    raid_6 = build_raid6()
    img_path = "data/sample.jpg"
    output_path = "data/cockatoo.jpg"
    raid_6.save_data(img_path, name="cockatoo")
    raid_6.check_disks_status()
    raid_6.load_data("cockatoo", out_path=output_path, verify=True)

    # compare md5 checksum
    print(f"MD5 of {img_path}: {calculate_md5(img_path)}")
    print(f"MD5 of {output_path}: {calculate_md5(output_path)}")
    assert calculate_md5(img_path) == calculate_md5(output_path)

    




if __name__=="__main__":
    import src

