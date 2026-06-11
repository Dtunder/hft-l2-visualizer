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
    import io
    import logging

    input_data = io.StringIO(
        json.dumps({"bids": [[10, 1]], "asks": [[11, 2]]})
        + "\n"
        + "invalid json\n"
        + "\n"  # Empty line
        + json.dumps({"bids": "invalid", "asks": []})
        + "\n"
        + json.dumps({"bids": [], "asks": []})
        + "\n"
    )

    with patch("sys.stdin", input_data), patch(
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
            "Failed to parse JSON" in record.message
            for record in caplog.records
        )
        assert any(
            "Data validation error" in record.message
            for record in caplog.records
        )


def test_main_keyboard_interrupt(caplog: pytest.LogCaptureFixture) -> None:
    import logging

    def mock_stdin_iter():
        yield json.dumps({"bids": [], "asks": []}) + "\n"
        raise KeyboardInterrupt()

    class MockStdin:
        def __iter__(self):
            return mock_stdin_iter()

    with patch("sys.stdin", MockStdin()), patch(
        "main.visualize_book"
    ) as mock_visualize:

        with caplog.at_level(logging.INFO):
            # main() should gracefully exit on KeyboardInterrupt
            main.main()

        assert mock_visualize.call_count == 1
        assert any(
            "Visualizer shutting down gracefully" in record.message
            for record in caplog.records
        )


def test_main_loop_unexpected_error(caplog: pytest.LogCaptureFixture) -> None:
    import io
    import logging

    input_data = io.StringIO(
        json.dumps({"bids": [[10, 1]], "asks": [[11, 2]]}) + "\n"
    )

    with patch("sys.stdin", input_data), patch(
        "main.visualize_book"
    ) as mock_visualize:

        mock_visualize.side_effect = Exception("Unexpected")

        with caplog.at_level(logging.ERROR):
            main.main()

        assert any(
            "Unexpected error" in record.message for record in caplog.records
        )
