from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from utils import load_db, save_db, get_random_timestamp
from datetime import datetime, timezone
import secrets
import uvicorn
import uuid
import random
from models import UserCreate, TweetCreate, Tweet, TweetsResponse, QueryRequest
from db import users_collection, tweets_collection
from pymongo.errors import PyMongoError
from agent import SupervisorAgent

app = FastAPI()

origins = [
    "http://localhost:5173",  # your frontend dev server
    "http://127.0.0.1:5173",
    "https://twitter-clone-ui.pages.dev",
    "https://social-gpt-ui.pages.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # or use ["*"] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DEFAULT_USAGE_LIMIT = 1000


# -------------------------
# Auth Dependency
# -------------------------

def verify_api_key(api_key: str = Header(...)):
    user = users_collection.find_one({"api_key": api_key})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return user["username"]



# -------------------------
# Routes
# -------------------------

@app.get("/")
def read_root():
    return {"message": "Welcome to the API!"}



@app.post("/create_user")
def create_user(user: UserCreate):
    # Check for existing user
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    try:
        api_key = f"{user.username}_{secrets.token_hex(16)}"

        user_doc = {
            "username": user.username,
            "api_key": api_key,
            "usage_count": 0,              # How many times the API key has been used
            "usage_limit": DEFAULT_USAGE_LIMIT  # Max allowed uses
        }

        users_collection.insert_one(user_doc)

        return {
            "status": "success",
            "data": {
                "message": "User created",
                "api_key": api_key,
                "usage_limit": DEFAULT_USAGE_LIMIT
            }
        }

    except PyMongoError as e:
        return {"status": "error", "data": {"message": str(e), "api_key": ""}}



# Inside your post_tweet endpoint:

@app.post("/post_tweet")
def post_tweet(
    tweet: TweetCreate,
    api_user: str = Depends(verify_api_key)
):
    if tweet.username != api_user:
        raise HTTPException(status_code=403, detail="API Key does not match username")

    # Fetch user to check usage
    user = users_collection.find_one({"username": api_user})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    usage_count = user.get("usage_count", 0)
    usage_limit = user.get("usage_limit", 1000)  # default fallback

    if usage_count >= usage_limit:
        raise HTTPException(status_code=429, detail="API usage limit exceeded")

    # Prepare tweet data
    tweet_id = uuid.uuid4().int >> 96  # Random 32-bit int
    tweet_record = {
        "id": tweet_id,
        "username": tweet.username,
        "handle": f"@{tweet.username.lower()}",
        "content": tweet.text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "likes": random.randint(0, 100),
        "retweets": random.randint(0, 50),
        "replies": random.randint(0, 20),
        "isLiked": random.choice([True, False]),
        "isRetweeted": random.choice([True, False])
    }

    try:
        # Insert tweet
        tweets_collection.insert_one(tweet_record)

        # Increment usage
        users_collection.update_one(
            {"username": api_user},
            {"$inc": {"usage_count": 1}}
        )
        
        return {
            "status": "success",
            "data": {
                "message": "Tweet posted",
                "tweet_id": tweet_id
            }
        }
    
    except PyMongoError as e:
        return {
            "status": "error",
            "data": {
                "message": str(e)
            }
        }


@app.get("/tweets", response_model=TweetsResponse)
def get_all_tweets(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    try:
        skip = (page - 1) * limit
        total = tweets_collection.count_documents({})
        tweet_docs = list(
            tweets_collection.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit)
        )
        return TweetsResponse(
            status="success",
            count=total,
            data=tweet_docs
        )
    except PyMongoError as e:
        return TweetsResponse(
            status="error",
            count=total,
            data=tweet_docs
        )




@app.delete("/tweet/{tweet_id}")
def delete_tweet(tweet_id: int, api_user: str = Depends(verify_api_key)):
    tweet = tweets_collection.find_one({"id": tweet_id})

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if tweet["username"] != api_user:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this tweet")

    result = tweets_collection.delete_one({"id": tweet_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete tweet")

    return { "status": "success", "data": {"message": "Tweet deleted", "tweet_id": tweet_id}}



@app.get("/tweet/{tweet_id}", response_model=Tweet, dependencies=[Depends(verify_api_key)])
def get_tweet_by_id(tweet_id: int):
    db = load_db()
    for tweet in db["tweets"]:
        if tweet["id"] == tweet_id:
            return tweet
    raise HTTPException(status_code=404, detail="Tweet not found")


@app.post("/process-prompt")
async def process_request(
    request: QueryRequest,
    x_api_key: str = Header(..., alias="x-api-key")  # 👈 Custom header
):
    try:
        api_key = x_api_key 

        # Pass prompt and api_key to your agent logic
        supervisor = SupervisorAgent()
        result = await supervisor.process_request(request.prompt, api_key)
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




# -------------------------
# Run with uvicorn
# -------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
