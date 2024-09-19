#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    : test_modification.py
@Time    : 2024/09/19
@Version : 0.1
@License : TOADD
@Desc    : NONE
'''


import src
import pytest
from test_save_load import build_raid6, calculate_md5

def test_modify_single_large_file():
    '''
    Test the modification of a single file from the RAID6 system
    The src file is smaller than the target file
    '''
    raid6 = build_raid6()
    # Case 1: replace the image with a black and white image
    img_path = "data/sample.jpg"
    replace_img_path = "data/sample_bw.jpg"
    output_path = "data/cockatoo_bw.jpg"
    raid6.save_data(img_path, name="cockatoo")
    raid6.check_disks_status()
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    raid6.modify_data("cockatoo", "cockatoo_bw", replace_img_path)

    # # check if the file is deleted
    print(f"After Modification================================")
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    # # load the file and check if the image is the same
    raid6.load_data("cockatoo_bw", output_path, verify=True)

def test_modify_single_small_file():
    '''
    Test the modification of a single file from the RAID6 system
    The src file is smaller than the target file
    '''
    raid6 = build_raid6()
    # Case 2: replace a black and white image with a colored image
    img_path = "data/sample_bw.jpg"
    replace_img_path = "data/sample.jpg"
    output_path = "data/cockatoo.jpg"
    raid6.save_data(img_path, name="cockatoo")
    raid6.check_disks_status()
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    raid6.modify_data("cockatoo", "cockatoo_bw", replace_img_path)

    # # check if the file is deleted
    print(f"After Modification================================")
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    # # load the file and check if the image is the same
    raid6.load_data("cockatoo_bw", output_path, verify=True)


def test_merge_tuple():
    from src.utils import merge_tuples

    tuple_list = [(0, 5), (5, 10), (20, 5), (25, 10)]
    merged, merge_points = merge_tuples(tuple_list)
    print(merged)
    print(merge_points)

    complex_tuple_list = [
        (0, 10), (10, 5),   #(0, 15)
        (25, 5), (30, 10), (40, 20),   #(25, 35)
        (100, 50), 
        (200, 25), (225, 25), (250, 25),   #(200, 75)
        (400, 50), (450, 10), (460, 20),   #(400, 80)
        (500, 30), 
        (600, 15), (615, 10), (625, 15),   #(600, 40)
    ]
    merged, merge_points = merge_tuples(complex_tuple_list)
    print(merged)
    print(merge_points)