# fxbstage
Create better embeds for pixy bstage

To run:

`docker build -t fxbstage:latest .`

```
docker run --name fxbstage \
  -p 80:5000 \
  -e DOWNLOAD_PATH="/" \
  fxbstage:latest
