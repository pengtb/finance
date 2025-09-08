import pandas as pd
import time
import os
import json
import pdfplumber
from . import Account, AccountImporter

class AlipayImporter(AccountImporter):
    def import_accounts(self, file_path: str, update_info: bool = True, update_info_fp: str = 'datatables/fund_info.tsv'):
        """
        Import accounts from file
        """
        # read tables from pdf
        with pdfplumber.open(file_path) as pdf:
            tables = []
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    tables.append(table)
            raw_df = pd.concat([pd.DataFrame(table) for table in tables], axis=0)
            
        # preprocess
        ## adjust columns
        raw_df = raw_df.drop(index=0).reset_index(drop=True)
        raw_df.columns = ["idx", "trade_acocunt", "name", "code", "amount", "value", "balanceTime", "balance"]
        ## subset
        raw_df.drop(columns=["idx", "trade_account", "value"])
        ## format
        raw_df["name"] = raw_df["name"].str.replace("\n", "")
        raw_df["code"] = raw_df["code"].astype(int)
        raw_df["amount"] = raw_df["amount"].astype(float)
        raw_df["balance"] = raw_df["balance"].astype(float)
        raw_df["balanceTime"] = raw_df["balanceTime"].apply(lambda x: time.mktime(time.strptime(x, "%Y%m%d")))
        ## add columns: currency, source
        raw_df["currency"] = "CNY"
        raw_df["source"] = "支付宝"
        
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
    