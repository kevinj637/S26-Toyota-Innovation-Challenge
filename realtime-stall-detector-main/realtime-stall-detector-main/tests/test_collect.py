import pandas as pd
from src.collect import generate_sim_dataset, DEFAULT_SCENARIO

def test_generate_sim_dataset_writes_labeled_csv(tmp_path):
    out = tmp_path / "labeled.csv"
    generate_sim_dataset(out, scenario=DEFAULT_SCENARIO, fs=1000, seed=0)
    df = pd.read_csv(out)
    assert list(df.columns) == ["t_s", "current_a", "label"]
    assert set(df["label"].unique()) == {"normal", "startup", "stall"}
    assert len(df) > 1000
