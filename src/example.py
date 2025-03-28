from donation_analyzer import DonationAnalyzer

def main():
    # Create analyzer
    analyzer = DonationAnalyzer()
    
    # YouTube video URL to analyze
    video_url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
    
    # Run analysis
    analyzer.analyze_video(video_url)

if __name__ == "__main__":
    main() 