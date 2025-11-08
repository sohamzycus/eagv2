import os
import json
from typing import List
from mcp.server.fastmcp import FastMCP, Context

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "")

mcp = FastMCP("google-drive-sheets")


def _load_creds(scopes: List[str]) -> Credentials:
    if not TOKEN_PATH or not CREDENTIALS_PATH:
        raise RuntimeError("Set GOOGLE_TOKEN_PATH and GOOGLE_CREDENTIALS_PATH in env")
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)
    if not creds or not creds.valid:
        raise RuntimeError("Invalid or missing Google OAuth token. Run local auth flow first.")
    return creds


@mcp.tool()
async def create_spreadsheet(title: str, ctx: Context) -> str:
    """Create a Google Spreadsheet and return JSON with id and url"""
    try:
        creds = _load_creds(SHEETS_SCOPES + DRIVE_SCOPES)
        service = build("sheets", "v4", credentials=creds)
        body = {"properties": {"title": title}}
        resp = service.spreadsheets().create(body=body, fields="spreadsheetId,spreadsheetUrl").execute()
        await ctx.info("Spreadsheet created")
        return json.dumps(resp)
    except HttpError as e:
        await ctx.error(f"Sheets API error: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        await ctx.error(f"Error creating spreadsheet: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def append_values(spreadsheet_id: str, sheet_range: str, values: list[list[str]], ctx: Context) -> str:
    """Append rows to sheet. values is a list of list of strings."""
    try:
        creds = _load_creds(SHEETS_SCOPES)
        service = build("sheets", "v4", credentials=creds)
        body = {"values": values}
        resp = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=sheet_range,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        await ctx.info("Values appended")
        return json.dumps(resp)
    except HttpError as e:
        await ctx.error(f"Sheets API error: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        await ctx.error(f"Error appending values: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def share_file(file_id: str, user_email: str, role: str = "reader", ctx: Context = None) -> str:
    """Share a Drive file with a user. role: reader|writer"""
    try:
        creds = _load_creds(DRIVE_SCOPES)
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

