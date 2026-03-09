import time

class Crawler:
    update_time: str = "01:00"
    update_interval: int = 86400
    save_fp: str = ""
    max_retry: int = 5
    retry_interval: int = 60
    
    def __init__(self, update_time: str = "01:00", update_interval: int = 86400, save_fp: str = "", max_retry: int = 5, retry_interval: int = 60):
        self.update_time = update_time
        self.update_interval = update_interval
        self.save_fp = save_fp
        self.max_retry = max_retry
        self.retry_interval = retry_interval
        
    def crawl_info(self, **kwargs):
        raise NotImplementedError("crawl_info should be implemented")
    
    def schedule_crawling(self):
        """
        Schedule crawling at the specified time interval.
        """
        while True:
            # wait until the specified time
            current_time = time.strftime("%H:%M", time.localtime())
            if current_time == self.update_time:
                try:
                    self.crawl_info()
                    print(f"[{time.strftime('%Y-%m-%d %H:%M', time.localtime())}] {self.save_fp} updated")
                    # sleep for the specified interval
                    time.sleep(self.update_interval)
                except:
                    print("Failed to update this time.")
                    print(f"Next update scheduled at {self.update_time}.")
                    time.sleep(60)
            else:
                time.sleep(60)