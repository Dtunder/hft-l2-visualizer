import sys
import json
import os

def clear_screen():
    # ANSI escape code to clear the screen and move cursor to top-left
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

def format_level(price, size, max_size, is_bid):
    if not isinstance(price, (int, float)) or not isinstance(size, (int, float)) or not isinstance(max_size, (int, float)):
        raise TypeError("price, size, and max_size must be numeric")
    if size < 0 or max_size < 0:
        raise ValueError("size and max_size must be non-negative")

    # Calculate the bar length based on max size, max width is say 20 chars
    max_bar_len = 20
    if max_size == 0:
        bar_len = 0
    else:
        bar_len = int((size / max_size) * max_bar_len)
    
    bar = "█" * bar_len
    
    # Standard format: Size (8 chars) Price (8 chars) | Bar
    return f"{size:8.2f}  @  {price:8.2f} | {bar}"

def visualize_book(data):
    if not isinstance(data, dict):
        raise TypeError("Input data must be a dictionary")
    
    raw_bids = data.get('bids', [])
    raw_asks = data.get('asks', [])
    
    if not isinstance(raw_bids, list) or not isinstance(raw_asks, list):
        raise TypeError("bids and asks must be lists")

    def parse_levels(levels):
        parsed = []
        for item in levels:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                try:
                    price = float(item[0])
                    size = float(item[1])
                    if price < 0 or size < 0:
                        continue
                    parsed.append([price, size])
                except (ValueError, TypeError):
                    continue
        return parsed

    bids = parse_levels(raw_bids)
    asks = parse_levels(raw_asks)
    
    # Sort bids descending (highest price first)
    bids = sorted(bids, key=lambda x: x[0], reverse=True)[:5]
    # Sort asks ascending (lowest price first)
    asks = sorted(asks, key=lambda x: x[0])[:5]
    
    # To print order book, usually asks are on top (highest to lowest), then bids (highest to lowest)
    # Let's reverse asks to print highest ask at the top
    asks = asks[::-1]
    
    # Find max size to normalize the bars
    all_sizes = [float(x[1]) for x in bids] + [float(x[1]) for x in asks]
    max_size = max(all_sizes) if all_sizes else 1.0
    
    # Build output
    output = []
    output.append("=== L2 ORDER BOOK ===")
    output.append(f"{'SIZE':>8}     {'PRICE':>8} | {'VOLUME'}")
    output.append("-" * 40)
    
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
