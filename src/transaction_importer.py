#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.transaction import Transaction_API
from importer.alipay import AlipayTransactionImporter
from importer.yulibao import YuLiBaoTransactionImporter
from importer import TransactionImporter
import argparse
import time
from tqdm import tqdm
import pandas as pd

def parse_args(cmdline=None):
    parser = argparse.ArgumentParser(description="ezBookkeeping Transaction Updater")
    parser.add_argument("--action", type=str, help="Action to perform", choices=["add", "list", "delete", "modify", "list-category", "list-tag"])
    parser.add_argument("--dry-run", action="store_true", help="Dry run, do not actually add, modify or delete transactions")
    args = parser.parse_known_args(cmdline)[0]
        
    # extra options for add
    if args.action == "add":
        parser.add_argument("--importer", type=str, help="Importer to use", choices=["alipay", "yulibao"], default="alipay")
        parser.add_argument("--file", type=str, help="Path to the input file")
        parser.add_argument("--rest-file", type=str, help="Path to the rest and not imported file", default="./datatables/rest_transactions.tsv")
        parser.add_argument("--save-dir", type=str, help="Path to save account and transaction subcategories", default="./datatables")
    # extra options for list
    if args.action == "list":
        parser.add_argument("--history", action="store_true", help="List all past transactions, not only this month")
        parser.add_argument("--type", type=int, help="Transaction type: 根据交易类型（1：修改余额，2：收入，3：支出，4：转账）过滤交易", choices=[1, 2, 3, 4], default=3)
        parser.add_argument("--categories", type=str, help="Comma-separated list of transaction categories to filter", default=None)
    # extra options for modify & delete
    if (args.action == "modify") or (args.action == "delete"):
        parser.add_argument("--id", type=str, help="Transaction ID to modify or delete", default=None, required=True)
        
    args = parser.parse_known_args(cmdline)[0]
        
    return args

if __name__ == "__main__":
    # parse arguments
    args = parse_args()
    
    # create api
    api = Transaction_API()
            
    if args.action == "add":
        ## create importer
        if args.importer == "alipay":
            importer = AlipayTransactionImporter(args.save_dir)
            ## create transactions
            query_transactions = importer.import_transactions(args.file, args.rest_file)
        elif args.importer == "yulibao":
            importer = YuLiBaoTransactionImporter(args.save_dir)
            ## create transactions
            query_transactions = importer.import_transactions(args.file, args.rest_file)
        ## import transactions
        for transaction in tqdm(query_transactions):
            if args.dry_run:
                print(transaction.to_dict())
                continue
            response = api.add_transaction(**transaction.to_dict())
            if response["success"] != True: 
                print(transaction.to_dict())
                raise Exception(response)
        print(f"Added {len(query_transactions)} transactions")
        
    elif (args.action == "list"):
        transaction_filters = {"count": 50, "type": args.type}
        ## if only list this month
        if not args.history:
            current_month = time.strftime("%Y-%m", time.localtime())
            min_time = current_month + "-01"
            min_timestamp = int(time.mktime(time.strptime(min_time, "%Y-%m-%d")))
            transaction_filters["min_time"] = min_timestamp
            transaction_filters["max_time"] = 0
        ## if categories are specified
        if args.categories:
            categories_df = TransactionImporter.collect_categories()
            categories_df = categories_df[categories_df["name"].isin(args.categories.split(","))]
            transaction_filters["category_ids"] = ",".join(categories_df["id"].astype(str).tolist())
        ## request transactions
        if args.dry_run:
            print(transaction_filters)
        else:
            response = api.list_transactions(**transaction_filters)
        ## convert to dataframe
            if response["success"] != True: 
                raise Exception(response)
            result = response['result']["items"]
            result_df = pd.DataFrame(result)
        
        # list accounts
            pd.set_option('display.max_columns', None)
            print(result_df.loc[:, ["id", "type", "time", 
                                    'sourceAccount', 'destinationAccount',
                                    'sourceAmount']])
            
    elif args.action == "list-category":
        category_df = TransactionImporter.collect_categories()
        print(category_df)
        
    elif args.action == "list-tag":
        response = api.list_transaction_tags()
        print(response)
        
    elif args.action == "delete":
        if args.dry_run:
            print(f"Delete transaction {args.id}")
        else:
            response = api.delete_transaction(args.id)
            if response["success"] != True: 
                raise Exception(response)
            print(f"Deleted transaction {args.id}")
