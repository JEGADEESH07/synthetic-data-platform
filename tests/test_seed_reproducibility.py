import random

import numpy as np
import pytest
import torch

from synthetic_data.generation.ctgan_generator import (
    _seeded_training_context,
)


def _numpy_states_equal(left, right):
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def _random_values_for_seed(seed):
    with _seeded_training_context(seed):
        return (
            random.random(),
            np.random.random(),
            torch.rand(1).item(),
        )


def test_same_seed_repeats_random_values():
    first = _random_values_for_seed(42)
    second = _random_values_for_seed(42)

    assert first == second


def test_training_context_restores_rng_states():
    random.seed(123)
    np.random.seed(456)
    torch.manual_seed(789)

    python_before = random.getstate()
    numpy_before = np.random.get_state()
    torch_before = torch.random.get_rng_state().clone()

    with _seeded_training_context(42):
        random.random()
        np.random.random()
        torch.rand(1)

    assert random.getstate() == python_before
    assert _numpy_states_equal(
        np.random.get_state(), numpy_before
    )
    assert torch.equal(
        torch.random.get_rng_state(), torch_before
    )


def test_training_context_restores_rng_states_after_exception():
    random.seed(123)
    np.random.seed(456)
    torch.manual_seed(789)

    python_before = random.getstate()
    numpy_before = np.random.get_state()
    torch_before = torch.random.get_rng_state().clone()

    with pytest.raises(RuntimeError, match="test failure"):
        with _seeded_training_context(42):
            random.random()
            np.random.random()
            torch.rand(1)
            raise RuntimeError("test failure")

    assert random.getstate() == python_before
    assert _numpy_states_equal(
        np.random.get_state(), numpy_before
    )
    assert torch.equal(
        torch.random.get_rng_state(), torch_before
    )
