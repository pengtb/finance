import pandas as pd
import time
import json
from . import Transaction, TransactionImporter

class AlipayTransaction(Transaction):
    def assign_categoryId(self, categoryid_description: str, transaction_description: str):
        return super().assign_categoryId(categoryid_description, transaction_description)
    
    def assign_accountId(self, accounts_df: pd.DataFrame, transaction_description: str, transaction_subcategory: str, subcategories_df: pd.DataFrame):
        """
        Assign accountId to transaction by hard coding
        """
        # parse transaction_description
        transaction_des_json = json.loads(transaction_description)
        payee = transaction_des_json["payee"]
        item = transaction_des_json["item"]
        status = transaction_des_json["status"]
        # assign by subcategory
        source_account_name = None
        target_account_name = None

        if transaction_subcategory == "赎回":
            if "余额宝-转出到余额" in item:
                source_account_name = "余额宝"
                target_account_name = "支付宝余额"
            elif "余额宝-转出到银行卡" in item:
                source_account_name = "余额宝"
                target_account_name = payee ### like "招商银行"
            elif "余利宝转出到支付宝" in item:
                source_account_name = "余利宝"
                target_account_name = "支付宝余额"
        elif transaction_subcategory == "投资":
            if ("余额宝-大额转入" in item) or ("余额宝-单次转入" in item):
                pass ### 忽略余额宝转入，手动处理/在导入银行账户明细时处理
            elif "支付宝转入到余利宝" in item:
                source_account_name = "支付宝余额"
                target_account_name = "余利宝"
            elif "余利宝-银行卡转入" in item:
                pass ### 忽略余利宝银行卡转入，手动处理/在导入余利宝明细时处理
        elif transaction_subcategory == "信用卡还款":
            if "自动还款-花呗" in item:
                source_account_name = "余额宝"
                target_account_name = "花呗|信用购"
            elif "先享后付" in item:
                source_account_name = "余额宝"
                target_account_name = "饿了么先享后付"
            elif "白条" in item: ### to check
                source_account_name = "余额宝"
                target_account_name = "京东白条"
            elif "月付" in item:
                source_account_name = "余额宝"
                target_account_name = "美团月付"
            else:
                pass
        elif transaction_subcategory in ["投资支出", "投资赎回", "利息分红"]:
            source_account_name = "余额宝"
            target_account_name = None
        else:
            transaction_typedes = subcategories_df.loc[subcategories_df["name"]==transaction_subcategory, "typeDesc"].values[0]
            if transaction_typedes == "支出":
                source_account_name = "花呗|信用购"
                target_account_name = None
            else:
                pass
        
        # transform to account id
        try:
            if source_account_name is not None:
                source_account_id = accounts_df.loc[accounts_df["name"]==source_account_name, "id"].values[0]
            else:
                source_account_id = None
            if target_account_name is not None:
                target_account_id = accounts_df.loc[accounts_df["name"]==target_account_name, "id"].values[0]
            else:
                target_account_id = None
            
        except:
            source_account_id = None
            target_account_id = None
        return source_account_id, target_account_id
    
class AlipayAppTransaction(Transaction):
    def assign_categoryId(self, categoryid_description: str, transaction_description: str):
        ## parse transaction_description
        transaction_des_json = json.loads(transaction_description)
        payee = transaction_des_json["payee"]
        item = transaction_des_json["item"]
        status = transaction_des_json["status"]
        
        ## replace status
        replace_dict = {"收入": "已收入", "支出": "已支出", "不计收支": "资金转移"}
        transaction_des_json["status"] = replace_dict[status]
        
        ## adjust status
        if ("卖出至余额宝" in item) or ("收益发放" in item) or ("分红至余额宝" in item) or ("退款" in item):
            transaction_des_json["status"] = "已收入"
        
        ## new transaction_description
        transaction_description = json.dumps(transaction_des_json, ensure_ascii=False)
        
        # same as AlipayTransaction
        return super().assign_categoryId(categoryid_description, transaction_description)
        
    def assign_accountId(self, accounts_df: pd.DataFrame, transaction_description: str, transaction_subcategory: str, subcategories_df: pd.DataFrame):
        # parse transaction_description
        transaction_des_json = json.loads(transaction_description)
        item = transaction_des_json["item"]
        method = transaction_des_json["method"]
        if not isinstance(method, str):
            method = "余额宝"
        
        ## new transaction_description
        transaction_description = json.dumps(transaction_des_json, ensure_ascii=False)
        return super().assign_accountId(accounts_df, transaction_description, transaction_subcategory, subcategories_df)

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
            transaction = AlipayTransaction()
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
            ignored["refund"] = ignored["refund"].astype(float)/100
            ignored.to_csv(rest_file_path, sep='\t', index=False)
            
        return transactions
    
class AlipayAppTransactionImporter(TransactionImporter):
    def __init__(self, save_dir: str | None = None):
        super().__init__(save_dir)
    
    def import_transactions(self, file_path: str, rest_file_path: str | None = None):
        """
        Import transactions from file & return a list of Transaction objects
        """
        # read table from csv
        raw_df = pd.read_csv(file_path, skiprows=24, encoding='gbk', engine='python',
                             usecols=[0,1,2,4,5,6,7,8]
                            #  usecols=["交易时间", "交易分类", "交易对方", "商品说明", 
                            #           "收/支", "金额", "收/付款方式", "交易状态"]
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
            "交易时间": "time",
            "交易分类": "category",
            "交易对方": "payee",
            "商品说明": "item",
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
            transaction = AlipayAppTransaction()
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
    
if __name__ == "__main__":
    importer = AlipayTransactionImporter()
    # print(importer.subcategories)
    pd.DataFrame(importer.subcategories).to_csv("./datatables/transaction_subcategories.tsv", sep='\t', index=False)
    # transactions = importer.import_transactions("D:\\netdisk\\nextcloud\\本地\\finance\\支付宝\\alipay_record_20250905_1745_1.csv")
    # print(transactions[0].to_dict())