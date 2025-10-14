import pandas as pd
import os
import json
import time
from api.transaction import Transaction_API
from api.account import Account_API
from crawler.fund import FundCrawler
        
# account icons
icon_mapping = {
    "stocks": "800",
    "bonds": "520",
    "gold": "10",
    "savings": "30",
    "deposit": "110",
    "dollar": "1000",
    "global": "990",
    "bank": "100",
    "alipay": "8300"
}

# account colors
color_mapping = {
    "deposit": '4cd964', # green
    "bonds": 'ffcc00', # yellow
    "stocks": 'ff3b30', # red
    "gold": '8e8e93', # grey
}

# account category
category_mapping = {
    "deposit": 9,
    "investment": 7,
    "savings": 8,
}

class Account:
    name: str
    currency: str = "CNY"
    balance: int = 0
    balanceTime: int = 0
    category: int = 7
    icon: str = "800"
    color: str = ""
    account_type: int = 1 # seperate account
    comment: str = ""

    def assign_icon(self, source: str | None = None):
        """
        Assign icon to account based on fund name and source
        """
        # assign icon based on source
        if source:
            if "蚂蚁" in source:
                self.icon = icon_mapping["alipay"]
            elif "银行" in source:
                self.icon = icon_mapping["bank"]
            else:
                self.icon = icon_mapping["stocks"]
        else:
            self.icon = icon_mapping["stocks"]
            
        # assign icon based on name
        if "存款" in self.name:
            self.icon = icon_mapping["deposit"]
        elif "货币" in self.name:
            self.icon = icon_mapping["savings"]
        elif ("股" in self.name) or ("ETF" in self.name) or ("研究" in self.name) or ("创新" in self.name):
            self.icon = icon_mapping["stocks"]
        elif ("债" in self.name) or ("混合" in self.name):
            self.icon = icon_mapping["bonds"]
        elif "黄金" in self.name:
            self.icon = icon_mapping["gold"]
        if ("美国" in self.name) or ("美元" in self.name):
            self.icon = icon_mapping["dollar"]
        elif "全球" in self.name:
            self.icon = icon_mapping["global"]
    
    def assign_color(self):
        """
        Assign color to account based on fund name
        """
        if ("存款" in self.name) or ("货币" in self.name):
            self.color = color_mapping["deposit"]
        elif ("债" in self.name) or ("混合" in self.name):
            self.color = color_mapping["bonds"]
        elif "黄金" in self.name:
            self.color = color_mapping["gold"]
        else:
            self.color = color_mapping["stocks"]
            
    def assign_category(self):
        """
        Assign category to account based on fund name
        """
        if "存款" in self.name:
            self.category = category_mapping["deposit"]
        elif "货币" in self.name:
            self.category = category_mapping["savings"]
        else:
            self.category = category_mapping["investment"]
            
    def to_dict(self):
        """
        Convert account to dict
        """
        account_dict = {
            "name": self.name,
            "currency": self.currency,
            "balance": self.balance,
            "balanceTime": self.balanceTime,
            "category": self.category,
            "icon": self.icon,
            "color": self.color,
            "type": self.account_type,
            "comment": self.comment,
        }
        return account_dict
    
class ParentAccount:
    name: str
    category: int = 7
    icon: str = "800"
    color: str = ""
    account_type: int = 2 # parent account
    subAccounts: list[Account] = []
    currency: str = "---"
    
    def to_dict(self):
        """
        Convert account to dict
        """
        account_dict = {
            "name": self.name,
            "category": self.category,
            "icon": self.icon,
            "color": self.color,
            "type": self.account_type,
            "currency": self.currency,
            "subAccounts": [subAccount.to_dict() for subAccount in self.subAccounts],
        }
        return account_dict
            
class AccountImporter:
    def import_accounts(self, file_path: str):
        """
        Import accounts from file & return a list of Account objects
        """
        raise NotImplementedError("import_accounts method not implemented")
    
    def format_accounts(self, accounts: list[Account]):
        """
        Format accounts: assign icon, color, category
        """
        formatted = []
        for account in accounts:
            account.assign_icon()
            account.assign_color()
            account.assign_category()
            formatted.append(account)
        return formatted
    
    def update_info(self, accounts: list, update_info_fp: str, strict: bool = False):
        """
        Update account information using update-info-fp tsv file:
        strict: only keep those with available values in update_info_df
        """
        # load update info
        if (update_info_fp is not None) and (os.path.exists(update_info_fp)):
            update_info_df = pd.read_table(update_info_fp, usecols=['code', 'value'], dtype={'code': int})
        else:
            fund_crawler = FundCrawler(save_fp=update_info_fp)
            update_info_df = fund_crawler.crawl_info(save=update_info_fp is not None)
            update_info_df.loc[:, 'code'] = update_info_df.loc[:, 'code'].astype(int)
            update_info_df = update_info_df.loc[:, ["code", "value"]]

        update_info_df.loc[:, 'code'] = update_info_df.loc[:, 'code'].astype(str)
        if strict: update_info_df = update_info_df.loc[update_info_df.value!='---']
        
        # preprocess
        ## only with comment / fund code
        accounts = [account for account in accounts if account.comment!=""]
        ## current account df
        accounts_df = pd.DataFrame([account.to_dict() for account in accounts])
        ## release json
        accounts_df.loc[:, 'amount'] = accounts_df.loc[:, 'comment'].apply(lambda x: json.loads(x)['amount']).astype(float)
        accounts_df.loc[:, 'code'] = accounts_df.loc[:, 'comment'].apply(lambda x: json.loads(x)['code']).astype(str)
        ## previous value
        accounts_df.loc[:, 'prev_value'] = accounts_df.loc[:, 'balance'] / accounts_df.loc[:, 'amount'] / 100 ### restore to original value
        
        # merge
        update_info_df.loc[:, 'code'] = update_info_df.loc[:, 'code'].astype(str)
        merged = pd.merge(accounts_df, update_info_df, on='code', how='inner')
        
        # keep previous value if new value is not available
        merged.loc[:, 'value'] = merged.loc[:, 'value'].where(merged.loc[:, 'value']!='---', merged.loc[:, 'prev_value'])
        
        # udpate balance
        merged.loc[:, 'balance'] = (merged.loc[:, 'value'].astype(float) * merged.loc[:, 'amount'].astype(float) * 100).astype(int)

        # update balanceTime
        ## modification time of update info file
        if (update_info_fp is not None) and (os.path.exists(update_info_fp)):
            merged.loc[:, 'balanceTime'] = int(os.path.getmtime(update_info_fp))
        else:
            merged.loc[:, 'balanceTime'] = int(time.time())
        
        # create updated accounts
        toupdate_accounts = [account for account in accounts if account.name in merged['name'].values]
        updated_accounts = []
        for account in toupdate_accounts:
            account.prev_balance = account.balance
            account.balance = int(merged.loc[merged['name']==account.name, 'balance'].values[0])
            account.balanceTime = int(merged.loc[merged['name']==account.name, 'balanceTime'].values[0])
            updated_accounts.append(account)
        
        return updated_accounts
        
class Transaction:
    type: int = 2
    categoryId: int = 0
    time: int = 0
    utcOffset: int = 8 * 60 # GMT+8 in min
    sourceAccountId: str = ""
    destinationAccountId: str = ""
    sourceAmount: int = 0
    destinationAmount: int = 0
    # tagIds: list[int] = []
    comment: str = ""
    # geoLocation: dict = {}
    
    def to_dict(self):
        """
        Convert transaction to dict
        """
        transaction_dict = {
            "type": self.type,
            "categoryId": self.categoryId,
            "time": self.time,
            "utcOffset": self.utcOffset,
            "sourceAccountId": self.sourceAccountId,
            "destinationAccountId": self.destinationAccountId,
            "sourceAmount": self.sourceAmount,
            "destinationAmount": self.destinationAmount,
            # "tagIds": self.tagIds,
            "comment": self.comment,
        }
        if self.type != 4:
            del transaction_dict["destinationAccountId"]
            del transaction_dict["destinationAmount"]
        return transaction_dict
    
    def assign_categoryId(self):
        raise NotImplementedError("assign_categoryId method not implemented")
    
    def assign_accountId(self):
        raise NotImplementedError("assign_accountId method not implemented")

class TransactionImporter:
    def __init__(self, save_dir: str | None = None):
        # collect categories & accounts
        self.subcategories = TransactionImporter.collect_categories() # id, name, parentId, parentName
        self.accounts = TransactionImporter.collect_accounts() # id, name
        
        # save
        if save_dir is not None:
            os.makedirs(save_dir, exist_ok=True)
            self.subcategories.to_csv(os.path.join(save_dir, "transaction_subcategories.tsv"), sep='\t', index=False)
            self.accounts.to_csv(os.path.join(save_dir, "accounts.tsv"), sep='\t', index=False)
    
    def import_transactions(self, file_path: str):
        """
        Import transactions from file & return a list of Transaction objects
        """
        raise NotImplementedError("import_transactions method not implemented")
    
    @staticmethod
    def collect_categories():
        # collect categoryids info
        ## collect current categoryids
        api = Transaction_API()
        response = api.list_transaction_categories()
        ## flatten categoryids
        categories = response["result"]
        incomes = categories["1"]
        expenses = categories["2"]
        transfers = categories["3"]
        subcategories = [category["subCategories"] for category in incomes + expenses + transfers]
        subcategories = [subcategory for subcategory_list in subcategories for subcategory in subcategory_list]
        ## only id & name (& parentId)
        subcategories = [{
            "id": subcategory["id"],
            "name": subcategory["name"],
            "parentId": subcategory["parentId"]
        } for subcategory in subcategories]
        incomes = [{
            "parentId": category["id"],
            "parentName": category["name"],
            "type": 2,
            "typeDesc": "收入",
        } for category in incomes]
        expenses = [{
            "parentId": category["id"],
            "parentName": category["name"],
            "type": 3,
            "typeDesc": "支出",
        } for category in expenses]
        transfers = [{
            "parentId": category["id"],
            "parentName": category["name"],
            "type": 4,
            "typeDesc": "转账",
        } for category in transfers]
        ## merge using pandas df
        subcategories_df = pd.DataFrame(subcategories)
        categories_df = pd.DataFrame(incomes + expenses + transfers)
        merged_df = pd.merge(subcategories_df, 
                             categories_df, 
                             on='parentId', how='inner').reset_index(drop=True)
        return merged_df
    
    @staticmethod
    def collect_accounts():
        # collect accounts info
        ## collect current accounts
        api = Account_API()
        response = api.list_accounts()
        accounts = response["result"]
        accounts_df = pd.DataFrame(accounts).loc[:, ['id', 'name']].reset_index(drop=True)
        return accounts_df