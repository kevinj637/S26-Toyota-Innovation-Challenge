# tests/test_export_c.py
import numpy as np
from src.collect import generate_sim_dataset, DEFAULT_SCENARIO
from src.train import build_dataset, train_model
from src.export_c import tree_to_c, py_classify

def test_py_reference_matches_sklearn(tmp_path):
    csv = tmp_path / "d.csv"
    generate_sim_dataset(csv, DEFAULT_SCENARIO, fs=1000, seed=0)
    X, y = build_dataset(csv); model, _ = train_model(X, y, seed=0)
    classes = list(model.classes_)
    for row in X[:200]:
        ref = py_classify(model.tree_, row)
        sk = list(model.classes_).index(model.predict(row.reshape(1, -1))[0])
        assert ref == sk

def test_c_header_has_classify(tmp_path):
    csv = tmp_path / "d.csv"
    generate_sim_dataset(csv, DEFAULT_SCENARIO, fs=1000, seed=0)
    X, y = build_dataset(csv); model, _ = train_model(X, y, seed=0)
    code = tree_to_c(model)
    assert "int classify(const float f[6])" in code
    assert "return" in code
