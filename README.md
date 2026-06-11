# hft-l2-visualizer

Real-time L2 orderbook stream parser and ASCII visualizer.

This tool takes incoming L2 order book data streams (in JSON format with bids/asks lists) from standard input and prints an ASCII visualization of the top 5 levels of bids and asks. The output displays prices, sizes, and a horizontal bar representing relative volume.

## Usage

You can use the provided mock stream generator to see it in action:

```bash
python mock_stream.py | python main.py
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
