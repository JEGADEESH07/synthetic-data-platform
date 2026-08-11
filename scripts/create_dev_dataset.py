import random

import pandas as pd
from faker import Faker


fake = Faker("en_IN")

random.seed(42)
Faker.seed(42)


CITIES = [
    "Chennai",
    "Bangalore",
    "Mumbai",
    "Hyderabad",
    "Delhi",
    "Pune",
    "Kolkata",
    "Coimbatore",
]

CITY_WEIGHTS = [
    0.18,
    0.20,
    0.16,
    0.12,
    0.12,
    0.10,
    0.06,
    0.06,
]


def generate_dataset(
    rows: int = 5000,
) -> pd.DataFrame:

    data = []

    for index in range(rows):

        age = random.randint(18, 65)

        city = random.choices(
            CITIES,
            weights=CITY_WEIGHTS,
            k=1,
        )[0]

        transaction_amount = round(
            random.lognormvariate(
                9.2,
                0.7,
            ),
            2,
        )

        transaction_amount = min(
            max(transaction_amount, 500),
            100000,
        )

        data.append(
            {
                "Customer_ID": (
                    f"CUST{index + 1:06d}"
                ),
                "Customer_Name": fake.name(),
                "Age": age,
                "City": city,
                "Transaction_Amount": (
                    transaction_amount
                ),
            }
        )

    return pd.DataFrame(data)


def main():

    output_path = (
        "data/input/dev_dataset.csv"
    )

    df = generate_dataset(5000)

    df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"Created {output_path}"
    )

    print(
        f"Rows: {len(df)}"
    )

    print(
        f"Columns: {list(df.columns)}"
    )


if __name__ == "__main__":
    main()