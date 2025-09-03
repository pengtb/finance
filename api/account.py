from . import Updater_API

class Account_API(Updater_API):
    def __init__(self):
        super().__init__()
        
    def list_accounts(self):
        url = f"{self.base_url}/accounts/list.json"
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
        :return: Response
        """
        url = f"{self.base_url}/accounts/add.json"
        response = self.request_data(url, method='POST', data=account_data)
        return response
    
    def delete_account(self, id: str):
        """
        Delete an account:
        :param id: Account ID
        :return: Response
        """
        url = f"{self.base_url}/accounts/delete.json"
        response = self.request_data(url, method='POST', data={'Id': id})
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
        :return: Response
        """
        url = f"{self.base_url}/accounts/modify.json"
        response = self.request_data(url, method='POST', data=account_data)
        return response