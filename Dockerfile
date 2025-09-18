FROM docker.xuanyuan.me/continuumio/miniconda3
# install deps
RUN conda install -n base -c conda-forge pandas tqdm requests -y && \
conda clean -a -y && \
pip install -U pdfplumber fast-agent-mcp openpyxl akshare && \
pip cache purge
# copy code
COPY src /app/src
# work dir
WORKDIR /app/src