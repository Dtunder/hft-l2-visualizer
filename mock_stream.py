"""
Mock stream generator for real-time L2 order book data.

Generates random mock L2 order book updates in JSON format
and prints them to standard output continuously.
"""

import json
import time
import random
import sys

def generate_mock_book():
    """
    Generates a mock L2 order book with 10 bids and 10 asks.
    
    Returns:
        dict: A dictionary containing 'asks' and 'bids', where each
              is a list of [price, size] float pairs.
    """
    # Base price
    mid_price = 100.0
    
    # Generate asks (prices > mid_price)
    asks = []
    current_ask_price = mid_price + random.uniform(0.01, 0.05)
    for _ in range(10):
        size = random.uniform(1.0, 50.0)
        asks.append([round(current_ask_price, 2), round(size, 2)])
        current_ask_price += random.uniform(0.01, 0.10)
        
    # Generate bids (prices < mid_price)
    bids = []
    current_bid_price = mid_price - random.uniform(0.01, 0.05)
    for _ in range(10):
        size = random.uniform(1.0, 50.0)
        bids.append([round(current_bid_price, 2), round(size, 2)])
        current_bid_price -= random.uniform(0.01, 0.10)
        
    return {
        "asks": asks,
        "bids": bids
    }

def main():
    """
    Main loop to continuously generate and output mock order books.
    Outputs JSON lines to standard output every 0.5 seconds.
    """
    try:
        while True:
            try:
                book = generate_mock_book()
                print(json.dumps(book))
                sys.stdout.flush()
            except (TypeError, ValueError, IOError) as e:
                print(f"Error generating or writing mock data: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Unexpected error in mock stream: {e}", file=sys.stderr)
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
