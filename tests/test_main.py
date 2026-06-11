import sys
import json
from unittest.mock import patch, MagicMock, call
import pytest
import main

def test_clear_screen():
    with patch('sys.stdout') as mock_stdout:
        main.clear_screen()
        mock_stdout.write.assert_called_once_with('\033[2J\033[H')
        mock_stdout.flush.assert_called_once()

def test_format_level_max_size_zero():
    # When max_size is 0, bar_len should be 0
    result = main.format_level(100.5, 0, 0, is_bid=True)
    expected = "    0.00  @    100.50 | "
    assert result == expected

def test_format_level_normal():
    result = main.format_level(100.5, 5, 10, is_bid=False)
    # size = 5, max_size = 10, max_bar_len = 20 -> bar_len = 10
    expected_bar = "█" * 10
    expected = f"    5.00  @    100.50 | {expected_bar}"
    assert result == expected

def test_format_level_invalid_types():
    with pytest.raises(TypeError):
        main.format_level("100", 5, 10, is_bid=False)
    with pytest.raises(TypeError):
        main.format_level(100.5, "5", 10, is_bid=False)
    with pytest.raises(TypeError):
        main.format_level(100.5, 5, "10", is_bid=False)

def test_format_level_invalid_values():
    with pytest.raises(ValueError):
        main.format_level(100.5, -5, 10, is_bid=False)
    with pytest.raises(ValueError):
        main.format_level(100.5, 5, -10, is_bid=False)

def test_visualize_book():
    data = {
        "bids": [[99.0, 10], [98.0, 5], [97.0, 2], [96.0, 1], [95.0, 1], [94.0, 1]], # More than 5
        "asks": [[101.0, 20], [102.0, 10], [103.0, 5]]
    }
    with patch('main.clear_screen') as mock_clear, \
         patch('builtins.print') as mock_print:
        main.visualize_book(data)
        
        mock_clear.assert_called_once()
        mock_print.assert_called_once()
        
        # Verify output content
        output = mock_print.call_args[0][0]
        assert "=== L2 ORDER BOOK ===" in output
        assert "ASK:    20.00  @    101.00 |" in output
        assert "BID:    10.00  @     99.00 |" in output
        # Should not have the 6th bid
        assert "BID:     1.00  @     94.00 |" not in output

def test_visualize_book_empty():
    data = {}
    with patch('main.clear_screen') as mock_clear, \
         patch('builtins.print') as mock_print:
        main.visualize_book(data)
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        assert "=== L2 ORDER BOOK ===" in output

def test_visualize_book_invalid_types():
    with pytest.raises(TypeError, match="Input data must be a dictionary"):
        main.visualize_book(["not a dict"])
        
    with pytest.raises(TypeError, match="bids and asks must be lists"):
        main.visualize_book({"bids": "not a list", "asks": []})

def test_visualize_book_invalid_levels():
    data = {
        "bids": [[99.0, 10], ["invalid", 5], [97.0, -2], [96.0], "not a list", [95.0, 1]],
        "asks": [[101.0, 20], [102.0, "invalid"]]
    }
    with patch('main.clear_screen'), patch('builtins.print') as mock_print:
        main.visualize_book(data)
        output = mock_print.call_args[0][0]
        
        # Valid bids and asks should still be processed
        assert "BID:    10.00  @     99.00 |" in output
        assert "BID:     1.00  @     95.00 |" in output
        assert "ASK:    20.00  @    101.00 |" in output
        
        # Invalid ones should be skipped
        assert "97.0" not in output  # Negative size
        assert "96.0" not in output  # Missing size
        assert "102.0" not in output # Invalid size type

def test_main_loop():
    import io
    input_data = io.StringIO(
        json.dumps({"bids": [[10, 1]], "asks": [[11, 2]]}) + "\n" +
        "invalid json\n" +
        "\n" +  # Empty line
        json.dumps({"bids": "invalid", "asks": []}) + "\n" +
        json.dumps({"bids": [], "asks": []}) + "\n"
    )
    
    with patch('sys.stdin', input_data), \
         patch('main.visualize_book') as mock_visualize, \
         patch('sys.stderr') as mock_stderr:
         
        # Make visualize_book raise an Exception on the second call to simulate unhandled error
        mock_visualize.side_effect = [None, TypeError("bids and asks must be lists"), None]
         
        main.main()
        
        # visualize_book should be called 3 times total
        assert mock_visualize.call_count == 3
        
        # stderr should have been written to for invalid json and validation error
        assert mock_stderr.write.call_count >= 2

def test_main_keyboard_interrupt():
    def mock_stdin_iter():
        yield json.dumps({"bids": [], "asks": []}) + "\n"
        raise KeyboardInterrupt()

    class MockStdin:
        def __iter__(self):
            return mock_stdin_iter()

    with patch('sys.stdin', MockStdin()), \
         patch('main.visualize_book') as mock_visualize:
        # main() should gracefully exit on KeyboardInterrupt
        main.main()
        
        assert mock_visualize.call_count == 1
