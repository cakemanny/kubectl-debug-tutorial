FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y \
        bpftrace

RUN pip install py-spy

CMD ["bash", "--login", "-i"]
