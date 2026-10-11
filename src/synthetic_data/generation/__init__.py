"""Synthetic data generation package."""

from synthetic_data.generation.ctgan_generator import (
    GenerationResult,
    SyntheticGenerationError,
    generate_synthetic_data,
)

__all__ = [
    "GenerationResult",
    "SyntheticGenerationError",
    "generate_synthetic_data",
]
