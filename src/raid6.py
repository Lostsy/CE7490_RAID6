import numpy as np
from copy import deepcopy
from galois_field import GaloisField
from utils import Disk, RAID6Config


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
        self.disk_size = config.disk_size
        self.stripe_size = self.block_size * self.data_disks
        
        self.disks = [Disk(self.disk_size, id=_) for _ in range(self.stripe_width)]
        self.table = None
        self._parity_PQ_idx = [self.data_disks, self.data_disks + 1]
        self._parity_PQ_idxs = []
        self._padding_sizes = []

        self.galois_field = GaloisField()

    def _update_table(self):
        '''
        Called when a stripe is written to the RAID6 system. The table is updated to record the block type.
        '''
        # Stripe and Parity are maintained in a table. Table is a 2D array for disk index and block index.
        # 0 for data, 1 for parity. For the first stripe, the parity is saved in the last two disks.
        if self.table is None:
            self.table = np.zeros((1, self.stripe_width), dtype=np.uint8)
            self.table[-1, self._parity_PQ_idx] = 1
        else:
            new_stripe = np.zeros((1, self.stripe_width), dtype=np.uint8)
            new_stripe[0, self._parity_PQ_idx] = 1
            self.table = np.vstack((self.table, new_stripe))

        self._parity_PQ_idxs.append(deepcopy(self._parity_PQ_idx))

        # Update the parity disk index
        for idx in range(self.parity_disks):
            _parity_idx = self._parity_PQ_idx[idx]
            self._parity_PQ_idx[idx] = _parity_idx + 1 if _parity_idx + 1 < self.stripe_width \
                else _parity_idx + 1 - self.stripe_width

    def _num_stripes(self):
        '''
        Get the number of stripes in the RAID6 system.
        '''
        if self.table is None:
            return 0
        return len(self.table)
    
    def compute_parity_P(self, data_blocks: list):
        '''
        Compute the parity P block from the data blocks.
        '''
        parity_P = bytearray(self.block_size)
        for block in data_blocks:
            parity_P = bytearray([self.galois_field.add(parity_P[i], block[i]) for i in range(self.block_size)])
            # parity_P = bytearray(self.galois_field.add(parity_P, block))
        return parity_P
    
    def compute_parity_Q(self, data_blocks: list):
        '''
        Compute the parity Q block from the data blocks.
        '''
        parity_Q = bytearray(self.block_size)
        for idx, block in enumerate(data_blocks):
            # parity_Q = bytearray(self.galois_field.add(parity_Q, self.galois_field.multiply(self.galois_field.gfilog[idx], block)))
            parity_Q = bytearray([self.galois_field.add(parity_Q[i], self.galois_field.multiply(self.galois_field.gfilog[idx], block[i])) for i in range(self.block_size)])
        return parity_Q
    
    def _distribute_stripe(self, stripe_data: bytearray):
        '''
        Distribute a stripe of data to the RAID6 system.
        '''
        pid, qid = self._parity_PQ_idx
        self._update_table()

        # Compute the padding size and zero pad the stripe data if it is not a full stripe
        padding_size = self.stripe_size - len(stripe_data)
        stripe_data += bytearray(self.stripe_size - len(stripe_data))
        self._padding_sizes.append(padding_size)
        
        # split the stripe data into data blocks
        data_blocks = [stripe_data[i : i+self.block_size] for i in range(0, len(stripe_data), self.block_size)]
        assert len(data_blocks[-1]) == self.block_size, "Invalid block size"

        # Calculate the parity blocks, initialize with zeros
        parity_P = self.compute_parity_P(data_blocks)
        parity_Q = self.compute_parity_Q(data_blocks)
        # parity_P = bytearray(self.block_size)
        # parity_Q = bytearray(self.block_size)
        # for idx, block in enumerate(data_blocks):
        #     parity_P = bytearray([self.galois_field.add(parity_P[i], block[i]) for i in range(self.block_size)])
        #     parity_Q = bytearray([self.galois_field.add(parity_Q[i], self.galois_field.multiply(self.galois_field.gfilog[idx], block[i])) for i in range(self.block_size)])

        # Write the data and parity blocks to the disks, in the last stripe
        self.disk_start = (self._num_stripes() - 1) * self.block_size
        for idx, block_type in enumerate(self.table[-1]):
            if block_type == 0:
                self.disks[idx].write(self.disk_start, data_blocks.pop(0))

        self.disks[pid].write(self.disk_start, parity_P)
        self.disks[qid].write(self.disk_start, parity_Q)

    def _distribute_data(self, data: bytearray):
        '''
        Distribute data to the RAID6 system.
        '''
        # [SYM][To do] how to handle the small data.
        # [SYM][To do] how to track different data and realize the data update.
        data_size = len(data)
        stripe_count = (data_size + self.stripe_size - 1) // self.stripe_size

        for i in range(stripe_count):
            start = i * self.stripe_size
            end = min((i + 1) * self.stripe_size, data_size)
            stripe_data = data[start:end]
            self._distribute_stripe(stripe_data)

    def display_table(self):
        '''
        Display the table of the RAID6 system.
        '''
        if self.table is None:
            print("Table is empty")
        else:
            # Print the table in the visualized format
            TABLE_BORDER_UNIT = "+" + "-" * 8
            table_border = TABLE_BORDER_UNIT * self.stripe_width + "+"
            print(table_border.replace("-", "="))
            print("|", end="")
            for idx in range(self.stripe_width):
                print(f" Disk {idx} |", end="")
            print()
            print(table_border.replace("-", "="))
            for row in self.table:
                print("|", end="")
                for col in row:
                    print(f" {'Data  ' if col == 0 else 'Parity'} |", end="")
                print()
                print(table_border)

    def save_data(self, data_path: str):
        '''
        Save Data to the RAID6 system.
        '''
        with open(data_path, "rb") as f:
            data = f.read()
        self._distribute_data(data)
        print(f"Data saved to RAID6 system successfully!")
    
    def verify_stripe(self, stripe_idx: int):
        '''
        Verify the integrity of a stripe in the RAID6 system.
        '''
        if stripe_idx >= self._num_stripes():
            raise ValueError("Invalid stripe index")
        data_blocks, _, parity_blocks = self.load_stripes(stripe_idx)
        parity_P, parity_Q = parity_blocks

        recompute_parity_P = bytearray(self.block_size)
        recompute_parity_Q = bytearray(self.block_size)
        for idx, block in enumerate(data_blocks):
            recompute_parity_P = bytearray([self.galois_field.add(recompute_parity_P[i], block[i]) for i in range(self.block_size)])
            recompute_parity_Q = bytearray([self.galois_field.add(recompute_parity_Q[i], self.galois_field.multiply(self.galois_field.gfilog[idx], block[i])) for i in range(self.block_size)])
        
        return recompute_parity_P == parity_P, recompute_parity_Q == parity_Q
        

    def load_data(self, out_path: str, verify=False):
        '''
        Load data from the RAID6 system.
        In a RAID6 system, the data is distributed across multiple disks.
        In order to load the data, we need to read the data from the disks and reconstruct the original data.
        '''
        data = bytearray()
        for i in range(self._num_stripes()):
            stripe = self.table[i]
            if verify:
                stripe_status = self.verify_stripe(i)
                if stripe_status[0] and stripe_status[1]:
                    print(f"Stripe {i} is verified.")
                else:
                    print(f"Stripe {i} is corrupted with status P:{stripe_status[0]}, Q:{stripe_status[1]}")
                    return False
            data_blocks = []
            for idx, block_type in enumerate(stripe):
                if block_type == 0:
                    data_blocks.append(self.disks[idx].read(i * self.block_size, self.block_size))
            # consider padding
            data += b"".join(data_blocks)[:self.stripe_size - self._padding_sizes[i]]
        with open(out_path, "wb") as f:
            f.write(data)
        return True
    
    def detect_failed_blocks(self, stripe_idx: int):
        '''
        Detect failed blocks in a stripe.
        '''
        # failed_disks = []
        # for idx, disk in enumerate(self.disks):
        #     if disk.failed:
        #         failed_disks.append(idx)
        # return failed_disks
        # Random generate 1 or 2 failed disks

        if np.random.rand() < 0.5:
            return [np.random.randint(0, self.stripe_width)]
        else:
            return np.random.choice(self.stripe_width, 2, replace=False)

    def _recover_stripe(self, stripe_idx: int):
        '''
        Recover a stripe in the RAID6 system when one or two disks are failed.
        '''
        failed = self.detect_failed_disks() # list of IDs of failed disks
        if len(failed) == 0:
            print("No disk is failed.")
            return
        if len(failed) == 1:
            self.recover_one(stripe_idx, failed)
        if len(failed) == 2:
            self.recover_two(stripe_idx, failed)
        else:
            raise ValueError("More than two disks are failed.")

    def _recover_one_stripe(self, stripe_idx: int, failed: list):
        '''
        Recover the RAID6 system when one disk is failed.
        There are two cases:
        1. The failed disk is a parity disk.
        2. The failed disk is a data disk. Use the P recovery method to recover the data.
        '''
        assert len(failed) == 1, "Invalid failed disk list"
        stripe_attr = self.table[stripe_idx]
        data_blocks, _,  parity_blocks = self.load_stripes(stripe_idx)
        parity_P, parity_Q = parity_blocks

        if stripe_attr[failed[0]] == 1:
            print(f"Parity disk {failed[0]} is failed.")
            # Recompute the parity blocks
            if failed[0] == self._parity_PQ_idx[0]:
                # Recompute parity P
                parity_P = bytearray(self.block_size)
                for idx, block in enumerate(data_blocks):
                    parity_P = bytearray([self.galois_field.add(parity_P[i], block[i]) for i in range(self.block_size)])
                self.disk_start = stripe_idx * self.block_size
                self.disks[failed[0]].write(self.disk_start, parity_P)
            else:
                # Recompute parity Q
                parity_Q = bytearray(self.block_size)
                for idx, block in enumerate(data_blocks):
                    parity_Q = bytearray([self.galois_field.add(parity_Q[i], self.galois_field.multiply(self.galois_field.gfilog[idx], block[i])) for i in range(self.block_size)])
                self.disk_start = stripe_idx * self.block_size
                self.disks[failed[0]].write(self.disk_start, parity_Q)

            print(f"Parity disk {failed[0]} is recovered successfully.") # Replace it with logger output
        else:
            print(f"Data disk {failed[0]} is failed.")
            # Recover the data
            recovered_data = bytearray()
            for idx, block in enumerate(data_blocks):
                if idx == failed[0]:
                    continue
                recovered_data = bytearray([self.galois_field.add(recovered_data[i], block[i]) for i in range(self.block_size)])
            recovered_data = bytearray([self.galois_field.add(recovered_data[i], parity_P[i]) for i in range(self.block_size)])

            # Write the recovered data to the disk
            self.disk_start = stripe_idx * self.block_size
            self.disks[failed[0]].write(self.disk_start, recovered_data)
            print(f"Data disk {failed[0]} is recovered successfully.")
        return
    
    def _recover_two_stripe(self, stripe_idx: int, failed: list):
        '''
        There are three cases.
        1. Two parity disks are failed.
        2. One parity disk and one data disk are failed.
            - P parity disk is failed
            - Q parity disk is failed
        3. Two data disks are failed
        '''
        assert len(failed) == 2, "Invalid failed disk list"
        stripe_attr = self.table[stripe_idx]
        data_blocks, data_blocks_idxs, parity_blocks = self.load_stripes(stripe_idx)
        parity_P, parity_Q = parity_blocks

        disk_start = stripe_idx * self.block_size

        if stripe_attr[failed[0]] + stripe_attr[failed[1]] == 2:
            print(f"Two parity disks {failed[0]} and {failed[1]} are failed.")
            # Recompute the parity blocks from the data blocks
            parity_P = self.compute_parity_P(data_blocks)
            parity_Q = self.compute_parity_Q(data_blocks)
            # Write the recovered parity blocks to the disks
            p_idx, q_idx = self._parity_PQ_idxs[stripe_idx]
            self.disks[p_idx].write(disk_start, parity_P)
            self.disks[q_idx].write(disk_start, parity_Q)
            print(f"Two parity disks {failed[0]} and {failed[1]} are recovered successfully.")

        elif stripe_attr[failed[0]] + stripe_attr[failed[1]] == 1:
            p_idx, q_idx = self._parity_PQ_idxs[stripe_idx]
            failed_data_idx = failed[0] if stripe_attr[failed[0]] == 0 else failed[1]
            failed_parity_idx = failed[0] if stripe_attr[failed[0]] == 1 else failed[1]
            # P and a data disk are failed
            if p_idx in failed:
                # Recover the data block using the Q parity block
                recovered_data = bytearray(parity_Q)
                for idx, block in enumerate(data_blocks):
                    if data_blocks_idxs[idx] == failed_data_idx:
                        remark_id = idx
                        continue
                    recovered_data = bytearray([self.galois_field.add(recovered_data[i], self.galois_field.multiply(self.galois_field.gfilog[idx], block[i])) for i in range(self.block_size)])
                
                div_result = self.galois_field.divide(1, self.galois_field.gfilog[remark_id])
                recovered_data = bytearray([self.galois_field.multiply(div_result, recovered_data[i]) for i in range(self.block_size)])

                data_blocks[failed_data_idx] = recovered_data
                # save the recovered data block to the disk
                self.disks[failed_data_idx].write(disk_start, recovered_data)

                # Recompute the parity P block
                parity_P = self.compute_parity_P(data_blocks)
                # Write the recovered parity P block to the disk
                self.disks[failed_parity_idx].write(disk_start, parity_P)

            # Q and a data disk are failed
            elif q_idx in failed:
                # Galois Field add the rest data blocks and the P parity block to recover the broken data block
                recovered_data = bytearray()
                for idx, block in enumerate(data_blocks):
                    if idx == failed_data_idx:
                        continue
                    recovered_data = bytearray([self.galois_field.add(recovered_data[i], block[i]) for i in range(self.block_size)])
                recovered_data = bytearray([self.galois_field.add(recovered_data[i], parity_P[i]) for i in range(self.block_size)])
                data_blocks[failed_data_idx] = recovered_data

                # Write the recovered data block to the disk
                self.disks[failed_data_idx].write(disk_start, recovered_data)

                # Recover the parity Q block
                parity_Q = self.compute_parity_Q(data_blocks)
                # Write the recovered parity Q block to the disk
                self.disks[q_idx].write(disk_start, parity_Q)
    
            print(f"Q Parity disk {failed_parity_idx} and data disk {failed_data_idx} are recovered successfully.")
        else:
            # Two data disks are failed
            print(f"Two data disks {failed[0]} and {failed[1]} are failed.")
            # Recover the data blocks using the parity blocks
            parity_P, parity_Q = parity_blocks
            # copy parity P as xor_sum and compute Pxy
            xor_sum = bytearray(parity_P)
            for idx, block in enumerate(data_blocks):
                if data_blocks_idxs[idx] == failed[0] or data_blocks_idxs[idx] == failed[1]:
                    continue
                xor_sum = bytearray([self.galois_field.add(xor_sum[i], block[i]) for i in range(self.block_size)])
            # copy parity Q as gf_sum and compute Qxy
            gf_sum = bytearray(parity_Q)
            for idx, block in enumerate(data_blocks):
                if data_blocks_idxs[idx] == failed[0] or data_blocks_idxs[idx] == failed[1]:
                    continue
                gf_sum = bytearray([self.galois_field.add(gf_sum[i], self.galois_field.multiply(self.galois_field.gfilog[idx], block[i])) for i in range(self.block_size)])
            # Recover the data blocks
            # [SY] [TODO] complete the rest of the code
        pass

    def load_stripes(self, stripe_idx: int):
        '''
        Load the stripe data from the RAID6 system.
        input
        - stripe_idx: int, the index of the stripe to be loaded
        output
        - data_blocks: list of bytearrays, the data blocks in the stripe. Zero bytearrays are filled for parity blocks.
        - parity_blocks: list of bytearrays, the parity blocks in the stripe
        '''
        stripe = self.table[stripe_idx]
        data_blocks = []
        data_blocks_idx = []
        for idx, block_type in enumerate(stripe):
            if block_type == 0:
                data_blocks.append(self.disks[idx].read(stripe_idx * self.block_size, self.block_size))
                data_blocks_idx.append(idx)

        parity_blocks = []
        for idx in self._parity_PQ_idxs[stripe_idx]:
            parity_blocks.append(self.disks[idx].read(stripe_idx * self.block_size, self.block_size))
        return data_blocks, data_blocks_idx, parity_blocks

    def dataidx2stripeidx(self, stripe_idx: int, data_idx: int):
        '''
        Map the index in stripe to the data list index. For Error correction.
        e.g.
        data_indexs: 0 1 2 3
        stripe: 0 1 2(P) 3(Q) 4 5
        stripe_attr: 0 0 1 1 0 0
        if idx is 2, the mapping is 4 
        '''
        stripe_attr = self.table[stripe_idx]
        data_idx_list = []
        for idx, block_type in enumerate(stripe_attr):
            if block_type == 0:
                data_idx_list.append(idx)
        return data_idx_list[data_idx]
        

# Example usage
if __name__ == "__main__":
    # pass


    config = RAID6Config()
    config.block_size = 1024 * 256
    print(config)
    raid6 = RAID6(config)
    raid6.display_table()

    # fp = "../data/sample.png"
    fp = "data/sample.jpg"
    raid6.save_data(fp)
    raid6.display_table()

    raid6.load_data("data/sample_out.png", verify=True)
    print(raid6._parity_PQ_idxs)
    print(raid6._padding_sizes)
    raid6.display_table()
    # breakpoint()