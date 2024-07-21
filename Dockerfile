From ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    git \
    pip 

RUN rm -rf /usr/lib/python3.12/EXTERNALLY-MANAGED

RUN git clone https://github.com/tthogho1/awsOperation.git

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

CMD ["python3","/awsOperation/AWSSQS.py"]