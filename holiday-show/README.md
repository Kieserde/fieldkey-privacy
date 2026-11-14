# Holiday Santa (Raspberry Pi 5)
Voice-interactive, lip-synced AI Santa. See the blueprint for the full spec.
- `viseme_aligner.py`, `ai_backend.py` are pure Python and tested: `python -m pytest tests`
- `sprite_player.py`, `holiday_show.py` need the Pi (KMSDRM, ALSA, /dev/video0).
- Art assets (`packs/santa/sprites/`) are not generated yet; the renderer skips missing PNGs.
- Run `packs/santa/make_lines.py` on the Pi to pre-render canned lines.
- Deploy files in `deploy/` (systemd units, `/etc/default/holiday-show`).
- Unverified: Gemini TTS response field path in `_speak_gemini`.
