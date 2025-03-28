# YouTube Donation Analyzer

A powerful Python tool designed to analyze YouTube video comments and track donation amounts. It supports donation detection in both USD ($) and INR (₹) currencies, with automatic currency conversion to USD.

## Features

- 🚀 **High-Performance Processing** – Parallel comment analysis with configurable batch sizes.
- 💰 **Accurate Donation Detection** – Identifies USD ($) and INR (₹) donations with precision.
- 💱 **Real-Time Currency Conversion** – Converts INR donations to USD using live exchange rates.
- 📊 **Comprehensive Logging & Progress Tracking** – Provides real-time updates on processing status.
- ⚡ **Efficient & Robust** – Optimized processing with timeout protection.
- ⚙️ **Fully Configurable** – Easily adjustable settings via a JSON configuration file.

## Requirements

- Python **3.8+**
- Active **internet connection** for fetching YouTube comments and exchange rates

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/youtube-donation-analyzer.git
   cd youtube-donation-analyzer
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line Execution
```bash
python src/donation_analyzer.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### As a Python Module
```python
from donation_analyzer import DonationAnalyzer

# Initialize the analyzer
analyzer = DonationAnalyzer()

# Analyze a YouTube video
analyzer.analyze_video("https://www.youtube.com/watch?v=VIDEO_ID")
```

## Configuration

The tool is fully customizable through `src/config.json`:

```json
{
    "max_workers": 4,          // Number of parallel workers
    "batch_size": 1000,        // Comments per batch
    "batch_timeout": 10,       // Timeout per batch (seconds)
    "processing_timeout": 5,   // Timeout per comment (seconds)
    "max_usd_amount": 10000,   // Maximum valid USD donation
    "max_inr_amount": 100000   // Maximum valid INR donation
}
```

## File Structure

```
youtube-donation-analyzer/
                
├── src/                     # Source code directory
│   ├── donation_analyzer.py # Main analyzer implementation
│   ├── config.json         # Configuration settings
│   └── example.py          # Usage example script
├── README.md               # Project documentation
└── requirements.txt        # Python dependencies
```

## Example Output

```
Fetching current exchange rates...
Fetching comments from: https://www.youtube.com/watch?v=VIDEO_ID
Processed 1000 comments... (125.3 comments/sec)
Processed 2000 comments... (130.1 comments/sec)

Extracted Donations:
$50.00 from User123 (original: donated $50)
₹1000.00 from User456 (original: ₹1000 sent)

Totals by Currency:
USD: $50.00
INR: ₹1000.00
  = $12.05 USD

Total Donations in USD: $62.05
```

## Detailed Feature Breakdown

### 🎯 Donation Detection
- Recognizes multiple donation-related keywords (e.g., *donated, sent, giving*).
- Detects currency symbols both before and after the amount.
- Filters out unrealistic or incorrectly formatted donations.
- Supports both whole numbers and decimal values.

### 🚀 Optimized Performance
- Parallel batch processing for faster execution.
- Configurable timeout settings to avoid prolonged operations.
- Real-time progress tracking with speed metrics.
- Graceful handling of process interruptions.

### 🌎 Multi-Currency Support
- USD ($) detection with automatic symbol recognition.
- INR (₹) support, including "Rs." notation.
- Live exchange rate conversion for accurate calculations.

## Error Handling

The tool includes comprehensive error-handling mechanisms for:
- **Network Issues** – Handles timeouts and connection failures.
- **Invalid Video URLs** – Detects and reports incorrect input URLs.
- **Processing Failures** – Logs and skips problematic comments.
- **Exchange Rate API Errors** – Prevents crashes due to API downtime.
- **Invalid Donation Formats** – Filters out non-monetary values.

## License

This project is licensed under the **MIT License**.

