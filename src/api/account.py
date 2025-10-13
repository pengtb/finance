from . import BaseAPI

class Account_API(BaseAPI):
    def __init__(self):
        super().__init__()
        self.base_url = f"{self.base_url}/accounts"
        
    def list_accounts(self):
        url = f"{self.base_url}/list.json"
        response = self.request_data(url, method='GET')
        return response

    def add_account(self, **account_data):
        """
        Add a new account:
        :param account_data: Account data:
            name: Account name
            balance
            balanceTime
            currency
            type
            category
            color
            icon
            comment
        :return: Response
        """
        url = f"{self.base_url}/add.json"
        response = self.request_data(url, method='POST', data=account_data)
        return response
    
    def delete_account(self, **account_data):
        """
        Delete an account:
        :param account_data: Account data:
            id: Account ID
        :return: Response
        """
        url = f"{self.base_url}/delete.json"
        response = self.request_data(url, method='POST', data=account_data)
        return response
    
    def modify_account(self, **account_data):
        """
        Modify an account:
        :param account_data: Account data:
            id
            name
            balance
            balanceTime
            currency
            type
            category
            color
            icon
            comment
        :return: Response
        """
        url = f"{self.base_url}/modify.json"
        response = self.request_data(url, method='POST', data=account_data)
        return response