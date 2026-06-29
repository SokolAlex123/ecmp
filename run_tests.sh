#!/bin/bash
set -e
echo "=== Запуск настройки ECMP стенда ==="
/usr/local/bin/setup_ecmp.sh

echo ""
echo "=== Запуск автотестов ==="
cd /tests
pytest test_ecmp.py -v --tb=short

