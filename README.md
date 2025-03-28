# YouTube Donation Analyzer

A Python tool that analyzes YouTube video comments to identify and track donation amounts. It supports detection of donations in USD ($) and INR (₹) currencies, with automatic currency conversion to USD.

## Features

- 🚀 Fast parallel comment processing with configurable batch sizes
- 💰 Accurate detection of USD ($) and INR (₹) donations
- 💱 Automatic currency conversion to USD using real-time exchange rates
- 📊 Detailed progress tracking and logging
- ⚡ Efficient processing with timeout protection
- ⚙️ Fully configurable through JSON settings

## Requirements

- Python 3.8+
- Internet connection for YouTube access and exchange rates

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

## Usage

### Command Line
```bash
python src/donation_analyzer.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### As a Module
```python
from donation_analyzer import DonationAnalyzer

# Initialize analyzer
analyzer = DonationAnalyzer()

# Analyze video
analyzer.analyze_video("https://www.youtube.com/watch?v=VIDEO_ID")
```

## Configuration

The tool is configurable through `src/config.json`:

```json
{
    "max_workers": 4,          // Number of parallel workers
    "batch_size": 1000,        // Comments per batch
    "batch_timeout": 10,       // Batch processing timeout (seconds)
    "processing_timeout": 5,   // Individual comment timeout (seconds)
    "max_usd_amount": 10000,   // Maximum valid USD donation
    "max_inr_amount": 100000,  // Maximum valid INR donation
}
```

## Output Example

```
Fetching current exchange rates...
Fetching comments from: https://www.youtube.com/watch?v=VIDEO_ID
Processed 1000 comments... (125.3 comments/sec)
Processed 2000 comments... (130.1 comments/sec)

Extracted donations:
$50.00 from User123 (original: donated $50)
₹1000.00 from User456 (original: ₹1000 sent)

Totals by currency:
USD: $50.00
INR: ₹1000.00
  = $12.05 USD

Total donations in USD: $62.05
```

## Features in Detail

### Donation Detection
- Recognizes various donation phrases ("donated", "sent", "giving", etc.)
- Supports both currency symbol before and after amount
- Validates amounts to filter out unrealistic donations
- Handles decimal values and whole numbers

### Performance
- Parallel processing of comment batches
- Configurable timeouts to prevent hanging
- Progress tracking with processing speed
- Graceful handling of interruptions

### Currency Support
- USD ($) with automatic symbol detection
- INR (₹) with support for both ₹ symbol and "Rs." notation
- Real-time currency conversion using exchange rates API

## Error Handling

The tool includes comprehensive error handling for:
- Network timeouts and connection issues
- Invalid video URLs
- Comment processing errors
- Exchange rate API failures
- Invalid donation formats

## License

This project is licensed under the MIT License. 