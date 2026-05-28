import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from sf6_env.engine.drive import DriveGauge, DRIVE_MAX, BURNOUT_RECOVERY_FRAMES


def test_initial_state():
    dg = DriveGauge()
    assert dg.value == DRIVE_MAX
    assert not dg.burnout


def test_spend_reduces_gauge():
    dg = DriveGauge()
    assert dg.spend(1.0)
    assert dg.value == DRIVE_MAX - 1.0


def test_cannot_spend_more_than_available():
    dg = DriveGauge()
    dg.value = 0.5
    assert not dg.spend(1.0)
    assert dg.value == 0.5


def test_burnout_on_empty():
    dg = DriveGauge()
    dg.value = 0.5
    dg._drain(0.5)
    assert dg.burnout
    assert dg.value == 0.0


def test_burnout_recovery():
    dg = DriveGauge()
    dg._enter_burnout()
    for _ in range(BURNOUT_RECOVERY_FRAMES):
        dg.tick()
    assert not dg.burnout
    assert dg.value == DRIVE_MAX


def test_gain_does_not_exceed_max():
    dg = DriveGauge()
    dg.gain(100.0)
    assert dg.value == DRIVE_MAX


def test_gain_ignored_in_burnout():
    dg = DriveGauge()
    dg._enter_burnout()
    dg.gain(3.0)
    assert dg.value == 0.0


def test_drive_rush_direct_cost():
    dg = DriveGauge()
    assert dg.start_drive_rush(from_parry=False)
    assert dg.value == DRIVE_MAX - 1.5
    assert dg.rushing
