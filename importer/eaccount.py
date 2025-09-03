import pandas as pd
import time
from . import Account, AccountImporter

class EAccountImporter(AccountImporter):
    def import_accounts(self, file_path: str):
        """
        Import accounts from file
        """
        # load from excel
        raw_df = pd.read_excel(file_path, 
                               sheet_name="持有信息",
                               skiprows=4,
                               usecols=["基金名称", "销售机构", "净值日期", "资产情况\n（结算币种）", "结算币种"]).dropna()
        
        # format df
        ## rename columns
        raw_df.columns = ["name", "source", "date", "balance", "currency"]
        ## convert curreny to ISO 4217
        raw_df["currency"] = raw_df["currency"].apply(lambda x: {"人民币": "CNY", "美元": "USD"}.get(x, "CNY"))
        ## convert date to seconds (starting from 1970-01-01)
        raw_df["date"] = pd.to_datetime(raw_df["date"])
        raw_df["balanceTime"] = raw_df["date"].apply(lambda x: time.mktime(x.timetuple()))
        raw_df["balanceTime"] = raw_df["balanceTime"].astype(int)
        ## convert balance to int: 10.23 -> 1023
        raw_df["balance"] = raw_df["balance"].apply(lambda x: float(x) * 100)
        raw_df["balance"] = raw_df["balance"].astype(int)
        
        # create accounts
        accounts = []
        for _, row in raw_df.iterrows():
            account = Account()
            account.name = row["name"]
            account.balanceTime = row["balanceTime"]
            account.account_type = 1
            account.balance = row["balance"]
            account.currency = row["currency"]
            account.source = row["source"]
            accounts.append(account)
            
        # format accounts
        accounts = self.format_accounts(accounts)
        print(f"Imported {len(accounts)} accounts")
        
        return accounts
    
