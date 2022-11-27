FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /usr/local/src/p2p
WORKDIR /usr/local/src/p2p
COPY requirements.txt /usr/local/src/p2p
RUN pip install -r requirements.txt
COPY . /usr/local/src/p2p
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt install android-tools-adb android-tools-fastboot -y
RUN chmod +x /usr/local/src/p2p/entrypoint.sh
# Expose default ADB port
EXPOSE 5037
ENTRYPOINT ["/usr/local/src/p2p/entrypoint.sh"]