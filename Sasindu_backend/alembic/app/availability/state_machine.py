import numpy as np

STATES = ["online", "busy", "offline"]

# Row-stochastic transition matrix: P[from][to]. Tuned so "online" is the
# common resting state, matching a realistic on-call provider pool.
_TRANSITIONS = {
    "online": {"online": 0.75, "busy": 0.20, "offline": 0.05},
    "busy": {"online": 0.40, "busy": 0.50, "offline": 0.10},
    "offline": {"online": 0.30, "busy": 0.05, "offline": 0.65},
}


class ProviderStateMachine:
    def next_state(self, current: str, rng: np.random.Generator) -> str:
        probs = _TRANSITIONS[current]
        return rng.choice(list(probs.keys()), p=list(probs.values()))
