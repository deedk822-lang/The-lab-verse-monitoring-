import subprocess
import os
import pytest

def test_safety_check_aborts_on_no_input():
    """safety_check must abort when user types 'n' (simulated)."""
    # Run a target that calls safety_check with FORCE unset
    env = os.environ.copy()
    env.pop("FORCE", None)  # ensure FORCE is not set

    # Simulate user typing 'n' + ENTER
    proc = subprocess.Popen(
        ["make", "reset"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=os.path.dirname(os.path.dirname(__file__)),
    )
    stdout, stderr = proc.communicate(input="n\n")

    # Should abort with exit code 1 and contain "Aborted."
    assert proc.returncode == 1
    assert "Aborted." in stdout + stderr