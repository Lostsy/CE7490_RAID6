#include "galois_field.h"

GaloisField::GaloisField() : gflog(256, 0), gfilog(512, 0) {
    initializeTables();
}

void GaloisField::initializeTables() {
    int value = 1;
    for (int exp = 0; exp < 255; ++exp) {
        gfilog[exp] = value;
        gflog[value] = exp;
        value <<= 1;
        if (value & 0b100000000) { // if value >= 256
            value ^= POLYNOMIAL;
        }
    }

    // optimization: double the size of the tables to avoid modulo
    for (int exp = 255; exp < 512; ++exp) {
        gfilog[exp] = gfilog[exp - 255];
    }
}

uint8_t GaloisField::add(uint8_t a, uint8_t b) const {
    return a ^ b;
}

uint8_t GaloisField::subtract(uint8_t a, uint8_t b) const {
    return a ^ b;
}

uint8_t GaloisField::multiply(uint8_t a, uint8_t b) const {
    if (a == 0 || b == 0) {
        return 0;
    }
    return gfilog[gflog[a] + gflog[b]];
}

uint8_t GaloisField::divide(uint8_t a, uint8_t b) const {
    if (a == 0) {
        return 0;
    }
    if (b == 0) {
        throw std::runtime_error("division by zero");
    }
    return gfilog[255 + gflog[a] - gflog[b]];
}

uint64_t GaloisField::add(uint64_t a, uint64_t b) const {
    return a ^ b;
}

uint64_t GaloisField::mult2(uint64_t a) const {
    uint64_t result = 0;
    result = (a << 1) & 0xfefefefefefefefe;
    result ^= mask(a) & 0x1d1d1d1d1d1d1d1d;
    return result;
}

std::vector<uint8_t> GaloisField::get_gfilog() {
    return gfilog;
}

uint64_t GaloisField::mask(uint64_t a) const {
    a &= 0x8080808080808080;
    return (a << 1) - (a >> 7);
}