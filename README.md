# 경비보고서 자동화 시스템

영수증 이미지를 업로드하면 Claude AI가 자동으로 OCR 처리하고 Excel 경비보고서를 생성합니다.

## 주요 기능

- 영수증 이미지(JPG, PNG, HEIC, WEBP) 일괄 업로드
- Claude Vision AI로 한국어 영수증 OCR (날짜·금액·상호명 자동 추출)
- 카테고리 자동 분류 (LUNCH / DINNER / ENTERTAINMENT / TAXI / MISC 등)
- OCR 결과 웹 UI에서 직접 수정 가능
- 기존 Excel 템플릿에 자동 입력 (List 시트 + 주간 시트)
- Docker로 사내 서버 1분 배포

---

## 시작하기

### 무료 호스팅으로 테스트 배포

Render 무료 플랜 배포 가이드는 아래 문서를 참고하세요.

- `DEPLOY_FREE_RENDER.md`

### 방법 1: Docker (권장)

```bash
# 1. 이 폴더로 이동
cd expense-processor

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에서 SECRET_KEY 변경 (필수)
# ANTHROPIC_API_KEY 설정 (선택 - 비워두면 사용자가 웹에서 입력)

# 3. 서버 시작
docker-compose up -d

# 4. 브라우저에서 접속
open http://localhost:5000
```

### 방법 2: Python 직접 실행

```bash
# Python 3.10+ 필요
pip install -r requirements.txt

# 환경변수 설정 (Windows)
set SECRET_KEY=your-secret-key
set ANTHROPIC_API_KEY=sk-ant-...   # 선택

# 서버 실행
python app.py

# 브라우저 접속
open http://localhost:5000
```

---

## 사용 방법

1. **로그인**: `/login`에서 Microsoft 365 SSO 또는 로컬 비밀번호 로그인
2. **기본 설정**: Anthropic API 키, 직원 이름, 출장 제목 입력
3. **파일 업로드**: 영수증 이미지들 + Excel 템플릿 드래그앤드롭
4. **OCR 시작**: "OCR 시작" 버튼 클릭 → 자동 처리 (영수증 1장당 약 2~3초)
5. **데이터 검토**: OCR 결과 확인 및 오류 수정
6. **보고서 생성**: "보고서 생성" 클릭 → Excel 파일 다운로드

---

## Excel 템플릿 요구사항

기존에 사용하던 경비보고서 Excel 템플릿(.xlsx)을 그대로 사용할 수 있습니다.

시스템이 자동으로 감지하는 시트 구조:
- **List 시트**: `List`, `list`, `LIST`, `목록`, `리스트` 이름의 시트
- **주간 시트**: `1019`, `1026`, `1102` 등 MMDD 형식의 숫자 이름 시트

주간 시트의 기본 행 번호 (템플릿이 다를 경우 `excel_filler.py`의 `CATEGORY_ROW_MAP` 수정):
```python
CATEGORY_ROW_MAP = {
    "LUNCH":              18,
    "DINNER":             19,
    "ENTERTAINMENT":      20,
    "TAXI":               23,
    "OTHER TRANSPORT'N":  24,
    "TELEPHONE/INTERNET": 32,
    "MISCELLANEOUS":      33,
}
```

---

## API 키 관리

**옵션 A**: 서버에 미리 설정 (팀 전체 공유)
```bash
# .env 파일에서
ANTHROPIC_API_KEY=sk-ant-...
```
→ 사용자가 API 키를 입력하지 않아도 됩니다.

**옵션 B**: 사용자 입력 (개인별 API 키 사용)
→ `.env`에서 ANTHROPIC_API_KEY를 비워두면 웹 UI에서 매번 입력

---

## SSO (MS365) + 내부 사용자 DB

관리자 인증은 2가지 방식 중 선택할 수 있습니다.
- 로컬 비밀번호 로그인 (`ADMIN_PASSWORD`)
- Microsoft 365 SSO 로그인 (Entra ID OIDC)

SSO를 켜려면 `.env`에 아래를 설정하세요:
```bash
SSO_ENABLED=true
SSO_PROVIDER=microsoft
MS_TENANT_ID=<your-tenant-id-or-common>
MS_CLIENT_ID=<app-client-id>
MS_CLIENT_SECRET=<app-client-secret>
# 선택: 비우면 /auth/callback/microsoft 자동 사용
MS_REDIRECT_URI=
SSO_SCOPES=openid profile email User.Read
SSO_FETCH_ORG=true
ADMIN_EMAILS=admin1@company.com,admin2@company.com
```

Docker 사용 시에도 위 변수들을 `docker-compose`가 자동 전달합니다.

동작 방식:
- 첫 SSO 로그인 시 `users.db`에 사용자/아이덴티티를 자동 생성(JIT)
- `ADMIN_EMAILS`는 고객사 관리자 계정 목록
- `OPERATOR_EMAILS` / `OPERATOR_DOMAINS`는 운영자(서비스 제공사) 관리자 계정 정책
- `PROTECT_OPERATOR_ACCOUNTS=true`이면 운영자 계정은 강등/비활성화 불가
- 관리자 페이지는 로그인 세션이 있어야 접근 가능

관리자 페이지의 **Login Page Visuals** 섹션에서:
- 로그인 배경 슬라이드 이미지 여러 장 업로드
- 슬라이드 변경 인터벌(초) 설정

---

## 비용 안내

Claude API 사용료:
- 영수증 1장당 약 $0.003 (약 4원)
- 영수증 64장 처리 시 약 $0.20 (약 280원)

API 키 발급: https://console.anthropic.com

---

## 파일 구조

```
expense-processor/
├── app.py              # Flask 웹 서버
├── ocr.py              # Claude API OCR 처리
├── excel_filler.py     # Excel 템플릿 자동 입력
├── user_db.py          # SSO 사용자/아이덴티티 DB 관리
├── templates/
│   └── index.html      # 웹 UI
├── uploads/            # 업로드된 파일 (자동 생성)
├── outputs/            # 생성된 보고서 (자동 생성)
├── users.db            # 로컬 사용자 DB (자동 생성)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

# Receipt Inbox SaaS

Before implementing any UI or navigation changes, read:

docs/product/Receipt_Inbox_SaaS_PM_Reference_for_Codex_v1.md
docs/ux/receipt_inbox_saas_screenmap_userflow_routemap.md
docs/ux/receipt_inbox_saas_ui_component_map.md
