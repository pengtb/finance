from api.account import Account_API
from importer.eaccount import EAccountImporter
from importer.alipayfund import AlipayFundImporter
import argparse
import json
import time
from tqdm import tqdm
import pandas as pd

def parse_args(cmdline=None):
    parser = argparse.ArgumentParser(description="ezBookkeeping Account Updater")
    parser.add_argument("--file", type=str, help="Path to the input file")
    parser.add_argument("--action", type=str, help="Action to perform", choices=["add", "list", "delete", "modify"])
    parser.add_argument("--importer", type=str, help="Importer to use", choices=["eaccount", "alipay"], default="alipay")
    parser.add_argument("--update-info", action='store_true')
    parser.add_argument("--dry-run", action='store_true')
    args = parser.parse_known_args(cmdline)[0]
    
    # extra options for add
    if args.action == "add":
        parser.add_argument("--not-delete-previous", action='store_true', help="Only add accounts and not delete previous accounts")
        args = parser.parse_known_args(cmdline)[0]
        
    # no need for importer when action is list
    if args.action == "list":
        args.importer = None
    return args

if __name__ == "__main__":
    # parse arguments
    args = parse_args()
    
    # create api
    api = Account_API()
    
    # create importer
    if args.importer == "eaccount":
        importer = EAccountImporter()
        query_accounts = importer.import_accounts(args.file, update_info=args.update_info)
        
    elif args.importer == "alipay":
        importer = AlipayFundImporter()
        query_accounts = importer.import_accounts(args.file, update_info=args.update_info)
            
    # first list available accounts
    response = api.list_accounts()
    result = response['result']
    result_df = pd.DataFrame(result)
        
    if (args.action == "list"):
        print(result_df.loc[:, ['id', 'name', 'balance', 'currency']])
        
    # add accounts
    elif args.action == "add":
        ## check existing accounts
        existing_accounts = result_df[result_df['comment']!=""]
        existing_accounts = existing_accounts[existing_accounts['comment'].apply(lambda x: json.loads(x).get('source', None)==args.importer)]
        if len(existing_accounts) > 0:
            print(f"Accounts already exist: {existing_accounts[['id', 'name']].to_dict(orient='records')}")
            ## delete existing accounts
            if not args.not_delete_previous:
                for _, account in existing_accounts.iterrows():
                    if args.dry_run:
                        print(f"Delete account {account['id']}")
                    else:
                        response = api.delete_account(id=account['id'])
                        if response["success"] != True: 
                            print(f"Delete account failed: {account.to_dict()}")
                            print(response)
                            continue
        ## add others
            query_accounts = [account for account in query_accounts if account.name not in existing_accounts['name'].tolist()]
        for account in tqdm(query_accounts):
            if args.dry_run:
                print(account.to_dict())
                continue
            response = api.add_account(**account.to_dict())
            if response["success"] != True: 
                print(f"Add account failed: {account.to_dict()}")
                print(response)
                continue
        print(f"Added {len(query_accounts)} accounts")
        
    elif (args.action == "modify") or (args.action == "delete"):
        ## filter accounts according to query
        query_df = pd.DataFrame([account.to_dict() for account in query_accounts])
        ## merge dataframes
        merged_df = pd.merge(result_df.loc[:, ['id', 'name']], query_df, on='name', how='inner')
        
        # modify accounts
        if (args.action == "modify"):
            for id in tqdm(merged_df['id']):
                if args.dry_run:
                    modified_accounts = merged_df[merged_df['id'] == id]
                    print(modified_accounts)
                    continue
                response = api.modify_account(**modified_accounts.to_dict())
                if response["success"] != True: 
                    print(f"Modify account failed: {modified_accounts.to_dict()}")
                    print(response)
                    continue
            print(f"Modified {len(merged_df)} accounts")

        # delete accounts
        elif (args.action == "delete"):
            for id in tqdm(merged_df['id']):
                if args.dry_run:
                    print(f"Delete account {id}")
                    continue
                response = api.delete_account(id=id)
                if response["success"] != True: 
                    print(f"Delete account failed: {id}")
                    print(response)
                    continue
            print(f"Deleted {len(merged_df)} accounts")
            