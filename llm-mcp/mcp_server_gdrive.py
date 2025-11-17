import os
import json
from typing import List, Optional
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

load_dotenv()


SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "")

mcp = FastMCP("google-drive-sheets")


def _load_creds(scopes: List[str]):
    # Lazy import to keep tool discovery fast and avoid heavy imports at module import time
    from google.oauth2.credentials import Credentials
    if not TOKEN_PATH or not CREDENTIALS_PATH:
        raise RuntimeError("Set GOOGLE_TOKEN_PATH and GOOGLE_CREDENTIALS_PATH in env")
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)
    if not creds or not creds.valid:
        raise RuntimeError("Invalid or missing Google OAuth token. Run local auth flow first.")
    return creds


@mcp.tool()
async def create_spreadsheet(title: Optional[str] = None, ctx: Context = None) -> str:
    """Create a Google Spreadsheet and return JSON with id and url"""
    try:
        # Lazy imports
        from googleapiclient.discovery import build
        import httplib2
        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.errors import HttpError
        creds = _load_creds(SHEETS_SCOPES + DRIVE_SCOPES)
        insecure = os.getenv("INSECURE_SSL", "0") in ("1", "true", "TRUE")
        if insecure:
            http = httplib2.Http(disable_ssl_certificate_validation=True)
            authed = AuthorizedHttp(creds, http=http)
            service = build("sheets", "v4", http=authed)
        else:
            service = build("sheets", "v4", credentials=creds)
        body = {"properties": {"title": title or "Agent Sheet"}}
        resp = service.spreadsheets().create(body=body, fields="spreadsheetId,spreadsheetUrl").execute()
        if ctx:
            await ctx.info("Spreadsheet created")
        return json.dumps(resp)
    except HttpError as e:
        if ctx:
            await ctx.error(f"Sheets API error: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        if ctx:
            await ctx.error(f"Error creating spreadsheet: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def append_values(spreadsheet_id: str, values: list[list[str]], ctx: Context = None, sheet_range: Optional[str] = None) -> str:
    """Append rows to sheet. values is a list of list of strings. Defaults range to Sheet1!A1."""
    try:
        from googleapiclient.discovery import build
        import httplib2
        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.errors import HttpError
        creds = _load_creds(SHEETS_SCOPES)
        insecure = os.getenv("INSECURE_SSL", "0") in ("1", "true", "TRUE")
        if insecure:
            http = httplib2.Http(disable_ssl_certificate_validation=True)
            authed = AuthorizedHttp(creds, http=http)
            service = build("sheets", "v4", http=authed)
        else:
            service = build("sheets", "v4", credentials=creds)
        body = {"values": values}
        resp = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=sheet_range or "Sheet1!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        if ctx:
            await ctx.info("Values appended")
        return json.dumps(resp)
    except HttpError as e:
        if ctx:
            await ctx.error(f"Sheets API error: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        if ctx:
            await ctx.error(f"Error appending values: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def share_file(file_id: str, user_email: Optional[str] = None, role: str = "reader", ctx: Context = None) -> str:
    """Share a Drive file with a user. role: reader|writer. Defaults user_email to GMAIL_DEFAULT_TO if omitted."""
    try:
        from googleapiclient.discovery import build
        import httplib2
        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.errors import HttpError
        if not user_email:
            user_email = os.getenv("GMAIL_DEFAULT_TO")
        if not user_email:
            if ctx:
                await ctx.error("Missing user_email; set GMAIL_DEFAULT_TO or pass user_email")
            return json.dumps({"error": "missing user_email"})
        creds = _load_creds(DRIVE_SCOPES)
        insecure = os.getenv("INSECURE_SSL", "0") in ("1", "true", "TRUE")
        if insecure:
            http = httplib2.Http(disable_ssl_certificate_validation=True)
            authed = AuthorizedHttp(creds, http=http)
            drive = build("drive", "v3", http=authed)
        else:
            drive = build("drive", "v3", credentials=creds)
        permission = {"type": "user", "role": role, "emailAddress": user_email}
        resp = drive.permissions().create(fileId=file_id, body=permission, sendNotificationEmail=False).execute()
        if ctx:
            await ctx.info("File shared")
        return json.dumps(resp)
    except HttpError as e:
        if ctx:
            await ctx.error(f"Drive API error: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        if ctx:
            await ctx.error(f"Error sharing file: {e}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")

