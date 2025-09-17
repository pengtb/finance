import pandas as pd
import time
import json
from . import Transaction, TransactionImporter

class YuLiBaoTransactionImporter(TransactionImporter):
    def __init__(self, save_dir: str | None = None):
        super().__init__(save_dir)
    
    def import_transactions(self, file_path: str, rest_file_path: str | None = None):
        """
        Import transactions from file & return a list of Transaction objects
        """
        # read table from xlsx
        raw_df = pd.read_excel(file_path, sheet_name=0, skiprows=7)
        # preprocess
        ## remove white space
        raw_df = raw_df.map(lambda x: x.strip() if isinstance(x, str) else x)
        ## remove white space in columns
        raw_df.columns = raw_df.columns.str.strip()
        ## subset
        raw_df = raw_df.loc[:, ["交易时间", "交易类型", "对方机构名称", "交易金额", "备注"]]
        ## rename
        raw_df = raw_df.rename(columns={
            "交易时间": "time",
            "交易类型": "status",
            "对方机构名称": "payee",
            "交易金额": "amount",
            "备注": "item"
        })
        ## convert time to timestamp
        raw_df["time"] = raw_df["time"].apply(lambda x: time.mktime(time.strptime(x, "%Y-%m-%d %H:%M:%S"))).astype(int)
        ## format amount
        raw_df["amount"] = abs(raw_df["amount"].astype(float)*100).astype(int)
        
        # init transactions
        ## init transactions list
        transactions = []
        ignored_rows = []
        for _, row in raw_df.iterrows():
            transaction = Transaction()
            transaction.time = row["time"]
            transaction.sourceAmount = row["amount"]
            transaction.destinationAmount = row["amount"]
            transaction.comment = json.dumps(row[["payee", "item", "status"]].to_dict(), ensure_ascii=False)
            ## assign categoryId
            if ("余利宝转入" in row["item"]) or ("余利宝转出" in row["item"]) or ("基金申购" in row["item"]):
                transaction_subcategory_name = "银行转账"
            elif "收益" in row["item"]:
                transaction_subcategory_name = "利息分红"
            elif "消费" in row["item"]:
                transaction_subcategory_name = "投资支出"
            else:
                ignored_rows.append(row)
                continue
            transaction.categoryId = self.subcategories.loc[self.subcategories["name"] == transaction_subcategory_name, "id"].values[0]
            ## assign type
            transaction.type = int(self.subcategories.loc[self.subcategories["id"]==transaction.categoryId, "type"].iloc[0])
            ## assign accountid
            source_account_name = None
            destination_account_name = None
            if (transaction_subcategory_name != "银行转账"):
                source_account_name = "余利宝"
            else:
                destination_account_name = "余利宝"
                if row["payee"] == "支付宝":
                    # source_account_name = "支付宝余额"
                    continue ## already imported in alipay
                elif row["payee"] == "贵阳银行股份有限公司":
                    source_account_name = "贵阳银行"
                elif row["payee"] == "招商银行":
                    source_account_name = "招商银行"
                elif row["payee"] == "成都银行":
                    source_account_name = "成都银行"
                elif row["payee"] == "中国农业银行":
                    source_account_name = "农业银行0679"
                elif row["payee"] == "浙江网商银行":
                    destination_account_name = None ## ignored, manually import
                if ("余利宝转入" in row["item"]) or ("基金申购" in row["item"]):
                    pass
                else:
                    source_account_name, destination_account_name = destination_account_name, source_account_name
            if (source_account_name is None) and (destination_account_name is None):
                ignored_rows.append(row)
                continue
            sourceAccountId = None
            destinationAccountId = None
            if source_account_name is not None:
                sourceAccountId = self.accounts.loc[self.accounts["name"] == source_account_name, "id"].values[0]
            if destination_account_name is not None:
                destinationAccountId = self.accounts.loc[self.accounts["name"] == destination_account_name, "id"].values[0]
            transaction.sourceAccountId = sourceAccountId
            transaction.destinationAccountId = destinationAccountId
            ## collect processed
            transactions.append(transaction)
            
        # save ignored rows
        if (rest_file_path is not None) and (len(ignored_rows) > 0):
            ignored = pd.DataFrame(ignored_rows)
            print(ignored)
            ## restore
            ignored["time"] = ignored["time"].apply(lambda x: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x)))
            ignored["amount"] = ignored["amount"].astype(float)/100
            ignored.to_csv(rest_file_path, sep='\t', index=False)
        
        return transactions 
    
if __name__ == "__main__":
    importer = YuLiBaoTransactionImporter()
    importer.import_transactions("datatables/yulibao_account.xlsx", "datatables/yulibao_transactions_rest.tsv")
    