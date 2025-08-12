from solarwindpy import plasma
from . import test_base


def test_save_and_load(tmp_path):
    data = test_base.TestData().plasma_data
    plas = plasma.Plasma(data, "a", "p1")
    fname = tmp_path / "plasma.h5"
    plas.save(fname)
    loaded = plasma.Plasma.load_from_file(fname, "a", "p1", sckey=None, akey=None)
    assert loaded == plas
    assert loaded.species == plas.species
