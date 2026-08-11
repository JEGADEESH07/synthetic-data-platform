from app.cli import create_parser


def test_cli_generate_arguments():

    parser = create_parser()

    args = parser.parse_args(
        [
            "generate",
            "--input",
            "data/input/test.csv",
            "--rows",
            "100",
            "--epochs",
            "10",
        ]
    )

    assert args.command == "generate"
    assert args.input == "data/input/test.csv"
    assert args.rows == 100
    assert args.epochs == 10


def test_cli_default_arguments():

    parser = create_parser()

    args = parser.parse_args(
        [
            "generate",
            "--input",
            "data/input/test.csv",
            "--rows",
            "100",
        ]
    )

    assert args.epochs == 300
    assert (
        args.output
        == "data/output/synthetic_data.csv"
    )
    assert (
        args.report
        == "data/output/evaluation_report.json"
    )