FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /usr/local/src/sparklab
WORKDIR /usr/local/src/sparklab
COPY requirements.txt /usr/local/src/sparklab
RUN pip install -r requirements.txt
COPY . /usr/local/src/sparklab

RUN chmod +x /usr/local/src/sparklab/entrypoint.sh
ENTRYPOINT ["/usr/local/src/sparklab/entrypoint.sh"]