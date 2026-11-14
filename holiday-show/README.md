# Holiday Show (Raspberry Pi 5)
Voice-interactive, lip-synced Christmas characters: Santa, Mrs. Claus, Jingle and Holly the elves, Rudolph, Frosty, Ginger the gingerbread cookie.

## Every visit is different
`variety.py` rotates the character (no repeat within 3 visits) and a conversation "mode" (joke, fact, riddle, game...), randomizes
LLM temperature, picks canned lines without repeating the last one, and avoids paraphrasing the last 40 replies.
Each visit opens with a fresh LLM-written line spoken in that character's own Gemini voice.

## Art
`python art.py` redraws all characters, eyes, 7 mouth shapes, and the workshop background in code (no image credits). `preview.png` is a contact sheet.

## Check it
`python -m pytest tests` (needs `pytest pillow numpy`; `pygame` optional for the headless render test).

## Still needs the real Pi
Camera/mic capture, KMSDRM display, HDMI audio, whisper-server, and the Gemini TTS response shape
(`_speak_gemini` field path is a guess). Run `packs/santa/make_lines.py` once to render canned lines for every character.
Deploy files are in `deploy/`.
