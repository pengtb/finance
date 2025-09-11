import pandas as pd
import os
import json
import asyncio
import json
from mcp_agent.core.fastagent import FastAgent
        
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
        update_info_df = pd.read_table(update_info_fp, usecols=['code', 'value'])
        if strict: update_info_df = update_info_df.loc[update_info_df.value!='---']
        
        # current account df
        accounts_df = pd.DataFrame([account.to_dict() for account in accounts])
        ## release json
        accounts_df.loc[:, 'source'] = accounts_df.loc[:, 'comment'].apply(lambda x: json.loads(x)['source'])
        accounts_df.loc[:, 'amount'] = accounts_df.loc[:, 'comment'].apply(lambda x: json.loads(x)['amount']).astype(float)
        accounts_df.loc[:, 'code'] = accounts_df.loc[:, 'comment'].apply(lambda x: json.loads(x)['code']).astype(int)
        ## previous value
        accounts_df.loc[:, 'prev_value'] = accounts_df.loc[:, 'balance'] / accounts_df.loc[:, 'amount']
        
        # merge
        merged = pd.merge(accounts_df, update_info_df, on='code', how='inner')
        
        # keep previous value if new value is not available
        merged.loc[:, 'value'] = merged.loc[:, 'value'].where(merged.loc[:, 'value']!='---', merged.loc[:, 'prev_value'])
        
        # udpate balance
        merged.loc[:, 'balance'] = (merged.loc[:, 'value'].astype(float) * merged.loc[:, 'amount'].astype(float) * 100).astype(int)
        
        # update balanceTime
        ## modification time of update info file
        merged.loc[:, 'balanceTime'] = int(os.path.getmtime(update_info_fp))
        
        # create updated accounts
        updated_accounts = []
        for _, row in merged.iterrows():
            account = Account()
            account.name = row["name"]
            account.balanceTime = row["balanceTime"]
            account.account_type = 1
            account.balance = row["balance"]
            account.currency = row["currency"]
            account.comment = row[["code","amount"]].to_json()
            updated_accounts.append(account)
        
        return updated_accounts
        
class Transaction:
    type: str = 1
    categoryId: int = 0
    time: int = 0
    utcOffset: int = 0
    sourceAccountId: str = ""
    destinationAccountId: str = ""
    sourceAmount: int = 0
    destinationAmount: int = 0
    tagIds: list[int] = []
    comment: str = ""
    # geoLocation: dict = {}
    
    def assign_categoryId(self, categoryid_description: str, description: str):
        """
        use llm to assign categoryId based on given discription dict
        :param categoryid_description: categoryId description json built from transaction categories list API
        :param description: transaction description json imported from file
        """
        # create prompt
        prompt = f"""
        交易描述: {description}
        交易类别列表: {categoryid_description}
        请为这笔交易分配一个类别ID（即id字段），直接返回该id，不需要解释。形式如123，可直接输入到int()函数。
        """
        
        # create app & agent
        fast = FastAgent("transaction", quiet=True)
        @fast.agent(
            name="category-assigner",
            model="openai.gpt-4o-mini.medium",
            instruction="你是一个交易分类器，根据交易描述和交易类别列表，为交易分配正确的类别ID。"
        )
        
        # run agent
        async def run_agent (prompt):
            async with fast.run() as agent:
                response = await agent(prompt)
            return int(response)
            
        return asyncio.run(run_agent(prompt))
    
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
            "tagIds": self.tagIds,
            "comment": self.comment,
        }
        return transaction_dict

class TransactionImporter:
    def import_transactions(self, file_path: str):
        """
        Import transactions from file & return a list of Transaction objects
        """
        raise NotImplementedError("import_transactions method not implemented")