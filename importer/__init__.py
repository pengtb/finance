import pandas as pd
import os
import json
import asyncio
import json
from mcp_agent.core.fastagent import FastAgent
from api.transaction import Transaction_API
from api.account import Account_API
        
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
            if ("网商银行" in payee) or ("余额宝" in payee) or ("蚂蚁财富" in payee) or ("黄金" in payee) or ("保险" in payee):
                if ("转入" in item) or ("买入" in item) or ("转换" in item):
                    subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="投资支出", "id"].values[0]
                elif ("转出" in item) or ("卖出" in item):
                    subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="投资赎回", "id"].values[0]
            elif ("余额宝-转出到余额" in item) or ("余额宝-转出到银行卡" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="银行转账", "id"].values[0]
            elif ("自动还款-花呗" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="信用卡还款", "id"].values[0]
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
                        or ("排" in item) or ("披萨" in item) or ("海鲜" in item)\
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
            elif ("打车" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="打车租车", "id"].values[0]
        ### subscription
            elif ("连续" in item) or ("极速下载" in item) or (item == "PC 1 Month") \
                or ("88VIP" in item) or ("吃货卡" in item) or ("会员" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="会员订阅", "id"].values[0]
        ### game
            elif ("DL点数" in item) or ("Steam" in item) or ("哔哩哔哩会员购" in payee) \
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
            elif ("携程" in payee) or ("博物馆" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="旅游度假", "id"].values[0]
        ### public transport
            elif ("互通卡" in item) or ("交运" in item) or ("交通" in item) or ("地铁" in item) or ("公交" in item):
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="公共交通", "id"].values[0]
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
            if "余额宝" in item:
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="利息收入", "id"].values[0]
            elif "蚂蚁财富" in item:
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="投资赎回", "id"].values[0]
            elif "退款" in item:
                subcategory_id = categoryid_des_df.loc[categoryid_des_df["name"]=="退款", "id"].values[0]
        if subcategory_id is not None: 
            return subcategory_id

        # then by llm
        ## create prompt
        prompt = f"""
        交易描述: {transaction_description}
        交易类别列表: {categoryid_description}
        请为这笔交易分配一个类别ID（即id字段），直接返回该id，不需要解释。形式如123，可直接输入到int()函数。
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
            return int(response)
            
        subcategory_id = asyncio.run(run_agent(prompt))
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
            source_account_name = "余额宝"
            target_account_name = None
        ## investment
        else:
            if transaction_subcategory == "银行转账":
                if "余额宝-转出到余额" in item:
                    source_account_name = "余额宝"
                    target_account_name = "支付宝余额"
                elif "余额宝-转出到银行卡" in item:
                    source_account_name = "余额宝"
                    target_account_name = payee ### like "招商银行"
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
    def __init__(self, save_dir: str | None = None):
        # collect categoryids info
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
        
        self.subcategories = merged_df # id, name, parentId, parentName
        
        # collect accounts info
        ## collect current accounts
        api = Account_API()
        response = api.list_accounts()
        accounts = response["result"]
        accounts = pd.DataFrame(accounts).loc[:, ['id', 'name']]
        
        self.accounts = accounts # id, name
        
        # save
        if save_dir is not None:
            os.makedirs(save_dir, exist_ok=True)
            self.subcategories.to_csv(os.path.join(save_dir, "transaction_subcategories.tsv"), sep='\t', index=False)
            self.accounts.to_csv(os.path.join(save_dir, "transaction_accounts.tsv"), sep='\t', index=False)
    
    def import_transactions(self, file_path: str):
        """
        Import transactions from file & return a list of Transaction objects
        """
        raise NotImplementedError("import_transactions method not implemented")