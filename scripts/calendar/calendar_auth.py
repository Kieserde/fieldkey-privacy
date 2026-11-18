#!/usr/bin/env python3
"""One-time Google sign-in for Jarvis's calendar tool. Run this on your Mac.

Usage:
  pip3 install google-auth-oauthlib
  python3 calendar_auth.py ~/Downloads/client_secret_XXXX.json

It opens a browser, you approve access to your calendar EVENTS only, and it prints a
token JSON. Paste that JSON into the tool's TOKEN_JSON setting in Open WebUI.
The token is a credential: don't commit it or share it.
"""
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

if len(sys.argv) != 2:
    sys.exit(__doc__)

flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
creds = flow.run_local_server(port=0)
print("\n--- Copy everything between the lines into TOKEN_JSON ---")
print(creds.to_json())
print("--- end ---")
