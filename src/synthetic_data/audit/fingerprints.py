
"""Dataset and schema fingerprint utilities."""

import hashlib
import json

import pandas as pd


def fingerprint_schema(dataframe: pd.DataFrame) -> str:
    """Return a stable SHA-256 fingerprint of column names and data types."""

    schema = [
        {
            "column": str(column),
            "dtype": str(dataframe[column].dtype),
        }
        for column in dataframe.columns
    ]

    canonical_schema = json.dumps(
        schema,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return hashlib.sha256(canonical_schema.encode("utf-8")).hexdigest()


def fingerprint_dataset(dataframe: pd.DataFrame) -> str:
    """Return a SHA-256 fingerprint of the dataset's ordered contents."""

    content_hash = hashlib.sha256()

    schema_fingerprint = fingerprint_schema(dataframe)
    content_hash.update(schema_fingerprint.encode("ascii"))

    row_hashes = pd.util.hash_pandas_object(
        dataframe,
        index=True,
        categorize=True,
    )

    content_hash.update(row_hashes.to_numpy().tobytes())

    return content_hash.hexdigest()
