#!/usr/bin/env bash
# RC rehearsal: everything the public flip will do, in scratch, without touching this repository or GitHub.
#
#   bash scripts/rc-rehearsal.sh [--keep]
#
# Steps, in order:
#   1. Build the clean public branch and check it, by calling the family's shared step
#      ~/launch/comms/flip/public-branch.sh (one orphan commit, INTERNAL.md gone, flip-check on an
#      isolated clone). This script does not carry its own copy of that recipe.
#   2. Build the wheel from that clean tree and install it into a clean virtualenv outside any checkout.
#   3. Run the tool from the installed wheel with no model and no Sonic Pi: init a brief, score it on the
#      synth engine, and confirm the gate passed in the manifest.
#   4. Print a one-line verdict for FEATURES.md.
#
# Read-only against this repository and against GitHub. Nothing is pushed, no repository is renamed.
# Exit 0 only when every step passed.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOL=underscore
PKG=rawlslab-underscore
LAUNCH="${LAUNCH_DIR:-$HOME/launch}"
FLIP_CHECK="${FLIP_CHECK:-$LAUNCH/comms/flip/flip-check.sh}"
PUBLIC_BRANCH="${PUBLIC_BRANCH:-$LAUNCH/comms/flip/public-branch.sh}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/rc-rehearsal-$TOOL.XXXXXX")"
KEEP="${KEEP:-0}"
[ "${1:-}" = "--keep" ] && KEEP=1

FAILED=0
PASSES=0
FAILURES=()
step() { printf '\n== %s ==\n' "$1"; }
ok()   { PASSES=$((PASSES+1)); printf '[PASS] %s\n' "$1"; }
bad()  { FAILED=1; FAILURES+=("$1"); printf '[FAIL] %s\n' "$1"; }
cleanup() { [ "$KEEP" = 1 ] && printf '\nworkspace kept: %s\n' "$WORK" || rm -rf "$WORK"; }
trap cleanup EXIT

printf 'RC rehearsal for %s\nrepository: %s\ncommit:     %s\nworkspace:  %s\n' \
  "$TOOL" "$REPO_ROOT" "$(git -C "$REPO_ROOT" rev-parse --short HEAD)" "$WORK"

# ---------------------------------------------------------------- 1. public branch and flip check
step "Clean public branch and flip check (shared step)"
[ -x "$PUBLIC_BRANCH" ] || { bad "$PUBLIC_BRANCH is missing; it is the shared orphan-rebuild step"; exit 2; }
# public-branch.sh builds the orphan branch in a fresh clone, verifies it in an isolated clone with
# flip-check.sh, and pushes nothing. Exit 0 means the branch was built and the check passed.
if "$PUBLIC_BRANCH" "$REPO_ROOT" --out "$WORK" --keep --skip-build > "$WORK/public-branch.log" 2>&1; then
  ok "public branch built and flip-check PASS"
else
  case $? in
    1) bad "flip-check failed on the public branch" ;;
    *) bad "public-branch.sh could not run (usage or environment)" ;;
  esac
fi
grep -E '^(RESULT|\[FAIL\]|isolated|build|commit)' "$WORK/public-branch.log" | sed 's/^/        /'
CLEAN="$WORK/$(basename "$REPO_ROOT")-isolated"
[ -d "$CLEAN" ] || { bad "no isolated clone at $CLEAN"; exit 1; }
COMMITS="$(git -C "$CLEAN" log --all --oneline | wc -l | tr -d ' ')"
[ "$COMMITS" = 1 ] && ok "one commit in the isolated clone" || bad "isolated clone has $COMMITS commits, expected 1"
[ -e "$CLEAN/INTERNAL.md" ] && bad "INTERNAL.md still present" || ok "INTERNAL.md gone"

# ---------------------------------------------------------------- 2. wheel into a clean venv
step "Wheel into a clean virtualenv"
python3 -m venv "$WORK/build-venv" >/dev/null 2>&1
"$WORK/build-venv/bin/pip" install -q build >/dev/null 2>&1
if ( cd "$CLEAN" && "$WORK/build-venv/bin/python" -m build --wheel --outdir "$WORK/dist" >"$WORK/build.log" 2>&1 ); then
  WHEEL="$(ls "$WORK"/dist/*.whl 2>/dev/null | head -1)"
  ok "wheel built: $(basename "$WHEEL")"
else
  bad "wheel build"; tail -5 "$WORK/build.log" | sed 's/^/        /'
fi
if [ -n "${WHEEL:-}" ]; then
  python3 -m venv "$WORK/venv" >/dev/null 2>&1
  if "$WORK/venv/bin/pip" install -q "$WHEEL" >"$WORK/install.log" 2>&1; then
    ok "installs into a clean venv"
    V="$("$WORK/venv/bin/python" -c "import importlib.metadata as m; print(m.version('$PKG'))" 2>/dev/null)"
    [ -n "$V" ] && ok "$PKG $V" || bad "version not readable"
    "$WORK/venv/bin/$TOOL" --help >/dev/null 2>&1 && ok "$TOOL --help" || bad "$TOOL --help"
  else
    bad "wheel install"; tail -5 "$WORK/install.log" | sed 's/^/        /'
  fi
fi

# ---------------------------------------------------------------- 3. the tool runs, offline
step "Synth-engine run from the installed wheel, no model, no Sonic Pi"
if [ -x "$WORK/venv/bin/$TOOL" ]; then
  RUN="$WORK/run"; mkdir -p "$RUN"
  if ( cd "$RUN" && env -u UNDERSCORE_CLI -u UNDERSCORE_API_URL -u UNDERSCORE_API_KEY -u UNDERSCORE_LOCAL \
        "$WORK/venv/bin/$TOOL" init rehearsal --duration 20 >/dev/null 2>&1 && \
        env -u UNDERSCORE_CLI -u UNDERSCORE_API_URL -u UNDERSCORE_API_KEY -u UNDERSCORE_LOCAL \
        "$WORK/venv/bin/$TOOL" score --brief rehearsal.brief.json --engine synth >"$WORK/score.log" 2>&1 ); then
    ok "init and score ran"
    if "$WORK/venv/bin/python" - "$RUN/out/rehearsal/manifest.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
assert m["gate_passed"], m["gate_reasons"]
assert m["files"].get("master") and m["files"].get("preview"), m["files"]
print("        gate passed, %d files, %.1f LUFS" % (len(m["files"]), m["measurements"]["lufs_integrated"]))
PY
    then ok "gate passed in the manifest"; else bad "manifest check"; fi
    [ -s "$RUN/out/rehearsal/gates.json" ] && ok "gates.json written" || bad "gates.json missing"
    [ -s "$RUN/out/rehearsal/LICENSE-CC0.txt" ] && ok "CC0 dedication in the bundle" || bad "LICENSE-CC0.txt missing"
  else
    bad "score run"; tail -5 "$WORK/score.log" | sed 's/^/        /'
  fi
fi

# ---------------------------------------------------------------- 4. verdict
step "Verdict"
printf '%d check(s) passed, %d failed\n' "$PASSES" "${#FAILURES[@]}"
for f in ${FAILURES+"${FAILURES[@]}"}; do printf '  failed: %s\n' "$f"; done
if [ "$FAILED" = 0 ]; then
  printf 'RC REHEARSAL PASS for %s at %s on %s\n' "$TOOL" "$(git -C "$REPO_ROOT" rev-parse --short HEAD)" "$(date -u +%Y-%m-%d)"
  exit 0
fi
printf 'RC REHEARSAL FAIL for %s at %s on %s\n' "$TOOL" "$(git -C "$REPO_ROOT" rev-parse --short HEAD)" "$(date -u +%Y-%m-%d)"
exit 1
