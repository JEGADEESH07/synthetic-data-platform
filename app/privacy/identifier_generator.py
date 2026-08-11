import random

import pandas as pd
from faker import Faker


fake = Faker("en_IN")


def generate_identifier_values(
    synthetic_data: pd.DataFrame,
    identifier_columns: list[str],
    forbidden_values: dict[str, set[str]] | None = None,
    num_rows: int | None = None,
) -> pd.DataFrame:
    """
    Generate fresh identifier values for the synthetic dataset.

    Values found in forbidden_values are never reused.

    Direct identifiers are generated independently and are
    never learned by the synthetic-data model.
    """

    if not isinstance(synthetic_data, pd.DataFrame):
        raise TypeError(
            "synthetic_data must be a pandas DataFrame."
        )

    if synthetic_data.empty:
        raise ValueError(
            "Cannot generate identifiers for an empty dataset."
        )

    if num_rows is None:
        num_rows = len(synthetic_data)

    if num_rows != len(synthetic_data):
        raise ValueError(
            "num_rows must match the number of synthetic rows."
        )

    if forbidden_values is None:
        forbidden_values = {}

    result = synthetic_data.copy()

    for column in identifier_columns:

        normalized = column.strip().lower()

        forbidden = {
            str(value)
            for value in forbidden_values.get(
                column,
                set(),
            )
        }

        # --------------------------------------------------
        # Customer / User ID
        # --------------------------------------------------

        if normalized in {
            "customer_id",
            "user_id",
        }:

            prefix = (
                "SYN"
                if normalized == "customer_id"
                else "SYNUSR"
            )

            generated_values = []

            counter = 100000

            while len(generated_values) < num_rows:

                candidate = (
                    f"{prefix}{counter}"
                )

                if candidate not in forbidden:
                    generated_values.append(
                        candidate
                    )

                counter += 1

            result[column] = generated_values

        # --------------------------------------------------
        # Customer Name
        # --------------------------------------------------

        elif normalized in {
            "customer_name",
            "name",
        }:

            generated_values = []
            generated_set = set()

            while len(generated_values) < num_rows:

                candidate = fake.name()

                if (
                    candidate not in forbidden
                    and candidate not in generated_set
                ):
                    generated_values.append(
                        candidate
                    )

                    generated_set.add(candidate)

            result[column] = generated_values

        # --------------------------------------------------
        # Phone Number
        # --------------------------------------------------

        elif normalized in {
            "phone",
            "phone_number",
            "mobile",
            "mobile_number",
        }:

            generated_values = []
            generated_set = set()

            while len(generated_values) < num_rows:

                candidate = (
                    "+91 "
                    f"{random.randint(60000, 99999)} "
                    f"{random.randint(10000, 99999)}"
                )

                if (
                    candidate not in forbidden
                    and candidate not in generated_set
                ):
                    generated_values.append(
                        candidate
                    )

                    generated_set.add(candidate)

            result[column] = generated_values

        # --------------------------------------------------
        # Email
        # --------------------------------------------------

        elif normalized in {
            "email",
            "email_address",
        }:

            generated_values = []
            generated_set = set()

            while len(generated_values) < num_rows:

                candidate = fake.email()

                if (
                    candidate not in forbidden
                    and candidate not in generated_set
                ):
                    generated_values.append(
                        candidate
                    )

                    generated_set.add(candidate)

            result[column] = generated_values

        # --------------------------------------------------
        # Address
        # --------------------------------------------------

        elif normalized == "address":

            generated_values = []
            generated_set = set()

            while len(generated_values) < num_rows:

                candidate = fake.address().replace(
                    "\n",
                    ", ",
                )

                if (
                    candidate not in forbidden
                    and candidate not in generated_set
                ):
                    generated_values.append(
                        candidate
                    )

                    generated_set.add(candidate)

            result[column] = generated_values

        else:

            raise ValueError(
                f"Identifier column '{column}' was detected, "
                "but no generation strategy exists for it."
            )

    return result