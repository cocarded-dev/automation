import schedule
import time
from datetime import datetime
from order_processor import OrderProcessor
from config import Config

def run_order_processing():
    """Main function to run order processing"""
    print(f"Starting order processing at {datetime.now()}")
    
    try:
        # Validate configuration
        Config.validate()
        
        # Initialize order processor
        processor = OrderProcessor()
        
        # Process all new orders
        stats = processor.process_all_new_orders()
        
        # Print statistics
        print("\n=== Processing Statistics ===")
        print(f"Total orders: {stats['total']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Skipped: {stats['skipped']}")
        
        # Cleanup
        processor.cleanup()
        
        print(f"Order processing completed at {datetime.now()}")
        
    except Exception as e:
        print(f"Error in order processing: {e}")

def main():
    """Main entry point"""
    print("Etsy Order Fulfillment Automation")
    print("===================================")
    
    # Parse schedule time from config
    schedule_time = Config.SCHEDULE_TIME
    
    # Schedule the job
    schedule.every().day.at(schedule_time).do(run_order_processing)
    
    print(f"Scheduler configured to run daily at {schedule_time}")
    print("Press Ctrl+C to exit")
    
    # Run once immediately for testing
    print("Running initial test...")
    run_order_processing()
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")

if __name__ == "__main__":
    main()
