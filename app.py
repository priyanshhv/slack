import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

app = FastAPI()

SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")

@app.get("/")
async def root(request: Request):
    base_url = str(request.base_url)
    redirect_uri = f"{base_url.rstrip('/')}{os.getenv('SLACK_REDIRECT_URI')}"
    print(redirect_uri)
    auth_url = f"https://slack.com/oauth/v2/authorize?client_id={SLACK_CLIENT_ID}&scope=chat:write,users:read&user_scope=chat:write,users:read&redirect_uri={redirect_uri}"
    return HTMLResponse(f'<a href="{auth_url}">Install Slack App</a>')

@app.get("/slack/oauth_redirect")
async def slack_oauth_redirect(request: Request, code: str):
    base_url = str(request.base_url)
    redirect_uri = f"{base_url.rstrip('/')}{os.getenv('SLACK_REDIRECT_URI')}"
    try:
        client = WebClient()
        response = client.oauth_v2_access(
            client_id=SLACK_CLIENT_ID,
            client_secret=SLACK_CLIENT_SECRET,
            code=code,
            redirect_uri=redirect_uri
        )
        # Sending message from user to channel
        # Extract the user token
        user_token = response['authed_user']['access_token']
        print(user_token)
        
        # Send a test message
        channel = "#general"  # Replace with your desired channel
        message = "Hello! This is a test message sent on behalf of the user."
        send_result = await send_message_channel(user_token, channel, message)

         # Sending direct message to all user
        # Get a list of all users
        users_response = client.users_list(token=user_token)
        users = users_response['members']
        # Send personalized messages to each user
        for user in users:
            failed = False
            user_id = user['id']
            user_name = user['real_name']  # Use the appropriate field for the user's name
            message = f"Hello {user_name}! This is a personalized message sent on behalf of the user."
            await send_message_user(user_token, user_id, message)
        
        if send_result and send_result['ok']:
            return HTMLResponse(f"Installation successful! Message sent to {channel}")
        else:
            return HTMLResponse("Installation successful, but failed to send message.")
        
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack OAuth error: {str(e)}")

# Function to send a message to a channel
async def send_message_channel(token: str, channel: str, message: str):
    try:
        client = WebClient(token=token)
        response = client.chat_postMessage(
            channel=channel,
            text=message
        )
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e}")
        return None
#Function to send a direct message to another user
async def send_message_user(token: str, user_id: str, message: str):
    try:
        client = WebClient(token=token)
        response = client.chat_postMessage(
            channel=user_id,  # Use the user ID as the channel
            text=message
        )
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e}")
        return None

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)

