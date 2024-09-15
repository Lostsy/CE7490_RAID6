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

void q_recover_data(py::buffer data, py::buffer q, py::buffer inter_q, int idx) {
    py::buffer_info q_info = q.request();
    py::buffer_info inter_q_info = q.request();
    py::buffer_info data_info = data.request();

    auto q_ptr = static_cast<uint8_t *>(q_info.ptr);
    auto inter_q_ptr = static_cast<uint8_t *>(inter_q_info.ptr);
    auto data_ptr = static_cast<uint8_t *>(data_info.ptr);
    
    int block_size = q_info.shape[0];
    uint8_t g = gf.get_gfilog()[idx];

    int i = 0;
    for (i = 0; i < block_size - 3; i += 4) {
        data_ptr[i] = gf.divide(gf.add(q_ptr[i], inter_q_ptr[i]), g);
        data_ptr[i + 1] = gf.divide(gf.add(q_ptr[i + 1], inter_q_ptr[i + 1]), g);
        data_ptr[i + 2] = gf.divide(gf.add(q_ptr[i + 2], inter_q_ptr[i + 2]), g);
        data_ptr[i + 3] = gf.divide(gf.add(q_ptr[i + 3], inter_q_ptr[i + 3]), g);
    }
    for (; i < block_size; i++) {
        data_ptr[i] = gf.divide(gf.add(q_ptr[i], inter_q_ptr[i]), g);
    }
}

void recover_data_data(py::buffer data1, py::buffer data2,
                       py::buffer p, py::buffer inter_p,
                       py::buffer q, py::buffer inter_q,
                       int idx1, int idx2) {
    py::buffer_info data1_info = data1.request();
    py::buffer_info data2_info = data2.request();
    py::buffer_info p_info = p.request();
    py::buffer_info inter_p_info = inter_p.request();
    py::buffer_info q_info = q.request();
    py::buffer_info inter_q_info = inter_q.request();

    auto data1_ptr = static_cast<uint8_t *>(data1_info.ptr);
    auto data2_ptr = static_cast<uint8_t *>(data2_info.ptr);
    auto p_ptr = static_cast<uint8_t *>(p_info.ptr);
    auto inter_p_ptr = static_cast<uint8_t *>(inter_p_info.ptr);
    auto q_ptr = static_cast<uint8_t *>(q_info.ptr);
    auto inter_q_ptr = static_cast<uint8_t *>(inter_q_info.ptr);

    int block_size = p_info.shape[0];

    uint8_t g1 = gf.get_gfilog()[idx2 - idx1];
    uint8_t g2 = gf.get_gfilog()[idx1];
    g2 = gf.divide(1, g2);
    uint8_t a = gf.divide(g1, gf.add(g1, 1));
    uint8_t b = gf.divide(g2, gf.add(g1, 1));

    int i = 0;
    for (i = 0; i < block_size - 3; i += 4) {
        data1_ptr[i] = gf.add(gf.multiply(gf.add(p_ptr[i], inter_p_ptr[i]), a),
                              gf.multiply(gf.add(q_ptr[i], inter_q_ptr[i]), b));
        data1_ptr[i + 1] = gf.add(gf.multiply(gf.add(p_ptr[i + 1], inter_p_ptr[i + 1]), a),
                                  gf.multiply(gf.add(q_ptr[i + 1], inter_q_ptr[i + 1]), b));
        data1_ptr[i + 2] = gf.add(gf.multiply(gf.add(p_ptr[i + 2], inter_p_ptr[i + 2]), a),
                                  gf.multiply(gf.add(q_ptr[i + 2], inter_q_ptr[i + 2]), b));
        data1_ptr[i + 3] = gf.add(gf.multiply(gf.add(p_ptr[i + 3], inter_p_ptr[i + 3]), a),
                                  gf.multiply(gf.add(q_ptr[i + 3], inter_q_ptr[i + 3]), b));

        data2_ptr[i] = gf.add(gf.add(p_ptr[i], inter_p_ptr[i]), data1_ptr[i]);
        data2_ptr[i + 1] = gf.add(gf.add(p_ptr[i + 1], inter_p_ptr[i + 1]), data1_ptr[i + 1]);
        data2_ptr[i + 2] = gf.add(gf.add(p_ptr[i + 2], inter_p_ptr[i + 2]), data1_ptr[i + 2]);
        data2_ptr[i + 3] = gf.add(gf.add(p_ptr[i + 3], inter_p_ptr[i + 3]), data1_ptr[i + 3]);
    }
    for (; i < block_size; i++) {
        data1_ptr[i] = gf.add(gf.multiply(gf.add(p_ptr[i], inter_p_ptr[i]), a),
                              gf.multiply(gf.add(q_ptr[i], inter_q_ptr[i]), b));
        data2_ptr[i] = gf.add(gf.add(p_ptr[i], inter_p_ptr[i]), data1_ptr[i]);
    }
}
