#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    : test_deletion.py
@Time    : 2024/09/19
@Version : 0.1
@License : TOADD
@Desc    : Unit tests for the deletion of data from the raid6 database
'''

import src
import pytest
from test_save_load import build_raid6, calculate_md5

def test_delete_single_file():
    '''
    Test the deletion of a single file from the RAID6 system
    '''
    raid6 = build_raid6()
    img_path = "data/sample.png"
    output_path = "data/cockatoo.png"
    raid6.save_data(img_path, name="cockatoo")
    raid6.check_disks_status()
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    raid6.delete_data("cockatoo")

    # check if the file is deleted
    print(f"After Delete================================")
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

def test_delete_multiple_files():
    '''
    Test the deletion of multiple files from the RAID6 system
    '''
    raid6 = build_raid6()
    img_paths = ["data/sample.jpg", "data/sample.png"]
    # output = ["data/cockatoo.jpg", "data/cockatoo.png"]
    names = ["cockatoo.jpg", "cockatoo.png"]
    for img_path, name in zip(img_paths, names):
        raid6.save_data(img_path, name=name)
    raid6.check_disks_status()
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    # for name in names:
    #     raid6.delete_data(name)
    raid6.delete_data("cockatoo.jpg")
    
    # check if the files are deleted
    print(f"After Delete================================")
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    raid6.delete_data("cockatoo.png")
    
    # check if the files are deleted
    print(f"After Delete================================")
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)


def test_delete_withadd_multiple_files():
    '''
    Test the deletion of multiple files from the RAID6 system
    '''
    raid6 = build_raid6()
    img_paths = ["data/sample.jpg", "data/sample.png"]
    # output = ["data/cockatoo.jpg", "data/cockatoo.png"]
    names = ["cockatoo.jpg", "cockatoo.png"]
    for img_path, name in zip(img_paths, names):
        raid6.save_data(img_path, name=name)
    raid6.check_disks_status()
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    # for name in names:
    #     raid6.delete_data(name)
    raid6.delete_data("cockatoo.jpg")
    
    # check if the files are deleted
    print(f"After Delete================================")
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    raid6.save_data(img_paths[1], name="cockatoo2.png")
    print(f"After Save================================")
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)

    raid6.save_data(img_paths[0], name="cockatoo.jpg")
    print(f"After Save================================")
    print(raid6.stripe2file)
    print(raid6.file2stripe)
    print(raid6.stripe_status)


if __name__=="__main__":
    import src

