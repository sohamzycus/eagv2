import os
import json
from datetime import datetime
from typing import Optional, List, Dict

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import httplib2
from google_auth_httplib2 import AuthorizedHttp

load_dotenv()

mcp = FastMCP("workflows")
VERIFY_SSL = not (os.getenv("INSECURE_SSL", "0") in ("1", "true", "TRUE"))

def _google_http():
    # Use SSL-bypass for Google APIs when requested (corporate proxies)
    if not VERIFY_SSL:
        return None
    return None  # kept for interface completeness

def _build_service(api: str, version: str, creds):
    if VERIFY_SSL:
        return build(api, version, credentials=creds)
    # INSECURE path: wrap creds with AuthorizedHttp over a permissive httplib2 client
    http = httplib2.Http(disable_ssl_certificate_validation=True)
    authed = AuthorizedHttp(creds, http=http)
    return build(api, version, http=authed)

def _load_creds(scopes: List[str]) -> Credentials:
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "")
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "")
    if not token_path or not creds_path:
        raise RuntimeError("Set GOOGLE_TOKEN_PATH and GOOGLE_CREDENTIALS_PATH in env")
    creds = Credentials.from_authorized_user_file(token_path, scopes)
    if not creds or not creds.valid:
        raise RuntimeError("Invalid Google OAuth token; run local auth flow")
    return creds


def _fetch_f1_standings() -> List[List[str]]:
    # Try Ergast first (commonly used by the F1 community)
    try:
        resp = requests.get("https://ergast.com/api/f1/current/driverStandings.json", timeout=10, verify=VERIFY_SSL)
        if resp.ok:
            data = resp.json()
            lists = data["MRData"]["StandingsTable"]["StandingsLists"]
            if lists:
                standings = lists[0]["DriverStandings"]
                rows = [["Pos", "Driver", "Constructor", "Points", "Wins"]]
                for s in standings:
                    pos = s.get("position", "")
                    drv = s.get("Driver", {})
                    name = f'{drv.get("givenName","")} {drv.get("familyName","")}'.strip()
                    cons = s.get("Constructors", [{}])[0].get("name", "")
                    pts = s.get("points", "")
                    wins = s.get("wins", "")
                    rows.append([pos, name, cons, str(pts), str(wins)])
                return rows
    except Exception:
        pass

    # Fallback 1: Wikipedia scrape
    try:
        url = "https://en.wikipedia.org/wiki/Formula_One_World_Championship"
        r = requests.get(url, timeout=10, verify=VERIFY_SSL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.select_one("table.wikitable")
        if not table:
            return [["Info"], ["Could not locate standings table on Wikipedia."]]
        rows = [["Pos", "Driver", "Constructor", "Points"]]
        for tr in table.select("tr")[1:]:
            cols = [c.get_text(strip=True) for c in tr.select("td,th")]
            if len(cols) >= 4:
                rows.append(cols[:4])
        return rows if len(rows) > 1 else [["Info"], ["No rows parsed from Wikipedia."]]
    except Exception:
        pass

    # Fallback 2: Official F1 results page (static table)
    try:
        from datetime import datetime as _dt
        year = _dt.utcnow().year
        url = f"https://www.formula1.com/en/results.html/{year}/drivers.html"
        r = requests.get(
            url,
            timeout=15,
            verify=VERIFY_SSL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.formula1.com/",
            },
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Try primary selector
        table = soup.select_one("table.resultsarchive-table")
        rows: List[List[str]] = [["Pos", "Driver", "Constructor", "Points"]]
        if table:
            for tr in table.select("tbody tr"):
                tds = tr.select("td")
                if len(tds) < 5:
                    continue
                pos = tds[1].get_text(strip=True)
                drv = tds[2].get_text(strip=True)
                team = tds[3].get_text(strip=True)
                pts = tds[-1].get_text(strip=True)
                rows.append([pos, drv, team, pts])
            if len(rows) > 1:
                return rows

        # Generic fallback: parse first table with 4+ columns and header containing Pos/Driver
        for tbl in soup.find_all("table"):
            head_cells = [th.get_text(strip=True) for th in tbl.select("thead th")]
            body_rows = tbl.select("tbody tr")
            if not head_cells and body_rows:
                # try first row as header if no thead
                first_tr = body_rows[0]
                head_cells = [c.get_text(strip=True) for c in first_tr.find_all(["th", "td"])]
                body_rows = body_rows[1:]
            if len(head_cells) >= 3 and ("Pos" in head_cells[0] or "Position" in head_cells[0] or "Driver" in " ".join(head_cells)):
                parsed = [head_cells]
                for tr in body_rows:
                    cols = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
                    if cols:
                        parsed.append(cols[:len(head_cells)])
                if len(parsed) > 1:
                    return parsed

        return [["Info"], [f"Could not locate results table on F1 site for {year}."]]
    except Exception:
        pass

    # Fallback 3: ESPN standings page
    try:
        from datetime import datetime as _dt
        year = _dt.utcnow().year
        espn = f"https://www.espn.com/f1/standings/_/season/{year}"
        r = requests.get(
            espn,
            timeout=15,
            verify=VERIFY_SSL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.espn.com/",
            },
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Find first table with "POS" and "DRIVER" in header row
        for tbl in soup.find_all("table"):
            headers = [th.get_text(strip=True).upper() for th in tbl.select("thead th")]
            if headers and (("POS" in headers[0]) or ("DRIVER" in headers)):
                parsed: List[List[str]] = [headers]
                for tr in tbl.select("tbody tr"):
                    cols = [c.get_text(strip=True) for c in tr.find_all("td")]
                    if cols:
                        parsed.append(cols[:len(headers)])
                if len(parsed) > 1:
                    return parsed
        return [["Info"], ["Could not parse ESPN standings table."]]
    except Exception:
        return [["Info"], ["Failed to fetch F1 standings from all sources."]]


@mcp.tool()
async def get_f1_standings(ctx: Context) -> str:
    """
    Return current F1 driver standings as JSON list of lists.
    First row is headers.
    """
    try:
        rows = _fetch_f1_standings()
        return json.dumps({"rows": rows})
    except Exception as e:
        await ctx.error(str(e))
        return json.dumps({"error": str(e)})


def _create_sheet_and_append(rows: List[List[str]]) -> Dict[str, str]:
    SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
    creds = _load_creds(SHEETS_SCOPES + DRIVE_SCOPES)
    sheets = _build_service("sheets", "v4", creds)

    title = f"F1 Driver Standings - {datetime.utcnow().strftime('%Y-%m-%d')}"
    body = {"properties": {"title": title}}
    created = sheets.spreadsheets().create(body=body, fields="spreadsheetId,spreadsheetUrl").execute()
    ssid = created["spreadsheetId"]
    ssurl = created["spreadsheetUrl"]

    sheets.spreadsheets().values().append(
        spreadsheetId=ssid,
        range="Sheet1!A1",
        valueInputOption="USER_ENTERED",
        body={"values": rows}
    ).execute()
    return {"spreadsheetId": ssid, "spreadsheetUrl": ssurl, "title": title}


def _send_email_link(url: str, to_email: Optional[str]) -> str:
    GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    creds = _load_creds(GMAIL_SCOPES)
    from email.mime.text import MIMEText
    import base64

    to_addr = to_email or os.getenv("GMAIL_DEFAULT_TO")
    if not to_addr:
        return "No recipient configured. Set GMAIL_DEFAULT_TO or pass to_email."

    service = _build_service("gmail", "v1", creds)
    subject = "F1 Driver Standings - Google Sheet"
    body = f"Here is the Google Sheet link with the latest F1 driver standings:\n\n{url}"

    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to_addr
    msg["from"] = "me"
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    resp = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"Email sent to {to_addr}, id={resp.get('id')}"


@mcp.tool()
async def process_f1_to_sheet_and_email(ctx: Context, to_email: Optional[str] = None) -> str:
    """
    Fetch current F1 driver standings, create a Google Sheet, append standings, and email the link.
    Uses GOOGLE_TOKEN_PATH/GOOGLE_CREDENTIALS_PATH and optional GMAIL_DEFAULT_TO.
    """
    try:
        await ctx.info("Fetching F1 standings")
        rows = _fetch_f1_standings()
        await ctx.info(f"Got {len(rows)-1 if len(rows)>0 else 0} rows")

        await ctx.info("Creating Google Sheet and appending data")
        sheet = _create_sheet_and_append(rows)

        await ctx.info("Sending email with sheet link")
        email_status = _send_email_link(sheet["spreadsheetUrl"], to_email)

        return json.dumps({
            "sheet": sheet,
            "email": email_status
        })
    except Exception as e:
        await ctx.error(str(e))
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")

