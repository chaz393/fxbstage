import requests
import os
import subprocess
from BstagePost import BstagePost
from BstagePostType import PostType
from flask import Flask, request, send_file

app = Flask(__name__)
media_base_url = "https://pixy.fxbstage.in/story/feed/"
base_download_path = os.getenv('DOWNLOAD_PATH')
if base_download_path is None:
    base_download_path = ""


@app.route('/')
def index():
    return "<meta http-equiv=\"Refresh\" content=\"0; url='https://pixy.bstage.in/'\" />"


@app.route('/story/feed/<post_id>')
def get_post(post_id: str):
    print(request.host.split(":")[0])
    print(post_id)
    post_url = f"https://pixy.bstage.in/story/feed/{post_id}"
    response = requests.get(post_url)
    post_type = get_post_type(response)
    if post_type is PostType.PhotoPost:
        post = get_photo_post_metadata(response)
        download_photo(post)
    elif post_type is PostType.VideoPost:
        post = get_video_post_metadata(response)
        download_video(post)
    else:
        # either errored or a text post
        return ""
    return get_html(post)


@app.route('/story/feed/<post_id>/<media>')
def get_media(post_id: str, media: str):
    print(post_id)
    print(media)
    media_path = f"{base_download_path}downloads/{post_id}/{media}"
    print(media_path)
    return send_file(media_path)


def download_photo(post: BstagePost):
    folder_path = f"{base_download_path}downloads/{post.post_id}"
    os.makedirs(folder_path, exist_ok=True)
    for media_id in post.image_urls:
        image_url = post.image_urls[media_id]
        full_path = folder_path + f"/{media_id}.jpeg"
        if os.path.isfile(full_path):
            print(f"{full_path} already exists, skipping download")
        else:
            image_response = requests.get(image_url)
            if image_response.status_code != 200:
                return
            with open(full_path, 'wb') as file:
                file.write(image_response.content)
                file.close()


def download_video(post: BstagePost):
    full_path = f"{base_download_path}downloads/{post.post_id}/{post.media_ids[0]}.mp4"
    print(full_path)
    if os.path.isfile(full_path):
        print(f"{full_path} already exists, skipping download")
    else:
        subprocess.run(["yt-dlp", "-o", full_path, post.video_url])


def get_photo_post_metadata(response):
    if response.status_code != 200:
        return ""

    post_id = str(response.text).split("\"post\":{\"id\":\"")[1].split("\"")[0]
    author = str(response.text).split("\"nickname\":\"")[1].split("\"")[0]
    post_text = str(response.text).split("\"body\":\"")[1].split("\"")[0]
    print(post_id)
    print(author)
    print(post_text)

    media_ids = []
    image_url_dictionary = {}
    image_urls = str(response.content).split("\"images\":[")[1].split("]")[0]
    for image_url in image_urls.split(","):
        image_url = image_url.split("\"")[1]
        media_id = image_url.split("/")[-2]
        print(image_url)
        print(media_id)
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

    print(post_id)
    print(media_id)
    print(author)
    print(post_text)
    print(video_url)

    return BstagePost(PostType.VideoPost, post_id, post_text, [media_id], author, video_url=video_url)


def get_post_type(response):
    if response.status_code != 200:
        return
    if "\"video\":{\"id\"" in str(response.content):
        print("downloading video")
        return PostType.VideoPost
    elif "\"images\":[" in str(response.content):
        print("downloading photo")
        return PostType.PhotoPost
    else:
        print("text post, skipping")
        return PostType.TextPost


def get_html(post: BstagePost):
    if post.post_type is PostType.PhotoPost:
        html = f"<meta http-equiv=\"Refresh\" content=\"0; url='https://pixy.bstage.in/story/feed/{post.post_id}'\" />"
        html = html + "<title>Pixy bstage Post</title>"
        html = html + f"<meta content=\"Pixy bstage Post by {post.author}\" property=\"og:title\" />"
        html = html + f"<meta content=\"{post.post_text}\" property=\"og:description\" />"
        html = html + f"<meta content=\"https://pixy.bstage.in/story/feed/{post.post_id}\" property=\"og:url\" />"
        html = html + f"<meta content=\"{media_base_url}/{post.post_id}/{post.media_ids[0]}.jpeg\" " \
                      f"property=\"og:image\" />"
        html = html + "<meta name=\"twitter:card\" content=\"summary_large_image\">"
        return html
    elif post.post_type is PostType.VideoPost:
        html = f"<meta http-equiv=\"Refresh\" content=\"0; url='https://pixy.bstage.in/story/feed/{post.post_id}'\" />"
        html = html + "<title>Pixy bstage Post</title>"
        html = html + f"<meta name=\"twitter:description\" content=\"{post.post_text}\" />"
        html = html + f"<meta name=\"twitter:title\" content=\"Pixy bstage Post by {post.author}\" />"
        html = html + "<meta name=\"twitter:card\" content=\"player\" />"
        html = html + "<meta name=\"twitter:player:width\" content=\"320\" />"
        html = html + "<meta name=\"twitter:player:height\" content=\"180\" />"
        html = html + f"<meta name=\"twitter:player:stream\" content=\"{media_base_url}/story/feed/" \
                      f"{post.post_id}/{post.media_ids[0]}.mp4\" />"
        html = html + "<meta name=\"twitter:player:stream:content_type\" content=\"video/mp4\" />"
        return html


if __name__ == "__main__":
    app.run(host="0.0.0.0")
