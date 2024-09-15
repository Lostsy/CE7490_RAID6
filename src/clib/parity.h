#ifndef PARITY_H
#define PARITY_H

#include <vector>
#include <string>
#include <pybind11/numpy.h>
#include <pybind11/stl.h> 

namespace py = pybind11;

void cal_parity(py::buffer p, py::buffer q, py::buffer data);
void cal_parity_8(py::buffer p, py::buffer q, py::buffer data);
void cal_parity_p(py::buffer p, py::buffer data);
void cal_parity_q(py::buffer q, py::buffer data, std::vector<int> idxs);
void cal_parity_q_8(py::buffer q, py::buffer data);

void q_recover_data(py::buffer new_data, py::buffer q, py::buffer data, std::vector<int> idxs);
void recover_data_data(py::buffer data1, py::buffer data2,
                       py::buffer p, py::buffer inter_p,
                       py::buffer q, py::buffer inter_q,
                       int idx1, int idx2);
#endif