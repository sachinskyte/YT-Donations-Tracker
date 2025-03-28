# YouTube Donation Analyzer

A Python tool for analyzing donations mentioned in YouTube video comments. This tool efficiently processes comments to identify and track donation amounts in USD and INR currencies.

## Features

- Fast parallel comment processing
- Configurable batch processing with timeouts
- Support for USD ($) and INR (₹) donations
- Currency conversion to USD
- Progress tracking and detailed logging
- Customizable currency patterns and validation rules

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/youtube-donation-analyzer.git
cd youtube-donation-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `src/config.json` to customize:

- `max_workers`: Number of parallel workers (default: 4)
- `batch_size`: Comments processed per batch (default: 1000)
- `batch_timeout`: Timeout for batch processing in seconds (default: 10)
- `processing_timeout`: Timeout for individual comment processing in seconds (default: 5)
- `max_usd_amount`: Maximum valid USD donation amount (default: 10000)
- `max_inr_amount`: Maximum valid INR donation amount (default: 100000)
- `currency_patterns`: Regular expressions for detecting donations

## Usage

1. Import the DonationAnalyzer class:
```python
from donation_analyzer import DonationAnalyzer
```

2. Create an analyzer instance and process a video:
```python
analyzer = DonationAnalyzer()
results = analyzer.analyze_video("VIDEO_ID")
print(results)
```

## Example Output

```python
{
    'total_comments': 5000,
    'donations': {
        'USD': {'total': 150.0, 'count': 3},
        'INR': {'total': 1000.0, 'count': 5}
    },
    'total_usd_equivalent': 162.50,
    'processing_time': '2.5 seconds'
}
```

## Error Handling

The tool includes robust error handling for:
- Network timeouts
- Invalid video IDs
- Comment processing errors
- Currency conversion failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 