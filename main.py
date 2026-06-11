import sys
import json
import os

def clear_screen():
    # ANSI escape code to clear the screen and move cursor to top-left
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

def format_level(price, size, max_size, is_bid):
    # Calculate the bar length based on max size, max width is say 20 chars
    max_bar_len = 20
    if max_size == 0:
        bar_len = 0
    else:
        bar_len = int((size / max_size) * max_bar_len)
    
    bar = "█" * bar_len
    
    # Format string. Bids have bar on right, Asks have bar on left maybe?
    # Actually let's just make it uniform: [Bar] [Size] @ [Price]
    # For Asks: [Price] [Size] [Bar] (red?)
    # For Bids: [Price] [Size] [Bar] (green?)
    # Let's keep it simple without color for now, just ASCII
    
    # To make it look like an order book:
    # Asks:  Size  Price | Bar
    # Bids:  Size  Price | Bar
    
    # Standard format: Size (8 chars) Price (8 chars) | Bar
    
    return f"{size:8.2f}  @  {price:8.2f} | {bar}"

def visualize_book(data):
    # Data is expected to be a dict with 'bids' and 'asks' lists
    # Each list contains [price, size]
    
    bids = data.get('bids', [])
    asks = data.get('asks', [])
    
    # Sort bids descending (highest price first)
    bids = sorted(bids, key=lambda x: float(x[0]), reverse=True)[:5]
    # Sort asks ascending (lowest price first)
    asks = sorted(asks, key=lambda x: float(x[0]))[:5]
    
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
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
