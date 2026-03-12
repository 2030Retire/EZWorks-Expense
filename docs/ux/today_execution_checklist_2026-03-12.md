# Today Execution Checklist (2026-03-12)

## 오늘 목표
- 출시 blocker의 실제 남은 양을 확인할 수 있게, 실환경 핵심 검증 4가지를 끝낸다.

## 오늘 할 일

### 1. SSO 실로그인
- 관리자 계정 로그인 1회
- 일반 사용자 계정 로그인 1회
- 로그인 후 `/dashboard`, `/inbox/review`, `/admin` 접근 확인
- 다른 host 접근 시 차단 여부 확인

## 2. OCR 샘플 3종
- 정상 영수증 1건 OCR 실행
- 저신뢰 또는 unreadable 영수증 1건 OCR 실행
- 실패 케이스 1건 OCR 실행
- Review에서 상태와 메시지 확인

## 3. 실제 템플릿 1세트 검증
- 실제 domestic 템플릿으로 보고서 1회 생성
- 가능하면 international 또는 document override 1회 추가 생성
- 생성 Excel 열어서 금액/날짜/카테고리/직원 정보 위치 확인

## 4. 결과 기록
- `docs/ux/release_smoke_checklist.md`에 PASS/FAIL 표시
- 증적 파일 경로 또는 스크린샷 위치 기록
- blocker가 남으면 원인 1줄 기록

## 오늘 완료 기준
- SSO 2계정 확인 완료
- OCR 3케이스 확인 완료
- 템플릿 생성 결과 1세트 이상 확인 완료
- UAT/릴리즈 문서에 오늘 결과 반영 완료
