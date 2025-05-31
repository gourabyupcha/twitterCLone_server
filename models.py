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
    status: str
    count: int
    data: List[Tweet]


class APIResponse(BaseModel):
    status: str
    data: dict
    
class QueryRequest(BaseModel):
    prompt: str