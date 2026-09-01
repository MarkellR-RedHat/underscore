#!/usr/bin/env bash
# Step zero: can this machine render Sonic Pi headlessly?
set -u
ok(){ printf "  \033[32m✓\033[0m %s\n" "$1"; }
no(){ printf "  \033[31m✗\033[0m %s\n" "$1"; }
echo "Underscore render check"
[ -d "/Applications/Sonic Pi.app" ] && ok "Sonic Pi.app installed" || no "Sonic Pi.app missing  (brew install --cask sonic-pi)"
command -v ffmpeg >/dev/null && ok "ffmpeg" || no "ffmpeg missing  (brew install ffmpeg)"
command -v sox >/dev/null && ok "sox" || no "sox missing  (brew install sox)"
R="/Applications/Sonic Pi.app/Contents/Resources/app/server/ruby/bin/headless-record.rb"
[ -f "$R" ] && ok "headless-record.rb present (Sonic Pi 5 headless recorder)" || no "headless recorder missing: Sonic Pi 5.0+ required"
echo
echo "If any ✗ remain, the built-in synth engine still runs the whole pipeline:"
echo "  underscore score --brief examples/brief.example.json --engine synth"
