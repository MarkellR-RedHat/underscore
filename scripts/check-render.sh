#!/usr/bin/env bash
# Step zero: can this machine render Sonic Pi headlessly?
set -u
ok(){ printf "  \033[32m✓\033[0m %s\n" "$1"; }
no(){ printf "  \033[31m✗\033[0m %s\n" "$1"; }
echo "Underscore render check"
APP_SERVER="/Applications/Sonic Pi.app/Contents/Resources/app/server"
[ -d "/Applications/Sonic Pi.app" ] && ok "Sonic Pi.app installed" || no "Sonic Pi.app missing  (brew install --cask sonic-pi)"
[ -x "$APP_SERVER/native/ruby/bin/ruby" ] && ok "bundled ruby present" || no "bundled ruby missing: Sonic Pi 5.0+ required"
[ -f "$APP_SERVER/ruby/bin/headless_boot.rb" ] && ok "headless_boot.rb present (Sonic Pi 5 headless boot library)" || no "headless boot library missing: Sonic Pi 5.0+ required"
command -v ffmpeg >/dev/null && ok "ffmpeg" || no "ffmpeg missing  (brew install ffmpeg)"
command -v ffprobe >/dev/null && ok "ffprobe" || no "ffprobe missing  (comes with ffmpeg)"
echo
echo "If any ✗ remain, the built-in synth engine still runs the whole pipeline:"
echo "  underscore score --brief examples/brief.example.json --engine synth"
