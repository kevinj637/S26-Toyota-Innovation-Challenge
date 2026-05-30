# tests/test_state_machine.py
from src.detect import StallStateMachine

def test_sustained_stall_raises_alarm():
    sm = StallStateMachine(enter_n=3, exit_m=5)
    states = [sm.update("stall") for _ in range(3)]
    assert states[-1] == "stall"

def test_single_stray_stall_does_not_alarm():
    sm = StallStateMachine(enter_n=3, exit_m=5)
    sm.update("normal")
    assert sm.update("stall") == "normal"   # one stray stall, streak=1 < enter_n

def test_startup_never_alarms():
    sm = StallStateMachine(enter_n=3, exit_m=5)
    out = [sm.update(p) for p in ["startup", "startup", "startup", "normal"]]
    assert "stall" not in out

def test_recovery_after_enough_normals():
    sm = StallStateMachine(enter_n=3, exit_m=5)
    for _ in range(3): sm.update("stall")
    assert sm.state == "stall"
    states = [sm.update("normal") for _ in range(5)]
    assert states[-1] == "normal"
