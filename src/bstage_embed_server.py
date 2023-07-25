import requests
import os
import subprocess
from glob import glob
from io import BytesIO
from zipfile import ZipFile
from BstagePost import BstagePost
from BstagePostType import PostType
from flask import Flask, request, send_file

app = Flask(__name__)
media_base_url = os.getenv("MEDIA_BASE_URL")
if media_base_url is None:
    media_base_url = "https://{artist}.fxbstage.in/story/feed/"
base_download_path = os.getenv('DOWNLOAD_PATH')
if base_download_path is None:
    base_download_path = ""


@app.route('/')
def index_route():
    host = request.host.split(":")[0]
    artist = host.split(".")[0]
    # handle redirecting to bstage.in where there is no artist
    # ex: pixy.fxbstage.in = length 3, fxbstage.in = length 2
    if len(host.split(".")) < 3:
        print(f"redirecting to https://bstage.in/")
        return f"<meta http-equiv=\"Refresh\" content=\"0; url='https://bstage.in/'\" />"
    print(f"redirecting to https://{artist}.bstage.in/")
    return f"<meta http-equiv=\"Refresh\" content=\"0; url='https://{artist}.bstage.in/'\" />"


@app.route('/story/feed/<post_id>')
@app.route('/story/feed/<post_id>/')
def get_post_route(post_id: str):
    host = request.host.split(":")[0]
    print(host)
    artist = host.split(".")[0]
    post = get_post(post_id, artist)
    if post is None:  # post is either a text post or something errored
        return f"<meta http-equiv=\"Refresh\" content=\"0; url='https://{artist}.bstage.in/story/feed/{post_id}'\" />"
    download_post(post)
    if "dlbstage.in" in host or "dlstagingbstage" in host:
        return get_dl_bstage_file(post)
    return get_html(post, artist)


@app.route('/story/feed/<post_id>/<media>')
@app.route('/story/feed/<post_id>/<media>/')
def get_media_route(post_id: str, media: str):
    host = request.host.split(":")[0]
    print(host)
    artist = host.split(".")[0]
    media_path = f"{base_download_path}downloads/{post_id}/{media}"
    post = get_post(post_id, artist)
    download_post(post)
    return send_file(media_path)


def download_post(post: BstagePost):
    if post.post_type is PostType.PhotoPost:
        download_photo(post)
    elif post.post_type is PostType.VideoPost:
        download_video(post)


def get_post(post_id: str, artist: str):
    post_url = f"https://{artist}.bstage.in/story/feed/{post_id}"
    response = requests.get(post_url)
    post_type = get_post_type(response)
    if post_type is PostType.PhotoPost:
        post = get_photo_post_metadata(response)
        return post
    elif post_type is PostType.VideoPost:
        post = get_video_post_metadata(response)
        return post
    else:
        # either errored or a text post
        return None


def get_dl_bstage_file(post: BstagePost):
    if len(post.media_ids) > 1:
        return send_file(zip_and_get_stream(post.post_id), as_attachment=True, download_name=f"{post.post_id}.zip")
    elif post.post_type is PostType.PhotoPost:
        return send_file(f"{base_download_path}downloads/{post.post_id}/{post.media_ids[0]}.jpeg",
                         as_attachment=True)
    elif post.post_type is PostType.VideoPost:
        return send_file(f"{base_download_path}downloads/{post.post_id}/{post.media_ids[0]}.mp4",
                         as_attachment=True)


def download_photo(post: BstagePost):
    folder_path = f"{base_download_path}downloads/{post.post_id}"
    os.makedirs(folder_path, exist_ok=True)
    for media_id in post.image_urls:
        image_url = post.image_urls[media_id]
        full_path = folder_path + f"/{media_id}.jpeg"
        if os.path.isfile(full_path):
            print(f"{full_path} already exists, skipping download")
        else:
            print(f"downloading photo: {full_path}")
            image_response = requests.get(image_url)
            if image_response.status_code != 200:
                return
            with open(full_path, 'wb') as file:
                file.write(image_response.content)
                file.close()


def download_video(post: BstagePost):
    full_path = f"{base_download_path}downloads/{post.post_id}/{post.media_ids[0]}.mp4"
    if os.path.isfile(full_path):
        print(f"{full_path} already exists, skipping download")
    else:
        print(f"downloading video: {full_path}")
        subprocess.run(["yt-dlp", "-o", full_path, post.video_url])


def get_photo_post_metadata(response):
    if response.status_code != 200:
        return ""

    post_id = str(response.text).split("\"post\":{\"id\":\"")[1].split("\"")[0]
    author = str(response.text).split("\"nickname\":\"")[1].split("\"")[0]
    post_text = str(response.text).split("\"body\":\"")[1].split("\"")[0]

    media_ids = []
    image_url_dictionary = {}
    image_urls = str(response.content).split("\"images\":[")[1].split("]")[0]
    for image_url in image_urls.split(","):
        image_url = image_url.split("\"")[1]
        media_id = image_url.split("/")[-2]
        media_ids.append(media_id)
        image_url_dictionary[media_id] = image_url

    return BstagePost(PostType.PhotoPost, post_id, post_text, media_ids, author, image_urls=image_url_dictionary)


def get_video_post_metadata(response):
    if response.status_code != 200:
        return ""

    post_id = str(response.text).split("\"post\":{\"id\":\"")[1].split("\"")[0]
    media_id = str(response.text).split("\"video\":{\"id\":\"")[1].split("\"")[0]
    author = str(response.text).split("\"nickname\":\"")[1].split("\"")[0]
    post_text = str(response.text).split("\"body\":\"")[1].split("\"")[0]
    video_url = str(response.text).split("\"dashPath\":\"")[1].split("\"")[0]

    return BstagePost(PostType.VideoPost, post_id, post_text, [media_id], author, video_url=video_url)


def get_post_type(response):
    if response.status_code != 200:
        return
    if "\"video\":{\"id\"" in str(response.content):
        return PostType.VideoPost
    elif "\"images\":[" in str(response.content):
        return PostType.PhotoPost
    else:
        print("text post, skipping")
        return PostType.TextPost


def get_html(post: BstagePost, artist: str):
    if post.post_type is PostType.PhotoPost:
        html = f"<meta http-equiv=\"Refresh\" content=\"0; url='https://{artist}.bstage.in/story/feed/{post.post_id}'\" />"
        html = html + f"<title>{artist} bstage Post</title>"
        html = html + f"<meta content=\"{artist} bstage Post by {post.author}\" property=\"og:title\" />"
        html = html + f"<meta content=\"{post.post_text}\" property=\"og:description\" />"
        html = html + f"<meta content=\"https://{artist}.bstage.in/story/feed/{post.post_id}\" property=\"og:url\" />"
        html = html + f"<meta content=\"{media_base_url.format(artist=artist)}/{post.post_id}/{post.media_ids[0]}.jpeg\" " \
                      f"property=\"og:image\" />"
        html = html + "<meta name=\"twitter:card\" content=\"summary_large_image\">"
        return html
    elif post.post_type is PostType.VideoPost:
        html = f"<meta http-equiv=\"Refresh\" content=\"0; url='https://{artist}.bstage.in/story/feed/{post.post_id}'\" />"
        html = html + f"<title>{artist} bstage Post</title>"
        html = html + f"<meta name=\"twitter:description\" content=\"{post.post_text}\" />"
        html = html + f"<meta name=\"twitter:title\" content=\"{artist} bstage Post by {post.author}\" />"
        html = html + "<meta name=\"twitter:card\" content=\"player\" />"
        html = html + "<meta name=\"twitter:player:width\" content=\"320\" />"
        html = html + "<meta name=\"twitter:player:height\" content=\"180\" />"
        html = html + f"<meta name=\"twitter:player:stream\" content=\"{media_base_url.format(artist=artist)}" \
                      f"{post.post_id}/{post.media_ids[0]}.mp4\" />"
        html = html + "<meta name=\"twitter:player:stream:content_type\" content=\"video/mp4\" />"
        return html


def zip_and_get_stream(post_id: str):
    print(f"zipping {post_id} media for dl")
    stream = BytesIO()
    with ZipFile(stream, 'w') as zf:
        for file in glob(os.path.join(f"{base_download_path}downloads/{post_id}", '*')):
            zf.write(file, os.path.basename(file))
    stream.seek(0)
    return stream


if __name__ == "__main__":
    app.run(host="0.0.0.0")
