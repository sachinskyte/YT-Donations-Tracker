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
import os

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
    def __init__(self):
        self.downloader = YoutubeCommentDownloader()
        self.config = self._load_config()
        self.exchange_rates = None
        signal.signal(signal.SIGINT, self._signal_handler)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
        
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        self.logger.info("\nStopping comment collection...")
        sys.exit(0)

    def _load_config(self) -> dict:
        """Load configuration from config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_exchange_rates(self) -> None:
        """Fetch current exchange rates"""
        try:
            self.logger.info("Fetching current exchange rates...")
            response = requests.get(self.config['exchange_rate_api'])
            data = response.json()
            self.exchange_rates = {
                'USD': 1.0,
                'INR': data['rates']['INR']
            }
        except Exception as e:
            self.logger.warning(f"Warning: Could not fetch exchange rates: {e}")
            self.exchange_rates = {'USD': 1.0, 'INR': 83.0}  # Fallback rates
    
    def _extract_donation(self, text: str) -> List[Tuple[float, str, str]]:
        """Extract donation amount and currency from text"""
        donations = []
        
        for pattern, (currency, max_amount, symbol) in self.config['currency_patterns'].items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get the first non-None group (amount)
                amount = next((g for g in match.groups() if g is not None), None)
                if amount:
                    try:
                        amount = float(amount)
                        if 0 < amount <= max_amount:
                            donations.append((amount, currency, symbol))
                    except ValueError:
                        continue
        
        return donations
    
    def _process_comment_batch(self, comments: List[dict]) -> List[Tuple[float, str, str, str]]:
        """Process a batch of comments to extract donations"""
        donations = []
        for comment in comments:
            try:
                extracted = self._extract_donation(comment['text'])
                for amount, currency, symbol in extracted:
                    donations.append((amount, currency, symbol, comment['author']))
            except Exception as e:
                self.logger.error(f"Error processing comment: {e}")
        return donations
    
    def analyze_video(self, video_url: str) -> None:
        """Analyze donations in a YouTube video's comments"""
        if not self.exchange_rates:
            self._get_exchange_rates()
        
        self.logger.info(f"\nFetching comments from: {video_url}")
        
        try:
            comments = []
            batch = []
            total_processed = 0
            start_time = time.time()
            donations_by_currency = {'USD': [], 'INR': []}
            
            # Initialize thread pool
            with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
                futures = []
                
                # Fetch and process comments in batches
                for comment in self.downloader.get_comments_from_url(video_url, sort_by=None):
                    batch.append(comment)
                    
                    if len(batch) >= self.config['batch_size']:
                        futures.append(executor.submit(self._process_comment_batch, batch.copy()))
                        total_processed += len(batch)
                        batch.clear()
                        
                        elapsed = time.time() - start_time
                        rate = total_processed / elapsed if elapsed > 0 else 0
                        self.logger.info(f"Processed {total_processed} comments... ({rate:.1f} comments/sec)")
                
                # Process remaining comments
                if batch:
                    futures.append(executor.submit(self._process_comment_batch, batch))
                    total_processed += len(batch)
                
                # Collect results
                self.logger.info("\nExtracting donations...")
                for future in as_completed(futures):
                    for amount, currency, symbol, author in future.result():
                        donations_by_currency[currency].append((amount, author))
                        self.logger.info(f"{symbol}{amount:.2f} from {author}")
            
            # Calculate totals
            self.logger.info("\nTotals by currency:")
            total_usd = 0
            for currency, donations in donations_by_currency.items():
                if donations:
                    total = sum(amount for amount, _ in donations)
                    if currency == 'USD':
                        self.logger.info(f"USD: ${total:.2f}")
                        total_usd += total
                    else:
                        usd_value = total / self.exchange_rates[currency]
                        self.logger.info(f"{currency}: {currency}{total:.2f}")
                        self.logger.info(f"  = ${usd_value:.2f} USD")
                        total_usd += usd_value
            
            self.logger.info(f"\nTotal donations in USD: ${total_usd:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error analyzing video: {e}")

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