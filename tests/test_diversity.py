import math
from pipeline.diversity import shannon, richness, evenness

def test_shannon_even_community():
    # 4 species each 25% -> Shannon = ln(4)
    assert math.isclose(shannon([25, 25, 25, 25]), math.log(4), rel_tol=1e-9)

def test_richness_ignores_zeros():
    assert richness([50, 50, 0, 0]) == 2

def test_evenness_even_community_is_one():
    assert math.isclose(evenness([25, 25, 25, 25]), 1.0, rel_tol=1e-9)
