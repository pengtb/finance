from api.transaction import Transaction_API
from importer.alipay import AlipayTransactionImporter
import argparse
from tqdm import tqdm
import pandas as pd

def parse_args(cmdline=None):
    parser = argparse.ArgumentParser(description="ezBookkeeping Transaction Updater")
    parser.add_argument("--file", type=str, help="Path to the input file")
    parser.add_argument("--rest-file", type=str, help="Path to the rest and not imported file")
    parser.add_argument("--save-dir", type=str, help="Path to save account and transaction subcategories", default="./datatables")
    parser.add_argument("--action", type=str, help="Action to perform", choices=["add", "list", "delete", "modify", "list-category", "list-tag"])
    parser.add_argument("--importer", type=str, help="Importer to use", choices=["alipay"], default="alipay")
    args = parser.parse_args(cmdline)
    
    # no need for importer if list-category or list-tag
    if (args.action == "list-category") or (args.action == "list-tag"):
        args.importer = None
    return args

if __name__ == "__main__":
    # parse arguments
    args = parse_args()
    
    # create api
    api = Transaction_API()
    
    # create importer
    if args.importer == "alipay":
        importer = AlipayTransactionImporter(args.save_dir)
        query_transactions = importer.import_transactions(args.file, args.rest_file)
            
    # add transaction
    if args.action == "add":
        for transaction in tqdm(query_transactions):
            response = api.add_transaction(**transaction.to_dict())
            if response["success"] != True: 
                print(transaction.to_dict())
                raise Exception(response)
        print(f"Added {len(query_transactions)} transactions")
        
    # list & modify & delete transactions
    elif (args.action == "list") or (args.action == "modify") or (args.action == "delete"):
        response = api.list_transactions(count=50)
        ## convert to dataframe
        result = response['result']
        result_df = pd.DataFrame(result)
        
        # list accounts
        if (args.action == "list"):
            print(result_df.loc[:, ['name', 'balance', 'currency']])
            
    elif args.action == "list-category":
        response = api.list_transaction_categories()
        print(response)
        
    elif args.action == "list-tag":
        response = api.list_transaction_tags()
        print(response)