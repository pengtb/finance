import pandas as pd
import time
import json
import asyncio
import os
from mcp_agent.core.fastagent import FastAgent
from . import Transaction, TransactionImporter

class AlipayTransaction(Transaction):
    def assign_categoryId(self, categoryid_description: str, transaction_description: str):
        """
        use keywords & llm to assign categoryId based on given discription dict
        :param categoryid_description: categoryId description json built from transaction categories list API
        :param transaction_description: transaction description json imported from file
        """
        # first by keywords
        ## parse to form json & df
        categoryid_des_json = json.loads(categoryid_description)
        categoryid_des_df = pd.DataFrame(categoryid_des_json)

        transaction_des_json = json.loads(transaction_description)
        payee = transaction_des_json["payee"]
        item = transaction_des_json["item"]
        status = transaction_des_json["status"]
        
        ## by keywords
        subcategory_id = None
        ### investment
        if status == "资金转移":
            if ("余额宝-转出到余额" in item) or ("余额宝-转出到银行卡" in item) or ("余额宝-转出到支付宝" in item) \
                or ("余利宝转出到支付宝" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="赎回", "id"].values[0]
            elif ("余额宝-单次转入" in item) or ("余额宝-大额转入" in item) \
                or ("支付宝转入到余利宝" in item) or ("余利宝-银行卡转入" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="投资", "id"].values[0]
            elif ("自动还款-花呗" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="信用卡还款", "id"].values[0]
            elif ("网商银行" in payee) or ("余额宝" in payee) or ("蚂蚁财富" in payee) or ("黄金" in payee) or ("保险" in payee):
                if ("转入" in item) or ("买入" in item) or ("转换" in item):
                    subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="投资支出", "id"].values[0]
                elif ("转出" in item) or ("卖出" in item):
                    subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="投资赎回", "id"].values[0]
            
        elif status == "已支出":
        ### investment
            if ("帮你投" in item) or ("余利宝" in item) or ("蚂蚁财富" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="投资支出", "id"].values[0]
        ### food
            elif ("肯德基" in payee) or ("麦当劳" in payee) or ("塔斯汀" in payee) or ("德克士" in payee) or ("萨莉亚" in item)\
                or ("肯德基" in item) or ("麦当劳" in item) or ("塔斯汀" in item) or ("德克士" in item) or ("萨莉亚" in payee)\
                or ("面" in item) or ("粉" in item) or ("饭" in item) or ("水饺" in item) or ("包子" in item) \
                    or ("紫光园" in item) or ("眉州东坡" in item)\
                    or ("麻辣烫" in item) or ("烧" in item) or ("汉堡" in item) or ("塔可" in item) \
                        or ("排" in item) or ("披萨" in item) or ("海鲜" in item) or ("涮肉" in item)\
                        or ("牛" in item) or ("鸡" in item) or ("鸭" in item) or ("鱼" in item) or ("兔" in item) \
                    or ("快餐" in item) or ("简餐" in item) or ("酒馆" in item) or ("食品" in payee)\
                or ("美团" in item) or ("扫码付" in item) \
                    or ("餐厅" in payee) or ("餐厅" in item) or ("餐馆" in payee) or ("餐馆" in item) \
                        or ("餐饮" in payee) or ("餐饮" in item) or ("食堂" in payee) or ("食堂" in item) \
                    or ("经营码交易" in item) or ("orderno" in item) or ("堂食" in item) or ("一卡通" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="吃饭", "id"].values[0]
        ### drink & others
            elif ("农夫山泉" in item) or ("luckincoffee" in payee) or ("蜜雪冰城" in payee) \
                or ("CoCo" in item) or ("喜茶" in item) or ("库迪" in payee) or ("书亦烧仙草" in payee)\
                or ("麦叔" in item) or ("超市发" in item) or ("便利" in item)or ("便利" in payee) or ("多点" in item) or ("多点" in payee) or ("好邻居" in item) \
                    or ("智能柜" in payee) or ("7-11" in payee) or ("LAWSON" in item) or ("物美" in payee) or ("全家" in item)\
                    or ("盒马鲜生" in item) or ("外卖" in item) or ("收钱码收款" in item) or ("个体" in item)\
                        or ("商户" in item) or ("百货" in item) or ("经营部" in item) or ("连锁" in item) or ("零售" in item)\
                        or ("果" in item) or ("果" in payee) or ("优鲜" in item) \
                        or ("咖啡" in item) or ("咖啡" in payee) or ("茶" in item)\
                            or ("糕点" in item) or ("小吃" in item) or ("零食" in payee) or ("泡芙" in item) or ("桃酥" in item)\
                                or ("消费" in item) or ("购物" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="饮料水果零食外卖", "id"].values[0]
        ### clothes
            elif ("衫" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="衣服", "id"].values[0]
        ### public transport
            elif ("互通卡" in item) or ("交运" in item) or ("交通" in item) or ("地铁" in item) or ("公交" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="公共交通", "id"].values[0]
        ### hospital
            elif ("医院" in payee) or ("医院" in item) or ("体检" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="检查治疗", "id"].values[0]
        ### drug        
            elif ("药" in item) or ("药店" in payee) or ("药房" in payee):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="药品器械", "id"].values[0]
        ### movie
            elif ("电影" in item) or ("观影" in item) or ("演唱会" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="电影演出", "id"].values[0]
        ### taxi
            elif ("打车" in item) or ("租车" in item) or ("电瓶车" in payee):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="打车租车", "id"].values[0]
        ### subscription
            elif ("连续" in item) or ("极速下载" in item) or (item == "PC 1 Month") \
                or ("88VIP" in item) or ("吃货卡" in item) or ("会员" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="会员订阅", "id"].values[0]
        ### game
            elif ("DL点数" in item) or ("Steam" in item) or ("steam" in item) or ("哔哩哔哩会员购" in payee) \
                or ("起点读书" in payee) or ("阅读" in payee) or ("漫画" in payee)\
                or ("游戏" in item) or ("烧录卡" in item) or ("文创" in item) or ("扩展通行证" in item) or ("书币" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="玩具游戏", "id"].values[0]
        ### network
            elif ("流量" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="电话费", "id"].values[0]
        ### delivery
            elif ("邮寄" in item) or ("运费" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="快递费", "id"].values[0]
        ### travel
            elif ("携程" in payee) or ("博物馆" in item) or ("旅游" in item) or ("导览" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="旅游度假", "id"].values[0]
        ### private car fee
            elif ("停车场" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="私家车费用", "id"].values[0]
        ### airplane
            elif ("机票" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="飞机票", "id"].values[0]
        ### train
            elif ("火车票" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="火车票", "id"].values[0]
        ### phone
            elif ("话费" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="电话费", "id"].values[0]
        ### network
            elif ("网费" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="上网费", "id"].values[0]
        ### tools
            elif ("文化用品" in item) or ("文具" in item) or ("办公" in item) \
                or ("微软授权" in payee) or ("文档订单" in item) \
                    or ("ai" in payee) or ("人工智能" in payee) or ("云计算" in payee) or ("物联网" in payee) or ("数码" in payee) or ("科大讯飞" in payee)\
                        or ("邀请码" in item) or ("授权码" in item)\
                    or ("润雨" in payee):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="工具软件", "id"].values[0]
        ### rent
            elif ("自如" in payee):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="租金贷款", "id"].values[0]
        ### property
            elif ("物业" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="家政物业", "id"].values[0]
        ### water, elec, gas
            elif ("浴卡" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="水电煤气", "id"].values[0]
        ### exam
            elif ("考试费" in item) or ("测试报名费" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="认证考试", "id"].values[0]
        ### tax
            elif ("缴税" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="税费支出", "id"].values[0]
        ### net purchase
            elif ("拼多多" in payee) or ("电源" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="家居电子网购", "id"].values[0]
        ### other fees
            elif ("党费" in item) or ("拍照" in item) or ("大学" in item) or ("图片" in item) or ("便民服务" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="其他支出", "id"].values[0]
        ### credit card / service
            elif ("先享后付" in item) or ("白条" in item) or ("月付" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="信用卡还款", "id"].values[0]
        elif status == "已收入":
        ### investment
            if "卖出至余额宝" in item:
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="投资赎回", "id"].values[0]
            elif ("收益发放" in item) or ("分红至余额宝" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="利息分红", "id"].values[0]
            elif "退款" in item:
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="退款", "id"].values[0]
        if subcategory_id is not None: 
            return subcategory_id

        # then by llm
        if "OPENAI_API_KEY" not in os.environ:
            return None
        ## create prompt
        prompt = f"""
        交易描述: {transaction_description}
        交易类别列表: {categoryid_description}
        请为这笔交易分配一个类别ID（即交易类别列表中的id字段），直接返回该id，不需要解释。形式如123，可直接输入到int()函数。
        """
        
        ## create app & agent
        fast = FastAgent("transaction", quiet=True)
        @fast.agent(
            name="category-assigner",
            model="openai.gpt-4o-mini.medium",
            instruction="你是一个交易分类器，根据交易描述和交易类别列表，为交易分配正确的类别ID。"
        )
        
        ## run agent
        async def run_agent (prompt):
            async with fast.run() as agent:
                response = await agent(prompt)
            return response
        try:
            subcategory_id = int(asyncio.run(run_agent(prompt)))
        except (ValueError, TypeError):
            subcategory_id = None
        return subcategory_id
    
    def assign_accountId(self, accounts_df: pd.DataFrame, transaction_description: str, transaction_subcategory: str):
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
        ## income or expense
        if transaction_subcategory not in ["银行转账", "信用卡还款", "存款取款", "投资", "赎回",
                                           "借入", "借出", "还款", "收债", 
                                           "垫付支出", "报销", "其他转账"]:
            if ("余利宝转入" in item): ### 余利宝仅支持支付宝余额
                pass ### 忽略余利宝转入，手动处理/在导入余利宝明细时处理
            else:
                source_account_name = "余额宝"
                target_account_name = None
        ## investment
        else:
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
            else:
                pass
        
        # transform to account id
        if source_account_name is not None:
            source_account_id = accounts_df.loc[accounts_df["name"]==source_account_name, "id"].values[0]
        else:
            source_account_id = None
        if target_account_name is not None:
            target_account_id = accounts_df.loc[accounts_df["name"]==target_account_name, "id"].values[0]
        else:
            target_account_id = None
        
        return source_account_id, target_account_id

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