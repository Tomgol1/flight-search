import datetime

def run_job():
    now = datetime.datetime.utcnow()
    print(f"Job ran at {now} UTC")

if __name__ == "__main__":
    run_job()
