# Jarvis calendar access (read/write)

Lets your local AI (Open WebUI + Ollama) list, create, update and delete Google Calendar events.
It uses the Google Calendar API with OAuth and the narrow `calendar.events` scope
(events only, no calendar settings or sharing).

## One-time setup (about 10 minutes)

1. **Google Cloud project:** go to console.cloud.google.com, create a project, then
   *APIs & Services → Library → Google Calendar API → Enable*.
2. **Consent screen:** *APIs & Services → OAuth consent screen* (or "Google Auth Platform").
   User type *External*, add your own Gmail address as a **test user**.
3. **Credentials:** *Credentials → Create credentials → OAuth client ID → Desktop app*.
   Download the JSON (`client_secret_….json`).
4. **Sign in once, on your Mac:**
   ```bash
   pip3 install google-auth-oauthlib
   python3 scripts/calendar/calendar_auth.py ~/Downloads/client_secret_XXXX.json
   ```
   A browser opens; approve access. Copy the token JSON it prints.
5. **Install the tool:** Open WebUI → Workspace → Tools → "+" → paste
   `openwebui_calendar_tool.py` → Save. Click the gear icon and set:
   - `TOKEN_JSON`: the JSON from step 4
   - `TIMEZONE`: e.g. `Europe/Berlin`
6. In a chat, enable the tool from the "+" menu and try: "What's on my calendar this week?"

## Notes

- Use a tool-calling-capable model (e.g. `qwen2.5:32b`). Small models call tools unreliably.
- While the Google app is in "Testing" mode, the sign-in expires after 7 days; re-run step 4,
  or publish the app to "In production" (fine for personal use).
- Deleting asks for confirmation: the tool refuses until the model passes `confirmed=True`,
  and its instructions tell it to ask you first. Still, check changes in Google Calendar,
  since a local model can misread a request.
- Never commit `client_secret_*.json` or the token JSON.
