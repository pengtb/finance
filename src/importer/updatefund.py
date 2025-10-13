import json
import pandas as pd
import time
from . import Transaction
from . import Account, AccountImporter

class FundUpdateImporter(AccountImporter):
    def import_accounts(self, result_df: pd.DataFrame, 
                        update_info: bool = True, 
                        update_info_fp: str | None = 'datatables/fund_info.tsv'):
        """
        update fund accounts
        :param result_df: result dataframe from list account api
        :param update_info: whether to update fund account balance
        :param update_info_fp: path to tsv file
        """
        
        # create accounts
        accounts = []
        ## ignore parent account
        result_df = result_df[result_df["type"]==1]
        
        for _, row in result_df.iterrows():
            account = Account()
            ## as previous account
            account.name = row["name"]
            account.balanceTime = int(time.time()) ### current timestampe
            account.account_type = 1
            account.balance = row["balance"]
            account.currency = row["currency"]
            account.comment = row["comment"]
            account.icon = row["icon"]
            account.color = row["color"]
            account.category = row["category"]
            ## extra attributes
            account.id = row["id"]
            
            accounts.append(account)
        
        print(f"Imported {len(accounts)} accounts")
        
        # update account info
        if update_info:
            accounts = self.update_info(accounts, update_info_fp, strict=True)
            print(f"Updated {len(accounts)} accounts")
        
        return accounts

class FundUpdateTransaction(Transaction):
    amount: float
    
    def assign_categoryId(self, categoryid_description: str):
        ## parse to form json & df
        categoryid_des_json = json.loads(categoryid_description)
        categoryid_des_df = pd.DataFrame(categoryid_des_json)
        ## assign categoryId
        if self.amount > 0:
            subcategory_id = categoryid_des_df[categoryid_des_df['name']=="投资收入"]['id'].values[0]
        else:
            subcategory_id = categoryid_des_df[categoryid_des_df['name']=="投资损失"]['id'].values[0]
        return subcategory_id
    
class FundZeroTransaction(Transaction):
    def assign_categoryId(self, categoryid_description: str):
        ## parse to form json & df
        categoryid_des_json = json.loads(categoryid_description)
        categoryid_des_df = pd.DataFrame(categoryid_des_json)
        ## assign categoryId
        subcategory_id = categoryid_des_df[categoryid_des_df['name']=="投资支出"]['id'].values[0]
        return subcategory_id