# Rot report: Underscore

`README.md` · **FRESH** · run 2026-09-02T03:05:45Z · image `python:3.12-slim` · engine docker

| # | line | status | time | detail |
|---|---|---|---|---|
| 1 | 55 | works | 0.5s |  |
| 2 | 62 | skipped |  |  |
| 3 | 69 | output differs | 20.3s | same exit code, different output (nothing documented; informational) |
| 4 | 80 | skipped |  |  |
| 5 | 117 | skipped |  |  |
| 6 | 135 | skipped |  |  |
| 7 | 177 | works | 6.4s |  |
| 8 | 185 | skipped |  |  |
| 9 | 212 | output differs | 8.3s | same exit code, different output (nothing documented; informational) |

works: 2, skipped: 5, output differs: 2

### Block 3 (line 69): output differs

```diff
@@ -178,3 +178,3 @@
  Building editable for rawlslab-underscore (pyproject.toml): finished with status 'done'
- Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9451 sha256=<masked>
+ Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9699 sha256=<masked>
  Stored in directory: <masked><masked>
```

### Block 9 (line 212): output differs

```diff
@@ -54,3 +54,3 @@
  Building editable for rawlslab-underscore (pyproject.toml): finished with status 'done'
- Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9451 sha256=<masked>
+ Created wheel for rawlslab-underscore: filename=rawlslab_underscore-0.1.0rc1-0.editable-py3-none-any.whl size=9699 sha256=<masked>
  Stored in directory: <masked><masked>
```
