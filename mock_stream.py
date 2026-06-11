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
import os
from typing import Dict, Any
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


def get_config() -> Dict[str, Any]:
    """
    Reads configuration from config.json, environment variables with graceful fallbacks.

    Returns:
        Dict[str, Any]: A dictionary containing configuration values.
    """
    config_file_data: Dict[str, Any] = {}
    try:
        with open("config.json", "r") as f:
            config_file_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load config.json: {e}, using defaults/env vars")

    # STREAM_TIMEOUT
    try:
        stream_timeout_val = os.environ.get(
            "STREAM_TIMEOUT", config_file_data.get("STREAM_TIMEOUT", 5.0)
        )
        stream_timeout = float(stream_timeout_val)
        if stream_timeout <= 0:
            raise ValueError("Timeout must be positive")
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid STREAM_TIMEOUT: {e}, falling back to 5.0")
        stream_timeout = 5.0

    # SIMULATE_FAILURE
    simulate_failure_val = os.environ.get(
        "SIMULATE_FAILURE", config_file_data.get("SIMULATE_FAILURE", False)
    )
    if isinstance(simulate_failure_val, str):
        simulate_failure = simulate_failure_val.lower() in ("true", "1", "yes")
    else:
        simulate_failure = bool(simulate_failure_val)

    # UPDATE_INTERVAL
    try:
        update_interval_val = os.environ.get(
            "UPDATE_INTERVAL", config_file_data.get("UPDATE_INTERVAL", 0.5)
        )
        update_interval = float(update_interval_val)
        if update_interval <= 0:
            raise ValueError("Interval must be positive")
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid UPDATE_INTERVAL: {e}, falling back to 0.5")
        update_interval = 0.5

    return {
        "stream_timeout": stream_timeout,
        "simulate_failure": simulate_failure,
        "update_interval": update_interval,
    }


def main() -> None:
    """
    Main execution loop to continuously generate and output mock order book data.

    This function sets up structured JSON logging to stderr. In an infinite loop,
    it generates a mock L2 order book, serializes it to a JSON string, and prints
    it to standard output. A configurable delay is introduced between each output
    to simulate a continuous, real-time data stream. Exceptions are caught and logged.

    If `SIMULATE_FAILURE` is set to true in config or env, it will randomly
    insert long delays to simulate network timeouts, or output malformed JSON
    to simulate data corruption.

    Returns:
        None
    """
    setup_logging()
    logger.info("Starting mock L2 order book stream generator")

    config = get_config()
    simulate_failure = config["simulate_failure"]
    update_interval = config["update_interval"]
    stream_timeout = config["stream_timeout"]

    try:
        while True:
            try:
                if simulate_failure and random.random() < 0.1:
                    # 10% chance to simulate a long network delay
                    logger.warning("Simulating network delay...")
                    time.sleep(stream_timeout + 1.0)  # Longer than configured timeout
                elif simulate_failure and random.random() < 0.1:
                    # 10% chance to simulate malformed data
                    logger.warning("Simulating malformed data...")
                    print('{"asks": [[100, "bad_size"]], "bids": "missing_data"')
                    sys.stdout.flush()
                else:
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
                logger.error(f"Unexpected error in mock stream: {e}", exc_info=True)

            time.sleep(update_interval)
    except KeyboardInterrupt:
        logger.info("Mock stream generator shutting down gracefully")


if __name__ == "__main__":
    main()
