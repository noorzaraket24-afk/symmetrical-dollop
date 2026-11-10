# مفكرة الحياة الطيّبة ٢٠٢٧ — التطبيق التفاعلي

نسخة تفاعلية من الدفاتر الثلاثة لمفكرة «الحياة الطيّبة»:
المحطة الأولى (الجذر)، والثانية (الساق والأغصان)، والثالثة (الثمر).

## ما فيه
- **صفحة لكلّ يوم من أيّام ٢٠٢٧ (٣٦٥ يوماً)**، فيها أسئلة الصبح والنهار والمسا كما وردت في الدفتر، ومكان للكتابة، و«نيّتي اليوم»، و«أطيب ما في يومي»، ومتابعة العبادات.
- **البذرة / الورقة / الثمرة** تمتلئ وحدها: نصفها عند إتمام وقت أو وقتين، وكلّها عند إتمام الأوقات الثلاثة.
- **خريطة كلّ محطة**: كلّ يوم بذرة، والخطّ الذهبي يفصل بين الأسابيع، وكلّ بذرة رابط إلى صفحة يومها.
- **صفحات الأشهر والأسابيع**: الآية، والاقتباس، و«من سيرته / من وصاياه»، والتقويم، والنيّة، ووقفة آخر الأسبوع.
- **عهد المحطة، والخطاب الكبير، وميزان الشهر، والحصاد**.
- **الحفظ**: تُحفظ الكتابة تلقائياً على الجهاز (وفي الحساب عند فتحه كـ Artifact على claude.ai)، مع نسخة احتياطية يمكن نسخها واستعادتها.

## التشغيل
افتح `index.html` في أيّ متصفّح، على الهاتف أو الحاسوب. لا يحتاج إلى خادم ولا إلى تثبيت.
ولنشره على رابط، فعّل GitHub Pages لهذا المستودع وافتح `hayat-tayyiba-app/index.html`.

## البنية
| الملف | الوظيفة |
|---|---|
| `src/app.html` | قالب التطبيق (التصميم والمنطق) |
| `data/hayat-tayyiba-2027.json` | محتوى الدفاتر الثلاثة مستخرجاً من ملفات PDF |
| `tools/build_app.py` | يدمج المحتوى في القالب ويُخرج `index.html` و`artifact.html` |
| `tools/extract/` | سكربتات استخراج النصّ العربي من ملفات PDF (تُعيد ترتيب الشدّة والتنوين اللذين يفصلهما الـPDF عن الحروف) |

بعد تعديل القالب أو المحتوى: `python3 tools/build_app.py`

## Notes (English)
Interactive web app built from the three 2027 "Al-Hayat Al-Tayyiba" notebook PDFs.
All 365 daily pages, 48 weekly pages, 12 monthly pages, monthly reviews, covenants, harvests
and seed maps are reproduced from the PDFs. Quranic verses were re-entered by hand because
the PDF's Quran font does not extract cleanly. Entries are stored in `localStorage`
(and in the viewer's private store when opened as a claude.ai Artifact), with JSON backup/restore.
