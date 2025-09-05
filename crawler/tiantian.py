import requests
import json
import re
import time

FUND_PRICE_BASE_URL = "http://fundgz.1234567.com.cn/js"
HISTORY_DETAILS_BASE_URL = "http://fund.eastmoney.com/pingzhongdata"

class Fund_API:
    def __init__(self):
        pass
    
    def get_fund_price(self, fund_code: str):
        """
        Get fund price & time:
        :param fund_code: Fund code
        :return: Fund price, fund time
        """
        # make url
        timestamp = int(time.time() * 1000)
        url = f"{FUND_PRICE_BASE_URL}/{fund_code}.js?rt={timestamp}"
        
        # get data
        response = requests.get(url)
        if response.status_code == 200:
            """ output is sth like: 
            jsonpgz({"fundcode":"001186","name":"富国文体健康股票A","jzrq":"2025-09-03","dwjz":"2.8960","gsz":"2.8654","gszzl":"-1.06","gztime":"2025-09-04 15:00"});"""
            data = response.text
            
            # parse data
            data = re.findall(r"\{.+\}", data)[0]
            fund_info = json.loads(data)
            fund_price = fund_info["gsz"]
            fund_time = fund_info["gztime"]
            fund_time = time.mktime(time.strptime(fund_time, "%Y-%m-%d %H:%M"))
            return fund_price, fund_time
        else:
            return None
        
    def get_fund_details(self, fund_code: str):
        """
        Get fund details:
        :param fund_code: Fund code
        :return: Fund details
        """
        # make url
        timestamp = int(time.time() * 1000)
        url = f"{HISTORY_DETAILS_BASE_URL}/{fund_code}.js?rt={timestamp}"
        
        # get data
        response = requests.get(url)
        if response.status_code == 200:
            data = response.text
            
            # parse data for yield rate
            """
            yield rate sth like:
            /*近一年收益率*/var syl_1n="41.94";
            /*近三月收益率*/var syl_3y="37.25";
            /*近六月收益率*/var syl_6y="35.22";
            """
            data_1y_yield = re.findall("var syl_1n=.*?;", data)[0]
            data_1m_yield = re.findall("var syl_1y=.*?;", data)[0]
            data_3m_yield = re.findall("var syl_3y=.*?;", data)[0]
            data_6m_yield = re.findall("var syl_6y=.*?;", data)[0]
            data_1y_yield = float(data_1y_yield.replace("var syl_1n=", "").replace(";", "")[1:-1])
            data_1m_yield = float(data_1m_yield.replace("var syl_1y=", "").replace(";", "")[1:-1])
            data_3m_yield = float(data_3m_yield.replace("var syl_3y=", "").replace(";", "")[1:-1])
            data_6m_yield = float(data_6m_yield.replace("var syl_6y=", "").replace(";", "")[1:-1])
            
            # parse data for bond & stock ratio
            """
            sth like:
            债券占净比","type":null,"data":[0,0,0,0.91]
            """
            data_bond_ratio = re.findall("\"债券占净比\",\"type\":null,\"data\":.*?]", data)[0]
            data_bond_ratio = data_bond_ratio.replace("\"债券占净比\",\"type\":null,\"data\":", "")
            data_bond_ratio = json.loads(data_bond_ratio)[-1]
            
            data_stock_ratio = re.findall("\"股票占净比\",\"type\":null,\"data\":.*?]", data)[0]
            data_stock_ratio = data_stock_ratio.replace("\"股票占净比\",\"type\":null,\"data\":", "")
            data_stock_ratio = json.loads(data_stock_ratio)[-1]
            
            # collect data
            fund_details = {
                "1y_yield": data_1y_yield,
                "1m_yield": data_1m_yield,
                "3m_yield": data_3m_yield,
                "6m_yield": data_6m_yield,
                "bond_ratio": data_bond_ratio,
                "stock_ratio": data_stock_ratio,
            }
            return fund_details
        else:
            return None
        
if __name__ == "__main__":
    fund_api = Fund_API()
    fund_price, fund_time = fund_api.get_fund_price("007540")
    print(fund_price, fund_time)
    fund_details = fund_api.get_fund_details("001186")
    print(fund_details)
            
            
            
            
            
