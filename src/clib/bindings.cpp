#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
#include "galois_field.h"
#include "parity.h"

namespace py = pybind11;

PYBIND11_MODULE(galois_field, m) {
    // py::class_<GaloisField>(m, "GaloisField")
    //     .def(py::init<>())
    //     .def("add", &GaloisField::add)
    //     .def("subtract", &GaloisField::subtract)
    //     .def("multiply", &GaloisField::multiply)
    //     .def("divide", &GaloisField::divide)
    //     .def("get_gfilog", &GaloisField::get_gfilog);
    
    m.def("cal_parity", &cal_parity);
    m.def("cal_parity_8", &cal_parity_8);
    m.def("cal_parity_p", &cal_parity_p);
    m.def("cal_parity_q", &cal_parity_q);
    m.def("cal_parity_q_8", &cal_parity_q_8);
    m.def("q_recover_data", &q_recover_data);
    m.def("recover_data_data", &recover_data_data);
}