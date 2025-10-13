import pandas as pd
import time
from . import Account, AccountImporter

class EAccountImporter(AccountImporter):
    def import_accounts(self, file_path: str, update_info: bool = True, update_info_fp: str = 'datatables/fund_info.tsv'):
        """
        Import accounts from file
        """
        # load from excel
        raw_df = pd.read_excel(file_path, 
                               sheet_name="持有信息",
                               skiprows=4,
                               usecols=["基金代码", "基金名称", "销售机构", "持有份额", "净值日期", "资产情况\n（结算币种）", "结算币种"]).dropna()
        
        # format df
        ## rename columns
        raw_df.columns = ["code", "name", "source", "amount", "date", "balance", "currency"]
        ## convert curreny to ISO 4217
        raw_df["currency"] = raw_df["currency"].apply(lambda x: {"人民币": "CNY", "美元": "USD"}.get(x, "CNY"))
        ## convert date to seconds (starting from 1970-01-01)
        raw_df["balanceTime"] = raw_df["date"].apply(lambda x: time.mktime(time.strptime(x, "%Y/%m/%d")))
        raw_df["balanceTime"] = raw_df["balanceTime"].astype(int)
        ## convert balance to int: 10.23 -> 1023
        raw_df["balance"] = raw_df["balance"].apply(lambda x: float(x) * 100)
        raw_df["balance"] = raw_df["balance"].astype(int)
        ## code to int
        raw_df["code"] = raw_df["code"].astype(int)
        
        # create accounts
        accounts = []
        for _, row in raw_df.iterrows():
            account = Account()
            account.name = row["name"]
            account.balanceTime = row["balanceTime"]
            account.account_type = 1
            account.balance = row["balance"]
            account.currency = row["currency"]
            account.comment = row[["code","amount","source"]].to_json()
            accounts.append(account)
            
        # update account info
        if update_info:
            accounts = self.update_info(accounts, update_info_fp)
            
        # format accounts
        accounts = self.format_accounts(accounts)
        print(f"Imported {len(accounts)} accounts")
        
        return accounts
