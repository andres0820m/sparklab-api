FROM python:3
ENV PYTHONUNBUFFERED 1
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8

RUN mkdir /usr/local/src/sparklab
WORKDIR /usr/local/src/sparklab
COPY requirements.txt /usr/local/src/sparklab
RUN pip install -r requirements.txt
COPY . /usr/local/src/sparklab
RUN chmod +x /usr/local/src/sparklab/entrypoint.sh
ENTRYPOINT ["/usr/local/src/sparklab/entrypoint.sh"]