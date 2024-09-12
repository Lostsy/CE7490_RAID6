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
    std::vector<uint8_t> get_gfilog();

private:
    void initializeTables();

    static const int POLYNOMIAL = 0b100011101;
    std::vector<int> gflog;
    std::vector<uint8_t> gfilog;
};

#endif // GALOISFIELD_H
