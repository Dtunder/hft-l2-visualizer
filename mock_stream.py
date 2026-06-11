"""
Mock stream generator for real-time L2 order book data.

Generates random mock L2 order book updates in JSON format
and prints them to standard output continuously.
"""

import json
import time
import random
import sys
import logging
from log_config import setup_logging

logger = logging.getLogger(__name__)


def generate_mock_book() -> dict:
    """
    Generates a mock L2 order book structure with 10 bids and 10 asks.

    This function creates a randomly populated L2 order book centered around
    a base mid-price. It sequentially generates asks moving upwards in price
    and bids moving downwards. The resulting structure mimics real-time market data.

    Returns:
        dict: A dictionary containing 'asks' and 'bids' keys. The value for each
              key is a list of lists, where each inner list contains two float
              values representing `[price, size]`.
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

    return {"asks": asks, "bids": bids}


def main() -> None:
    """
    Main execution loop to continuously generate and output mock order book data.

    This function sets up structured JSON logging to stderr. In an infinite loop,
    it generates a mock L2 order book, serializes it to a JSON string, and prints
    it to standard output. A 0.5-second delay is introduced between each output
    to simulate a continuous, real-time data stream. Exceptions are caught and logged.

    Returns:
        None
    """
    setup_logging()
    logger.info("Starting mock L2 order book stream generator")
    try:
        while True:
            try:
                book = generate_mock_book()
                print(json.dumps(book))
                sys.stdout.flush()
                logger.debug("Successfully generated and output mock book")
            except (TypeError, ValueError, IOError) as e:
                logger.error(
                    f"Error generating or writing mock data: {e}",
                    exc_info=True,
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error in mock stream: {e}", exc_info=True
                )

            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Mock stream generator shutting down gracefully")


if __name__ == "__main__":
    main()
