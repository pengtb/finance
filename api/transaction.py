from . import BaseAPI

class Transaction_API(BaseAPI):
    def __init__(self):
        super().__init__()
        self.base_url = f"{self.base_url}/transactions"
        
    def list_transactions(self):
        url = f"{self.base_url}/list.json"
        response = self.request_data(url, method='GET')
        return response

    def add_transaction(self, **transaction_data):
        """
        Add a new transaction:
        :param transaction_data: Transaction data:
            type
            categoryId
            time
            utcOffset
            sourceAccountId
            destinationAccountId
            sourceAmount
            destinationAmount
            comment
        :return: Response
        """
        url = f"{self.base_url}/add.json"
        response = self.request_data(url, method='POST', data=transaction_data)
        return response
    
    def delete_transaction(self, id: str):
        """
        Delete a transaction:
        :param id: Transaction ID
        :return: Response
        """
        url = f"{self.base_url}/delete.json"
        response = self.request_data(url, method='POST', data={'Id': id})
        return response
    
    def modify_transaction(self, **transaction_data):
        """
        Modify a transaction:
        :param transaction_data: Transaction data:
            id
            categoryId
            time
            utcOffset
            sourceAccountId
            destinationAccountId
            sourceAmount
            destinationAmount
            comment
        :return: Response
        """
        url = f"{self.base_url}/modify.json"
        response = self.request_data(url, method='POST', data=transaction_data)
        return response