FROM python:3.11

RUN apt-get update && \
    apt-get install -y \
        bpftrace

RUN pip install py-spy

CMD ["bash", "-i", "--login"]
