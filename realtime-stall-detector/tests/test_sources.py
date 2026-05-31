from src.sources import SimulatedSource, parse_serial_line

def test_simulated_source_yields_tuples():
    src = SimulatedSource([("off", 0.05), ("stall", 0.05)], fs=1000, seed=0)
    samples = list(src)
    assert len(samples) == 100
    t0, x0 = samples[0]
    assert isinstance(t0, float) and isinstance(x0, float)
    # time monotonic
    times = [t for t, _ in samples]
    assert all(b > a for a, b in zip(times, times[1:]))

def test_parse_serial_line():
    assert parse_serial_line("1500,0.1234") == (0.0015, 0.1234)
    assert parse_serial_line("# banner R_SHUNT=1.0") is None
    assert parse_serial_line("garbage") is None
    assert parse_serial_line("") is None
