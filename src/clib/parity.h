#ifndef PARITY_H
#define PARITY_H

#include <vector>
#include <string>
#include <pybind11/numpy.h>
#include <pybind11/stl.h> 

namespace py = pybind11;

void cal_parity(py::buffer p, py::buffer q, py::buffer data);

#endif