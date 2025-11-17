import os
import base64
import json
from email.mime.text import MIMEText
from typing import Optional
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

load_dotenv()

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import httplib2
from google_auth_httplib2 import AuthorizedHttp
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
async def send_email(to: Optional[str] = None, subject: Optional[str] = None, body: Optional[str] = None, ctx: Context = None, sender: Optional[str] = None) -> str:
    """
    Send an email via Gmail API. 'sender' defaults to the authorized account.
    """
    try:
        # Defaults from env to reduce failures when planner omits fields
        default_to = os.getenv("GMAIL_DEFAULT_TO")
        if not to:
            to = default_to
        if not subject:
            subject = "Automated Update"
        if not body:
            body = "No body provided."
        if not to:
            if ctx:
                await ctx.error("Missing recipient email (to). Set GMAIL_DEFAULT_TO or pass 'to'.")
            return json.dumps({"error": "missing 'to'"})

        creds = _load_creds()
        insecure = os.getenv("INSECURE_SSL", "0") in ("1", "true", "TRUE")
        if insecure:
            http = httplib2.Http(disable_ssl_certificate_validation=True)
            authed = AuthorizedHttp(creds, http=http)
            service = build("gmail", "v1", http=authed)
        else:
            service = build("gmail", "v1", credentials=creds)
        message = _create_message(sender or "me", to, subject, body)
        resp = service.users().messages().send(userId="me", body=message).execute()
        if ctx:
            await ctx.info(f"Email sent to {to}, id={resp.get('id')}")
        return json.dumps({"id": resp.get("id"), "to": to})
    except HttpError as e:
        await ctx.error(f"Gmail API error: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        await ctx.error(f"Error sending email: {e}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")

