# Rot report: Underscore

`README.md` · **FRESH** · run 2026-09-02T03:12:55Z · image `python:3.12-slim` · engine docker

| # | line | status | time | detail |
|---|---|---|---|---|
| 1 | 55 | works | 0.7s |  |
| 2 | 62 | skipped |  |  |
| 3 | 69 | output differs | 35.6s | same exit code, different output (nothing documented; informational) |
| 4 | 80 | skipped |  |  |
| 5 | 117 | skipped |  |  |
| 6 | 135 | skipped |  |  |
| 7 | 177 | works | 13.4s |  |
| 8 | 185 | skipped |  |  |
| 9 | 216 | output differs | 17.1s | same exit code, different output (nothing documented; informational) |

works: 2, skipped: 5, output differs: 2

### Block 3 (line 69): output differs

```diff
@@ -178,3 +178,3 @@
  Building editable for rawlslab-underscore (pyproject.toml): finished with status 'done'
- Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9451 sha256=<masked>
+ Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9824 sha256=<masked>
  Stored in directory: <masked><masked>
```

### Block 9 (line 216): output differs

```diff
@@ -54,3 +54,3 @@
  Building editable for rawlslab-underscore (pyproject.toml): finished with status 'done'
- Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9451 sha256=<masked>
+ Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9824 sha256=<masked>
  Stored in directory: <masked><masked>
```
