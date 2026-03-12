# Weekly Execution Checklist (2026-03-12)

## 목적
- 이번 주에 출시 blocker를 줄이기 위한 실제 실행 순서를 한 페이지로 정리한다.
- 자동 테스트 완료 이후, 실환경 검증과 UAT 증적 채우기에 집중한다.

## 이번 주 우선순위
1. SSO 실환경 검증
2. OCR 실영수증 검증
3. 템플릿 실파일 검증
4. UAT 결과 문서 확정
5. 백업/운영 절차 정리

## 1. SSO 실환경 검증
- 관리자 계정 1개로 로그인 성공 확인
- 일반 사용자 계정 1개로 로그인 성공 확인
- redirect URI가 현재 host와 맞는지 확인
- 로그인 후 세션이 유지되고 `/dashboard`, `/inbox/review`, `/admin` 접근이 기대대로 동작하는지 확인
- 다른 host로 바꿨을 때 cross-tenant 접근이 차단되는지 확인

## 2. OCR 실영수증 검증
- 정상 영수증 1건 이상 OCR 성공 확인
- 저신뢰 또는 unreadable 샘플 1건 이상 확인
- 실패 케이스 1건 이상 확인
- Review에서 `needs_review`, `duplicate`, `low confidence` 관련 상태가 실제로 읽히는지 확인
- force 없는 OCR 재실행 차단 문구 확인

## 3. 템플릿 실파일 검증
- 실제 고객사 domestic 템플릿으로 1회 생성
- 실제 고객사 international 템플릿으로 1회 생성
- document override 템플릿이 있으면 1회 생성
- 생성된 Excel 파일을 열어 List / 주간 시트 매핑이 맞는지 확인
- 금액/날짜/카테고리/직원 정보가 기대 위치에 들어가는지 확인

## 4. UAT 결과 문서 확정
- `docs/ux/release_smoke_checklist.md` 기준으로 PASS/FAIL 입력
- critical 케이스별 실제 결과와 증적 파일 경로 기록
- `docs/ux/uat_evidence/2026-03-08/uat_result_summary.md` 상태 갱신
- blocker가 남으면 이유와 재시험 조건 적기

## 5. 운영 절차 정리
- `users.db`, `receipt_inbox.db`, `uploads/`, `outputs/` 백업 위치 정의
- 백업 주기와 담당자 정의
- 배포 후 smoke 실행 담당자 정의
- 장애 시 확인할 로그/파일 위치 정리

## 완료 조건
- SSO / OCR / 템플릿 실검증 각각 최소 1회 이상 완료
- UAT critical 항목이 더 이상 전부 `PENDING`이 아님
- 운영자가 백업/복구 위치를 설명할 수 있음
