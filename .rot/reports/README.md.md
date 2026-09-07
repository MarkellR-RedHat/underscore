# Rot report: Underscore

`README.md` · **FRESH** · run 2026-09-07T17:25:12Z · image `python:3.12-slim` · engine docker

| # | line | status | time | detail |
|---|---|---|---|---|
| 1 | 55 | works | 0.7s |  |
| 2 | 62 | skipped |  |  |
| 3 | 69 | output differs | 38.3s | same exit code, different output (nothing documented; informational) |
| 4 | 80 | skipped |  |  |
| 5 | 117 | skipped |  |  |
| 6 | 135 | skipped |  |  |
| 7 | 177 | works | 13.2s |  |
| 8 | 185 | skipped |  |  |
| 9 | 216 | output differs | 16.9s | same exit code, different output (nothing documented; informational) |

works: 2, skipped: 5, output differs: 2

### Block 3 (line 69): output differs

```diff
@@ -10,166 +10,166 @@
 Collecting numpy>=1.24 (from rawlslab-underscore==0.1.0rc1)
- <masked> numpy-2.5.2-cp312-cp312-<masked> (<masked>)
+ Using cached numpy-2.5.3-cp312-cp312-<masked> (<masked>)
 Collecting soundfile>=0.12 (from rawlslab-underscore==0.1.0rc1)
- <masked> soundfile-0.14.0-py2.py3-none-<masked> (<masked>)
+ Using cached soundfile-0.14.0-py2.py3-none-<masked> (<masked>)
 Collecting pyloudnorm>=0.1.1 (from rawlslab-underscore==0.1.0rc1)
- <masked> pyloudnorm-0.2.0-py3-none-any.whl.metadata (<masked>)
+ Using cached pyloudnorm-0.2.0-py3-none-any.whl.metadata (<masked>)
 Collecting pedalboard>=0.9 (from rawlslab-underscore==0.1.0rc1)
- <masked> pedalboard-0.9.24-cp312-cp312-<masked> (<masked>)
```

### Block 9 (line 216): output differs

```diff
@@ -9,3 +9,3 @@
  Preparing editable metadata (pyproject.toml): finished with status 'done'
-Requirement already satisfied: numpy>=1.24 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (2.5.2)
+Requirement already satisfied: numpy>=1.24 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (2.5.3)
 Requirement already satisfied: soundfile>=0.12 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (0.14.0)
@@ -18,3 +18,3 @@
 Collecting pytest>=8 (from rawlslab-underscore==0.1.0rc1)
- <masked> pytest-9.1.1-py3-none-any.whl.metadata (<masked>)
+ Using cached pytest-9.1.1-py3-none-any.whl.metadata (<masked>)
 Requirement already satisfied: numba>=0.61.0 in ./.venv/lib/python3.12/site-packages (from librosa>=0.10->rawlslab-underscore==0.1.0rc1) (0.67.0)
@@ -29,8 +29,8 @@
 Collecting iniconfig>=1.0.1 (from pytest>=8->rawlslab-underscore==0.1.0rc1)
```
