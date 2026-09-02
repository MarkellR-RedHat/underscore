# Rot report: Underscore

`README.md` · **FRESH** · run 2026-09-02T03:26:52Z · image `python:3.12-slim` · engine docker

| # | line | status | time | detail |
|---|---|---|---|---|
| 1 | 55 | works | 0.7s |  |
| 2 | 62 | skipped |  |  |
| 3 | 69 | output differs | 37.1s | same exit code, different output (nothing documented; informational) |
| 4 | 80 | skipped |  |  |
| 5 | 117 | skipped |  |  |
| 6 | 135 | skipped |  |  |
| 7 | 177 | works | 13.1s |  |
| 8 | 185 | skipped |  |  |
| 9 | 216 | output differs | 16.0s | same exit code, different output (nothing documented; informational) |

works: 2, skipped: 5, output differs: 2

### Block 3 (line 69): output differs

```diff
@@ -23,2 +23,4 @@
  Using cached mutagen-1.48.1-py3-none-any.whl.metadata (<masked>)
+Collecting pyyaml>=6 (from rawlslab-underscore==0.1.0rc1)
+ Using cached pyyaml-6.0.3-cp312-cp312-<masked> (<masked>)
 Collecting scenedetect>=0.6 (from rawlslab-underscore==0.1.0rc1)
@@ -73,4 +75,2 @@
  Using cached pycparser-3.0-py3-none-any.whl.metadata (<masked>)
-Collecting pyyaml<7,>=5.3 (from ctranslate2<5,>=4.0->faster-whisper>=1.0->rawlslab-underscore==0.1.0rc1)
- Downloading pyyaml-6.0.3-cp312-cp312-<masked> (<masked>)
 Collecting filelock>=3.10.0 (from huggingface-hub>=0.21->faster-whisper>=1.0->rawlslab-underscore==0.1.0rc1)
@@ -123,2 +123,3 @@
 Using cached python_osc-1.10.2-py3-none-any.whl (<masked>)
```

### Block 9 (line 216): output differs

```diff
@@ -16,2 +16,3 @@
 Requirement already satisfied: mutagen>=1.47 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (1.48.1)
+Requirement already satisfied: pyyaml>=6 in ./.venv/lib/python3.12/site-packages (from rawlslab-underscore==0.1.0rc1) (6.0.3)
 Collecting pytest>=8 (from rawlslab-underscore==0.1.0rc1)
@@ -54,3 +55,3 @@
  Building editable for rawlslab-underscore (pyproject.toml): finished with status 'done'
- Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9451 sha256=<masked>
+ Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9836 sha256=<masked>
  Stored in directory: <masked><masked>
@@ -65,3 +66,3 @@
 <masked>
-...................................... [100%]
```
