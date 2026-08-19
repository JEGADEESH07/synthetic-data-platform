import argparse

from app.services.synthetic_data_service import (
    SyntheticDataService,
)


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.
    """

    parser = argparse.ArgumentParser(
        description="Synthetic Data Platform V0.3"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate synthetic data from an input dataset.",
    )

    generate_parser.add_argument(
        "--input",
        required=True,
        help="Path to the input CSV file.",
    )

    generate_parser.add_argument(
        "--rows",
        type=int,
        required=True,
        help="Number of synthetic rows to generate.",
    )

    generate_parser.add_argument(
        "--epochs",
        type=int,
        default=300,
        help="Number of CTGAN training epochs.",
    )

    generate_parser.add_argument(
        "--output",
        default="data/output/synthetic_data.csv",
        help="Output path for the synthetic CSV.",
    )

    generate_parser.add_argument(
        "--report",
        default="data/output/evaluation_report.json",
        help="Output path for the evaluation report.",
    )

    return parser


def execute_generate(args) -> dict:
    """
    Execute the generate command through the application service.
    """

    service = SyntheticDataService()

    return service.generate(
        input_path=args.input,
        output_rows=args.rows,
        epochs=args.epochs,
        output_data_path=args.output,
        output_report_path=args.report,
    )


def main() -> None:
    """
    CLI application entry point.
    """

    parser = create_parser()
    args = parser.parse_args()

    if args.command == "generate":

        print(
            "Starting Synthetic Data Platform V0.3..."
        )

        print(f"Input: {args.input}")
        print(f"Rows: {args.rows}")
        print(f"Epochs: {args.epochs}")

        result = execute_generate(args)

        print()
        print(
            "Generation completed successfully."
        )

        print(
            f"Synthetic data: "
            f"{result['saved_files']['synthetic_data']}"
        )

        print(
            f"Evaluation report: "
            f"{result['saved_files']['evaluation_report']}"
        )

        print()
        print("Schema valid:")
        print(
            result["evaluation"]["schema"]["valid"]
        )

        print()
        print("Privacy safe:")
        print(
            result["evaluation"]["privacy"]["safe"]
        )


if __name__ == "__main__":
    main()