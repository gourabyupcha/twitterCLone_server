from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from utils import load_db, save_db, get_random_timestamp
from datetime import datetime
import secrets
import uvicorn
import uuid
import random


app = FastAPI()

origins = [
    "http://localhost:5173",  # your frontend dev server
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # or use ["*"] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEYS = {}  # user: api_key (in-memory)

# -------------------------
# Models
# -------------------------

class UserCreate(BaseModel):
    username: str
    password: str

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

# -------------------------
# Auth Dependency
# -------------------------

def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    db = load_db()
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    for user in db["users"]:
        if user.get("api_key") == x_api_key:
            return user["username"]
    
    raise HTTPException(status_code=401, detail="Invalid API Key")


# -------------------------
# Routes
# -------------------------

@app.post("/create_user")
def create_user(user: UserCreate):
    db = load_db()
    for u in db["users"]:
        if u["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username already exists")

    api_key = secrets.token_hex(16)
    db["users"].append({
        "username": user.username,
        "password": user.password,
        "api_key": api_key
    })

    save_db(db)
    return {"message": "User created", "api_key": api_key}




# Inside your post_tweet endpoint:

@app.post("/post_tweet")
def post_tweet(
    tweet: TweetCreate,
    api_user: str = Depends(verify_api_key)
):
    # Check if API key's username matches the posted tweet username
    if tweet.username != api_user:
        raise HTTPException(status_code=403, detail="API Key does not match username")

    # Proceed with your tweet creation logic...
    db = load_db()
    tweet_id = uuid.uuid4().int >> 96  # random 32-bit int id

    # Random stats, timestamp, etc. (same as before)
    likes = random.randint(0, 100)
    retweets = random.randint(0, 50)
    replies = random.randint(0, 20)
    isLiked = random.choice([True, False])
    isRetweeted = random.choice([True, False])
    timestamp = datetime.utcnow().isoformat()

    tweet_record = {
        "id": tweet_id,
        "username": tweet.username,
        "handle": f"@{tweet.username.lower()}",
        "content": tweet.text,
        "timestamp": timestamp,
        "likes": likes,
        "retweets": retweets,
        "replies": replies,
        "isLiked": isLiked,
        "isRetweeted": isRetweeted
    }

    db["tweets"].append(tweet_record)
    save_db(db)

    return {"message": "Tweet posted", "tweet_id": tweet_id}




@app.get("/tweets", response_model=TweetsResponse)
def get_all_tweets():
    db = load_db()
    tweets = db["tweets"]
    return TweetsResponse(
        status=True,
        count=len(tweets),
        data=tweets
    )

@app.get("/tweet/{tweet_id}", response_model=Tweet, dependencies=[Depends(verify_api_key)])
def get_tweet_by_id(tweet_id: int):
    db = load_db()
    for tweet in db["tweets"]:
        if tweet["id"] == tweet_id:
            return tweet
    raise HTTPException(status_code=404, detail="Tweet not found")

# -------------------------
# Run with uvicorn
# -------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
