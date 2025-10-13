# ezBookkeeping的基金导入和更新工具

[English](README.md) | 中文

## 简介

该工具主要用于将支付宝基金账户导入[ezBookkeeping](https://github.com/mayswind/ezbookkeeping)，使用发送到指定邮箱的基金详情。 它还支持使用通过[AKShare](https://akshare.akfamily.xyz/index.html)获取的最新信息自动更新已导入账户的余额。基金账户的导入（即创建新账户）和余额更新（即创建新交易）通过ezBookkeeping API实现。

## 功能

- 导入从支付宝/易账户导出的基金详情；
- 使用[AKShare](https://akshare.akfamily.xyz/index.html)获取的基金最新信息更新已导入账户的余额；
- 基于关键词和LLM的交易类别分类；
- 列出所有账户、交易和交易分类；

## 安装

### 使用pip

1. 克隆项目仓库：`git clone https://github.com/pengtb/finance.git`
2. 进入项目目录：`cd finance`
3. 安装依赖：`pip install -r requirements.txt`
4. 配置ezBookkeeping API：确保ezBookkeeping已启动并运行，并且已获取[API密钥](http://ezbookkeeping.mayswind.net/httpapi)。
5. 设置环境变量：`copy .env.example .env`，编辑`.env`文件，填入自己的值，然后`source .env` （Linux or Mac）或 `set -a && source .env && set +a` （Windows）。
6. 列出账户测试：`python src/account_updater.py --action list`

### 使用Docker

1. 拉取Docker镜像：`docker pull ptbjerry/finance`
2. 配置ezBookkeeping API：确保ezBookkeeping已启动并运行，并且已获取[API密钥](http://ezbookkeeping.mayswind.net/httpapi)。
3. 设置环境变量：`copy .env.example .env`，编辑`.env`文件，填入自己的值，然后`source .env` （Linux or Mac）或 `set -a && source .env && set +a` （Windows）。
4. 列出账户测试：`docker run --env-file .env ptbjerry/finance python account_updater.py --action list`

## 使用：和ezBookkeeping一起Docker Compose

1. 应先确保ezBookkeeping已启动并[运行](http://ezbookkeeping.mayswind.net/installation#use-docker-compose)，并且已获取[API密钥](http://ezbookkeeping.mayswind.net/httpapi)。
2. 配置环境变量：
   - 复制`.env.example`文件为`.env`文件：`copy .env.example .env`
   - 编辑`.env`文件，填入ezBookkeeping的API密钥和其他必要的配置。
3. 根据仓库中的`docker-compose.yml`文件，添加以下服务：

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

4. 重启Docker Compose：`docker-compose up -d`

## 致谢

- [ezBookkeeping](https://github.com/mayswind/ezbookkeeping)
- [AKShare](https://akshare.akfamily.xyz/index.html)