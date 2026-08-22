from app.cli.parser import create_cli_parser


def test_cli_parser_defaults():
    parser = create_cli_parser()
    args = parser.parse_args([])
    assert args.reset is False
    assert args.reset_only is False
    assert args.config == "config.yaml"


def test_cli_parser_reset_flag():
    parser = create_cli_parser()
    args = parser.parse_args(["--reset"])
    assert args.reset is True
    assert args.reset_only is False


def test_cli_parser_reset_only_flag():
    parser = create_cli_parser()
    args = parser.parse_args(["--reset-only"])
    assert args.reset_only is True


def test_cli_parser_custom_config():
    parser = create_cli_parser()
    args = parser.parse_args(["--config", "custom.yaml"])
    assert args.config == "custom.yaml"
