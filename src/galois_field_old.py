import numpy as np

class GaloisField:
    # Galois Field GF(2^8) with modulo polynomial x^8 + x^4 + x^3 + x^2 + 1
    def __init__(self):
        self.polynomial = 0b100011101
        self.gflog = [0] * 256
        self.gfilog = [0] * 512
        self._initialize_tables()

    def _initialize_tables(self):
        value = 1
        for exp in range(255):
            self.gfilog[exp] = value # x^0 = 1, value = 1, exp = 0
            self.gflog[value] = exp
            value <<= 1
            if value & 0b100000000: # if value >= 256
                value ^= self.polynomial
    
        # optimization: double the size of the tables to avoid modulo
        for exp in range(255, 512):
            self.gfilog[exp] = self.gfilog[exp - 255]

    def add(self, a, b):
        return a ^ b

    def subtract(self, a, b):
        return a ^ b

    # deprecated
    def inverse(self, a):
        return self.gfilog[255 - self.gflog[a]] 
    
    def multiply(self, a, b):
        if a == 0 or b == 0:
            return 0
        return self.gfilog[self.gflog[a] + self.gflog[b]] # a * b = x^m + x^n = x^(m + n)

    def divide(self, a, b):
        if a == 0:
            return 0
        if b == 0:
            raise ZeroDivisionError("division by zero")
        # return self.multiply(a, self.inverse(b))
        return self.gfilog[255 + self.gflog[a] - self.gflog[b]] # a / b = x^m / x^n = x^(m - n) = x^(255 + m - n)
    
    def get_gfilog(self):
        return self.gfilog


def cal_parity_p_py(p, data):
    gf = GaloisField()
    
    block_size = len(p)
    width = len(data) // len(p)

    for i in range(0, width):
        base = i * block_size
        for j in range(0, block_size):
            p[j] = gf.add(p[j], data[base + j])


def cal_parity_q_py(q, data):
    gf = GaloisField()
    
    block_size = len(q)
    width = len(data) // len(q)

    for i in range(0, width):
        base = i * block_size
        g = gf.get_gfilog()[i]
        for j in range(0, block_size):
            q[j] = gf.add(q[j], gf.multiply(data[base + j], g))
