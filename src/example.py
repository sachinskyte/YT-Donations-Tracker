from donation_analyzer import DonationAnalyzer
import json
import time

def main():
    # Initialize the analyzer
    analyzer = DonationAnalyzer()
    
    # Example video ID
    video_id = "YOUR_VIDEO_ID"
    
    print(f"Analyzing donations for video: {video_id}")
    print("Processing comments...")
    
    start_time = time.time()
    
    try:
        # Run the analysis
        results = analyzer.analyze_video(video_id)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Print results
        print("\nAnalysis Results:")
        print("-" * 50)
        print(f"Total Comments Processed: {results['total_comments']}")
        print("\nDonations by Currency:")
        for currency, data in results['donations'].items():
            print(f"{currency}: {data['count']} donations totaling {data['total']:.2f}")
        print(f"\nTotal USD Equivalent: ${results['total_usd_equivalent']:.2f}")
        print(f"Processing Time: {processing_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    main() 