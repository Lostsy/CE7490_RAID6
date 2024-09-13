#ifndef GALOISFIELD_H
#define GALOISFIELD_H

#include <vector>

class GaloisField {
public:
    GaloisField();
    uint8_t add(uint8_t a, uint8_t b) const;
    uint8_t subtract(uint8_t a, uint8_t b) const;
    uint8_t multiply(uint8_t a, uint8_t b) const;
    uint8_t divide(uint8_t a, uint8_t b) const;

    uint64_t add(uint64_t a, uint64_t b) const;
    uint64_t mult2(uint64_t a) const;

    std::vector<uint8_t> get_gfilog();

private:
    void initializeTables();

    static const int POLYNOMIAL = 0b100011101;
    std::vector<int> gflog;
    std::vector<uint8_t> gfilog;
    uint64_t mask(uint64_t a) const;
};

#endif // GALOISFIELD_H
