# fxbstage
Create better embeds for pixy bstage

To run:

`docker build -t fxbstage-pixy:latest .`

```
docker run --name fxbstage-pixy \
  -p 80:5000 \
  -e DOWNLOAD_PATH="/" \
  fxbstage-pixy:latest