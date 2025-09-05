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
        return {
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
        