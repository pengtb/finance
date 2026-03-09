# Fund Import and Update Tools for ezBookkeeping

English | [中文](README.cn.md)

## Introduction

The tool is mainly used to import AliPay Fund accounts into [ezBookkeeping](https://github.com/mayswind/ezbookkeeping), using fund details sent to the specified email address.
It also supports automatically updating balances of imported accounts using latest info fetched via [AKShare](https://akshare.akfamily.xyz/index.html).
Importation of fund accounts (a.k.a. creating new accounts) and update of balances (a.k.a. creating new transactions) are implemented using [ezBookkeeping](https://github.com/mayswind/ezbookkeeping) API.

## Features

- Import Fund accounts from exported pdfs from AliPay / EAccount;
- Update balances of imported accounts using info from [AKShare](https://akshare.akfamily.xyz/index.html);
- Keyword-based and LLM-based category assignment of transactions from AliPay / YuLiBao exported tables;
- List accounts, transactions and transaction categories;

## Installation

### Using pip

1. Clone the repository: `git clone https://github.com/pengtb/finance.git`
2. Navigate to the project directory: `cd finance`
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables: `copy .env.example .env`, edit `.env` file with your own values, then `set -a && source .env && set +a` (for Linux/Mac).
5. Run the tool to list accounts for check: `python src/account_updater.py --action list`

### Using docker

1. Pull the docker image: `docker pull ptbjerry/finance`
2. Set up environment variables: `copy .env.example .env`, edit `.env` file with your own values, then `set -a && source .env && set +a` (for Linux/Mac).
3. Run the tool to list accounts for check: `docker run --env-file .env ptbjerry/finance python account_updater.py --action list`

## Usage: docker-compose with ezBookkeeping

1. ezBookkeeping should be configured (see [ezBookkeeping installation guide](http://ezbookkeeping.mayswind.net/installation#use-docker-compose)) and running with API enabled (see [ezBookkeeping API documentation](http://ezbookkeeping.mayswind.net/httpapi)) first. 
It is better to set a longer timeout for ezBookkeeping API in configuration file.
1. Set up environment variables: `copy .env.example .env`, edit `.env` file with your own values.
2. According to the `docker-compose.yml` file in the repo, add the following service, to auto update alipay fund accounts:

```yaml
  account_updater:
    image: docker.xuanyuan.me/ptbjerry/finance
    container_name: account_updater
    env_file:
      - .env
    restart: always
    volumes:
      - "./datatables:/app/src/datatables"
    command: ["python", "account_updater.py", "--action", "update-fund", "--update-info", "--crontab", "${CRON_ACCOUNT_UPDATER}"]

  alipay_account_importer:
    image: docker.xuanyuan.me/ptbjerry/finance
    container_name: alipay_account_importer
    env_file:
      - .env
    restart: always
    volumes:
      - "./datatables:/app/src/datatables"
    command: ["python", "account_updater.py", "--action", "add", "--importer", "alipay", "--crontab", "${CRON_ACCOUNT_IMPORTER}"]
```

3. Restart docker-compose: `docker-compose up -d`

## Acknoledgements

- [ezBookkeeping](https://github.com/mayswind/ezbookkeeping)
- [AKShare](https://akshare.akfamily.xyz/index.html)
