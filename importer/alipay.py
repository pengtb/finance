import pandas as pd
import time
import json
from . import Transaction, TransactionImporter

class AlipayTransactionImporter(TransactionImporter):
    def __init__(self, save_dir: str | None = None):
        super().__init__(save_dir)
    
    def import_transactions(self, file_path: str, rest_file_path: str | None = None):
        """
        Import transactions from file & return a list of Transaction objects
        """
        # read table from csv
        raw_df = pd.read_csv(file_path, skiprows=4, skipfooter=8, encoding='gbk', engine='python',
                             usecols=[2,7,8,9,11,13,15]
                            #  usecols=["交易创建时间", "交易对方", "商品名称", "金额（元）", 
                            #           "交易状态", "成功退款（元）","资金状态"]
                             )
        
        # preprocess
        ## remove white space
        raw_df = raw_df.map(lambda x: x.strip() if isinstance(x, str) else x)
        ## remove white space in column name
        raw_df.columns = raw_df.columns.str.strip()
        ## only success transaction
        raw_df = raw_df[raw_df["交易状态"].isin(["交易成功", "交易关闭"])].drop(columns=["交易状态"])
        ## rename columns
        raw_df = raw_df.rename(columns={
            "交易创建时间": "time",
            "交易对方": "payee",
            "商品名称": "item",
            "金额（元）": "amount",
            "成功退款（元）": "refund",
            "资金状态": "status",
        })
        ## convert time to timestamp
        raw_df = raw_df[raw_df["time"]!=""]
        raw_df["time"] = raw_df["time"].apply(lambda x: time.mktime(time.strptime(x, "%Y-%m-%d %H:%M:%S"))).astype(int)
        ## format amount & refund
        raw_df["amount"] = (raw_df["amount"].astype(float)*100).astype(int)
        raw_df["refund"] = (raw_df["refund"].astype(float)*100).astype(int)
        
        # init transactions
        ## init categoryids
        subcategories = list(self.subcategories.to_dict(orient="index").values())
        categories_description = json.dumps(subcategories, ensure_ascii=False)
        ## init transactions list
        transactions = []
        ignored_rows = []
        for _, row in raw_df.iterrows():
            if row["status"] == "冻结": 
                continue
            transaction = Transaction()
            transaction.time = row["time"]
            transaction.sourceAmount = row["amount"]
            transaction.destinationAmount = row["amount"]
            transaction.comment = json.dumps(row[["payee", "item", "status"]].to_dict(), ensure_ascii=False)
            ## assign categoryId
            transaction.categoryId = transaction.assign_categoryId(categories_description, transaction.comment)
            if transaction.categoryId not in self.subcategories["id"].values:
                print(f"Transaction {transaction.to_dict()} with subcategory unassigned.")
                ignored_rows.append(row)
                continue
            transaction_subcategory = self.subcategories.loc[self.subcategories["id"]==transaction.categoryId, "name"].iloc[0]
            ## assign type
            transaction.type = int(self.subcategories.loc[self.subcategories["id"]==transaction.categoryId, "type"].iloc[0])
            ## assign accountId
            sourceAccountId, destinationAccountId = transaction.assign_accountId(self.accounts, transaction.comment, transaction_subcategory)
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
            ignored["refund"] = ignored["refund"].astype(float)/100
            ignored.to_csv(rest_file_path, sep='\t', index=False)
            
        return transactions 
    
if __name__ == "__main__":
    importer = AlipayTransactionImporter()
    # print(importer.subcategories)
    pd.DataFrame(importer.subcategories).to_csv("./datatables/transaction_subcategories.tsv", sep='\t', index=False)
    # transactions = importer.import_transactions("D:\\netdisk\\nextcloud\\本地\\finance\\支付宝\\alipay_record_20250905_1745_1.csv")
    # print(transactions[0].to_dict())