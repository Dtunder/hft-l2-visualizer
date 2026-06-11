import sys
import json
import heapq
import logging
import os
import threading
import queue
from typing import TextIO, Iterator, Dict, Any, Optional

from log_config import setup_logging

logger = logging.getLogger(__name__)


def get_config() -> Dict[str, Any]:
    """
    Reads configuration from environment variables with graceful fallbacks.

    This function attempts to read 'STREAM_TIMEOUT' and 'STREAM_RETRIES'
    from the environment. If they are missing or malformed, it falls back
    to default values and logs a warning.

    Returns:
        Dict[str, Any]: A dictionary containing 'timeout' (float) and 'retries' (int).
    """
    try:
        timeout = float(os.environ.get("STREAM_TIMEOUT", "5.0"))
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
    except ValueError as e:
        logger.warning(f"Invalid STREAM_TIMEOUT: {e}, falling back to 5.0")
        timeout = 5.0

    try:
        retries = int(os.environ.get("STREAM_RETRIES", "3"))
        if retries < 0:
            raise ValueError("Retries cannot be negative")
    except ValueError as e:
        logger.warning(f"Invalid STREAM_RETRIES: {e}, falling back to 3")
        retries = 3

    return {"timeout": timeout, "retries": retries}


class ResilientStreamReader:
    """
    A stream reader that incorporates resilience by handling timeouts and retries.

    This class reads from the provided stream in a background thread and places
    lines into a queue. If no data is read within the specified timeout, it will
    retry up to the configured number of times before ultimately stopping.
    """

    def __init__(self, stream: TextIO, timeout: float = 5.0, retries: int = 3) -> None:
        """
        Initializes the ResilientStreamReader.

        Args:
            stream (TextIO): The input text stream to read from.
            timeout (float): The maximum time in seconds to wait for a line.
            retries (int): The maximum number of consecutive timeouts allowed.
        """
        self.stream: TextIO = stream
        self.timeout: float = timeout
        self.max_retries: int = retries
        self.queue: queue.Queue = queue.Queue()
        self.stop_event: threading.Event = threading.Event()
        self.thread: threading.Thread = threading.Thread(
            target=self._read_loop, daemon=True
        )
        self.thread.start()

    def _read_loop(self) -> None:
        """
        The background loop that continuously reads lines from the stream.

        Returns:
            None
        """
        try:
            for line in self.stream:
                if self.stop_event.is_set():
                    break
                self.queue.put(line)
        except Exception as e:
            logger.error(f"Stream read error: {e}")
        finally:
            self.queue.put(None)  # EOF marker

    def __iter__(self) -> Iterator[str]:
        """
        Iterates over lines from the stream, respecting timeouts and retries.

        Yields:
            str: The next line from the stream.

        Returns:
            None
        """
        retries_left = self.max_retries
        while not self.stop_event.is_set():
            try:
                line: Optional[str] = self.queue.get(timeout=self.timeout)
                if line is None:
                    break
                retries_left = self.max_retries  # Reset retries on successful read
                yield line
            except queue.Empty:
                if retries_left > 0:
                    logger.warning(
                        f"Stream read timeout. Retrying... ({retries_left} left)"
                    )
                    retries_left -= 1
                else:
                    logger.error("Max retries reached due to stream timeout. Exiting.")
                    break

    def stop(self) -> None:
        """
        Signals the background reader to stop and exit.

        Returns:
            None
        """
        self.stop_event.set()


def clear_screen() -> None:
    """
    Clears the terminal screen and moves the cursor to the top-left.

    This uses ANSI escape codes to clear the screen (`\\033[2J`) and
    reset the cursor position (`\\033[H`). It flushes standard output
    immediately.

    Returns:
        None
    """
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def format_level(price: float, size: float, max_size: float, is_bid: bool) -> str:
    """
    Formats a single price level for text visualization.

    This function computes the relative volume of a price level compared to the maximum
    size across all visible levels, and renders it as an ASCII bar. The returned string
    presents the size, price, and visual bar in a standardized 8-character-wide block format.

    Args:
        price (float): The price level value.
        size (float): The size/volume available at the price level.
        max_size (float): The maximum size across all visualized levels to use for bar scaling.
        is_bid (bool): True if the level is a bid, False if it is an ask.

    Returns:
        str: A formatted string containing the size, price, and the corresponding visual volume bar.

    Raises:
        TypeError: If `price`, `size`, or `max_size` are not numeric types.
        ValueError: If `size` or `max_size` are negative.
    """
    if (
        not isinstance(price, (int, float))
        or not isinstance(size, (int, float))
        or not isinstance(max_size, (int, float))
    ):
        raise TypeError("price, size, and max_size must be numeric")
    if size < 0 or max_size < 0:
        raise ValueError("size and max_size must be non-negative")

    # Calculate the bar length based on max size, max width is 20 chars
    max_bar_len = 20
    if max_size == 0:
        bar_len = 0
    else:
        bar_len = int((size / max_size) * max_bar_len)

    bar = "█" * bar_len

    # Standard format: Size (8 chars) Price (8 chars) | Bar
    return f"{size:8.2f}  @  {price:8.2f} | {bar}"


def _parse_level(item: list) -> list | None:
    """
    Helper function to parse a single price level entry.

    Validates that the input is a sequence of at least two items, and attempts
    to cast the first two items to floats representing `price` and `size`. Both values
    must be non-negative.

    Args:
        item (list or tuple): A single price level entry, typically a [price, size] pair.

    Returns:
        list or None: A list `[price, size]` parsed as floats, or `None` if the input is invalid.
    """
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        try:
            price = float(item[0])
            size = float(item[1])
            if price >= 0 and size >= 0:
                return [price, size]
        except (ValueError, TypeError):
            pass
    return None


def visualize_book(data: dict) -> None:
    """
    Parses and visualizes the top 5 levels of an L2 order book.

    The function extracts bids and asks from the provided dictionary, parses them,
    and sorts them to find the top 5 levels (highest bids and lowest asks). It then
    computes the maximum volume across these levels to relatively scale the ASCII bars
    and prints the fully formatted book to standard output.

    Args:
        data (dict): A dictionary containing 'bids' and 'asks' keys, each associated
                     with a list of [price, size] pairs.

    Raises:
        TypeError: If the input `data` is not a dictionary, or if `bids` and `asks`
                   are not lists.

    Returns:
        None
    """
    if not isinstance(data, dict):
        raise TypeError("Input data must be a dictionary")

    raw_bids = data.get("bids", [])
    raw_asks = data.get("asks", [])

    if not isinstance(raw_bids, list) or not isinstance(raw_asks, list):
        raise TypeError("bids and asks must be lists")

    # Use list comprehension to parse efficiently
    bids = [parsed for item in raw_bids if (parsed := _parse_level(item)) is not None]
    asks = [parsed for item in raw_asks if (parsed := _parse_level(item)) is not None]

    # Get top 5 bids (highest price) using heapq.nlargest
    bids = heapq.nlargest(5, bids, key=lambda x: x[0])

    # Get top 5 asks (lowest price) using heapq.nsmallest
    asks = heapq.nsmallest(5, asks, key=lambda x: x[0])

    # To print order book, usually asks are on top, then bids
    # Let's reverse asks to print highest ask at the top
    asks = asks[::-1]

    # Find max size to normalize the bars, computing efficiently via generator
    max_size = max((x[1] for x in bids + asks), default=1.0)

    # Build output
    output = [
        "=== L2 ORDER BOOK ===",
        f"{'SIZE':>8}     {'PRICE':>8} | {'VOLUME'}",
        "-" * 40,
    ]

    # Print Asks
    for price, size in asks:
        output.append(
            "ASK: " + format_level(float(price), float(size), max_size, is_bid=False)
        )

    output.append("-" * 40)

    # Print Bids
    for price, size in bids:
        output.append(
            "BID: " + format_level(float(price), float(size), max_size, is_bid=True)
        )

    output.append("=====================")

    # Print everything
    clear_screen()
    print("\n".join(output))


def main() -> None:
    """
    Main execution loop for reading from standard input and visualizing the order book.

    This function sets up structured JSON logging to stderr, then continually reads
    JSON-formatted lines from standard input (`sys.stdin`) using a resilient reader.
    Each line is parsed and visualized as an L2 order book. If the data is malformed
    or an error occurs, it is logged appropriately and the loop continues until interrupted.

    Returns:
        None
    """
    setup_logging()
    logger.info("Starting L2 order book visualizer")
    config = get_config()
    reader = ResilientStreamReader(
        sys.stdin, timeout=config["timeout"], retries=config["retries"]
    )

    try:
        for line in reader:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                visualize_book(data)
                logger.debug("Successfully visualized book update")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {line}")
            except (TypeError, ValueError) as e:
                logger.error(f"Data validation error: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Visualizer shutting down gracefully")
    finally:
        reader.stop()


if __name__ == "__main__":
    main()
