import os
import numpy as np
from copy import deepcopy
import logging
# from clib.galois_field import cal_parity_8, cal_parity_p, cal_parity_q_8, cal_parity_q, q_recover_data, recover_data_data
from src.clib.galois_field import cal_parity_8, cal_parity_p, cal_parity_q_8, cal_parity_q, q_recover_data, recover_data_data
from src.utils import Disk, RAID6Config
from sortedcontainers import SortedList
from enum import Enum
import time

# only use to check parity
# cannot detect disk failure
class ParityCode(Enum):
    ACCURATE = 0
    WRONG = 1

# related to the disk failure
class FailCode(Enum):
    DATA = 0
    Parity_P = 1
    Parity_Q = 2
    Data_P = 3
    Data_Q = 4
    DATA_DATA = 5
    PARITY_PARITY = 6
    CORUCPTED = 7
    GOOD = 8


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
        # Initialize the RAID6 system configuration
        self.data_path = config.data_path
        self.data_disks = config.data_disks
        self.parity_disks = config.parity_disks
        # self.stripe_width = config.stripe_width
        self.stripe_width = self.data_disks + self.parity_disks
        self.block_size = config.block_size
        self.stripe_num = config.disk_size // self.block_size
        self.stripe_size = self.block_size * self.data_disks
        
        # Create folders for data and parity disks
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path, exist_ok=True)
        
        self.disks = [Disk(config.data_path, config.disk_size, id=_) for _ in range(self.stripe_width)]
        self.file2stripe = {} # use to track the file storage location
        self.stripe2file = [{0: [None, self.stripe_size]} for _ in range(self.stripe_num)] # use to track the stripe and the file
        self.stripe_status = SortedList() # use to track the stripe status
        self.left_size = self.stripe_num * self.stripe_size # use to track the left size of the total raid6 system
        self.status = [[True for _ in range(self.stripe_width)] for _ in range(self.stripe_num)] # use to track the disk status

        # Init idle stripe status
        for i in range(self.stripe_num):
            self.stripe_status.add((self.stripe_size, i)) # ordered list

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(os.path.join(self.data_path, "Raid6.log"))
        file_handler.setFormatter(logging.Formatter('%(asctime)s - Func: %(name)s.%(funcName)s - [%(levelname)s] - %(message)s'))
        self.logger.addHandler(file_handler)
        self.logger.info(f"RAID6 system initialized with {self.data_disks} data disks and {self.parity_disks} parity disks")

    def _find_parity_PQ_idx(self, stripe_idx: int):
        '''
        Find the parity disk index for P and Q.
        '''
        base = self.data_disks + stripe_idx
        p_idx = base % self.stripe_width
        q_idx = (base + 1) % self.stripe_width
        data_idxs = [i for i in range(self.stripe_width) if i not in [p_idx, q_idx]]
        return (p_idx, q_idx), data_idxs
    
    def _cal_disk_and_offset(self, stripe_idx: int, offset: int):
        '''
        Calculate the disk idx and the offset in the disk.
        '''
        if offset > self.stripe_size:
            raise ValueError("Invalid offset")
        disk_idx = offset // self.block_size
        pq_index, data_index = self._find_parity_PQ_idx(stripe_idx)
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
    
    def _process_offset_list(self, stripe_idx: int, offset_list: list, mode: str, stripe_data: bytearray, idxs: list=None):
        '''
        Handle the offset list for a stripe.
        '''
        if idxs is None:
            (p_idx, q_idx), data_disk_idxs = self._find_parity_PQ_idx(stripe_idx)
        else:
            p_idx, q_idx, data_disk_idxs = idxs
        
        stripe_data_offset = 0
        for offset, size in offset_list:
            start_disk_idx, start_disk_offset = self._cal_disk_and_offset(stripe_idx, offset)
            end_disk_idx, end_disk_offset = self._cal_disk_and_offset(stripe_idx, offset + size - 1)

            # process the data
            for disk_idx in range(start_disk_idx, end_disk_idx + 1):
                if disk_idx == p_idx or disk_idx == q_idx:
                    continue
                # Find start offset
                disk_offset = start_disk_offset if disk_idx == start_disk_idx else stripe_idx * self.block_size
                # Find process size
                process_size = end_disk_offset - disk_offset + 1 if disk_idx == end_disk_idx else self.block_size * (stripe_idx + 1) - disk_offset

                # Process the data
                if mode == "read":
                    stripe_data[stripe_data_offset : stripe_data_offset + process_size] = self.disks[disk_idx].read(disk_offset, process_size)
                else:
                    self.disks[disk_idx].write(disk_offset, stripe_data[stripe_data_offset : stripe_data_offset + process_size])
                stripe_data_offset += process_size
        assert stripe_data_offset == len(stripe_data), "Something wrong with the process offset list"
    
    def _distribute_stripe(self, stripe_idx: int, stripe_data: bytearray, file_name: str):
        '''
        Distribute a stripe of data to the RAID6 system.
        '''
        # Assume the stripe data is less than the left capacity
        self.logger.info(f'Distribute stripe {stripe_idx} with data size {len(stripe_data)}')

        # Find the offset to write the stripe data
        left_size = len(stripe_data)
        offset_list = []
        for offset, info in self.stripe2file[stripe_idx].items():
            if info[0] is None:
                self.stripe2file[stripe_idx][offset][0] = file_name
                if info[1] > left_size:
                    offset_list.append((offset, left_size))
                    # update the stripe2file, split the fragment
                    self.stripe2file[stripe_idx][offset + left_size] = [None, info[1] - deepcopy(left_size)]
                    self.stripe2file[stripe_idx][offset][1] = deepcopy(left_size)
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
        (p_idx, q_idx), data_disk_idxs = self._find_parity_PQ_idx(stripe_idx)
        self._process_offset_list(stripe_idx, offset_list, "write", stripe_data, idxs=[p_idx, q_idx, data_disk_idxs])

        # Update the parity blocks
        p = bytearray(self.block_size)
        q = bytearray(self.block_size)
        if len(stripe_data) != self.stripe_size:
            _, _, stripe_data, _ = self._load_stripes(stripe_idx, idxs=[p_idx, q_idx, data_disk_idxs])

        cal_parity_8(p, q, stripe_data)

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
                for idx_sorted, stripe in enumerate(self.stripe_status):
                    if size <= stripe[0]:
                        stripe2data[stripe[1]] = data[idx * self.stripe_size : idx * self.stripe_size + size]
                        break
                # Update the stripe status
                stripe = self.stripe_status.pop(idx_sorted)
                if stripe[0] > size:
                    self.stripe_status.add((stripe[0] - size, stripe[1]))
        
        # Distribute the data to the stripes
        for stripe_idx, stripe_data in stripe2data.items():
            # print(f'Distribute stripe {stripe_idx}')
            self.logger.info(f'Distribute stripe {stripe_idx}')
            stripe2data[stripe_idx] = self._distribute_stripe(stripe_idx, stripe_data, file_name)
        
        self.left_size -= data_size
        return stripe2data
    
    def _load_stripes(self, stripe_idx: int, idxs: list=None, read_p: bool=False, read_q: bool=False):
        '''
        Load the stripe data from the RAID6 system.
        '''
        # [TODO] use multi-thread to load the data
        if idxs is None:
            (p_idx, q_idx), data_disk_idxs = self._find_parity_PQ_idx(stripe_idx)
        else:
            p_idx, q_idx, data_disk_idxs = idxs

        new_data_idxs = []
        stripe_data = bytearray(0)
        p = None
        q = None

        for idx, disk_idx in enumerate(data_disk_idxs):
            if self.status[stripe_idx][disk_idx] == False:
                continue
            now_data = self.disks[disk_idx].read(stripe_idx * self.block_size, self.block_size)
            stripe_data += now_data
            new_data_idxs.append(idx)
        
        if read_p:
            p = self.disks[p_idx].read(stripe_idx * self.block_size, self.block_size)
        if read_q:
            q = self.disks[q_idx].read(stripe_idx * self.block_size, self.block_size)

        return p, q, stripe_data, new_data_idxs
    
    def _recover_stripe(self, stripe_idx: int, wrong_code: int, failed_idxs: list):
        '''
        Recover a stripe in the RAID6 system.
        '''
        if wrong_code == FailCode.GOOD:
            print(f"Stripe {stripe_idx} is good.")
            return True
        
        if wrong_code == FailCode.CORUCPTED:
            print(f"Stripe {stripe_idx} cannot be recovered.")
            return False

        if wrong_code == FailCode.DATA:
            print(f"Recover stripe {stripe_idx} with data {failed_idxs[0]}")
            p, _, stripe_data, _ = self._load_stripes(stripe_idx, read_p=True)
            inter_res = p + stripe_data
            new_data = bytearray(self.block_size)
            cal_parity_p(new_data, inter_res)
            self.disks[failed_idxs[0]].write(stripe_idx * self.block_size, new_data)
            return True
        
        if wrong_code == FailCode.Parity_P:
            print(f"Recover stripe {stripe_idx} with p parity {failed_idxs[0]}")
            _, _, stripe_data, _ = self._load_stripes(stripe_idx)
            new_p = bytearray(self.block_size)
            cal_parity_p(new_p, stripe_data)
            self.disks[failed_idxs[0]].write(stripe_idx * self.block_size, new_p)
            return True
        
        if wrong_code == FailCode.Parity_Q:
            print(f"Recover stripe {stripe_idx} with q parity {failed_idxs[0]}")
            _, _, stripe_data, _ = self._load_stripes(stripe_idx)
            new_q = bytearray(self.block_size)
            cal_parity_q_8(new_q, stripe_data)
            self.disks[failed_idxs[0]].write(stripe_idx * self.block_size, new_q)
            return True

        if wrong_code == FailCode.PARITY_PARITY:
            print(f"Recover stripe {stripe_idx} with p parity {failed_idxs[0]} and q parity {failed_idxs[1]}")
            _, _, stripe_data, _ = self._load_stripes(stripe_idx)
            new_p = bytearray(self.block_size)
            new_q = bytearray(self.block_size)
            cal_parity_8(new_p, new_q, stripe_data)
            self.disks[failed_idxs[0]].write(stripe_idx * self.block_size, new_p)
            self.disks[failed_idxs[1]].write(stripe_idx * self.block_size, new_q)
            return True
        
        if wrong_code == FailCode.Data_P:
            print(f"Recover stripe {stripe_idx} with data {failed_idxs[1]} and p parity {failed_idxs[0]}")
            _, q, stripe_data, new_data_idxs = self._load_stripes(stripe_idx, read_q=True)
            inter_res = bytearray(self.block_size)
            cal_parity_q(inter_res, stripe_data, new_data_idxs)
            idx = -1
            exist_idxs = set(new_data_idxs)
            for i in range(self.data_disks):
                if i not in exist_idxs:
                    idx = i
            new_data = bytearray(self.block_size)
            q_recover_data(new_data, q, inter_res, idx)
            self.disks[failed_idxs[1]].write(stripe_idx * self.block_size, new_data)

            new_p = bytearray(self.block_size)
            inter_res = stripe_data + new_data
            cal_parity_p(new_p, inter_res)
            self.disks[failed_idxs[0]].write(stripe_idx * self.block_size, new_p)
            return True
        
        if wrong_code == FailCode.Data_Q:
            print(f"Recover stripe {stripe_idx} with data {failed_idxs[1]} and q parity {failed_idxs[0]}")
            p, _, stripe_data, new_data_idxs = self._load_stripes(stripe_idx, read_p=True)
            inter_res = p + stripe_data
            new_data = bytearray(self.block_size)
            cal_parity_p(new_data, inter_res)
            self.disks[failed_idxs[1]].write(stripe_idx * self.block_size, new_data)

            exist_idxs = set(new_data_idxs)
            for idx in range(self.data_disks):
                if idx not in exist_idxs:
                    new_data_idxs.append(idx)
                    break
            inter_res = stripe_data + new_data
            new_q = bytearray(self.block_size)
            cal_parity_q(new_q, inter_res, new_data_idxs)
            self.disks[failed_idxs[0]].write(stripe_idx * self.block_size, new_q)
            return True

        if wrong_code == FailCode.DATA_DATA:
            print(f"Recover stripe {stripe_idx} with data {failed_idxs[0]} and {failed_idxs[1]}")
            p, q, stripe_data, new_data_idxs = self._load_stripes(stripe_idx, read_p=True, read_q=True)
            inter_p = bytearray(self.block_size)
            inter_q = bytearray(self.block_size)
            cal_parity_p(inter_p, stripe_data)
            cal_parity_q(inter_q, stripe_data, new_data_idxs)
            
            idxs = []
            exist_idxs = set(new_data_idxs)
            for idx in range(self.data_disks):
                if idx not in exist_idxs:
                    idxs.append(idx)
            new_data1 = bytearray(self.block_size)
            new_data2 = bytearray(self.block_size)
            recover_data_data(new_data1, new_data2, p, inter_p, q, inter_q, idxs[0], idxs[1])
            self.disks[failed_idxs[0]].write(stripe_idx * self.block_size, new_data1)
            self.disks[failed_idxs[1]].write(stripe_idx * self.block_size, new_data2)
            return True
    
    def _detect_stripe_failcode(self, stripe_idx: int):
        '''
        Now we only consider the whole disks.
        '''
        (p_idx, q_idx), data_disk_idxs = self._find_parity_PQ_idx(stripe_idx)

        failed_data = []
        p_status = 0
        q_status = 0

        for disk_idx in data_disk_idxs:
            if self.status[stripe_idx][disk_idx] == False:
                failed_data.append(disk_idx)
        if self.status[stripe_idx][p_idx] == False:
            p_status = 1
        if self.status[stripe_idx][q_idx] == False:
            q_status = 1
        
        # return the fail code & the failed idx
        if len(failed_data) + p_status + q_status >= 3:
            return FailCode.CORUCPTED, []
        elif len(failed_data) == 2:
            return FailCode.DATA_DATA, failed_data
        elif len(failed_data) == 1 and p_status == 1:
            return FailCode.Data_P, [p_idx, failed_data[0]]
        elif len(failed_data) == 1 and q_status == 1:
            return FailCode.Data_Q, [q_idx, failed_data[0]]
        elif len(failed_data) == 1:
            return FailCode.DATA, failed_data
        elif p_status == 1 and q_status == 1:
            return FailCode.PARITY_PARITY, [p_idx, q_idx]
        elif p_status == 1:
            return FailCode.Parity_P, [p_idx]
        elif q_status == 1:
            return FailCode.Parity_Q, [q_idx]
        else:
            return FailCode.GOOD, []

    def save_data(self, data_path: str, name: str = None):
        '''
        Save Data to the RAID6 system.
        '''
        with open(data_path, "rb") as f:
            data = f.read()
        
        self.file2stripe[name] = self._distribute_data(data, name)
        # print(f"Data saved to RAID6 system successfully")
        self.logger.info(f"Data saved to RAID6 system successfully")
    
    def verify_stripe(self, stripe_idx: int, idxs: list=None):
        '''
        Verify the integrity of a stripe in the RAID6 system.
        '''
        if idxs is None:
            (p_idx, q_idx), data_disk_idxs = self._find_parity_PQ_idx(stripe_idx)
        else:
            p_idx, q_idx, data_disk_idxs = idxs
        
        p, q, stripe_data, new_disk_idxs = self._load_stripes(stripe_idx, idxs=[p_idx, q_idx, data_disk_idxs], read_p=True, read_q=True)
        if len(new_disk_idxs) != len(data_disk_idxs):
            return ParityCode.WRONG

        recompute_p = bytearray(self.block_size)
        recompute_q = bytearray(self.block_size)
        cal_parity_8(recompute_p, recompute_q, stripe_data)
        
        if recompute_p == p and recompute_q == q:
            return ParityCode.ACCURATE
        else:
            return ParityCode.WRONG

    def load_data(self, name: str, out_path: str, verify=False):
        '''
        Load data from the RAID6 system.
        In a RAID6 system, the data is distributed across multiple disks.
        In order to load the data, we need to read the data from the disks and reconstruct the original data.
        '''
        stripe2data = self.file2stripe[name]
        
        data = bytearray(0)
        for stripe_idx, offset_list in stripe2data.items():
            (p_idx, q_idx), data_disk_idxs = self._find_parity_PQ_idx(stripe_idx)

            if verify:
                stripe_status = self.verify_stripe(stripe_idx, [p_idx, q_idx, data_disk_idxs])
                if stripe_status == ParityCode.ACCURATE:
                    # print(f"Stripe {stripe_idx} is verified.")
                    self.logger.info(f"Stripe {stripe_idx} is verified.")
                else:
                    self.logger.error(f"Stripe {stripe_idx} is corrupted.")
                    raise ValueError(f"Stripe {stripe_idx} is corrupted.")

            stripe_data_size = sum(size for _, size in offset_list)
            stripe_data = bytearray(stripe_data_size)
            self._process_offset_list(stripe_idx, offset_list, "read", stripe_data, idxs=[p_idx, q_idx, data_disk_idxs])
            data += stripe_data

        with open(out_path, "wb") as f:
            f.write(data)
            # print(f"Data loaded from RAID6 system successfully")
            self.logger.info(f"Data loaded from RAID6 system successfully")
    
    def check_disks_status(self):
        '''
        Check the status of the disks in the RAID6 system.
        '''
        for i in range(self.stripe_width):
            flag = self.disks[i].check()
            # print(f"Disk {i} status: {flag}")
            self.logger.info(f"Disk {i} status: {flag}")
            for j in range(self.stripe_num):
                self.status[j][i] = flag
            if flag == False:
                self.disks[i].init_new_disk(self.disks[i].path + "_new")
    
    def recover_disks(self):
        '''
        Recover the disks in the RAID6 system.
        '''
        for stripe_idx in range(self.stripe_num):
            if len(self.stripe2file[stripe_idx]) == 1 and self.stripe2file[stripe_idx][0][0] is None:
                for i in range(self.stripe_width):
                    self.status[stripe_idx][i] = True
                continue
            fail_code, failed_idxs = self._detect_stripe_failcode(stripe_idx)
            if fail_code == FailCode.GOOD:
                continue
            self._recover_stripe(stripe_idx, fail_code, failed_idxs)
            for i in failed_idxs:
                self.status[stripe_idx][i] = True
        # print(f"Disks recovered successfully")
        self.logger.info(f"Disks recovered successfully")

    def _update_parity_by_stripe_id(self, stripe_idx: int):
        '''
        Update the parity blocks by stripe id.
        '''
        (p_idx, q_idx), data_disk_idxs = self._find_parity_PQ_idx(stripe_idx)
        p = bytearray(self.block_size)
        q = bytearray(self.block_size)
        _, _, stripe_data, _ = self._load_stripes(stripe_idx, idxs=[p_idx, q_idx, data_disk_idxs])
        cal_parity_8(p, q, stripe_data)
        self.disks[p_idx].write(stripe_idx * self.block_size, p)
        self.disks[q_idx].write(stripe_idx * self.block_size, q)
        return True


    def delete_data(self, file_name: str):
        '''
        Delete data from the RAID6 system.
        '''
        if file_name not in self.file2stripe:
            # print(f"File {file_name} does not exist in the RAID6 system")
            self.logger.error(f"File {file_name} does not exist in the RAID6 system")
            return False
        
        stripe_info = self.file2stripe[file_name]
        for stripe_idx, offset_list in stripe_info.items():
            for offset, size in offset_list:
                # Mark the blocks as empty
                self.stripe2file[stripe_idx][offset] = [None, size]
                # Merge the free space
                # Merge the space ahead
                new_offset = offset
                new_size = size
                for inn_offset, inn_info in self.stripe2file[stripe_idx].items():
                    inn_name, inn_size = inn_info
                    if inn_name == None and inn_offset + inn_size == new_offset:
                        self.stripe2file[stripe_idx][inn_offset] = [None, inn_size + new_size]
                        self.stripe2file[stripe_idx].pop(offset)
                        new_offset = inn_offset
                        new_size += inn_size
                        break
                # Merge the space behind
                for inn_offset, inn_info in self.stripe2file[stripe_idx].items():
                    inn_name, inn_size = inn_info
                    if inn_name == None and offset + size == inn_offset:
                        self.stripe2file[stripe_idx][new_offset] = [None, new_size + inn_size]
                        self.stripe2file[stripe_idx].pop(inn_offset)
                        break
                
                # Update the stripe status (add the freed space back)
                for idx, stripe in enumerate(self.stripe_status):
                    if stripe[1] == stripe_idx:
                        # Merge the free space with the existing stripe
                        new_size = stripe[0] + size
                        self.stripe_status.remove(stripe)
                        self.stripe_status.add((new_size, stripe_idx))
                        break
                else:
                    # If the stripe was fully used, add it back as free space
                    self.stripe_status.add((size, stripe_idx))


            # Do not need to update the parity blocks, lazy update for deletion
            # self._update_parity_by_stripe_id(stripe_idx)


        del self.file2stripe[file_name]
        self.left_size += sum(id_size[0][1] for _, id_size in stripe_info.items())

        # print(f"Data {file_name} deleted from RAID6 system successfully")
        self.logger.info(f"Data {file_name} deleted from RAID6 system successfully")

    def modify_data(self, file_name: str, data_path: str):
        '''
        Modify the data in the RAID6 system.
        Apply in-place modification to the data in the RAID6 system.
        input:
            file_name: str, the name of the file to be modified
            data_path: str, the path of the new data
        '''
        if file_name not in self.file2stripe:
            print(f"File {file_name} does not exist in the RAID6 system")
            return False
        
        with open(data_path, "rb") as f:
            data = f.read()

        stripe_info = self.file2stripe[file_name]
        # Update based on the original data size and the new data size
        # if data_size >= len(data): 
        # write the data to the location of current data
        # The rest part will be set empty
        # if data_size < len(data):
        # write the data to the location of current data
        # the rest part will request for new space
        involved_stripe = set(stripe_info.keys())

        for stripe_idx, offset_list in stripe_info.items():
            for offset, size in offset_list:
                if len(data) <= size:
                    self._process_offset_list(stripe_idx, [(offset, len(data))], "write", data[:size])
                    # Set the rest part empty
                    self.stripe2file[stripe_idx][offset + len(data)] = [None, size - len(data)]
                    data = data[size:]
        # Request for new space
        if len(data) > 0:
            # include the involve stripe into the involved_stripe
            self._distribute_data(data, file_name)

        # Update the parity blocks
        for stripe_idx in involved_stripe:
            self._update_parity_by_stripe_id(stripe_idx)

        return True


# Example usage
if __name__ == "__main__":
    # Initialize the RAID6 system
    config = RAID6Config(data_disks=6)
    print(config)
    raid6 = RAID6(config)

    # # Save data to the RAID6 system
    # fp = "../data/sample.png"
    # raid6.save_data(fp, name="sample.png")
    
    # time.sleep(10)

    # # Check the status of the disks
    # raid6.check_disks_status()
    # raid6.recover_disks()

    # # Load data from the RAID6 system
    # raid6.load_data("sample.png", "../data/sample_out.png", verify=True)