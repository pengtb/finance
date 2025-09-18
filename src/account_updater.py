#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api.account import Account_API
from api.transaction import Transaction_API
from importer.eaccount import EAccountImporter
from importer.alipayfund import AlipayFundImporter
from importer.updatefund import FundUpdateTransaction, FundUpdateImporter
from importer import TransactionImporter
from crawler.emailattachment import EmailCrawler
import argparse
import json
import time
from tqdm import tqdm
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

def parse_args(cmdline=None):
    parser = argparse.ArgumentParser(description="ezBookkeeping Account Updater")
    parser.add_argument("--file", type=str, help="Path to the input file")
    parser.add_argument("--action", type=str, help="Action to perform", choices=["add", "list", "delete", "update-fund"])
    parser.add_argument("--importer", type=str, help="Importer to use", choices=["eaccount", "alipay", "update-fund"], default="alipay")
    parser.add_argument("--dry-run", action='store_true')
    parser.add_argument("--crontab", type=str, help="Crontab expression")
    args = parser.parse_known_args(cmdline)[0]
    
    # extra options for add
    if args.action == "add":
        parser.add_argument("--delete-previous", action='store_true', help="if delete previous accounts with the same importer")
        args = parser.parse_known_args(cmdline)[0]
    # extra options for list
    elif args.action == "list":
        parser.add_argument("--show-all", action='store_true', help="if show all columns")
        args = parser.parse_known_args(cmdline)[0]
    elif args.action == "update-fund":
        parser.add_argument("--update-info", action='store_true', help="if update account info using fund crawler")
        parser.add_argument("--update-info-fp", type=str, help="Path to the fund info file", default="datatables/fund_info.tsv")
        args = parser.parse_known_args(cmdline)[0]
        if not args.update_info:
            print("update-info not enabled, you sure?")
        
    # no need for importer when action is list
    if args.action == "list":
        args.importer = None
    elif args.action == "update-fund":
        args.importer = "update-fund"
    return args

def fetch_accounts(api):
    response = api.list_accounts()
    result = response['result']
    result_df = pd.DataFrame(result)
    return result_df

def add_accounts(accounts, api, dry_run=False):
    for account in tqdm(accounts):
        if dry_run:
            print(account.to_dict())
            continue
        response = api.add_account(**account.to_dict())
        if response["success"] != True: 
            print(f"Add account failed: {account.to_dict()}")
            print(response)
            continue
        
def delete_accounts(account_ids, api, dry_run=False):
    for account_id in tqdm(account_ids):
        if dry_run:
            print(f"Delete account {account_id}")
            continue
        response = api.delete_account(id=account_id)
        if response["success"] != True: 
            print(f"Delete account failed: {account_id}")
            print(response)
            continue
        
def update_accounts(account_ids, transaction_api, delta_balances, dry_run=False):
    for account_id, delta_balance in tqdm(zip(account_ids, delta_balances), total=len(account_ids)):
        ### init transaction
        transaction = FundUpdateTransaction()
        transaction.sourceAccountId = account_id
        ### time
        transaction.time = int(time.time())
        ### amount
        transaction.amount = delta_balance
        if delta_balance == 0:
            print(f"Account {account_id} balance not changed, skip update")
            continue
        transaction.sourceAmount = int(abs(delta_balance))
        ### categoryId
        subcategories_df = TransactionImporter.collect_categories()
        subcategories = list(subcategories_df.to_dict(orient="index").values())
        categories_description = json.dumps(subcategories, ensure_ascii=False)
        transaction.categoryId = transaction.assign_categoryId(categories_description)
        transaction.type = int(subcategories_df.loc[subcategories_df["id"]==transaction.categoryId, "type"].iloc[0])
        
        ### add transaction
        if dry_run:
            print(transaction.to_dict())
            continue
        response = transaction_api.add_transaction(**transaction.to_dict())
        if response["success"] != True: 
            print(f"Add transaction failed: {transaction.to_dict()}")
            print(response)
            continue

def main(args):
    # create api
    api = Account_API()
    transaction_api = Transaction_API()
    
    # first list available accounts
    result_df = fetch_accounts(api)
    
    # fetch email attachments if file is not specified
    if not args.file:
        if args.importer == "alipay":
            args.file = "./datatables/alipay_accounts.pdf"
            from_addr = "service@mail.alipay.com"
            attachment_fn_pattern=".*pdf"
        else:
            print(f"Importer {args.importer} not supported, please specify file path")
            exit(1)
        email_crawler = EmailCrawler(save_fp=args.file, from_addr=from_addr, attachment_fn_pattern=attachment_fn_pattern)
        email_crawler.crawl_info()
            
    # create importer
    if args.importer == "eaccount":
        importer = EAccountImporter()
        query_accounts = importer.import_accounts(args.file)
    elif args.importer == "alipay":
        importer = AlipayFundImporter()
        query_accounts = importer.import_accounts(args.file)
    elif args.importer == "update-fund":
        importer = FundUpdateImporter()
        query_accounts = importer.import_accounts(result_df, update_info=args.update_info, update_info_fp=args.update_info_fp)
        
    if (args.action == "list"):
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        if args.show_all:
            print(result_df)
        else:
            print(result_df.loc[:, ['id', 'name', 'balance', 'currency']])
    # add accounts
    elif args.action == "add":
        ## check existing accounts
        existing_accounts_df = result_df[result_df['comment']!=""]
        existing_accounts_df = existing_accounts_df[existing_accounts_df['comment'].apply(lambda x: json.loads(x).get('source', None)==args.importer)]
        toadd_accounts = []
        todelete_accounts_df = []
        toupdate_accounts = []
        if len(existing_accounts_df) > 0: 
            print(f"{len(existing_accounts_df)} Accounts already exist.")
        
        ## delete existing accounts and add all query_accounts
        if args.delete_previous:
            toadd_accounts = query_accounts
            todelete_accounts_df = existing_accounts_df
        ## or update existing accounts and add new ones
        else:
            tobsolete_accounts_df = existing_accounts_df[~existing_accounts_df['name'].isin([account.name for account in query_accounts])]
            old_parent_accounts_df = result_df[result_df['subAccounts'].notna()]
            todelete_accounts_df = pd.concat([tobsolete_accounts_df, old_parent_accounts_df], axis=0)
            toupdate_accounts = [account for account in query_accounts if account.name in existing_accounts_df['name'].tolist()]
            toadd_accounts = [account for account in query_accounts if account.name not in existing_accounts_df['name'].tolist()]
        
        ## delete accounts
        delete_accounts(todelete_accounts_df['id'].tolist(), api, dry_run=args.dry_run)
        if len(todelete_accounts_df) > 0: 
            print(f"Deleted {len(todelete_accounts_df)} accounts")
        ## add accounts
        add_accounts(toadd_accounts, api, dry_run=args.dry_run)
        print(f"Added {len(toadd_accounts)} accounts")
        ## update existing accounts
        if len(toupdate_accounts) > 0:
            print(f"Accounts to update: {[account.name for account in toupdate_accounts]}")
            ### account ids
            toupdate_account_names = [account.name for account in toupdate_accounts]
            toupdate_account_ids = existing_accounts_df.set_index('name').loc[toupdate_account_names, 'id'].tolist()
            ### delta balances
            prev_balances = existing_accounts_df.set_index('name').loc[toupdate_account_names, 'balance'].tolist()
            current_balances = [account.balance for account in toupdate_accounts]
            delta_balances = [float(current_balance - prev_balance) for current_balance, prev_balance in zip(current_balances, prev_balances)]
            ### create transactions
            update_accounts(toupdate_account_ids, transaction_api, delta_balances, dry_run=args.dry_run)
        
    elif args.action == "delete":
        ## filter accounts according to query
        query_df = pd.DataFrame([account.to_dict() for account in query_accounts])
        ## merge dataframes
        merged_df = pd.merge(result_df.loc[:, ['id', 'name', 'type']], query_df, on='name', how='inner')

        # delete accounts
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
            
    # update-fund
    elif (args.action == "update-fund"):
        ### toupdate account ids
        toupdate_account_ids = [account.id for account in query_accounts]
        ### delta balances
        prev_balances = [account.prev_balance for account in query_accounts]
        current_balances = [account.balance for account in query_accounts]
        delta_balances = [float(current_balance - prev_balance) for current_balance, prev_balance in zip(current_balances, prev_balances)]
        ### create transactions
        update_accounts(toupdate_account_ids, transaction_api, delta_balances, dry_run=args.dry_run)
            
            
if __name__ == "__main__":
    # parse arguments
    args = parse_args()
    
    if args.crontab:
        # create scheduler
        scheduler = BackgroundScheduler()
        ## add job
        scheduler.add_job(main, CronTrigger.from_crontab(args.crontab), args=[args])
        ## start scheduler
        print(f"Add job: {args.crontab}")
        scheduler.start()
        ## block main thread
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            print("Scheduler shutdown.")
            exit(0)
    else:
        main(args)