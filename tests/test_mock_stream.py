import json
import time
from unittest.mock import patch, MagicMock
import pytest
import mock_stream

def test_generate_mock_book():
    # Test that it returns the expected structure
    book = mock_stream.generate_mock_book()
    
    assert "asks" in book
    assert "bids" in book
    
    assert len(book["asks"]) == 10
    assert len(book["bids"]) == 10
    
    # Check that prices are generally correct (asks > bids)
    # The first ask is usually > 100
    assert book["asks"][0][0] > 100.0
    # The first bid is usually < 100
    assert book["bids"][0][0] < 100.0
    
    # Check that lists are formatted as [price, size]
    assert len(book["asks"][0]) == 2
    assert len(book["bids"][0]) == 2
    
    # Check asks are increasing in price
    for i in range(1, len(book["asks"])):
        assert book["asks"][i][0] > book["asks"][i-1][0]
        
    # Check bids are decreasing in price
    for i in range(1, len(book["bids"])):
        assert book["bids"][i][0] < book["bids"][i-1][0]

def test_main_loop():
    # We want to run the loop for a small number of iterations then raise KeyboardInterrupt
    call_count = [0]
    
    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] >= 3:
            raise KeyboardInterrupt()
    
    with patch('time.sleep', side_effect=side_effect), \
         patch('builtins.print') as mock_print, \
         patch('sys.stdout') as mock_stdout:
        
        mock_stream.main()
        
        # It should have printed 3 times before exiting
        assert mock_print.call_count == 3
        mock_stdout.flush.assert_called()
        
        # Check output is valid json
        output = mock_print.call_args[0][0]
        data = json.loads(output)
        assert "asks" in data
        assert "bids" in data

def test_main_loop_exceptions():
    call_count = [0]

    def sleep_side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] >= 3:
            raise KeyboardInterrupt()

    with patch('time.sleep', side_effect=sleep_side_effect), \
         patch('mock_stream.generate_mock_book', side_effect=[
             ValueError("Mock value error"),
             Exception("Mock unexpected error"),
             {"asks": [], "bids": []}
         ]), \
         patch('sys.stderr') as mock_stderr:

        mock_stream.main()

        # Errors should be caught and logged
        assert mock_stderr.write.call_count >= 2
