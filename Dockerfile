FROM docker.xuyuan.me/python:3.12-slim
# install deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# copy code
COPY src /app/src
WORKDIR /app/src
# make cron
RUN chmod +x /app/src/make_crontab.sh && \
/app/src/make_crontab.sh /etc/cron.d/finance-crontab && \
chmod 644 /etc/cron.d/finance-crontab && \
crontab /etc/cron.d/finance-crontab
# start cron
CMD ["cron", "-f"]
