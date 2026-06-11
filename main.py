import sys
import json
import heapq

def clear_screen():
    """Clears the terminal screen and moves the cursor to the top-left."""
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

def format_level(price, size, max_size, is_bid):
    """
    Formats a single price level for visualization.

    Args:
        price (float): The price level.
        size (float): The size/volume at the price level.
        max_size (float): The maximum size across all visualized levels.
        is_bid (bool): True if the level is a bid, False if it is an ask.

    Returns:
        str: A formatted string containing size, price, and a volume bar.
    """
    if not isinstance(price, (int, float)) or not isinstance(size, (int, float)) or not isinstance(max_size, (int, float)):
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

def _parse_level(item):
    """Helper to parse a single level. Returns [price, size] or None if invalid."""
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        try:
            price = float(item[0])
            size = float(item[1])
            if price >= 0 and size >= 0:
                return [price, size]
        except (ValueError, TypeError):
            pass
    return None

def visualize_book(data):
    """
    Parses and visualizes the top 5 levels of an L2 order book.

    Args:
        data (dict): A dictionary containing 'bids' and 'asks' lists of [price, size].
    """
    if not isinstance(data, dict):
        raise TypeError("Input data must be a dictionary")
    
    raw_bids = data.get('bids', [])
    raw_asks = data.get('asks', [])
    
    if not isinstance(raw_bids, list) or not isinstance(raw_asks, list):
        raise TypeError("bids and asks must be lists")

    # Use list comprehension to parse efficiently
    bids = [parsed for item in raw_bids if (parsed := _parse_level(item)) is not None]
    asks = [parsed for item in raw_asks if (parsed := _parse_level(item)) is not None]

    # Get top 5 bids (highest price) using heapq.nlargest
    bids = heapq.nlargest(5, bids, key=lambda x: x[0])
    
    # Get top 5 asks (lowest price) using heapq.nsmallest
    asks = heapq.nsmallest(5, asks, key=lambda x: x[0])
    
    # To print order book, usually asks are on top (highest to lowest), then bids (highest to lowest)
    # Let's reverse asks to print highest ask at the top
    asks = asks[::-1]
    
    # Find max size to normalize the bars, computing efficiently via generator
    max_size = max((x[1] for x in bids + asks), default=1.0)
    
    # Build output
    output = [
        "=== L2 ORDER BOOK ===",
        f"{'SIZE':>8}     {'PRICE':>8} | {'VOLUME'}",
        "-" * 40
    ]
    
    # Print Asks
    for price, size in asks:
        output.append("ASK: " + format_level(float(price), float(size), max_size, is_bid=False))
        
    output.append("-" * 40)
    
    # Print Bids
    for price, size in bids:
        output.append("BID: " + format_level(float(price), float(size), max_size, is_bid=True))
        
    output.append("=====================")
    
    # Print everything
    clear_screen()
    print('\n'.join(output))

def main():
    """Main loop reading from stdin and visualizing real-time order books."""
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                visualize_book(data)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON: {line}", file=sys.stderr)
            except (TypeError, ValueError) as e:
                print(f"Data validation error: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Unexpected error: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
