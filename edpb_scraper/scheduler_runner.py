import schedule
import time
from main import main

def schedule_job():
    schedule.every().friday.at("08:00").do(main)
    print("Scheduler started. Waiting for Friday 08:00...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    schedule_job()
