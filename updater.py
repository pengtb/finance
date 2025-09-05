from api.account import Account_API
from importer.eaccount import EAccountImporter
import argparse
from tqdm import tqdm
import pandas as pd

def parse_args(cmdline=None):
    parser = argparse.ArgumentParser(description="ezBookkeeping Updater")
    parser.add_argument("--file", type=str, help="Path to the input file")
    parser.add_argument("--action", type=str, help="Action to perform", choices=["add", "list", "delete", "modify"])
    parser.add_argument("--api", type=str, help="API to use", choices=["account"], default="account")
    parser.add_argument("--importer", type=str, help="Importer to use", choices=["eaccount"], default="eaccount")
    parser.add_argument("--update-info", action='store_true')
    args = parser.parse_args(cmdline)
    return args

if __name__ == "__main__":
    # parse arguments
    args = parse_args()
    
    # create api
    if args.api == "account":
        api = Account_API()
        
        # create importer
        if args.importer == "eaccount":
            importer = EAccountImporter()
            query_accounts = importer.import_accounts(args.file, update_info=args.update_info)
                
        # add accounts
        if args.action == "add":
            for account in tqdm(query_accounts):
                api.add_account(**account.to_dict())
            print(f"Added {len(query_accounts)} accounts")
            
        # list & modify & delete accounts
        elif (args.action == "list") or (args.action == "modify") or (args.action == "delete"):
            response = api.list_accounts()
            ## convert to dataframe
            result = response['result']
            result_df = pd.DataFrame(result)
            
            # list accounts
            if (args.action == "list"):
                print(result_df.loc[:, ['name', 'balance', 'currency']])
                
            elif (args.action == "modify") or (args.action == "delete"):
                ## filter accounts according to query
                query_df = pd.DataFrame([account.to_dict() for account in query_accounts])
                ## merge dataframes
                merged_df = pd.merge(result_df.loc[:, ['id', 'name']], query_df, on='name', how='inner')
                
                # modify accounts
                if (args.action == "modify"):
                    for id in tqdm(merged_df['id']):
                        api.modify_account(**merged_df[merged_df['id'] == id].to_dict())
                    print(f"Modified {len(merged_df)} accounts")

                # delete accounts
                elif (args.action == "delete"):
                    for id in tqdm(merged_df['id']):
                        api.delete_account(id)
                    print(f"Deleted {len(merged_df)} accounts")
                