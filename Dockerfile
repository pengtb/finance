FROM docker.xuyuan.me/python:3.12-slim
# install deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# copy code
COPY src /app/src
WORKDIR /app/src
# make cron
RUN chmod +x /app/src/make_crontab.sh
# start cron
COPY entrypoint.sh /app/src/entrypoint.sh
CMD ["/app/src/entrypoint.sh"]
