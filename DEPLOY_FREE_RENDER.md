# 무료 호스팅 배포 가이드 (Render)

이 문서는 `expense-processor`를 무료 플랜으로 빠르게 테스트 배포하는 절차입니다.

## 1) GitHub 저장소 준비

Render는 Git 기반으로 배포하므로 먼저 코드를 GitHub에 올립니다.

```bash
git init
git add .
git commit -m "chore: add free hosting deploy config"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

이미 Git 저장소가 있다면 `git add/commit/push`만 하면 됩니다.

## 2) Render에 서비스 생성

1. [Render Dashboard](https://dashboard.render.com/) 접속
2. `New +` -> `Blueprint`
3. 방금 올린 GitHub 저장소 선택
4. `render.yaml`을 자동 인식하면 `Apply` 클릭

배포 완료 후 `https://<service-name>.onrender.com` 형태 URL이 발급됩니다.

## 3) 환경변수 설정

Render 대시보드 서비스 설정에서 아래 값 확인/수정:

- `SECRET_KEY`: 자동 생성값 사용 가능
- `ANTHROPIC_API_KEY`: 실제 OCR 테스트 시 필수 입력
- `LOCAL_LOGIN_PASSWORD`: 기본 `admin123` (배포 후 변경 권장)
- `SSO_ENABLED`: 기본 `false`

## 4) 테스트 포인트

- 첫 접속: 로그인 페이지 또는 메인 화면 열림
- 영수증 업로드 + OCR 실행 확인
- Excel 생성/다운로드 확인

## 주의사항 (무료 플랜)

- 유휴 시 슬립(재기동 지연) 가능
- 파일시스템은 영구 저장소가 아님
- `users.db`, `receipt_inbox.db`, `uploads`, `outputs`는 재배포/재시작 시 유실될 수 있음

즉, 현재 목적(실서비스 전 기능 검증용)에는 적합하지만 운영용으로는 별도 서버/스토리지 구성이 필요합니다.
