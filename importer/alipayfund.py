import pandas as pd
import time
import pdfplumber
from . import Account, ParentAccount, AccountImporter, icon_mapping, category_mapping, color_mapping

class AlipayFundImporter(AccountImporter):
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
        raw_df.columns = ["idx", "trade_account", "name", "code", "amount", "value", "balanceTime", "balance"]
        ## subset
        raw_df.drop(columns=["idx", "trade_account", "value"])
        ## format
        raw_df["name"] = raw_df["name"].str.replace("\n", "")
        raw_df["code"] = raw_df["code"].astype(int)
        raw_df["amount"] = raw_df["amount"].astype(float)
        raw_df["balance"] = (raw_df["balance"].astype(float)*100).astype(int)
        raw_df["balanceTime"] = raw_df["balanceTime"].apply(lambda x: time.mktime(time.strptime(x, "%Y%m%d"))).astype(int)
        ## add columns: currency, source
        raw_df["currency"] = "CNY"
        raw_df["source"] = "alipay"
        
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
        
        # group accounts by name
        accounts = self.group_accounts(accounts)
        print(f"Imported {len(accounts)} accounts")
        
        return accounts
    
    def group_accounts(self, accounts: list[Account]):
        """
        Group accounts by name suffix
        todo: api to support subaccounts
        """
        # assign accounts to groups
        d1_accounts = []
        d7_accounts = []
        d360_accounts = []
        other_accounts = []
        for account in accounts:
            if "活钱+" in account.name:
                account.category = category_mapping["savings"]
                d1_accounts.append(account)
            elif "7日" in account.name:
                account.category = category_mapping["savings"]
                d7_accounts.append(account)
            elif "定活" in account.name:
                account.category = category_mapping["investment"]
                d360_accounts.append(account)
            else:
                other_accounts.append(account)
                
        # make subaccounts
        d1_account = ParentAccount()
        d1_account.name = "活钱+"
        d1_account.account_type = 2
        d1_account.currency = "---"
        d1_account.icon = icon_mapping["savings"]
        d1_account.color = color_mapping["deposit"]
        d1_account.category = category_mapping["savings"]
        d1_account.subAccounts = d1_accounts
        
        d7_account = ParentAccount()
        d7_account.name = "7日理财+"
        d7_account.account_type = 2
        d7_account.currency = "---"
        d7_account.icon = icon_mapping["bonds"]
        d7_account.color = color_mapping["deposit"]
        d7_account.category = category_mapping["savings"]
        d7_account.subAccounts = d7_accounts
        
        d360_account = ParentAccount()
        d360_account.name = "定活理财360天"
        d360_account.account_type = 2
        d360_account.currency = "---"
        d360_account.icon = icon_mapping["bonds"]
        d360_account.color = color_mapping["bonds"]
        d360_account.category = category_mapping["investment"]
        d360_account.subAccounts = d360_accounts
                
        grouped_accounts = [d1_account, d7_account, d360_account] + other_accounts
        
        return grouped_accounts
    