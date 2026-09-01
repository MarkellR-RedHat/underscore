#!/usr/bin/env bash
# Step zero: can this machine render Sonic Pi headlessly?
set -u
ok(){ printf "  \033[32m✓\033[0m %s\n" "$1"; }
no(){ printf "  \033[31m✗\033[0m %s\n" "$1"; }
echo "Underscore render check"
[ -d "/Applications/Sonic Pi.app" ] && ok "Sonic Pi.app installed" || no "Sonic Pi.app missing  (brew install --cask sonic-pi)"
command -v sonic-pi-tool >/dev/null && ok "sonic-pi-tool on PATH" || no "sonic-pi-tool missing  (pip install sonic-pi-tool)"
command -v ffmpeg >/dev/null && ok "ffmpeg" || no "ffmpeg missing  (brew install ffmpeg)"
command -v sox >/dev/null && ok "sox" || no "sox missing  (brew install sox)"
if command -v sonic-pi-tool >/dev/null; then
  if sonic-pi-tool check >/dev/null 2>&1; then ok "Sonic Pi server reachable (app is running)";
  else no "Sonic Pi server not reachable: open Sonic Pi.app, then rerun"; fi
fi
echo
echo "If any ✗ remain, the built-in synth engine still runs the whole pipeline:"
echo "  underscore score --brief examples/brief.example.json --engine synth"
