"""Real-time web dashboard + collection console for the stall detector.

Reads the current stream (Arduino serial OR the simulator), shows a live chart and
state, and lets you record labeled segments, save a dataset, and train — all in the browser.

Run:
    python -m web.app --source serial --port /dev/cu.usbmodem1301
    python -m web.app --source sim            # no hardware needed (replays the simulator)

Then open http://localhost:5000
"""
import argparse
import csv
import json
import os
import threading
import time
from collections import Counter, deque

import numpy as np
from flask import Flask, Response, jsonify, request, send_from_directory

from src.sources import SerialSource, SimulatedSource
from src.features import FeatureStreamer
from src.config import CLASSES

MODEL_PATH = "model/tree.joblib"
DATA_PATH = "data/labeled.csv"
HERE = os.path.dirname(os.path.abspath(__file__))


class Hub:
    """Thread-shared live state between the serial reader and the web handlers."""
    def __init__(self):
        self.lock = threading.Lock()
        self.display = deque(maxlen=500)   # decimated (t, current) for the chart (~50 Hz)
        self.recent_mean = 0.0
        self.state = "live"                # 'live' (no model) or normal/startup/stall
        self.recording = False
        self.active_label = None
        self.collected = []                # (t, current, label)
        self.counts = Counter()
        self.model = None
        self.streamer = FeatureStreamer()
        self.sm = None
        self.running = True


hub = Hub()


def load_model():
    import joblib
    if os.path.exists(MODEL_PATH):
        bundle = joblib.load(MODEL_PATH)
        return bundle["model"]
    return None


def _source_samples(args):
    """Yield (t_s, current_a) forever from serial or a looping simulator."""
    if args.source == "sim":
        from src.collect import DEFAULT_SCENARIO
        t_off, seed = 0.0, 0
        while hub.running:
            src = SimulatedSource(DEFAULT_SCENARIO, fs=1000, seed=seed, realtime=True)
            last = 0.0
            for t, c in src:
                if not hub.running:
                    return
                yield t_off + t, c
                last = t
            t_off += last + 0.001
            seed += 1
    else:
        for t, c in SerialSource(args.port):
            if not hub.running:
                return
            yield t, c


def reader_thread(args):
    from src.detect import StallStateMachine
    with hub.lock:
        hub.model = load_model()
        hub.sm = StallStateMachine() if hub.model is not None else None
        if hub.model is not None:
            hub.state = "normal"
    win = deque(maxlen=200)
    decim = 0
    for t, cur in _source_samples(args):
        win.append(cur)
        feat = hub.streamer.push(t, cur)
        with hub.lock:
            if feat is not None and hub.model is not None:
                pred = hub.model.predict(feat.reshape(1, -1))[0]
                hub.state = hub.sm.update(pred)
            hub.recent_mean = sum(win) / len(win)
            if hub.recording and hub.active_label is not None:
                hub.collected.append((t, cur, hub.active_label))
                hub.counts[hub.active_label] += 1
        decim += 1
        if decim % 20 == 0:  # ~50 Hz to the chart
            with hub.lock:
                hub.display.append((round(t, 4), round(cur, 5)))


app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory(HERE, "index.html")


@app.route("/stream")
def stream():
    def gen():
        while True:
            with hub.lock:
                payload = {
                    "points": list(hub.display),
                    "mean": round(hub.recent_mean, 5),
                    "state": hub.state,
                    "recording": hub.recording,
                    "active_label": hub.active_label,
                    "counts": {c: hub.counts.get(c, 0) for c in CLASSES},
                    "total": len(hub.collected),
                    "has_model": hub.model is not None,
                }
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(0.08)
    return Response(gen(), mimetype="text/event-stream")


@app.post("/api/record/start")
def record_start():
    label = (request.get_json(silent=True) or {}).get("label", "normal")
    if label not in CLASSES:
        return jsonify(ok=False, error=f"unknown label {label}"), 400
    with hub.lock:
        hub.active_label = label
        hub.recording = True
    return jsonify(ok=True, label=label)


@app.post("/api/record/stop")
def record_stop():
    with hub.lock:
        hub.recording = False
    return jsonify(ok=True)


@app.post("/api/clear")
def clear():
    """Clear all collected samples, or just one label if {'label': ...} is given."""
    label = (request.get_json(silent=True) or {}).get("label")
    with hub.lock:
        if label:
            hub.collected = [r for r in hub.collected if r[2] != label]
            hub.counts[label] = 0
        else:
            hub.collected.clear()
            hub.counts.clear()
    return jsonify(ok=True, label=label)


@app.post("/api/save")
def save():
    os.makedirs("data", exist_ok=True)
    with hub.lock:
        rows = list(hub.collected)
    with open(DATA_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "current_a", "label"])
        w.writerows(rows)
    return jsonify(ok=True, path=DATA_PATH, rows=len(rows))


@app.post("/api/train")
def train():
    from src.train import build_dataset, train_model, save_model
    from src.detect import StallStateMachine
    # Persist the current collection, then train from it.
    save()
    try:
        X, y = build_dataset(DATA_PATH)
        if len(set(y)) < 2:
            return jsonify(ok=False, error="need at least 2 labels with data"), 400
        model, info = train_model(X, y)
        save_model(model)
    except Exception as exc:  # not enough data per class, etc.
        return jsonify(ok=False, error=f"{type(exc).__name__}: {exc}"), 400
    with hub.lock:
        hub.model = model
        hub.sm = StallStateMachine()
        hub.streamer = FeatureStreamer()
    return jsonify(ok=True, labels=info["labels"], confusion=info["confusion"].tolist(),
                   windows=len(y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["sim", "serial"], default="serial")
    ap.add_argument("--port", default=None)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--web-port", type=int, default=5050)  # avoid 5000 (macOS AirPlay Receiver)
    ap.add_argument("--resume", action="store_true",
                    help="preload an existing data/labeled.csv into the collection buffer")
    args = ap.parse_args()
    if args.resume and os.path.exists(DATA_PATH):
        import pandas as pd
        df = pd.read_csv(DATA_PATH)
        with hub.lock:
            for t, c, lab in zip(df["t_s"], df["current_a"], df["label"]):
                hub.collected.append((float(t), float(c), str(lab)))
                hub.counts[str(lab)] += 1
        print(f"resumed {len(hub.collected)} samples from {DATA_PATH}: {dict(hub.counts)}")
    threading.Thread(target=reader_thread, args=(args,), daemon=True).start()
    print(f"Dashboard: http://{args.host}:{args.web_port}  (source={args.source})")
    app.run(host=args.host, port=args.web_port, threaded=True)


if __name__ == "__main__":
    main()
