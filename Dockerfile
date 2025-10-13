FROM python:3.12-slim
# install deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# copy code
COPY src /app/src
WORKDIR /app/src

