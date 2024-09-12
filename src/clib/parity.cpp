#include "parity.h"
#include "galois_field.h"

GaloisField gf = GaloisField();

void cal_parity(py::buffer p, py::buffer q, py::buffer data) {
    py::buffer_info p_info = p.request();
    py::buffer_info q_info = q.request();
    py::buffer_info data_info = data.request();

    auto p_ptr = static_cast<uint8_t *>(p_info.ptr);
    auto q_ptr = static_cast<uint8_t *>(q_info.ptr);
    auto data_ptr = static_cast<uint8_t *>(data_info.ptr);

    int block_size = p_info.shape[0];
    int width = data_info.shape[0] / block_size;

    for (int i = 0; i < width; i++) {
        int base = i * block_size;
        uint8_t g = gf.get_gfilog()[i];
        for (int j = 0; j < block_size; j += 4) {
            // block_size is a multiple of 4
            p_ptr[j] = gf.add(p_ptr[j], data_ptr[base + j]);
            p_ptr[j + 1] = gf.add(p_ptr[j + 1], data_ptr[base + j + 1]);
            p_ptr[j + 2] = gf.add(p_ptr[j + 2], data_ptr[base + j + 2]);
            p_ptr[j + 3] = gf.add(p_ptr[j + 3], data_ptr[base + j + 3]);

            q_ptr[j] = gf.add(q_ptr[j], gf.multiply(data_ptr[base + j], g));
            q_ptr[j + 1] = gf.add(q_ptr[j + 1], gf.multiply(data_ptr[base + j + 1], g));
            q_ptr[j + 2] = gf.add(q_ptr[j + 2], gf.multiply(data_ptr[base + j + 2], g));
            q_ptr[j + 3] = gf.add(q_ptr[j + 3], gf.multiply(data_ptr[base + j + 3], g));
        }
    }
}
