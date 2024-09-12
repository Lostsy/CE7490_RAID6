#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
#include "galois_field.h"
#include "parity.h"

namespace py = pybind11;

PYBIND11_MODULE(galois_field, m) {
    py::class_<GaloisField>(m, "GaloisField")
        .def(py::init<>())
        .def("add", &GaloisField::add)
        .def("subtract", &GaloisField::subtract)
        .def("multiply", &GaloisField::multiply)
        .def("divide", &GaloisField::divide)
        .def("get_gfilog", &GaloisField::get_gfilog);
    
    m.def("cal_parity", &cal_parity);
}