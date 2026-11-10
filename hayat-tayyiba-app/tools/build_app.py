"""Inject the notebook content (data/hayat-tayyiba-2027.json) into the app template.

Outputs:
  index.html     standalone page (open in any browser, works offline after first load)
  artifact.html  same app without the document skeleton, for publishing as a claude.ai Artifact
"""
import json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
tpl = (root / 'src' / 'app.html').read_text()
data = json.loads((root / 'data' / 'hayat-tayyiba-2027.json').read_text())
blob = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
body = tpl.replace('/*DATA*/', blob)
(root / 'artifact.html').write_text(body)
head = ('<!doctype html>\n<html lang="ar" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<meta name="theme-color" content="#3c462f">\n'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}[hidden]{display:none!important}</style>\n'
        '</head>\n<body>\n')
(root / 'index.html').write_text(head + body + '\n</body>\n</html>\n')
print('built', len(body.encode()) // 1024, 'KB')
