import os
from dataclasses import dataclass, field

# Define a class to simulate each disk in the RAID6 system
class Disk:
    def __init__(self, path: str, size: int, id: int):
        self.size = size
        self.status = True # True: normal, False: damaged

        # create a file to simulate the disk
        self.path = os.path.join(path, f"disk{id}")

        try:
            with open(self.path, "rb") as f:
                f.seek(0, 2)
                if f.tell() != size:
                    raise ValueError("Disk size mismatch")
        except:
            self.init_new_disk(self.path)
            
        print(f"Disk {id} is loaded with size {size} bytes")
    
    def read(self, offset: int, size: int):
        if offset + size > self.size:
            raise ValueError("Read out of bound")
        
        try:
            with open(self.path, "rb") as f:
                f.seek(offset)
                return f.read(size)
        except:
            self.status = False

    def write(self, offset: int, data: bytearray):
        if offset + len(data) > self.size:
            raise ValueError("Write out of bound")

        try:
            with open(self.path, "r+b") as f:
                f.seek(offset)
                f.write(data)
        except:
            self.status = False

    def check(self):
        try:
            with open(self.path, "rb") as f:
                f.seek(0, 2)
                if f.tell() != self.size:
                    self.status = False
        except:
            self.status = False
        return self.status

    def init_new_disk(self, path: str):
        self.path = path
        self.status = True
        with open(path, "wb") as f:
            f.write(b"\x00" * self.size)

@dataclass
class RAID6Config:
    '''
    Configuration class for RAID6 system.
    '''
    data_path: str = field(default="./disk/data", metadata={"description": "Path to store data"})
    data_disks: int = field(default=4, metadata={"description": "Number of data disks"})
    parity_disks: int = field(default=2, metadata={"description": "Number of parity disks"})
    # stripe_width: int = field(default=6, metadata={"description": "Number of disks in a stripe"})
    block_size: int = field(default=1024 * 1024, metadata={"description": "Block size in bytes"})
    disk_size: int = field(default=1024*1024*1024, metadata={"description": "Disk size in bytes"})
    
    def __post_init__(self):
        assert self.parity_disks == 2, "RAID6 does not support 2 parity disks"
        # assert self.stripe_width == self.data_disks + self.parity_disks, "Invalid RAID6 configuration"
        assert self.disk_size % self.block_size == 0, "Disk size should be multiple of block size"


def merge_tuples(tuple_list):
    if len(tuple_list) <= 1:
        return tuple_list, []
    
    merged_list = []
    merge_point = []
    current_start, current_size = tuple_list[0]
    for i in range(1, len(tuple_list)):
        next_start, next_size = tuple_list[i]
        
        if current_start + current_size == next_start:
            current_size += next_size
            merge_point.append(next_start)
        else:
            merged_list.append((current_start, current_size))
            current_start, current_size = next_start, next_size
    
    merged_list.append((current_start, current_size))
    
    return merged_list, merge_point