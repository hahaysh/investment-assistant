#!/bin/bash
# 투자 비서 웹앱 실행 스크립트
# 사용법: bash ~/investment-assistant/webapp/start.sh

WEBAPP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$WEBAPP_DIR"

echo "[1/2] 패키지 설치 중..."
pip install -r requirements.txt --break-system-packages -q

echo "[2/2] 서버 시작 (포트 8000)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
