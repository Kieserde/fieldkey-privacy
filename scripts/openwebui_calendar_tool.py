"""
title: Google Calendar (read-only)
description: Lets the local AI read upcoming events from a Google Calendar iCal feed.
version: 0.1.0
requirements: icalendar, recurring-ical-events, requests
"""
# Install: Open WebUI -> Workspace -> Tools -> "+" -> paste this file -> Save.
# Then open the tool's settings (gear icon) and paste your secret iCal URL into ICAL_URL.
# Get the URL: Google Calendar -> Settings -> your calendar -> "Integrate calendar"
#   -> "Secret address in iCal format". Treat it like a password; never commit it.
# Enable the tool for a chat with the "+" menu in the message box.
#
# Quick test outside Open WebUI:  python3 openwebui_calendar_tool.py <ics-url-or-path> [days]

from datetime import date, datetime, timedelta

import icalendar
import recurring_ical_events
import requests
from pydantic import BaseModel, Field


def _load(source: str) -> icalendar.Calendar:
    if source.startswith(("http://", "https://")):
        resp = requests.get(source, timeout=20)
        resp.raise_for_status()
        data = resp.content
    else:
        with open(source, "rb") as f:
            data = f.read()
    return icalendar.Calendar.from_ical(data)


def _fmt(value) -> str:
    if isinstance(value, datetime):
        return value.astimezone().strftime("%a %d %b %H:%M")
    if isinstance(value, date):
        return value.strftime("%a %d %b (all day)")
    return str(value)


def list_events(source: str, days: int = 7) -> str:
    days = max(1, min(days, 90))
    start = datetime.now().astimezone()
    end = start + timedelta(days=days)
    cal = _load(source)
    events = recurring_ical_events.of(cal).between(start, end)

    def sort_key(e):
        s = e.get("DTSTART").dt
        return s.astimezone() if isinstance(s, datetime) else datetime.combine(s, datetime.min.time()).astimezone()

    events = sorted(events, key=sort_key)
    if not events:
        return f"No events in the next {days} days."
    lines = []
    for e in events:
        line = f"- {_fmt(e.get('DTSTART').dt)}: {e.get('SUMMARY', '(no title)')}"
        if e.get("LOCATION"):
            line += f" @ {e.get('LOCATION')}"
        lines.append(line)
    return "\n".join(lines)


class Tools:
    class Valves(BaseModel):
        ICAL_URL: str = Field(default="", description="Secret iCal address of your Google Calendar")

    def __init__(self):
        self.valves = self.Valves()

    def get_upcoming_events(self, days: int = 7) -> str:
        """
        Get the user's upcoming calendar events.
        :param days: How many days ahead to look (1-90). Use 1 for today, 7 for this week.
        :return: A list of events with date, time, title and location.
        """
        if not self.valves.ICAL_URL:
            return "Calendar is not configured: set ICAL_URL in this tool's settings."
        try:
            return list_events(self.valves.ICAL_URL, days)
        except Exception as exc:  # surface a readable error to the model
            return f"Could not read calendar: {exc}"


if __name__ == "__main__":
    import sys

    print(list_events(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 7))
