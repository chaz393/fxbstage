FROM python:3.9

RUN apt-get update
RUN apt-get install -y ffmpeg

RUN pip install -y requests flask yt-dlp

ADD src /src

CMD ["python3", "-u", "/src/bstage_embed_server.py"]