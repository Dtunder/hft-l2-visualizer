import json
from unittest.mock import patch
import pytest
import main


def test_clear_screen() -> None:
    with patch("sys.stdout") as mock_stdout:
        main.clear_screen()
        mock_stdout.write.assert_called_once_with("\033[2J\033[H")
        mock_stdout.flush.assert_called_once()


def test_format_level_max_size_zero() -> None:
    # When max_size is 0, bar_len should be 0
    result = main.format_level(100.5, 0, 0, is_bid=True)
    expected = "    0.00  @    100.50 | "
    assert result == expected


def test_format_level_normal() -> None:
    result = main.format_level(100.5, 5, 10, is_bid=False)
    # size = 5, max_size = 10, max_bar_len = 20 -> bar_len = 10
    expected_bar = "█" * 10
    expected = f"    5.00  @    100.50 | {expected_bar}"
    assert result == expected


def test_format_level_invalid_types() -> None:
    with pytest.raises(TypeError):
        main.format_level("100", 5, 10, is_bid=False)  # type: ignore
    with pytest.raises(TypeError):
        main.format_level(100.5, "5", 10, is_bid=False)  # type: ignore
    with pytest.raises(TypeError):
        main.format_level(100.5, 5, "10", is_bid=False)  # type: ignore


def test_format_level_invalid_values() -> None:
    with pytest.raises(ValueError):
        main.format_level(100.5, -5, 10, is_bid=False)
    with pytest.raises(ValueError):
        main.format_level(100.5, 5, -10, is_bid=False)


def test_visualize_book() -> None:
    data = {
        "bids": [
            [99.0, 10],
            [98.0, 5],
            [97.0, 2],
            [96.0, 1],
            [95.0, 1],
            [94.0, 1],
        ],  # More than 5
        "asks": [[101.0, 20], [102.0, 10], [103.0, 5]],
    }
    with patch("main.clear_screen"), patch("builtins.print") as mock_print:
        main.visualize_book(data)

        mock_print.assert_called_once()

        # Verify output content
        output = mock_print.call_args[0][0]
        assert "=== L2 ORDER BOOK ===" in output
        assert "ASK:    20.00  @    101.00 |" in output
        assert "BID:    10.00  @     99.00 |" in output
        # Should not have the 6th bid
        assert "BID:     1.00  @     94.00 |" not in output


def test_visualize_book_empty() -> None:
    data: dict = {}
    with patch("main.clear_screen"), patch("builtins.print") as mock_print:
        main.visualize_book(data)
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        assert "=== L2 ORDER BOOK ===" in output


def test_visualize_book_invalid_types() -> None:
    with pytest.raises(TypeError, match="Input data must be a dictionary"):
        main.visualize_book(["not a dict"])  # type: ignore

    with pytest.raises(TypeError, match="bids and asks must be lists"):
        main.visualize_book({"bids": "not a list", "asks": []})


def test_visualize_book_invalid_levels() -> None:
    data = {
        "bids": [
            [99.0, 10],
            ["invalid", 5],
            [97.0, -2],
            [96.0],
            "not a list",
            [95.0, 1],
        ],
        "asks": [[101.0, 20], [102.0, "invalid"]],
    }
    with patch("main.clear_screen"), patch("builtins.print") as mock_print:
        main.visualize_book(data)
        output = mock_print.call_args[0][0]

        # Valid bids and asks should still be processed
        assert "BID:    10.00  @     99.00 |" in output
        assert "BID:     1.00  @     95.00 |" in output
        assert "ASK:    20.00  @    101.00 |" in output

        # Invalid ones should be skipped
        assert "97.0" not in output  # Negative size
        assert "96.0" not in output  # Missing size
        assert "102.0" not in output  # Invalid size type


def test_main_loop(caplog: pytest.LogCaptureFixture) -> None:
    import logging

    lines = [
        json.dumps({"bids": [[10, 1]], "asks": [[11, 2]]}) + "\n",
        "invalid json\n",
        "\n",  # Empty line
        json.dumps({"bids": "invalid", "asks": []}) + "\n",
        json.dumps({"bids": [], "asks": []}) + "\n",
    ]

    class MockReader:
        def __init__(self, *args, **kwargs):
            pass

        def __iter__(self):
            return iter(lines)

        def stop(self):
            pass

    with patch("main.ResilientStreamReader", MockReader), patch(
        "main.visualize_book"
    ) as mock_visualize:
        # Make visualize_book raise an Exception on the second call to simulate unhandled error
        mock_visualize.side_effect = [
            None,
            TypeError("bids and asks must be lists"),
            None,
        ]

        with caplog.at_level(logging.ERROR):
            main.main()

        # visualize_book should be called 3 times total
        assert mock_visualize.call_count == 3

        # Check logs for invalid json and validation error
        assert any(
            "Failed to parse JSON" in record.message for record in caplog.records
        )
        assert any(
            "Data validation error" in record.message for record in caplog.records
        )


def test_main_keyboard_interrupt(caplog: pytest.LogCaptureFixture) -> None:
    import logging

    class MockReader:
        def __init__(self, *args, **kwargs):
            self.stopped = False

        def __iter__(self):
            yield json.dumps({"bids": [], "asks": []}) + "\n"
            raise KeyboardInterrupt()

        def stop(self):
            self.stopped = True

    mock_reader = MockReader()

    with patch("main.ResilientStreamReader", return_value=mock_reader), patch(
        "main.visualize_book"
    ) as mock_visualize:
        with caplog.at_level(logging.INFO):
            main.main()

        assert mock_visualize.call_count == 1
        assert mock_reader.stopped
        assert any(
            "Visualizer shutting down gracefully" in record.message
            for record in caplog.records
        )


def test_main_loop_unexpected_error(caplog: pytest.LogCaptureFixture) -> None:
    import logging

    lines = [json.dumps({"bids": [[10, 1]], "asks": [[11, 2]]}) + "\n"]

    class MockReader:
        def __init__(self, *args, **kwargs):
            pass

        def __iter__(self):
            return iter(lines)

        def stop(self):
            pass

    with patch("main.ResilientStreamReader", MockReader), patch(
        "main.visualize_book"
    ) as mock_visualize:
        mock_visualize.side_effect = Exception("Unexpected")

        with caplog.at_level(logging.ERROR):
            main.main()

        assert any("Unexpected error" in record.message for record in caplog.records)


def test_get_config_defaults() -> None:
    with patch.dict("os.environ", clear=True), patch(
        "builtins.open", side_effect=FileNotFoundError
    ):
        config = main.get_config()
        assert config["timeout"] == 5.0
        assert config["retries"] == 3


def test_get_config_custom_env() -> None:
    with patch.dict(
        "os.environ", {"STREAM_TIMEOUT": "2.5", "STREAM_RETRIES": "5"}
    ), patch("builtins.open", side_effect=FileNotFoundError):
        config = main.get_config()
        assert config["timeout"] == 2.5
        assert config["retries"] == 5


def test_get_config_custom_json() -> None:
    import json

    mock_json = json.dumps({"STREAM_TIMEOUT": 1.5, "STREAM_RETRIES": 10})
    from unittest.mock import mock_open

    with patch.dict("os.environ", clear=True), patch(
        "builtins.open", mock_open(read_data=mock_json)
    ):
        config = main.get_config()
        assert config["timeout"] == 1.5
        assert config["retries"] == 10


def test_get_config_custom_json_env_override() -> None:
    import json

    mock_json = json.dumps({"STREAM_TIMEOUT": 1.5, "STREAM_RETRIES": 10})
    from unittest.mock import mock_open

    with patch.dict("os.environ", {"STREAM_TIMEOUT": "2.5"}), patch(
        "builtins.open", mock_open(read_data=mock_json)
    ):
        config = main.get_config()
        assert config["timeout"] == 2.5
        assert config["retries"] == 10


def test_get_config_invalid() -> None:
    with patch.dict(
        "os.environ", {"STREAM_TIMEOUT": "-1.0", "STREAM_RETRIES": "invalid"}
    ), patch("builtins.open", side_effect=FileNotFoundError):
        config = main.get_config()
        assert config["timeout"] == 5.0
        assert config["retries"] == 3


def test_resilient_stream_reader_normal() -> None:
    import io
    import time

    class DummyStream(io.StringIO):
        def __init__(self, data):
            super().__init__(data)
            self.lines = data.splitlines(keepends=True)
            self.idx = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.idx < len(self.lines):
                # Small sleep to ensure thread switching
                time.sleep(0.01)
                line = self.lines[self.idx]
                self.idx += 1
                return line
            raise StopIteration

    stream = DummyStream("line1\nline2\nline3\n")
    reader = main.ResilientStreamReader(stream, timeout=1.0, retries=1)

    result = list(reader)
    assert result == ["line1\n", "line2\n", "line3\n"]
    reader.stop()


def test_resilient_stream_reader_timeout(caplog) -> None:
    import io
    import time
    import logging

    class SlowStream(io.StringIO):
        def __init__(self):
            super().__init__()

        def __iter__(self):
            return self

        def __next__(self):
            # Hang forever to trigger timeout
            time.sleep(10)
            raise StopIteration

    stream = SlowStream()
    # Fast timeout to trigger failure quickly
    reader = main.ResilientStreamReader(stream, timeout=0.1, retries=1)

    with caplog.at_level(logging.WARNING):
        result = list(reader)

    assert result == []
    assert any("Stream read timeout. Retrying" in r.message for r in caplog.records)
    assert any("Max retries reached" in r.message for r in caplog.records)

    reader.stop()
