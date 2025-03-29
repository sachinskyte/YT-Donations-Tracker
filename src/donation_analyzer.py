import re
from typing import List, Tuple, Dict, Optional
from youtube_comment_downloader import YoutubeCommentDownloader
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import signal
import sys

# Strict currency patterns - symbol based only
CURRENCY_PATTERNS = {
    # USD - Must have $ symbol directly attached to number
    r'\$(\d+(?:\.\d+)?)(?:\s|$)': ('USD', 10000, '$'),
    
    # INR - Must have ₹ symbol directly attached to number
    r'₹(\d+(?:\.\d+)?)(?:\s|$)': ('INR', 100000, '₹'),
    
    # EUR - Handle both formats properly
    r'€(\d+(?:\.\d+)?)(?:\s|$)': ('EUR', 10000, '€'),
    r'(\d+(?:\.\d+)?)\s*€(?:\s|$)': ('EUR', 10000, '€')
}

# Maximum reasonable amounts per currency
MAX_AMOUNTS = {
    'USD': 1000,  # Most donations are under $1000
    'INR': 10000, # Most donations are under ₹10000
    'EUR': 1000   # Most donations are under €1000
}

def signal_handler(signum, frame):
    print("\nStopping comment collection...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def get_exchange_rates() -> Dict[str, float]:
    """Get current exchange rates from ExchangeRate-API with fallback"""
    try:
        print("Fetching current exchange rates...")
        response = requests.get('https://open.er-api.com/v6/latest/USD', timeout=10)
        data = response.json()
        if 'rates' in data and 'INR' in data['rates'] and 'EUR' in data['rates']:
            return {
                'USD': 1.0,
                'INR': data['rates']['INR'],
                'EUR': 1/data['rates']['EUR']  # Convert EUR rate to USD
            }
        raise ValueError("Invalid response format")
    except Exception as e:
        print(f"Warning: Using fallback exchange rates due to error: {str(e)}")
        return {'USD': 1.0, 'INR': 83.0, 'EUR': 1.09}  # Fallback rates

def is_reasonable_amount(amount: float, currency: str) -> bool:
    """Check if donation amount is reasonable for the currency"""
    if amount <= 0:
        return False
    if 1900 <= amount <= 2100:  # Avoid year numbers
        return False
    return amount <= MAX_AMOUNTS.get(currency, 1000)

def extract_amount(match: re.Match) -> float:
    """Extract and validate amount from regex match"""
    try:
        # Get the first non-None group (amount)
        amount_str = next((g for g in match.groups() if g is not None), None)
        if not amount_str:
            return 0.0
        amount = float(amount_str)
        return amount if amount > 0 else 0.0
    except (ValueError, TypeError, StopIteration):
        return 0.0

def process_comment_batch(comments: List[dict], batch_num: int) -> List[Tuple[float, str, str, str]]:
    """Process a batch of comments for donations with strict validation"""
    try:
        donations = []
        
        for comment in comments:
            try:
                if not isinstance(comment, dict) or 'text' not in comment or 'author' not in comment:
                    continue
                    
                text = comment['text']
                author = comment['author']
                
                # Skip likely spam or invalid comments
                if not text or len(text) > 500 or not author:
                    continue
                
                # Process each currency pattern
                for pattern, (currency, _, symbol) in CURRENCY_PATTERNS.items():
                    matches = re.finditer(pattern, text)  # Case sensitive for symbols
                    for match in matches:
                        amount = extract_amount(match)
                        if amount > 0 and is_reasonable_amount(amount, currency):
                            donations.append((amount, currency, match.group(0).strip(), author))
                            print(f"Found {currency} {amount:.2f} from {author}")
                
            except Exception as e:
                print(f"Warning: Error processing comment: {str(e)}")
                continue
        
        return donations
        
    except Exception as e:
        print(f"Error processing batch {batch_num}: {str(e)}")
        return []

def get_video_comments(url: str) -> List[Tuple[float, str, str, str]]:
    """Fetch and process comments with improved error handling"""
    try:
        print(f"\nFetching comments from: {url}")
        downloader = YoutubeCommentDownloader()
        count = 0
        batch = []
        batch_size = 1000
        all_donations = []
        batch_num = 0
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            try:
                # Simpler comment fetching approach
                for comment in downloader.get_comments_from_url(url):
                    if not comment:
                        continue
                        
                    if isinstance(comment, dict) and 'text' in comment and 'author' in comment:
                        batch.append(comment)
                        count += 1
                        
                        if count % 1000 == 0:
                            elapsed = time.time() - start_time
                            rate = count / elapsed if elapsed > 0 else 0
                            print(f"Processed {count} comments... ({rate:.1f} comments/sec)")
                        
                        if len(batch) >= batch_size:
                            batch_num += 1
                            futures.append(executor.submit(process_comment_batch, batch.copy(), batch_num))
                            batch = []
                            
                            # Process completed futures
                            for future in list(as_completed(futures)):
                                try:
                                    result = future.result(timeout=10)
                                    if result:
                                        all_donations.extend(result)
                                    futures.remove(future)
                                except TimeoutError:
                                    print(f"Warning: Batch {batch_num} timed out, skipping...")
                                    futures.remove(future)
                                except Exception as e:
                                    print(f"Warning: Error processing batch: {str(e)}")
                                    futures.remove(future)
                
                # Process remaining batch
                if batch:
                    batch_num += 1
                    futures.append(executor.submit(process_comment_batch, batch, batch_num))
                    
                    for future in as_completed(futures):
                        try:
                            result = future.result(timeout=10)
                            if result:
                                all_donations.extend(result)
                        except TimeoutError:
                            print("Warning: Final batch processing timed out")
                        except Exception as e:
                            print(f"Warning: Error in final batch: {str(e)}")
            
            except KeyboardInterrupt:
                print("\nStopping comment collection...")
                for future in futures:
                    future.cancel()
                executor.shutdown(wait=False)
                return all_donations
            
            except Exception as e:
                print(f"Error fetching comments: {str(e)}")
                for future in futures:
                    future.cancel()
                return all_donations
            
            finally:
                # Ensure proper cleanup
                for future in futures:
                    if not future.done():
                        future.cancel()
        
        if count == 0:
            print("Warning: No comments were processed. The video might be unavailable or have no comments.")
            return []
            
        elapsed = time.time() - start_time
        rate = count / elapsed if elapsed > 0 else 0
        print(f"\nFinished processing {count} comments in {elapsed:.1f} seconds")
        print(f"Average processing rate: {rate:.1f} comments/sec")
        return all_donations
        
    except Exception as e:
        print(f'Error: {str(e)}')
        return []

def format_currency(amount: float, currency: str, original: str, author: str) -> str:
    """Format currency amounts with symbols"""
    try:
        symbols = {'USD': '$', 'INR': '₹', 'EUR': '€'}
        symbol = symbols.get(currency, '')
        return f"{symbol}{amount:.2f} from {author} (original: {original})"
    except Exception:
        return f"Error formatting amount for {author}"

def main():
    print("\nYouTube Donation Analyzer")
    print("=" * 50)
    print("Press Ctrl+C to stop collecting comments at any time\n")
    
    try:
        # Get exchange rates with fallback
        rates = get_exchange_rates()
        
        # Get and process comments
        donations = get_video_comments(VIDEO_URL)
        
        if not donations:
            print("\nNo valid donations found in comments.")
            return
        
        # Show individual donations
        print("\nExtracted donations:")
        print("-" * 50)
        for amount, currency, original, author in donations:
            print(format_currency(amount, currency, original, author))
        
        # Calculate and show totals
        currency_totals = {}
        for amount, currency, _, _ in donations:
            currency_totals[currency] = currency_totals.get(currency, 0) + amount
        
        print("\nTotals by currency:")
        print("-" * 50)
        total_usd = 0.0
        
        for currency, total in sorted(currency_totals.items()):
            if currency == 'USD':
                print(f"USD: ${total:.2f}")
            elif currency == 'INR':
                print(f"INR: ₹{total:.2f}")
            elif currency == 'EUR':
                print(f"EUR: €{total:.2f}")
            else:
                print(f"{currency}: {total:.2f}")
            
            # Convert to USD
            usd_amount = total / rates.get(currency, 1.0)
            total_usd += usd_amount
            print(f"  = ${usd_amount:.2f} USD")
        
        print("\nSummary:")
        print("-" * 50)
        print(f"Total donations found: {len(donations)}")
        print(f"Total value in USD: ${total_usd:.2f}")
    
    except KeyboardInterrupt:
        print("\nStopping analysis...")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()