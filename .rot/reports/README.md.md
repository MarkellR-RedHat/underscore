# Rot report: Underscore

`README.md` · **FRESH** · run 2026-09-22T19:41:08Z · image `python:3.12-slim` · engine docker

| # | line | status | time | detail |
|---|---|---|---|---|
| 1 | 55 | works | 0.6s |  |
| 2 | 62 | skipped |  |  |
| 3 | 69 | output differs | 37.2s | same exit code, different output (nothing documented; informational) |
| 4 | 80 | skipped |  |  |
| 5 | 117 | skipped |  |  |
| 6 | 131 | skipped |  |  |
| 7 | 160 | skipped |  |  |
| 8 | 203 | works | 13.3s |  |
| 9 | 211 | skipped |  |  |
| 10 | 243 | output differs | 19.2s | same exit code, different output (nothing documented; informational) |

works: 2, skipped: 6, output differs: 2

### Block 3 (line 69): output differs

```diff
@@ -9,175 +9,175 @@
  Preparing editable metadata (pyproject.toml): finished with status 'done'
-Collecting numpy>=1.24 (from rawlslab-underscore==0.1.0rc1)
- <masked> numpy-2.5.2-cp312-cp312-<masked> (<masked>)
-Collecting soundfile>=0.12 (from rawlslab-underscore==0.1.0rc1)
- <masked> soundfile-0.14.0-py2.py3-none-<masked> (<masked>)
-Collecting pyloudnorm>=0.1.1 (from rawlslab-underscore==0.1.0rc1)
- <masked> pyloudnorm-0.2.0-py3-none-any.whl.metadata (<masked>)
-Collecting pedalboard>=0.9 (from rawlslab-underscore==0.1.0rc1)
- <masked> pedalboard-0.9.24-cp312-cp312-<masked> (<masked>)
-Collecting librosa>=0.10 (from rawlslab-underscore==0.1.0rc1)
- <masked> librosa-1.0.0-py3-none-any.whl.metadata (<masked>)
```

### Block 10 (line 243): output differs

```diff
@@ -9,57 +9,57 @@
  Preparing editable metadata (pyproject.toml): finished with status 'done'
-Requirement already satisfied: numpy>=1.24 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (2.5.2)
-Requirement already satisfied: soundfile>=0.12 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (0.14.0)
-Requirement already satisfied: pyloudnorm>=0.1.1 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (0.2.0)
-Requirement already satisfied: pedalboard>=0.9 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (0.9.24)
-Requirement already satisfied: librosa>=0.10 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (1.0.0)
-Requirement already satisfied: python-osc>=1.8 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (1.10.2)
-Requirement already satisfied: mutagen>=1.47 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (1.48.1)
-Requirement already satisfied: pyyaml>=6 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (6.0.3)
-Collecting pytest>=8 (from rawlslab-underscore==0.1.0rc1)
- <masked> pytest-9.1.1-py3-none-any.whl.metadata (<masked>)
```
