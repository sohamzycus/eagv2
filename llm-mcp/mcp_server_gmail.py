import os
import base64
import json
from email.mime.text import MIMEText
from typing import Optional
from mcp.server.fastmcp import FastMCP, Context

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "")

mcp = FastMCP("gmail")


def _load_creds() -> Credentials:
    if not TOKEN_PATH or not CREDENTIALS_PATH:
        raise RuntimeError("Set GOOGLE_TOKEN_PATH and GOOGLE_CREDENTIALS_PATH in env")
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, GMAIL_SCOPES)
    if not creds or not creds.valid:
        raise RuntimeError("Invalid or missing Google OAuth token. Run local auth flow first.")
    return creds


def _create_message(sender: str, to: str, subject: str, body_text: str) -> dict:
    message = MIMEText(body_text, "plain", "utf-8")
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


@mcp.tool()
async def send_email(to: str, subject: str, body: str, ctx: Context, sender: Optional[str] = None) -> str:
    """
    Send an email via Gmail API. 'sender' defaults to the authorized account.
    """
    try:
        creds = _load_creds()
        service = build("gmail", "v1", credentials=creds)
        message = _create_message(sender or "me", to, subject, body)
        resp = service.users().messages().send(userId="me", body=message).execute()
        await ctx.info("Email sent")
        return json.dumps({"id": resp.get("id")})
    except HttpError as e:
        await ctx.error(f"Gmail API error: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        await ctx.error(f"Error sending email: {e}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")

