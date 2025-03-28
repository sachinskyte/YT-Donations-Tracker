import re
from typing import List, Tuple, Dict, Optional
from youtube_comment_downloader import YoutubeCommentDownloader
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import signal
import sys
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config = {
            'max_workers': 4,
            'batch_size': 1000,
            'batch_timeout': 10,
            'processing_timeout': 5,
            'max_usd_amount': 10000,
            'max_inr_amount': 100000,
            'exchange_rate_api': 'https://open.er-api.com/v6/latest/USD',
            'currency_patterns': {
                # Dollars ($) - must have $ symbol
                r'(?:donated?|sent|giving|gave|sending|paid|tipped|supporting|here\'s)\s+\$(\d+(?:\.\d{2})?)|(?<=^|\s)\$(\d+(?:\.\d{2})?)(?=\s|$)': ('USD', 10000, '$'),
                
                # Indian Rupees (₹) - must have ₹ symbol or Rs.
                r'(?:donated?|sent|giving|gave|sending|paid|tipped|supporting|here\'s)\s+(?:rs\.|₹)(\d+(?:\.\d{2})?)|(?<=^|\s)(?:rs\.|₹)(\d+(?:\.\d{2})?)(?=\s|$)': ('INR', 100000, '₹'),
            }
        }
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load configuration from a JSON file"""
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                self.config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {str(e)}")
            logger.warning("Using default configuration")

class DonationAnalyzer:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the donation analyzer with optional config"""
        self.config = Config(config_path)
        signal.signal(signal.SIGINT, self._signal_handler)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
        
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        self.logger.info("\nStopping comment collection...")
        sys.exit(0)

    def get_exchange_rates(self) -> Dict[str, float]:
        """Get current exchange rates from API"""
        try:
            response = requests.get(self.config.config['exchange_rate_api'])
            data = response.json()
            if data['result'] == 'success':
                return data['rates']
            return {}
        except Exception as e:
            self.logger.error(f"Error fetching exchange rates: {str(e)}")
            return {}

    def convert_to_usd(self, amount: float, currency: str, rates: Dict[str, float]) -> float:
        """Convert amount from given currency to USD"""
        if currency == 'USD':
            return amount
        if currency in rates:
            return amount / rates[currency]
        return 0.0

    def process_comment_batch(self, comments: List[dict], batch_num: int) -> List[Tuple[float, str, str, str]]:
        """Process a batch of comments for donations"""
        try:
            donations = []
            
            for comment in comments:
                text = comment['text'].lower()
                author = comment['author']
                
                if len(text) > 500:  # Skip likely spam
                    continue
                
                # Check each currency pattern
                for pattern, (currency, max_amount, symbol) in self.config.config['currency_patterns'].items():
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        try:
                            # Get the first non-None group (amount)
                            amount_str = next(g for g in match.groups() if g is not None)
                            amount = float(amount_str)
                            
                            # Validate amount
                            if 0 < amount <= max_amount and not (1900 <= amount <= 2100):
                                donations.append((amount, currency, match.group(0), author))
                                self.logger.debug(f"Found {currency} {amount} from {author}")
                        except (ValueError, StopIteration):
                            continue
            
            return donations
        except Exception as e:
            self.logger.error(f"Error processing batch {batch_num}: {str(e)}")
            return []

    def get_video_comments(self, video_url: str) -> List[Tuple[float, str, str, str]]:
        """Fetch and process ALL comments from a YouTube video"""
        try:
            self.logger.info(f"Fetching comments from: {video_url}")
            downloader = YoutubeCommentDownloader()
            count = 0
            batch = []
            all_donations = []
            batch_num = 0
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=self.config.config['max_workers']) as executor:
                futures = []
                
                try:
                    for comment in downloader.get_comments_from_url(video_url):
                        if 'text' in comment and 'author' in comment:
                            batch.append(comment)
                            count += 1
                            
                            if count % self.config.config['batch_size'] == 0:
                                elapsed = time.time() - start_time
                                rate = count / elapsed
                                self.logger.info(f"Processed {count} comments... ({rate:.1f} comments/sec)")
                            
                            if len(batch) >= self.config.config['batch_size']:
                                batch_num += 1
                                futures.append(
                                    executor.submit(
                                        self.process_comment_batch, 
                                        batch.copy(),
                                        batch_num
                                    )
                                )
                                batch = []
                                
                                # Process completed futures
                                done, not_done = futures[:-1], futures[-1:]
                                for future in as_completed(done, timeout=self.config.config['batch_timeout']):
                                    try:
                                        result = future.result(timeout=self.config.config['processing_timeout'])
                                        all_donations.extend(result)
                                    except TimeoutError:
                                        self.logger.warning(f"Batch {batch_num} timed out, skipping...")
                                    except Exception as e:
                                        self.logger.error(f"Error processing batch: {str(e)}")
                                futures = not_done
                    
                    # Process remaining batch
                    if batch:
                        batch_num += 1
                        futures.append(executor.submit(self.process_comment_batch, batch, batch_num))
                    
                    # Process remaining futures
                    for future in as_completed(futures, timeout=30):
                        try:
                            result = future.result(timeout=self.config.config['processing_timeout'])
                            all_donations.extend(result)
                        except TimeoutError:
                            self.logger.warning("Final batch processing timed out")
                        except Exception as e:
                            self.logger.error(f"Error in final batch: {str(e)}")
                
                except KeyboardInterrupt:
                    self.logger.info("\nStopping comment collection...")
                    executor.shutdown(wait=False)
                    return all_donations
                
                except Exception as e:
                    self.logger.error(f"Error fetching comments: {str(e)}")
                    return all_donations
            
            elapsed = time.time() - start_time
            rate = count / elapsed
            self.logger.info(f"\nFinished processing {count} comments in {elapsed:.1f} seconds")
            self.logger.info(f"Average processing rate: {rate:.1f} comments/sec")
            return all_donations
            
        except Exception as e:
            self.logger.error(f'An error occurred: {str(e)}')
            return []

    def format_currency(self, amount: float, currency: str, original: str, author: str) -> str:
        """Format currency amounts with symbols"""
        if currency == 'USD':
            return f"${amount:.2f} from {author} (original: {original})"
        else:
            return f"₹{amount:.2f} from {author} (original: {original})"

    def analyze_video(self, video_url: str) -> None:
        """Analyze donations in a YouTube video"""
        try:
            # Get exchange rates
            self.logger.info("Fetching current exchange rates...")
            rates = self.get_exchange_rates()
            if not rates:
                self.logger.warning("Could not fetch exchange rates. USD conversion will not be available.")
            
            donations = self.get_video_comments(video_url)
            
            if not donations:
                self.logger.info("\nNo valid donations found in comments.")
                return
            
            self.logger.info("\nExtracted donations:")
            for amount, currency, original, author in donations:
                self.logger.info(self.format_currency(amount, currency, original, author))
            
            # Group donations by currency
            currency_totals = {}
            for amount, currency, _, _ in donations:
                if currency not in currency_totals:
                    currency_totals[currency] = 0
                currency_totals[currency] += amount
            
            self.logger.info("\nTotals by currency:")
            total_usd = 0.0
            
            for currency, total in sorted(currency_totals.items()):
                if currency == 'USD':
                    self.logger.info(f"USD: ${total:.2f}")
                else:
                    self.logger.info(f"INR: ₹{total:.2f}")
                
                # Convert to USD
                if rates:
                    usd_amount = self.convert_to_usd(total, currency, rates)
                    total_usd += usd_amount
                    self.logger.info(f"  = ${usd_amount:.2f} USD")
            
            if rates:
                self.logger.info(f"\nTotal donations in USD: ${total_usd:.2f}")
        
        except KeyboardInterrupt:
            self.logger.info("\nStopping analysis...")
        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}")

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python donation_analyzer.py <youtube_url>")
        sys.exit(1)
    
    video_url = sys.argv[1]
    analyzer = DonationAnalyzer()
    analyzer.analyze_video(video_url)

if __name__ == "__main__":
    main() 