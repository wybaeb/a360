#!/bin/sh
# Полная пересборка артефактов после изменения промптов, данных или текстов.
# Порядок важен: страницы берут и промпты, и результаты прогонов, и отчёты.
set -e
cd "$(dirname "$0")/.."
python3 build/gen_data.py
python3 build/gen_js.py
python3 build/check_reports_safety.py
python3 build/pick_best.py
A360_PASSWORD="${A360_PASSWORD:?нужен A360_PASSWORD}" python3 build/build_pages.py
python3 build/build_scorm.py
python3 build/build_report.py
echo "готово"
