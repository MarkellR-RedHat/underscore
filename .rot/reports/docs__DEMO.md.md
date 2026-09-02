# Rot report: Underscore in twenty seconds

`docs/DEMO.md` · **STALE** · run 2026-09-02T03:12:55Z · image `python:3.12-slim` · engine docker

Stale since **2026-09-02**. Last fresh run: 2026-09-02.

| # | line | status | time | detail |
|---|---|---|---|---|
| 1 | 7 | dependency missing | 0.0s | exit 1, recorded 0 (first failure: underscore init demo --duration 90) |
| 2 | 13 | dependency missing | 0.0s | exit 1, recorded 0 (first failure: underscore score --brief demo.brief.json --engine synth) |
| 3 | 19 | command failed | 0.0s | exit 1, recorded 0 (first failure: python3 -c "import json; m = json.load(open('out/demo/manifest.json')); print('gate_passed', m['gate_passed'], '/', round(m['measurements']['lufs_integrated'], 1), 'LUFS')") |

dependency missing: 2, command failed: 1

### Block 1 (line 7): dependency missing

```diff
@@ -1 +1,11 @@
-wrote demo.brief.json (edit moods, energies, hits, speech; then: underscore score --brief demo.brief.json)
+Traceback (most recent call last):
+ File "/usr/local/bin/underscore", line 5, in <module>
+ from underscore.cli import main
+ File "/usr/local/lib/python3.12/site-packages/underscore/cli.py", line 10, in <module>
+ from .brief import Brief, BriefError, default_brief
+ File "/usr/local/lib/python3.12/site-packages/underscore/brief.py", line 20, in <module>
+ from ._vendor.brief import BriefError, Hit, MusicBrief, Section, Span, MOODS, HIT_KINDS # noqa: F401
+ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+ File "/usr/local/lib/python3.12/site-packages/underscore/_vendor/brief.py", line 27, in <module>
+ import yaml
```

Output (last lines; full log in `.rot/runs/docs__DEMO.md/`):

```text
Traceback (most recent call last):
  File "/usr/local/bin/underscore", line 5, in <module>
    from underscore.cli import main
  File "/usr/local/lib/python3.12/site-packages/underscore/cli.py", line 10, in <module>
    from .brief import Brief, BriefError, default_brief
  File "/usr/local/lib/python3.12/site-packages/underscore/brief.py", line 20, in <module>
    from ._vendor.brief import BriefError, Hit, MusicBrief, Section, Span, MOODS, HIT_KINDS  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/underscore/_vendor/brief.py", line 27, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
```

### Block 2 (line 13): dependency missing

```diff
@@ -1,4 +1,11 @@
-render: synth -> .underscore/demo/demo.raw.wav
-measure: -14.0 LUFS, peak -1.50 dBTP, LRA 3.0 LU -> PASS
-export: out/demo (8 files)
-timing: compose=<masked> render=<masked> master=<masked> measure=<masked>
+Traceback (most recent call last):
+ File "/usr/local/bin/underscore", line 5, in <module>
+ from underscore.cli import main
+ File "/usr/local/lib/python3.12/site-packages/underscore/cli.py", line 10, in <module>
+ from .brief import Brief, BriefError, default_brief
+ File "/usr/local/lib/python3.12/site-packages/underscore/brief.py", line 20, in <module>
+ from ._vendor.brief import BriefError, Hit, MusicBrief, Section, Span, MOODS, HIT_KINDS # noqa: F401
```

Output (last lines; full log in `.rot/runs/docs__DEMO.md/`):

```text
Traceback (most recent call last):
  File "/usr/local/bin/underscore", line 5, in <module>
    from underscore.cli import main
  File "/usr/local/lib/python3.12/site-packages/underscore/cli.py", line 10, in <module>
    from .brief import Brief, BriefError, default_brief
  File "/usr/local/lib/python3.12/site-packages/underscore/brief.py", line 20, in <module>
    from ._vendor.brief import BriefError, Hit, MusicBrief, Section, Span, MOODS, HIT_KINDS  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/underscore/_vendor/brief.py", line 27, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
```

### Block 3 (line 19): command failed

```diff
@@ -1 +1,3 @@
-gate_passed True | -14.0 LUFS
+Traceback (most recent call last):
+ File "<string>", line 1, in <module>
+FileNotFoundError: [Errno 2] No such file or directory: 'out/demo/manifest.json'
```

Output (last lines; full log in `.rot/runs/docs__DEMO.md/`):

```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
FileNotFoundError: [Errno 2] No such file or directory: 'out/demo/manifest.json'
```
