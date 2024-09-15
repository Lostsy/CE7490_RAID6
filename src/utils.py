from dataclasses import dataclass, field
from sortedcontainers import SortedList

# Define a class to simulate each disk in the RAID6 system
class Disk:
    def __init__(self, size: int, id: int):
        self.size = size
        self.status = True # True: normal, False: damaged

        # create a file to simulate the disk
        self.path = "../disk/disk_" + str(id)
        with open(self.path, "wb") as f:
            f.write(b"\x00" * size)
            print(f"Disk {id} size: {size}, path: {self.path}")
    
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


class DiskManager:
    def __init__(self, block_size, num_disks, num_stripes):
        self.num_stripes = num_stripes
        self.block_size = block_size
        self.num_disks = num_disks
        self.num_data_disks = num_disks - 2
        self.stripe_size = self.num_data_disks * self.block_size # For data disks only
        # available_stripes: [(remaining_size, stripe_id)]
        self.available_stripes = SortedList(
            [(self.stripe_size, i) for i in range(num_stripes)],
            key=lambda x: x[0]
        )
        self.stripe_usage = []
        self.file_tracking = {}

    def allocate(self, file_name, file_size):
        '''
        Given filename and file size, allocate space for the file.

        Logic:
        - For each file, allocate as less stripes as possible.
        - For files smaller than stripe size, try to use the remaining space to reduce fragmentation.
        '''
        # num_full_stripes, leftover_size = divmod(file_size, self.stripe_size)
        allocations = []
        remaining_size = file_size

        # find full stripes
        while remaining_size > 0:
            stripe_remaining, stripe_id = self._find_stripe(remaining_size) # remaining, stripe_id
            usage = min(remaining_size, stripe_remaining)
            allocations.append((stripe_id, usage))
            self._track_file(file_name, stripe_id, usage)
            self._update_stripe(stripe_id, stripe_remaining, usage)
            remaining_size -= self.stripe_size

        return allocations

    def _find_stripe(self, size_needed):
        '''
        Find a stripe of required size.
        If no stripe is available, return the stripe with maximum size.
        '''
        required_size = min(size_needed, self.stripe_size)
        for remaining, stripe_id in self.available_stripes:
            if remaining >= required_size:
                return remaining, stripe_id
        else:
            return self.available_stripes[-1]

    def _update_stripe(self, stripe_id, remaining, used_size):
        # [Yang]: TODO, is there any efficient way to search and update the stripe based on stripe_id?
        for i, (remaining, s_id) in enumerate(self.available_stripes):
            if s_id == stripe_id:
                self.available_stripes.remove((remaining, s_id))
                self.available_stripes.add((remaining - used_size, s_id))
                break

    def find_size_by_id(self, stripe_id):
        for size, item_id in self.available_stripes:
            if item_id == stripe_id:
                return [size, item_id]
        return None

    def _track_file(self, file_name, stripe_id, size):
        if file_name not in self.file_tracking:
            self.file_tracking[file_name] = {}
        if stripe_id not in self.file_tracking[file_name]:
            self.file_tracking[file_name][stripe_id] = []
        
        offset = self._get_stripe_offset(stripe_id)
        self.file_tracking[file_name][stripe_id].append((offset, size))

    def _get_stripe_offset(self, stripe_id):
        '''
        Get current offset according to stripe_id. We can use stripe_size - remaining_size.
        '''
        # get the remaining size of the stripe with stripe_id
        remaining_size = self.find_size_by_id(stripe_id)[0]
        return self.stripe_size - remaining_size


    def track_disk(self, stripe_id, block_offset, file_name, size):
        if stripe_id >= len(self.stripe_usage):
            self.stripe_usage.append({})
        self.stripe_usage[stripe_id][block_offset] = (file_name, size)

@dataclass
class RAID6Config:
    '''
    Configuration class for RAID6 system.
    '''
    data_disks: int = field(default=4, metadata={"description": "Number of data disks"})
    parity_disks: int = field(default=2, metadata={"description": "Number of parity disks"})
    stripe_width: int = field(default=6, metadata={"description": "Number of disks in a stripe"})
    block_size: int = field(default=1024 * 1024, metadata={"description": "Block size in bytes"})
    disk_size: int = field(default=1024*1024*1024, metadata={"description": "Disk size in bytes"})
    
    def __post_init__(self):
        assert self.parity_disks == 2, "RAID6 does not support 2 parity disks"
        assert self.stripe_width == self.data_disks + self.parity_disks, "Invalid RAID6 configuration"
        assert self.disk_size % self.block_size == 0, "Disk size should be multiple of block size"


if __name__=="__main__":
    # Test Manager
    config = RAID6Config(
        data_disks=4,
        parity_disks=2,
        stripe_width=6,
        block_size=16,
        disk_size=1024*1024*1024
    )
    dm = DiskManager(config.block_size, config.data_disks + config.parity_disks, 10)
    print(dm.available_stripes)

    # Test allocate
    allocations = dm.allocate("test_file0", 10 * config.block_size + 10)
    print(allocations)
    print(dm.available_stripes)
    print(dm.file_tracking)

    allocations = dm.allocate("test_file1", 16)
    print(allocations)
    print(dm.available_stripes)
    print(dm.file_tracking)

    allocations = dm.allocate("test_file2", 42)
    print(allocations)
    print(dm.available_stripes)
    print(dm.file_tracking)

    # Test find_size_by_id
    print(dm.find_size_by_id(0))

    # Test track_disk
    dm.track_disk(0, 0, "test_file", 10 * config.block_size)

    # Test get_stripe_offset
    print(dm._get_stripe_offset(0))