#!/usr/bin/env bash
target_file=$1

echo "${CRON_ACCOUNT_UPDATER} /app/src/account_updater.py --action update-fund" >> $target_file
echo "${CRON_ACCOUNT_IMPORTER} /app/src/account_updater.py --action add --importer alipay" >> $target_file
echo "${CRON_ACCOUNT_IMPORTER} /app/src/account_updater.py --action add --importer yulibao" >> $target_file
