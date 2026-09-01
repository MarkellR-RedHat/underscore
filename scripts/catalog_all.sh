#!/usr/bin/env bash
# Render every collection in sequence, one Sonic Pi render at a time.
# Resumable: finished beds are skipped, failed beds are retried on the next pass.
set -u
cd "$(dirname "$0")/.."
for c in "$@"; do
  echo "=== collection $c  $(date '+%H:%M')" >> catalog-run.log
  .venv/bin/python scripts/catalog.py --out catalog --collection "$c" --limit 18 >> catalog-run.log 2>&1
  .venv/bin/python scripts/catalog.py --out catalog --collection "$c" --limit 18 >> catalog-run.log 2>&1   # retry pass for any gate failures
done
.venv/bin/python scripts/build_catalog_page.py --catalog catalog >> catalog-run.log 2>&1
echo "=== ALL COLLECTIONS DONE $(date '+%H:%M')" >> catalog-run.log
