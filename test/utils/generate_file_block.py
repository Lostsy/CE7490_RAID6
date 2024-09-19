#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    : generate_file_block.py
@Time    : 2024/09/19
@Version : 0.1
@License : TOADD
@Desc    : NONE
'''

import os
import random


# Generate a file of given size
def generate_file(file_path, size):
    with open(file_path, "wb") as f:
        f.write(os.urandom(size))

if __name__ == "__main__":
    tgt_dir = "data/sample_data_pieces"
    os.makedirs(tgt_dir, exist_ok=True)
    # Generate a file of 1MB
    file_path = os.path.join(tgt_dir, "sample_2E20")
    generate_file(file_path, 1*1024*1024)

    # Generate a file of 0.5MB
    file_path = os.path.join(tgt_dir, "sample_2E19")
    generate_file(file_path, 512*1024)

    # Generate a file of 0.25MB
    file_path =  os.path.join(tgt_dir, "sample_2E18")
    generate_file(file_path, 256*1024)

    # Generate a file of 0.125MB
    file_path = os.path.join(tgt_dir, "sample_2E17")
    generate_file(file_path, 128*1024)
