from pydantic import BaseModel
from typing import List

class UserCreate(BaseModel):
    username: str

class TweetCreate(BaseModel):
    username: str
    text: str

class Tweet(BaseModel):
    id: int
    username: str
    handle: str
    content: str
    timestamp: str
    likes: int
    retweets: int
    replies: int
    isLiked: bool
    isRetweeted: bool
    
class TweetsResponse(BaseModel):
    status: bool
    count: int
    data: List[Tweet]
