# Google Sheets 수동 설정 가이드

비개발자 기준으로 작성. 코드 실행 없이 따라할 수 있습니다.

---

## 1단계 — Google Cloud 프로젝트 생성

1. https://console.cloud.google.com 접속 → Google 계정 로그인
2. 상단 프로젝트 선택 드롭다운 → **새 프로젝트** 클릭
3. 프로젝트 이름: `investment-assistant` → **만들기**

---

## 2단계 — Google Sheets API 활성화

1. 좌측 메뉴 → **API 및 서비스** → **라이브러리**
2. 검색창에 `Google Sheets API` 입력 → 클릭 → **사용 설정**
3. 동일하게 `Google Drive API`도 사용 설정

---

## 3단계 — OAuth 2.0 자격증명 생성

1. **API 및 서비스** → **사용자 인증 정보** → **사용자 인증 정보 만들기** → **OAuth 클라이언트 ID**
2. 처음이라면 **동의 화면 구성** 먼저:
   - 유형: **외부** → 앱 이름 입력 → 저장
   - 테스트 사용자에 본인 이메일 추가
3. 애플리케이션 유형: **데스크톱 앱** → 이름: `investment-assistant` → **만들기**
4. 팝업에서 **JSON 다운로드** → 파일을 `config/google_credentials.json`으로 저장

---

## 4단계 — Refresh Token 발급

터미널에서 아래 실행 (Python 필요):

```bash
pip install google-auth-oauthlib
python3 - <<'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
flow = InstalledAppFlow.from_client_secrets_file("config/google_credentials.json", SCOPES)
creds = flow.run_local_server(port=0)
print("REFRESH_TOKEN:", creds.refresh_token)
print("CLIENT_ID:", creds.client_id)
print("CLIENT_SECRET:", creds.client_secret)
EOF
```

브라우저가 열리면 Google 계정으로 로그인 → 권한 허용  
출력된 값을 `config/secrets.env`에 복사

---

## 5단계 — Google Sheets 파일 생성

1. https://sheets.google.com → 새 스프레드시트 생성
2. 탭 이름 변경: `Sheet1` → `일일브리핑`
3. 새 탭 추가: `주간포트폴리오리포트`
4. 각 탭에 `docs/google_sheets_schema.md`의 컬럼명을 1행에 입력
5. URL에서 Spreadsheet ID 복사:
   - URL 형식: `https://docs.google.com/spreadsheets/d/`**`[SPREADSHEET_ID]`**`/edit`
   - 이 ID를 `config/secrets.env`의 `GOOGLE_SHEETS_SPREADSHEET_ID`에 입력

---

## 6단계 — secrets.env 최종 확인

```env
GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxx
GOOGLE_REFRESH_TOKEN=1//0exxxxxxx
GOOGLE_SHEETS_SPREADSHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

---

## 연동 테스트

```bash
python3 scripts/test_sheets.py  # (생성 예정)
```

정상이면: `✅ Google Sheets 연결 성공` 출력
