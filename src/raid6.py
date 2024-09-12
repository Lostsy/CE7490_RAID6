import numpy as np
from copy import deepcopy
from galois_field import GaloisField
from utils import Disk, RAID6Config
from sortedcontainers import SortedList
from enum import Enum

class WrongCode(Enum):
    FULL = 0
    DATA = 1
    PARITY_P = 2
    PARITY_Q = 3
    DATA_PARITY_P = 4
    DATA_PARITY_Q = 5
    PARITY_P_PARITY_Q = 6
    DAMAGE = 7


class RAID6(object):
    '''
    This is a class for RAID6.
    In this distributed system, the storage location of parity blocks are rotated among the disks to ensure stability and efficiency.
    Here is a visualization of the RAID6 system with 4 data disks and 2 parity disks:
    +--------+--------+--------+--------+--------+--------+
    | Disk 0 | Disk 1 | Disk 2 | Disk 3 | Disk 4 | Disk 5 |
    +--------+--------+--------+--------+--------+--------+
    | Data 0 | Data 1 | Data 2 | Data 3 | Parity | Parity |
    +--------+--------+--------+--------+--------+--------+
    | Parity | Data 4 | Data 5 | Data 6 | Data 7 | Parity |
    +--------+--------+--------+--------+--------+--------+
    | Parity | Parity | Data 8 | Data 9 | Data 10| Data 11|
    +--------+--------+--------+--------+--------+--------+
    ...

    '''
    def __init__(self, config: RAID6Config):
        self.data_disks = config.data_disks
        self.parity_disks = config.parity_disks
        self.stripe_width = config.stripe_width
        self.block_size = config.block_size
        self.stripe_num = config.disk_size // self.block_size
        self.stripe_size = self.block_size * self.data_disks
        self.galois_field = GaloisField()
        
        self.disks = [Disk(config.disk_size, id=_) for _ in range(self.stripe_width)]
        self.file2stripe = {} # use to track the file storage location
        self.stripe2file = [{0: [None, self.stripe_size]} for _ in range(self.stripe_num)] # use to track the stripe and the file
        self.stripe_status = SortedList() # use to track the stripe status
        self.left_size = self.stripe_num * self.stripe_size # use to track the left size of the total raid6 system

        # Init idle stripe status
        for i in range(self.stripe_num):
            self.stripe_status.add((self.stripe_size, i)) # ordered list
    
    def _find_parity_PQ_idx(self, stripe_idx: int):
        '''
        Find the parity disk index for P and Q.
        '''
        base = self.data_disks + stripe_idx
        return (base % self.stripe_width, (base + 1) % self.stripe_width)
    
    def _cal_disk_and_offset(self, stripe_idx: int, offset: int):
        '''
        Calculate the disk idx and the offset in the disk.
        '''
        if offset > self.stripe_size:
            raise ValueError("Invalid offset")
        disk_idx = offset // self.block_size
        pq_index = self._find_parity_PQ_idx(stripe_idx)
        data_index = [i for i in range(self.stripe_width) if i not in pq_index]
        return data_index[disk_idx], offset % self.block_size + stripe_idx * self.block_size

    def _handle_fragment(self, size: int):
        '''
        [TODO]
        Handle the fragment circumstance.
        '''
        raise NotImplementedError("Not implemented yet")
        return {} # return stripe the data spilition mapping
    
    def _merge_fragment(self, stripe_idx: int):
        '''
        [TODO]
        Merge the continuous idle fragments.
        '''
        raise NotImplementedError("Not implemented yet")
    
    def _distribute_stripe(self, stripe_idx: int, stripe_data: bytearray, file_name: str):
        '''
        Distribute a stripe of data to the RAID6 system.
        '''
        # Assume the stripe data is less than the left capacity
        print(f'data size {len(stripe_data)}')

        # Find the offset to write the stripe data
        left_size = len(stripe_data)
        offset_list = []
        for offset, info in self.stripe2file[stripe_idx].items():
            if info[0] is None:
                self.stripe2file[stripe_idx][offset][0] = file_name
                if info[1] > left_size:
                    offset_list.append((offset, left_size))
                    # update the stripe2file, split the fragment
                    self.stripe2file[stripe_idx][offset][1] = left_size
                    self.stripe2file[stripe_idx][offset + left_size] = [None, info[1] - left_size]
                    left_size = 0
                    break
                elif info[1] < left_size:
                    offset_list.append((offset, info[1]))
                    left_size -= info[1]
                else:
                    offset_list.append((offset, left_size))
                    left_size = 0
                    break
        assert left_size == 0, "Something wrong with the distributed stripe data"

        # Write the stripe data to the disks
        p_idx, q_idx = self._find_parity_PQ_idx(stripe_idx)
        data_disk_idxs = [i for i in range(self.stripe_width) if i not in [p_idx, q_idx]]
        write_offset = 0
        for offset, size in offset_list:
            start_disk_idx, start_disk_offset = self._cal_disk_and_offset(stripe_idx, offset)
            end_disk_idx, end_disk_offset = self._cal_disk_and_offset(stripe_idx, offset + size - 1)

            # Write the data to the disks
            for disk_idx in range(start_disk_idx, end_disk_idx + 1):
                if disk_idx == p_idx or disk_idx == q_idx:
                    continue
                # Find start offset
                if disk_idx == start_disk_idx:
                    disk_offset = start_disk_offset
                else:
                    disk_offset = stripe_idx * self.block_size

                # Find write size
                if disk_idx == end_disk_idx:
                    write_size = end_disk_offset - disk_offset + 1
                else:
                    write_size = self.block_size * (stripe_idx + 1) - disk_offset

                # Write the data
                self.disks[disk_idx].write(disk_offset, stripe_data[write_offset : write_offset + write_size])
                write_offset += write_size
        assert write_offset == len(stripe_data), "Something wrong with writing the distributed stripe data"
        
        # Update the parity blocks
        p = bytearray(self.block_size)
        q = bytearray(self.block_size)
        for idx, disk_idx in enumerate(data_disk_idxs):
            if len(stripe_data) != self.stripe_size:
                data = self.disks[disk_idx].read(stripe_idx * self.block_size, self.block_size)
            else:
                data = stripe_data[idx * self.block_size : (idx + 1) * self.block_size]
            p = bytearray([self.galois_field.add(p[i], data[i]) for i in range(self.block_size)])
            q = bytearray([self.galois_field.add(q[i], self.galois_field.multiply(self.galois_field.gfilog[idx], data[i])) for i in range(self.block_size)])

        # Write back the parity blocks
        self.disks[p_idx].write(stripe_idx * self.block_size, p)
        self.disks[q_idx].write(stripe_idx * self.block_size, q)
        
        return offset_list

    def _distribute_data(self, data: bytearray, file_name: str):
        '''
        Distribute data to the RAID6 system.
        '''
        data_size = len(data)
        if data_size > self.left_size:
            raise ValueError("Not enough space in the RAID6 system")

        # Calculate the inital data size allocation for each stripe
        full_stripe_count = data_size // self.stripe_size
        stripe_data_size = [self.stripe_size] * full_stripe_count
        if data_size % self.stripe_size > 0:
            stripe_data_size.append(data_size % self.stripe_size)

        # Find the stripes for the data
        stripe2data = {}
        for idx, size in enumerate(stripe_data_size):
            # Handle the fragment circumstance
            if size > self.stripe_status[-1][0]:
                stripe2data.update(self._handle_fragment(data_size - idx * self.stripe_size))
                break
            
            # Handle the normal circumstance
            if size == self.stripe_size:
                stripe2data[self.stripe_status.pop()[1]] = data[idx * self.stripe_size : (idx + 1) * self.stripe_size] # pop the last stripe
            else:
                for idx, stripe in enumerate(self.stripe_status):
                    if size <= stripe[0]:
                        stripe2data[stripe[1]] = data[idx * self.stripe_size : idx * self.stripe_size + size]
                        break
                # Update the stripe status
                stripe = self.stripe_status.pop(idx)
                if stripe[0] > size:
                    self.stripe_status.add((stripe[0] - size, stripe[1]))
        
        # Distribute the data to the stripes
        for stripe_idx, stripe_data in stripe2data.items():
            print(f'Distribute stripe {stripe_idx}')
            stripe2data[stripe_idx] = self._distribute_stripe(stripe_idx, stripe_data, file_name)
        
        self.left_size -= data_size
        return stripe2data

    def save_data(self, data_path: str, name: str = None):
        '''
        Save Data to the RAID6 system.
        '''
        with open(data_path, "rb") as f:
            data = f.read()
        
        self.file2stripe[name] = self._distribute_data(data, name)
        print(f"Data saved to RAID6 system successfully")
    
    def verify_stripe(self, stripe_idx: int, p_idx: int, q_idx: int, data_disk_idxs: list):
        '''
        Verify the integrity of a stripe in the RAID6 system.
        '''
        p = self.disks[p_idx].read(stripe_idx * self.block_size, self.block_size)
        q = self.disks[q_idx].read(stripe_idx * self.block_size, self.block_size)

        recompute_p = bytearray(self.block_size)
        recompute_q = bytearray(self.block_size)
        for idx, disk_dix in enumerate(data_disk_idxs):
            data = self.disks[disk_dix].read(stripe_idx * self.block_size, self.block_size)
            recompute_p = bytearray([self.galois_field.add(recompute_p[i], data[i]) for i in range(self.block_size)])
            recompute_q = bytearray([self.galois_field.add(recompute_q[i], self.galois_field.multiply(self.galois_field.gfilog[idx], data[i])) for i in range(self.block_size)])
        
        if recompute_p == p and recompute_q == q:
            return WrongCode.FULL
        else:
            return WrongCode.DAMAGE
    
    def rebuild_stripe(self, stripe_idx: int, wrong_code: int):
        '''
        Rebuild a stripe in the RAID6 system.
        '''
        raise NotImplementedError("Not implemented yet")
        return True

    def load_data(self, name: str, out_path: str, verify=False):
        '''
        Load data from the RAID6 system.
        In a RAID6 system, the data is distributed across multiple disks.
        In order to load the data, we need to read the data from the disks and reconstruct the original data.
        '''
        stripe2data = self.file2stripe[name]
        
        data = bytearray()
        for stripe_idx, offset_list in stripe2data.items():
            p_idx, q_idx = self._find_parity_PQ_idx(stripe_idx)
            data_disk_idxs = [i for i in range(self.stripe_width) if i not in [p_idx, q_idx]]

            if verify:
                stripe_status = self.verify_stripe(stripe_idx, p_idx, q_idx, data_disk_idxs)
                if stripe_status == WrongCode.FULL:
                    print(f"Stripe {stripe_idx} is verified.")
                elif stripe_status == WrongCode.DAMAGE:
                    raise ValueError(f"Stripe {stripe_idx} is corrupted.")
                else:
                    self.rebuild_stripe(stripe_idx, stripe_status)

            for offset, size in offset_list:
                print(f'Load stripe {stripe_idx} offset {offset} size {size}')
                start_disk_idx, start_disk_offset = self._cal_disk_and_offset(stripe_idx, offset)
                end_disk_idx, end_disk_offset = self._cal_disk_and_offset(stripe_idx, offset + size - 1)

                # Read the data from the disks
                for disk_idx in range(start_disk_idx, end_disk_idx + 1):
                    if disk_idx == p_idx or disk_idx == q_idx:
                        continue

                    # Find start offset
                    if disk_idx == start_disk_idx:
                        disk_offset = start_disk_offset
                    else:
                        disk_offset = stripe_idx * self.block_size

                    # Find read size
                    if disk_idx == end_disk_idx:
                        read_size = end_disk_offset - disk_offset + 1
                    else:
                        read_size = self.block_size * (stripe_idx + 1) - disk_offset

                    data += self.disks[disk_idx].read(disk_offset, read_size)

        with open(out_path, "wb") as f:
            f.write(data)


# Example usage
if __name__ == "__main__":
    # Initialize the RAID6 system
    config = RAID6Config()
    print(config)
    raid6 = RAID6(config)

    # Save data to the RAID6 system
    fp = "../data/sample.png"
    raid6.save_data(fp, name="sample.png")

    raid6.load_data("sample.png", "../data/sample_out.png", verify=True)