from enum import Enum


class PostType(str, Enum):
    PhotoPost = 'PhotoPost'
    VideoPost = 'VideoPost'
    TextPost = 'TextPost'
