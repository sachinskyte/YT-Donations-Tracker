from donation_analyzer import DonationAnalyzer
import time

def main():
    # Initialize the analyzer
    analyzer = DonationAnalyzer()
    
    # Example video URL (replace with your video URL)
    video_url = "https://www.youtube.com/watch?v=EXAMPLE"
    
    print(f"Analyzing donations for video: {video_url}")
    print("Processing comments...")
    
    start_time = time.time()
    
    try:
        # Run the analysis
        analyzer.analyze_video(video_url)
        
        # Processing time
        processing_time = time.time() - start_time
        print(f"\nTotal Processing Time: {processing_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    main() 