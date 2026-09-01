import numpy as np

from app.availability.state_machine import STATES, ProviderStateMachine


def test_next_state_always_returns_valid_state():
    machine = ProviderStateMachine()
    rng = np.random.default_rng(1)
    for _ in range(100):
        state = machine.next_state("online", rng)
        assert state in STATES


def test_transitions_are_deterministic_given_seeded_rng():
    machine = ProviderStateMachine()
    seq_a = [machine.next_state("online", np.random.default_rng(42)) for _ in range(5)]
    seq_b = [machine.next_state("online", np.random.default_rng(42)) for _ in range(5)]
    assert seq_a == seq_b
