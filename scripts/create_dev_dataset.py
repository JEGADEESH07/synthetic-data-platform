"""Create a realistic synthetic development dataset for V0.2."""

from pathlib import Path
import random

import pandas as pd
from faker import Faker


SEED = 42
ROW_COUNT = 5000

OUTPUT_PATH = Path("data/input/dev_dataset.csv")


def main() -> None:
    """Generate and save the development dataset."""

    random.seed(SEED)

    faker = Faker("en_IN")
    faker.seed_instance(SEED)

    cities = [
        "Chennai",
        "Coimbatore",
        "Madurai",
        "Trichy",
        "Salem",
        "Tirunelveli",
        "Erode",
        "Vellore",
        "Thanjavur",
        "Bengaluru",
    ]

    rows = []

    for index in range(1, ROW_COUNT + 1):
        age = random.choices(
            population=[22, 27, 32, 38, 45, 52, 60],
            weights=[12, 20, 22, 18, 14, 9, 5],
        )[0]

        amount = round(
            random.lognormvariate(7.2, 0.65),
            2,
        )

        amount = min(max(amount, 100.00), 250000.00)

        rows.append(
            {
                "Customer_ID": f"CUST_{index:06d}",
                "Customer_Name": faker.name(),
                "Phone_Number": faker.phone_number(),
                "Email": faker.email(),
                "Age": age,
                "City": random.choice(cities),
                "Amount": amount,
            }
        )

    dataframe = pd.DataFrame(rows)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("Development dataset created.")
    print(f"Path       : {OUTPUT_PATH}")
    print(f"Rows       : {len(dataframe)}")
    print(f"Columns    : {len(dataframe.columns)}")
    print(f"Size       : {dataframe.shape}")
    print()
    print(dataframe.head())
    print()
    print("Amount statistics:")
    print(dataframe["Amount"].describe())


if __name__ == "__main__":
    main()