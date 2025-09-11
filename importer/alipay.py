import pandas as pd
import time
import json
from . import Transaction, TransactionImporter
from api.transaction import Transaction_API

class AlipayTransactionImporter(TransactionImporter):
    def __init__(self):
        # collect categoryids
        ## collect current categoryids
        api = Transaction_API()
        response = api.list_transaction_categories()
        ## flatten categoryids
        categories = response["result"]
        categories = categories["1"] + categories["2"] + categories["3"]
        subcategories = [category["subCategories"] for category in categories]
        subcategories = [subcategory for subcategory_list in subcategories for subcategory in subcategory_list]
        ## only id & name (& parentId)
        subcategories = [{
            "id": subcategory["id"],
            "name": subcategory["name"],
            "parentId": subcategory["parentId"]
        } for subcategory in subcategories]
        categories = [{
            "id": category["id"],
            "name": category["name"]
        } for category in categories]
        ## merge using pandas df
        subcategories_df = pd.DataFrame(subcategories)
        categories_df = pd.DataFrame(categories)
        merged_df = pd.merge(subcategories_df, 
                             categories_df.rename(columns={"id":"parentId", "name":"parentName"}), 
                             on='parentId', how='inner')
        subcategories = list(merged_df.to_dict(orient="index").values())
        
        self.subcategories = subcategories
    
    def import_transactions(self, file_path: str):
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
        raw_df = raw_df[raw_df["交易状态"] != "交易关闭"].drop(columns=["交易状态"])
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
        categories_description = json.dumps(self.subcategories, ensure_ascii=False)
        ## init transactions list
        transactions = []
        for _, row in raw_df.iterrows():
            transaction = Transaction()
            transaction.time = row["time"]
            transaction.sourceAmount = row["amount"] - row["refund"]
            transaction.comment = json.dumps(row[["payee", "item", "status"]].to_dict(), ensure_ascii=False)
            transaction.categoryId = transaction.assign_categoryId(categories_description, 
                                                                   transaction.comment)
            transactions.append(transaction)
            break
        return transactions 
    
if __name__ == "__main__":
    importer = AlipayTransactionImporter()
    transactions = importer.import_transactions("D:\\netdisk\\nextcloud\\本地\\finance\\支付宝\\alipay_record_20250905_1745_1.csv")
    print(transactions[0].to_dict())