FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y python wget && \
    rm -rf /var/lib/apt/lists/*

RUN wget -P / https://svn.apache.org/repos/asf/oodt/tools/oodtsite.publisher/trunk/distribute_setup.py && \
    python distribute_setup.py && \
    easy_install pip

RUN mkdir code

COPY watchdog.py /code
COPY config.py /code
COPY requirements.txt /code

WORKDIR /code

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "watchdog.py"]