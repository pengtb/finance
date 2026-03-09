import pandas as pd
import time
import json
from . import Transaction, TransactionImporter

class JDTransaction(Transaction):
    def assign_categoryId(self, categoryid_description: str, transaction_description: str):
        ## parse transaction_description
        transaction_des_json = json.loads(transaction_description)
        payee = transaction_des_json["payee"]
        item = transaction_des_json["item"]
        status = transaction_des_json["status"]
        
        ## replace status
        replace_dict = {"收入": "已收入", "支出": "已支出", "不计收支": "资金转移"}
        transaction_des_json["status"] = replace_dict[status]
        
        ## new transaction_description
        transaction_description = json.dumps(transaction_des_json, ensure_ascii=False)
        
        # same as AlipayTransaction
        return super().assign_categoryId(categoryid_description, transaction_description)
        
    def assign_accountId(self, accounts_df: pd.DataFrame, transaction_description: str, transaction_subcategory: str, subcategories_df: pd.DataFrame):
        return super().assign_accountId(accounts_df, transaction_description, transaction_subcategory, subcategories_df)
    
class JDTransactionImporter(TransactionImporter):
    def __init__(self, save_dir: str | None = None):
        super().__init__(save_dir)
        
    def import_transactions(self, file_path: str, rest_file_path: str | None = None):
            """
            Import transactions from file & return a list of Transaction objects
            """
            # read table from csv
            raw_df = pd.read_csv(file_path, skiprows=21, engine='python',
                             usecols=[0,1,2,3,4,5,6,7], index_col=False
                            #  usecols=["交易时间", "商户名称", "交易说明", "金额", 
                            #           "收/付款方式", "交易状态", "收/支", "交易分类"]
                             )
            
            # preprocess
            ## remove white space
            raw_df = raw_df.map(lambda x: x.strip() if isinstance(x, str) else x)
            ## remove white space in column name
            raw_df.columns = raw_df.columns.str.strip()
            ## only success transaction
            raw_df = raw_df[raw_df["交易状态"].isin(["交易成功", "还款成功"])].drop(columns=["交易状态"])
            ## rename columns
            raw_df = raw_df.rename(columns={
                "交易时间": "time",
                "交易分类": "category",
                "商户名称": "payee",
                "交易说明": "item",
                "金额": "amount",
                "收/支": "status",
                "收/付款方式": "method",
            })
            
            ## convert time to timestamp
            raw_df = raw_df[raw_df["time"]!=""]
            raw_df["time"] = raw_df["time"].apply(lambda x: time.mktime(time.strptime(x, "%Y-%m-%d %H:%M:%S"))).astype(int)
            ## format amount
            raw_df["amount"] = (raw_df["amount"].astype(float)*100).astype(int)
            
            # init transactions
            ## init categoryids
            subcategories = list(self.subcategories.to_dict(orient="index").values())
            categories_description = json.dumps(subcategories, ensure_ascii=False)
            ## init transactions list
            transactions = []
            ignored_rows = []
            for _, row in raw_df.iterrows():
                transaction = JDTransaction()
                transaction.time = row["time"]
                transaction.sourceAmount = row["amount"]
                transaction.destinationAmount = row["amount"]
                transaction.comment = json.dumps(row[["payee", "item", "status", "method"]].to_dict(), ensure_ascii=False)
                ## assign categoryId
                transaction.categoryId = transaction.assign_categoryId(categories_description, transaction.comment)
                if transaction.categoryId not in self.subcategories["id"].values:
                    print(f"Transaction {transaction.to_dict()} with subcategory unassigned.")
                    ignored_rows.append(row)
                    continue
                ## assign type
                transaction.type = int(self.subcategories.loc[self.subcategories["id"]==transaction.categoryId, "type"].iloc[0])
                ## assign accountId
                transaction_subcategory = self.subcategories.loc[self.subcategories["id"]==transaction.categoryId, "name"].iloc[0]
                sourceAccountId, destinationAccountId = transaction.assign_accountId(self.accounts, transaction.comment, transaction_subcategory, self.subcategories)
                if (sourceAccountId is None) and (destinationAccountId is None):
                    ignored_rows.append(row)
                    continue
                transaction.sourceAccountId = sourceAccountId
                transaction.destinationAccountId = destinationAccountId
                ## others
                transactions.append(transaction)
                
            # save ignored rows
            if (rest_file_path is not None) and (len(ignored_rows) > 0):
                ignored = pd.DataFrame(ignored_rows)
                ## restore
                ignored["time"] = ignored["time"].apply(lambda x: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x)))
                ignored["amount"] = ignored["amount"].astype(float)/100
                ignored.to_csv(rest_file_path, sep='\t', index=False)
                
            return transactions