from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from textblob import TextBlob
import requests
import os

# Initialize FastAPI app
app = FastAPI(title="Comment Sentiment Analysis")

# Configuration
FEDDIT_API_URL = "http://localhost:8080/api/v1"

# Define response model for comments
class CommentResponse(BaseModel):
    id: int
    text: str
    polarity: float
    classification: str


@app.get("/comments/{subfeddit_id}", response_model=List[CommentResponse])
def get_comments(
    subfeddit_id: int,
    start_time: Optional[int] = Query(None, description="Start time in Unix epoch"),
    end_time: Optional[int] = Query(None, description="End time in Unix epoch"),
    sort_by_polarity: Optional[bool] = Query(False, description="Sort by polarity score"),
):
    """
    Fetch and analyze comments for a given subfeddit.
    """
    # Log request details
    print(f"Received request for subfeddit_id: {subfeddit_id}")
    print(f"Query parameters - start_time: {start_time}, end_time: {end_time}, sort_by_polarity: {sort_by_polarity}")

    # Construct API URL
    api_url = f"{FEDDIT_API_URL}/comments/"
    params = {"subfeddit_id": subfeddit_id, "skip": 0, "limit": 25}
    print(f"Fetching comments from: {api_url} with params {params}")

    try:
        # Fetch comments from Feddit API
        response = requests.get(api_url, params=params)
        print(f"Feddit API response status: {response.status_code}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Subfeddit not found")

        comments_data = response.json().get("comments", [])  # Extract comments
    except requests.RequestException as e:
        print(f"Error connecting to Feddit API: {e}")
        raise HTTPException(status_code=500, detail="Error connecting to Feddit API")

    # Process comments
    comments = []
    for item in comments_data:
        created_at = item.get("created_at")
        if start_time and created_at < start_time:
            continue
        if end_time and created_at > end_time:
            continue

        text = item.get("text", "")
        polarity = TextBlob(text).sentiment.polarity
        classification = "positive" if polarity >= 0 else "negative"

        comment = CommentResponse(
            id=item["id"],
            text=text,
            polarity=polarity,
            classification=classification,
        )
        comments.append(comment)

    if sort_by_polarity:
        comments.sort(key=lambda x: x.polarity, reverse=True)

    print(f"Returning {len(comments)} comments")
    return comments


# Health Check Endpoint
@app.get("/")
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"message": "Service is running."}


