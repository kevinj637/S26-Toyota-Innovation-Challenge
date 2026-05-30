"""Data sources behind one interface so the same pipeline runs on sim or hardware."""
import time
from src.simulator import simulate

class DataSource:
    def __iter__(self):
        raise NotImplementedError

class SimulatedSource(DataSource):
    def __init__(self, segments, fs=1000, params=None, seed=0, realtime=False):
        self.t, self.x, self.labels = simulate(segments, fs, params, seed)
        self.realtime = realtime

    def __iter__(self):
        prev = None
        for ti, xi in zip(self.t, self.x):
            if self.realtime and prev is not None:
                time.sleep(max(0.0, ti - prev))
            prev = ti
            yield float(ti), float(xi)

def parse_serial_line(line):
    """'t_us,current_a' -> (t_s, current_a); None for banners/garbage."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = line.split(",")
    if len(parts) != 2:
        return None
    try:
        return float(parts[0]) / 1e6, float(parts[1])
    except ValueError:
        return None

class SerialSource(DataSource):
    def __init__(self, port, baud=115200):
        import serial  # pyserial, imported lazily so tests don't need hardware
        self.ser = serial.Serial(port, baud, timeout=1)

    def __iter__(self):
        for raw in self.ser:
            parsed = parse_serial_line(raw.decode("utf-8", "replace"))
            if parsed is not None:
                yield parsed
