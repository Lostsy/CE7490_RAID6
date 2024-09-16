#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
#include "galois_field.h"
#include "parity.h"

namespace py = pybind11;

PYBIND11_MODULE(galois_field, m) {
    m.def("cal_parity", &cal_parity);
    m.def("cal_parity_8", &cal_parity_8);
    m.def("cal_parity_p", &cal_parity_p);
    m.def("cal_parity_q", &cal_parity_q);
    m.def("cal_parity_q_8", &cal_parity_q_8);
    m.def("q_recover_data", &q_recover_data);
    m.def("recover_data_data", &recover_data_data);
    // Just for test
    m.def("cal_parity_p_rm8", &cal_parity_p_rm8);
    m.def("cal_parity_p_rmunrolling", &cal_parity_p_rmunrolling);
    m.def("cal_parity_q_rmunrolling", &cal_parity_q_rmunrolling);
    m.def("cal_parity_q_8_rmunrolling", &cal_parity_q_8_rmunrolling);
}