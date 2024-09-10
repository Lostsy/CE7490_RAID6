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
        parity_P = bytearray(self.block_size)
        parity_Q = bytearray(self.block_size)
        for idx, block in enumerate(data_blocks):
            parity_P = bytearray([self.galois_field.add(parity_P[i], block[i]) for i in range(self.block_size)])
            parity_Q = bytearray([self.galois_field.add(parity_Q[i], self.galois_field.multiply(self.galois_field.gfilog[idx], block[i])) for i in range(self.block_size)])

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
        stripe = self.table[stripe_idx]
        data_blocks = []
        parity_blocks = []
        for idx, block_type in enumerate(stripe):
            if block_type == 0:
                data_blocks.append(self.disks[idx].read(stripe_idx * self.block_size, self.block_size))
        for idx in self._parity_PQ_idxs[stripe_idx]:
            parity_blocks.append(self.disks[idx].read(stripe_idx * self.block_size, self.block_size))
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


# Example usage
if __name__ == "__main__":
    config = RAID6Config()
    print(config)
    raid6 = RAID6(config)
    raid6.display_table()

    fp = "../data/sample.png"
    # fp = "data/sample.jpg"
    raid6.save_data(fp)
    raid6.display_table()

    raid6.load_data("../data/sample_out.png", verify=True)
    # print(raid6._parity_PQ_idxs)
    # print(raid6._padding_sizes)
    # raid6.display_table()
    # breakpoint()