
# Slack AI Image Generator Bot

This project is a FastAPI-based Slack bot that generates AI images using a fine-tuned Replicate model and posts them back to Slack. It supports both real-time slash commands and direct Slack message events. Images are stored with metadata and can be accessed via secure shareable URLs.

---

## Features

- Slash command `/generateimage` to generate images based on user prompts
- Integration with a fine-tuned [Replicate](https://replicate.com/) model
- FastAPI backend with health checks, logging, and metadata storage
- OAuth2-based multi-workspace Slack app installation
- Image hosting with expiration and shareable pages
- Duplicate event protection
- HTML preview of generated images

---

## Architecture

- **Slack**: Receives slash command or bot mention
- **FastAPI**: Parses and processes the prompt, calls Replicate API
- **Replicate API**: Generates image from prompt
- **FastAPI**: Stores image locally, serves via `/image/{id}`, and shares a hosted HTML page
- **Slack SDK**: Posts generated image with links back to the same Slack thread

---

## Requirements

- Python 3.9+
- Slack App (with Events, Slash Commands, OAuth, Files Upload)
- Replicate account with a hosted model

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/slack-ai-image-bot.git
cd slack-ai-image-bot
````

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
SLACK_BOT_TOKEN=your-bot-token
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret
SLACK_REDIRECT_URI=https://yourdomain.com/slack/oauth/callback
REPLICATE_API_TOKEN=your-replicate-token
BASE_URL=https://yourdomain.com
```

### 4. Run the Server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

---

## Slack App Configuration

1. Enable the following features:

   * Slash Commands (`/generateimage`)
   * Event Subscriptions (message events)
   * Files\:Write, Files\:Read, Chat\:Write, Commands, OAuth Scopes

2. Set redirect URL:

   ```
   https://yourdomain.com/slack/oauth/callback
   ```

3. Slash command request URL:

   ```
   https://yourdomain.com/slack/command
   ```

4. Event Subscription URL:

   ```
   https://yourdomain.com/slack/events
   ```

---

## API Endpoints

| Endpoint                | Method | Description                                |
| ----------------------- | ------ | ------------------------------------------ |
| `/`                     | GET    | Root endpoint with basic info              |
| `/health`               | GET    | Health check                               |
| `/test`                 | GET    | Test connectivity                          |
| `/slack/events`         | POST   | Handle Slack event messages                |
| `/slack/command`        | POST   | Handle slash commands from Slack           |
| `/slack/oauth/callback` | GET    | OAuth callback for Slack workspace install |
| `/image/{image_id}`     | GET    | Serve image as direct link                 |
| `/share/{image_id}`     | GET    | Shareable image page with prompt metadata  |


