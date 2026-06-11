# hft-l2-visualizer

![Status](https://img.shields.io/badge/status-active-success.svg)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen.svg)

Real-time L2 orderbook stream parser and ASCII visualizer.

This tool takes incoming L2 order book data streams (in JSON format with bids/asks lists) from standard input and prints an ASCII visualization of the top 5 levels of bids and asks. The output displays prices, sizes, and a horizontal bar representing relative volume.

## Usage

### CLI Instructions

You can use the provided mock stream generator to see the visualization in action. To run the visualizer with the mock data stream, simply pipe the output of `mock_stream.py` into `main.py`:

```bash
python mock_stream.py | python main.py
```

**Running the Visualizer Only:**
If you have your own data source emitting JSON lines, you can pipe it directly to `main.py`:

```bash
cat my_data.jsonl | python main.py
```

**Running the Mock Stream Only:**
To see the raw JSON output being generated, run `mock_stream.py` by itself:

```bash
python mock_stream.py
```

### Input Format

The visualizer (`main.py`) expects JSON lines on standard input. Each JSON line should contain an object with `bids` and `asks` keys. The values should be lists of `[price, size]` pairs.

Example JSON input:
```json
{
  "asks": [[100.05, 10.5], [100.10, 25.0], [100.15, 5.0]],
  "bids": [[99.95, 15.0], [99.90, 8.5], [99.85, 30.0]]
}
```

The visualizer computes a maximum size relative to the visible bids/asks and renders ASCII bars (`█`) scaled to this maximum to provide an intuitive look at the relative depth of the top 5 levels of the order book.

## Configuration Setup

### Logging

The application utilizes structured JSON logging configured to output exclusively to the standard error stream (`sys.stderr`). This design ensures that log messages do not interfere with the primary data stream flowing through standard output (`sys.stdout`) when components are chained via pipes.

- Logs contain timestamps, log levels, logger names, and messages.
- If an exception occurs, the traceback is also captured in the structured JSON log.
- You can configure the default logging level by passing a standard Python `logging` module level (e.g., `logging.DEBUG`, `logging.INFO`) to the `setup_logging()` function in your application entry points.

## API Reference

### `main.py`

*   **`clear_screen() -> None`**: Clears the terminal screen and resets the cursor position using ANSI escape codes.
*   **`format_level(price: float, size: float, max_size: float, is_bid: bool) -> str`**: Formats a single price level, calculating relative volume compared to `max_size` and returning a padded string containing the size, price, and an ASCII bar.
*   **`_parse_level(item: list) -> list | None`**: Helper function to parse an individual `[price, size]` entry, ensuring values are non-negative floats.
*   **`visualize_book(data: dict) -> None`**: Takes a dictionary containing `bids` and `asks`, extracts the top 5 levels, computes maximum relative volume, and prints the fully visualized order book to standard output.
*   **`main() -> None`**: The main execution loop that configures logging, reads JSON lines from standard input, and invokes `visualize_book` for each line.

### `mock_stream.py`

*   **`generate_mock_book() -> dict`**: Generates a mock L2 order book centered around a base price, returning a dictionary containing 10 randomized `asks` and `bids` lists.
*   **`main() -> None`**: Continuously generates a mock book every 0.5 seconds, serializes it to JSON, and prints it to standard output.

### `log_config.py`

*   **`class JSONFormatter(logging.Formatter)`**: A custom logging formatter that parses `LogRecord` objects and outputs structured JSON strings.
    *   **`format(self, record: logging.LogRecord) -> str`**: Formats the log record, adding an ISO formatted timestamp, level, logger name, and message to the JSON payload.
*   **`setup_logging(level: int = logging.INFO) -> None`**: Configures the root logger to use `JSONFormatter` and output logs to `sys.stderr`. This should be called early in the application lifecycle.
