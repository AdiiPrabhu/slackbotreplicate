import os
import replicate
import requests
import urllib3
import uuid
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
import warnings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import logging


load_dotenv()


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()
os.makedirs("images", exist_ok=True)
os.makedirs("metadata", exist_ok=True)


slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


processed_events = set()


def save_image_metadata(image_id: str, prompt: str, user_id: str, channel: str):
    metadata = {
        "image_id": image_id,
        "prompt": prompt,
        "user_id": user_id,
        "channel": channel,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
    }
    with open(f"metadata/{image_id}.json", "w") as f:
        json.dump(metadata, f, indent=2)
    return metadata

def get_image_metadata(image_id: str):
    try:
        with open(f"metadata/{image_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


@app.get("/")
async def root():
    return {"message": "Slack AI Image Generator Bot", "version": "1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint working", "timestamp": datetime.now().isoformat()}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


@app.get("/image/{image_id}")
async def get_image(image_id: str):
    image_path = f"images/{image_id}.png"
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Image not found: {image_id}")
    metadata = get_image_metadata(image_id)
    if metadata:
        expires_at = datetime.fromisoformat(metadata["expires_at"])
        if datetime.now() > expires_at:
            raise HTTPException(status_code=410, detail="Image has expired")
    return FileResponse(image_path, media_type="image/png", filename=f"{image_id}.png")

@app.get("/share/{image_id}")
async def share_image(image_id: str):
    metadata = get_image_metadata(image_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Image not found")
    expires_at = datetime.fromisoformat(metadata["expires_at"])
    if datetime.now() > expires_at:
        raise HTTPException(status_code=410, detail="Image has expired")
    image_url = f"{BASE_URL}/image/{image_id}"
    html_content = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>AI Generated Image</title>
        <meta property='og:image' content='{image_url}'>
    </head>
    <body>
        <h1>🎨 AI Generated Image</h1>
        <p><strong>Prompt:</strong> {metadata['prompt']}</p>
        <img src='{image_url}' alt='AI Generated Image' style='max-width:100%;'>
        <p>Created: {metadata['created_at']}</p>
        <p>Expires: {metadata['expires_at']}</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/slack/command")
async def handle_slash_command(
    command: str = Form(...),
    text: str = Form(...),
    user_id: str = Form(...),
    response_url: str = Form(...)
):
    print(f"📥 Slash command received: {text}")
    try:
        output = replicate_client.run(
            "adiiprabhu/slack:a9a89a0a78b0f940776692731b49f5a3a17095a2a5d1dd88cd2196cbfb478fd5",
            input={"prompt": text, "num_outputs": 1}
        )
        image_url = str(output[0])
        image_block = {
            "response_type": "in_channel",
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": f" *Generated Image for:* `{text}`"}},
                {"type": "image", "image_url": image_url, "alt_text": "Generated image"}
            ]
        }
        requests.post(response_url, json=image_block)
        return PlainTextResponse("")
    except Exception as ex:
        print(" Error in slash command:", str(ex))
        return PlainTextResponse("")  # Fully silent


@app.get("/slack/oauth/callback")
async def slack_oauth_callback(code: str = Query(...)):
    client_id = os.getenv("SLACK_CLIENT_ID")
    client_secret = os.getenv("SLACK_CLIENT_SECRET")
    redirect_uri = os.getenv("SLACK_REDIRECT_URI")
    try:
        response = requests.post("https://slack.com/api/oauth.v2.access", data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        })
        result = response.json()
        if not result.get("ok"):
            return HTMLResponse(content="<h2>Slack OAuth failed. Please try again.</h2>", status_code=400)
        print(" Slack OAuth successful:", result)
        return HTMLResponse(content="<h2> Slack App installed successfully! You can now use the bot in your workspace.</h2>", status_code=200)
    except Exception as e:
        print("OAuth Exception:", str(e))
        return HTMLResponse(content="<h2> Unexpected error during OAuth. Check logs.</h2>", status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
