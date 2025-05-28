
import numpy as np
import pytest
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Mathematics.Arithmetic import get_weights, weighted_sum
from MDANSE.Framework.Jobs.XRayStaticStructureFactor import atomic_scattering_factor


@pytest.fixture(scope='function')
def weigths_dictionary_real():
    return {'A': 2.0, 'B': 0.5, 'C': 1.0}


@pytest.fixture(scope='function')
def weigths_dictionary_complex():
    return {'A': 2.0 -2.0j, 'B': 0.5, 'C': 1.0 + 0.1j}

test1_inputs_results = [
    ({'A':1},
     {('A',): 1, 'sum':2}),
    ({'A':10, 'B':10, 'C': 10},
     {('A',):0.5714285714285715,
      ('B',):0.14285714285714288,
      ('C',): 0.28571428571428575,
      'sum': 1.1666666666666665})
     ]

@pytest.mark.parametrize("atom_count, results", test1_inputs_results)
def test_weights_real_1D(weigths_dictionary_real, atom_count, results):
    calculated_weigths = get_weights(weigths_dictionary_real, atom_count, 1, conc_exp=1)
    for key in calculated_weigths:
        print(f"{key} {calculated_weigths[key]} {results[key]}")
        assert np.isclose(calculated_weigths[key], results[key])
    assert np.isclose(sum([value for key, value in calculated_weigths.items() if key != 'sum']), 1.0)

test2_inputs_results = [
    ({'A':1},
     {('A',): 1, 'sum':2-2j}),
    ({'A':10, 'B':10, 'C': 10},
     {('A',):0.6809583858764188-0.20176544766708698j,
      ('B',):0.11034047919293823+0.05989911727616647j,
      ('C',):0.20870113493064316+0.1418663303909206j,
      'sum': 1.1666666666666665-0.6333333333333333j})
     ]

@pytest.mark.parametrize("atom_count, results", test2_inputs_results)
def test_weights_complex_1D(weigths_dictionary_complex, atom_count, results):
    calculated_weigths = get_weights(weigths_dictionary_complex, atom_count, 1, conc_exp=1)
    for key in calculated_weigths:
        print(f"{key} {calculated_weigths[key]} {results[key]}")
        assert np.isclose(calculated_weigths[key], results[key])
    assert np.isclose(sum([value for key, value in calculated_weigths.items() if key != 'sum']), 1.0)

test3_inputs_results = [
    ({'A':1},
     {('A', 'A'): 1, 'sum':4}),
    ({'A':10, 'B':10, 'C': 10},
     {('A','A'):0.32653061224489793,
      ('A','B'):0.08163265306122448,
      ('A','C'):0.16326530612244897,
      ('B','A'):0.08163265306122448,
      ('B','B'):0.02040816326530612,
      ('B','C'):0.04081632653061224,
      ('C','A'): 0.16326530612244897,
      ('C','B'): 0.04081632653061224,
      ('C','C'): 0.08163265306122448,
      'sum': 1.3611111111111112})
     ]

@pytest.mark.parametrize("atom_count, results", test3_inputs_results)
def test_weights_real_2D(weigths_dictionary_real, atom_count, results):
    calculated_weigths = get_weights(weigths_dictionary_real, atom_count, 2, conc_exp=1)
    for key in calculated_weigths:
        print(f"{key} {calculated_weigths[key]} {results[key]}")
        assert np.isclose(calculated_weigths[key], results[key])
    assert np.isclose(sum([value for key, value in calculated_weigths.items() if key != 'sum']), 1.0)

test4_inputs_results = [
    ({'A':1},
     {('A', 'A'): 1, 'sum':8}),
    ({'A':10, 'B':10, 'C': 10},
     {('A','A'):0.5044136191677175+5.710238221372683e-18j,
      ('A','B'):0.06305170239596469+0.06305170239596469j,
      ('A','C'):0.11349306431273644+0.13871374527112235j,
      ('B','A'):0.06305170239596469-0.06305170239596469j,
      ('B','B'):0.015762925598991173+1.7844494441789635e-19j,
      ('B','C'):0.031525851197982346+0.0031525851197982354j,
      ('C','A'): 0.11349306431273644-0.13871374527112235j,
      ('C','B'): 0.031525851197982346-0.0031525851197982354j,
      ('C','C'): 0.06368221941992434+7.209175754483013e-19j,
      'sum': 1.7622222222222221-1.9949319973733282e-17j})
     ]

@pytest.mark.parametrize("atom_count, results", test4_inputs_results)
def test_weights_complex_2D(weigths_dictionary_complex, atom_count, results):
    calculated_weigths = get_weights(weigths_dictionary_complex, atom_count, 2, conc_exp=1)
    for key in calculated_weigths:
        print(f"{key} {calculated_weigths[key]} {results[key]}")
        assert np.isclose(calculated_weigths[key], results[key])
    assert np.isclose(sum([value for key, value in calculated_weigths.items() if key != 'sum']), 1.0)

def test_xray_weights():
    composition = {'Cu':5,'O':10}
    asf = dict(
            (
                element,
                atomic_scattering_factor(
                    element,
                    np.arange(1,10),
                    ATOMS_DATABASE,
                ),
            )
            for element in composition
        )
    weight_dict = get_weights(asf, composition, 2)
    assert True


def test_CuSbS():
    weights = {symbol: ATOMS_DATABASE.get_value(symbol, 'b_incoherent') for symbol in ['Cu', 'Sb', 'S']}
    composition = {'Cu': 208, 'S': 208, 'Sb': 64}
    wd = get_weights(weights, composition, 1)
    assert wd[('Cu',)] > wd[('S',)] > wd[('Sb',)]
