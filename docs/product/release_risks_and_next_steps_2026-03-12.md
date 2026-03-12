# Release Risks And Next Steps

## Goal
- 현재 구현/테스트 상태를 기준으로 출시 판단에 영향을 주는 남은 리스크를 분류한다.
- 다음 개발 우선순위를 `출시 blocker`, `출시 전 권장`, `후속 개선`으로 나눠 실행 순서를 명확히 한다.

## Constraints
- 백엔드 핵심 권한/운영 경계는 자동 테스트 21건으로 기본 회귀 방어가 생겼다.
- `python -m pytest` 기준 자동 스모크는 통과했지만, 실서비스 외부 연동과 브라우저 UX 확인은 별도다.
- 2026-03-08 기준 UAT 결과는 `CONDITIONAL NO-GO`이며 critical/manual 항목이 아직 전부 `PENDING`이다.
- 현재 저장 구조는 로컬 파일시스템 + SQLite이며, 대규모 운영/보관 정책은 아직 설계 단계다.

## Proposed Architecture Focus
- Auth / Tenant:
  로컬 로그인, MS365 SSO, host 스코프, operator/tenant admin 경계를 유지하되 실환경 검증을 추가한다.
- Data / Storage:
  현재 SQLite + 로컬 파일 업로드 구조는 MVP/파일럿에는 적합하지만 보관/백업/복구 기준이 필요하다.
- Admin / Operations:
  템플릿, 권한, 감사로그, KPI는 기본 기능이 있으므로 이제 운영 절차와 릴리즈 체크를 붙이는 단계다.
- UX / Release:
  자동 스모크와 수동 릴리즈 체크리스트를 연결했으므로, 이제 실제 UAT 증적을 채워 GO/NO-GO 기준을 완성해야 한다.

## Decision Log
1. 지금은 기능 추가보다 리스크 정리를 먼저 한다.
- 이유: 구현 폭이 넓어져서, 남은 공백을 분류하지 않으면 다음 개발 우선순위가 흔들리기 쉽다.

2. 출시 기준은 "자동 테스트 통과"만으로 보지 않는다.
- 이유: 현재 가장 큰 공백은 외부 연동과 수동 UAT라서, 실제 운영 환경 증적 없이는 출시 판단이 이르다.

3. 다음 개발은 blocker 해소와 운영성 보강을 나눠 진행한다.
- 이유: 출시 직전 필수 항목과 이후 개선 항목을 섞으면 일정과 기대치가 동시에 흐려진다.

## Delivery Phases

### Phase A. Release Blockers
- MS365 SSO 실환경 로그인/리다이렉트/세션 유지 검증
- Anthropic OCR 실환경 호출 검증과 실패 시 사용자 메시지 확인
- 템플릿 실파일 조합으로 국내/해외/document override 생성 결과 검증
- 수동 UAT 문서의 critical 케이스 실제 PASS/FAIL 기입

### Phase B. Release Readiness
- 운영자/고객사 관리자 계정 셋업 절차 문서화
- 백업/복구/DB 파일 보관 방식 정리
- 배포 후 smoke 수행 절차와 담당자 명확화
- 에러 로그/운영 관찰 포인트 최소 정의

### Phase C. Post-Release Hardening
- UI E2E 또는 브라우저 자동화 테스트 도입
- Object Storage 전환 검토
- 보관 정책/Retention 집계
- 이메일/푸시 알림 워크플로우

## Risks And Mitigations

### 출시 Blocker
- 리스크: MS365 SSO는 코드 경로가 있어도 실제 Entra 설정, redirect URI, 쿠키 도메인 이슈가 남아 있을 수 있다.
- 완화: 실도메인 또는 staging host에서 관리자/일반 사용자 로그인 시나리오를 최소 1회씩 실행한다.

- 리스크: OCR은 테스트에서 stub로 검증했기 때문에 실제 API key, 응답 지연, rate limit, 실패 메시지 품질은 미확인이다.
- 완화: 실영수증 샘플 묶음으로 성공/실패/저신뢰 케이스를 각각 1회 이상 검증한다.

- 리스크: 템플릿 생성은 API/파일 경로는 검증했지만, 실제 고객사 템플릿에서 셀 매핑이 깨질 가능성이 있다.
- 완화: 최소 1개 고객사 템플릿으로 domestic/international/document override 결과 파일을 직접 열어 확인한다.

- 리스크: UAT 문서가 아직 `CONDITIONAL NO-GO` 상태라, 출시 승인 근거가 부족하다.
- 완화: `docs/ux/release_smoke_checklist.md` 기준으로 수동 결과와 증적 파일을 채운다.

### 출시 전 권장
- 리스크: 현재 운영 저장소가 SQLite + 로컬 파일이라 백업/복구 기준이 없으면 운영 사고 시 복원 판단이 어렵다.
- 완화: DB/업로드/출력 파일 백업 주기와 보관 위치를 간단히라도 정한다.

- 리스크: 프런트엔드 상호작용은 자동 테스트가 없어서, JS 회귀는 브라우저에서만 드러날 수 있다.
- 완화: 위저드 핵심 경로를 Playwright 같은 E2E로 1~2개라도 도입하거나, 최소 수동 smoke 루틴을 고정한다.

### 후속 개선
- 리스크: 저장소/감사/알림/개인모드 등은 제품 확장 시 다시 구조 변경 비용이 커질 수 있다.
- 완화: 파일럿 범위에서는 현 구조를 유지하되, 후속 phase 요구사항을 별도 backlog로 관리한다.

## Recommended Next Build Order
1. 실환경 SSO/OCR/템플릿 UAT 증적 채우기
2. UAT 결과 문서 PASS/FAIL 확정
3. 백업/운영 절차 문서화
4. 그 다음에 신규 기능 개발 재개

## Acceptance Criteria
- 자동 테스트 `python -m pytest` 통과
- SSO 실환경 로그인 케이스 PASS
- OCR 실샘플 성공/실패 케이스 PASS
- 템플릿 실파일 생성 검증 PASS
- UAT critical 케이스에 실제 결과와 증적 링크 기입 완료
- 운영자가 배포 후 확인할 smoke 절차와 백업 위치를 설명할 수 있음
