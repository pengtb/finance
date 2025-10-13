import akshare as ak
import pandas as pd
import time
from . import Crawler

class FundCrawler(Crawler):
    """
    Fetch fund information from AkShare
    """
    def crawl_info(self, save=True):
        """
        Crawl fund information: fund code, name, type & value (estimation)
        """
        # fetch fund information
        for i in range(self.max_retry):
            try:
                fund_info = ak.fund_name_em()
                fund_value_estimation = ak.fund_value_estimation_em()
                break
            except:
                print(f"[{time.strftime('%Y-%m-%d %H:%M', time.localtime())}] {self.save_fp} failed to update, retry {i+1}/{self.max_retry}")
                time.sleep(self.retry_interval)
        else:
            raise Exception("Failed to update fund information")
        
        # merge
        merged = pd.merge(fund_info, fund_value_estimation, on="基金代码", how="left")
        # subset
        # value_colname = [colname for colname in merged.columns if colname.endswith("估算数据-估算值")][0]
        value_colname = [colname for colname in merged.columns if colname.endswith("单位净值")][-1]
        print(f"正在获取{value_colname}")
        subset = merged.loc[:, ["基金代码", "基金名称", "基金类型", value_colname]].fillna('---')
        subset.columns = ["code", "name", "type", "value"]
        
        # save
        if save:
            subset.to_csv(self.save_fp, index=False, sep='\t')
        return subset

if __name__ == "__main__":
    fund_crawler = FundCrawler(update_time="01:00", update_interval=86400, save_fp="datatables/fund_info.tsv")
    # fund_crawler.schedule_crawling()
    fund_crawler.crawl_info()