#include "parity.h"
#include "galois_field.h"

static GaloisField gf = GaloisField();

void cal_parity(py::buffer p, py::buffer q, py::buffer data) {
    py::buffer_info p_info = p.request();
    py::buffer_info q_info = q.request();
    py::buffer_info data_info = data.request();

    auto p_ptr = static_cast<uint8_t *>(p_info.ptr);
    auto q_ptr = static_cast<uint8_t *>(q_info.ptr);
    auto data_ptr = static_cast<uint8_t *>(data_info.ptr);

    int block_size = p_info.shape[0];
    int width = data_info.shape[0] / p_info.shape[0];

    for (int i = 0; i < width; i++) {
        int base = i * block_size;
        uint8_t g = gf.get_gfilog()[i];
        int j = 0;
        for (j = 0; j < block_size - 3; j += 4) {
            p_ptr[j] = gf.add(p_ptr[j], data_ptr[base + j]);
            p_ptr[j + 1] = gf.add(p_ptr[j + 1], data_ptr[base + j + 1]);
            p_ptr[j + 2] = gf.add(p_ptr[j + 2], data_ptr[base + j + 2]);
            p_ptr[j + 3] = gf.add(p_ptr[j + 3], data_ptr[base + j + 3]);

            q_ptr[j] = gf.add(q_ptr[j], gf.multiply(data_ptr[base + j], g));
            q_ptr[j + 1] = gf.add(q_ptr[j + 1], gf.multiply(data_ptr[base + j + 1], g));
            q_ptr[j + 2] = gf.add(q_ptr[j + 2], gf.multiply(data_ptr[base + j + 2], g));
            q_ptr[j + 3] = gf.add(q_ptr[j + 3], gf.multiply(data_ptr[base + j + 3], g));
        }
        for (; j < block_size; j++) {
            p_ptr[j] = gf.add(p_ptr[j], data_ptr[base + j]);
            q_ptr[j] = gf.add(q_ptr[j], gf.multiply(data_ptr[base + j], g));
        }
    }
}


void cal_parity_8(py::buffer p, py::buffer q, py::buffer data) {
    py::buffer_info p_info = p.request();
    py::buffer_info q_info = q.request();
    py::buffer_info data_info = data.request();

    auto p_ptr = static_cast<uint64_t *>(p_info.ptr);
    auto q_ptr = static_cast<uint64_t *>(q_info.ptr);
    auto data_ptr = static_cast<uint64_t *>(data_info.ptr);

    int block_size = p_info.shape[0] / 8;
    int width = data_info.shape[0] / p_info.shape[0];

    memcpy(q_ptr, data_ptr + (width - 1) * block_size, block_size * sizeof(uint64_t));
    memcpy(p_ptr, data_ptr + (width - 1) * block_size, block_size * sizeof(uint64_t));
    if (width == 1) { return; }

    for (int i = width - 2; i >= 0; i--) {
        int base = i * block_size;
        int j = 0;
        for (j = 0; j < block_size - 3; j += 4) {
            p_ptr[j] = gf.add(p_ptr[j], data_ptr[base + j]);
            p_ptr[j + 1] = gf.add(p_ptr[j + 1], data_ptr[base + j + 1]);
            p_ptr[j + 2] = gf.add(p_ptr[j + 2], data_ptr[base + j + 2]);
            p_ptr[j + 3] = gf.add(p_ptr[j + 3], data_ptr[base + j + 3]);

            q_ptr[j] = gf.add(gf.mult2(q_ptr[j]), data_ptr[base + j]);
            q_ptr[j + 1] = gf.add(gf.mult2(q_ptr[j + 1]), data_ptr[base + j + 1]);
            q_ptr[j + 2] = gf.add(gf.mult2(q_ptr[j + 2]), data_ptr[base + j + 2]);
            q_ptr[j + 3] = gf.add(gf.mult2(q_ptr[j + 3]), data_ptr[base + j + 3]);
        }
        for (; j < block_size; j++) {
            p_ptr[j] = gf.add(p_ptr[j], data_ptr[base + j]);
            q_ptr[j] = gf.add(gf.mult2(q_ptr[j]), data_ptr[base + j]);
        }
    }
}

void cal_parity_p(py::buffer p, py::buffer data) {
    py::buffer_info p_info = p.request();
    py::buffer_info data_info = data.request();

    auto p_ptr = static_cast<uint64_t *>(p_info.ptr);
    auto data_ptr = static_cast<uint64_t *>(data_info.ptr);

    int block_size = p_info.shape[0] / 8;
    int width = data_info.shape[0] / p_info.shape[0];

    for (int i = 0; i < width; i++) {
        int base = i * block_size;
        int j = 0;
        for (j = 0; j < block_size - 3; j += 4) {
            p_ptr[j] = gf.add(p_ptr[j], data_ptr[base + j]);
            p_ptr[j + 1] = gf.add(p_ptr[j + 1], data_ptr[base + j + 1]);
            p_ptr[j + 2] = gf.add(p_ptr[j + 2], data_ptr[base + j + 2]);
            p_ptr[j + 3] = gf.add(p_ptr[j + 3], data_ptr[base + j + 3]);
        }
        for(; j < block_size; j++) {
            p_ptr[j] = gf.add(p_ptr[j], data_ptr[base + j]);
        }
    }
}

void cal_parity_q(py::buffer q, py::buffer data, std::vector<int> idxs) {
    py::buffer_info q_info = q.request();
    py::buffer_info data_info = data.request();

    auto q_ptr = static_cast<uint8_t *>(q_info.ptr);
    auto data_ptr = static_cast<uint8_t *>(data_info.ptr);

    int block_size = q_info.shape[0];
    int width = data_info.shape[0] / q_info.shape[0];

    for (int i = 0; i < width; i++) {
        int base = i * block_size;
        uint8_t g = gf.get_gfilog()[idxs[i]];
        int j = 0;
        for (j = 0; j < block_size - 3; j += 4) {
            q_ptr[j] = gf.add(q_ptr[j], gf.multiply(data_ptr[base + j], g));
            q_ptr[j + 1] = gf.add(q_ptr[j + 1], gf.multiply(data_ptr[base + j + 1], g));
            q_ptr[j + 2] = gf.add(q_ptr[j + 2], gf.multiply(data_ptr[base + j + 2], g));
            q_ptr[j + 3] = gf.add(q_ptr[j + 3], gf.multiply(data_ptr[base + j + 3], g));
        }
        for(; j < block_size; j++) {
            q_ptr[j] = gf.add(q_ptr[j], gf.multiply(data_ptr[base + j], g));
        }
    }
}

void cal_parity_q_8(py::buffer q, py::buffer data) {
    py::buffer_info q_info = q.request();
    py::buffer_info data_info = data.request();

    auto q_ptr = static_cast<uint64_t *>(q_info.ptr);
    auto data_ptr = static_cast<uint64_t *>(data_info.ptr);

    int block_size = q_info.shape[0] / 8;
    int width = data_info.shape[0] / q_info.shape[0];

    memcpy(q_ptr, data_ptr + (width - 1) * block_size, block_size * sizeof(uint64_t));
    if (width == 1) { return; }

    for (int i = width - 2; i >= 0; i--) {
        int base = i * block_size;
        int j = 0;
        for (j = 0; j < block_size - 3; j += 4) {
            q_ptr[j] = gf.add(gf.mult2(q_ptr[j]), data_ptr[base + j]);
            q_ptr[j + 1] = gf.add(gf.mult2(q_ptr[j + 1]), data_ptr[base + j + 1]);
            q_ptr[j + 2] = gf.add(gf.mult2(q_ptr[j + 2]), data_ptr[base + j + 2]);
            q_ptr[j + 3] = gf.add(gf.mult2(q_ptr[j + 3]), data_ptr[base + j + 3]);
        }
        for(; j < block_size; j++) {
            q_ptr[j] = gf.add(gf.mult2(q_ptr[j]), data_ptr[base + j]);
        }
    }
}