# CE7490_RAID6
Codebase for CE7490 2024 Aug

## Introduction
A storage system based on RAID6, has features:
* Support **$m$ data** disks and 2 parity disks
* Recover from **arbitary 2 disks** corruption
* Support **save, delete and modify** files of **arbitary size**
* Support a naive **data allocation machanism**
* **Optimization** for RADI6 parity calculation

## Structure
```
.
├── data
├── disk # simulate disks
├── src # system codes
│   └── clib # c++ gf op & parity op codes
└── test # test codes
```

## Get started
```
conda create -n raid6 python=3.10
git clone https://github.com/Lostsy/CE7490_RAID6.git
cd CE7490_RAID6
pip install -e .
cd CE7490_RAID6/src/clib
python setup.py build_ext --inplace
```

## Test case
```
python test_parity.py
python test_recover.py
python test_save_load.py
```
