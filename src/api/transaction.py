from . import BaseAPI, BASE_URL

class Transaction_API(BaseAPI):
    def __init__(self):
        super().__init__()
        self.base_url = f"{self.base_url}/transactions"
        
    def list_transactions(self, **transaction_filters):
        """
        List transactions:
        :param transaction_filters: Transaction filters:
            type
            category_ids
            account_ids
            tag_ids
            tag_filter_type
            amount_filter
            keyword
            max_time
            min_time
            page
            count: necessary, max 50
            with_count
            with_pictures
            trim_account
            trim_category
            trim_tag
        :return: Response
        """
        url = f"{self.base_url}/list.json"
        response = self.request_data(url, method='GET', data=transaction_filters)
        return response

    def add_transaction(self, **transaction_data):
        """
        Add a new transaction:
        :param transaction_data: Transaction data:
            type: necessary
            categoryId: necessary
            time: necessary
            utcOffset: necessary
            sourceAccountId: necessary
            destinationAccountId: optional
            sourceAmount: necessary
            destinationAmount: optional
            tagIds: optional
            pictureIds: optional
            comment: optional
            geoLocation: optional
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
    
    def list_transaction_categories(self):
        url = f"{BASE_URL}/transaction/categories/list.json"
        response = self.request_data(url, method='GET')
        return response
    
    def add_transaction_category(self, **category_data):
        """
        Add a new transaction category:
        :param category_data: Category data:
            name
            type
            parentId
            color
            icon
            comment
        :return: Response
        """
        url = f"{BASE_URL}/transaction/categories/add.json"
        response = self.request_data(url, method='POST', data=category_data)
        return response
    
    def list_transaction_tags(self):
        url = f"{BASE_URL}/transaction/tags/list.json"
        response = self.request_data(url, method='GET')
        return response
    
    def add_transaction_tag(self, **tag_data):
        """
        Add a new transaction tag:
        :param tag_data: Tag data:
            name
        :return: Response
        """
        url = f"{BASE_URL}/transaction/tags/add.json"
        response = self.request_data(url, method='POST', data=tag_data)
        return response