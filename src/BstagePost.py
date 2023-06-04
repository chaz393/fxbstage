from BstagePostType import PostType


class BstagePost:
    post_type: PostType
    post_id: str
    post_text: str
    media_ids: []
    author: str
    image_urls: {}
    video_url: str

    def __init__(self, post_type: PostType, post_id: str, post_text: str, media_ids: [], author: str,
                 image_urls: {} = None, video_url: str = None):
        self.post_type = post_type
        self.post_id = post_id
        self.post_text = post_text
        self.media_ids = media_ids
        self.author = author
        self.image_urls = image_urls
        self.video_url = video_url
