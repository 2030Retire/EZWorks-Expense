# Release Smoke Checklist

## 목적
- 자동 테스트가 커버하는 경계와 배포 직전 수동 확인 포인트를 같은 언어로 맞춰, GO/NO-GO 판단 시간을 줄인다.
- 이 문서는 `python -m pytest`가 통과한 뒤 실제 브라우저/운영 설정에서 마지막으로 확인할 항목만 남긴다.

## 1. Auth / Tenant Boundary
- 익명 상태에서 `/api/inbox/permissions` 호출 시 로그인 차단이 보이는지 확인한다.
- 허용 도메인 계정은 로컬 로그인되고, 비허용 도메인은 차단되는지 확인한다.
- 같은 사용자라도 다른 host 데이터가 조회되지 않는지 확인한다.

## 2. Report Flow
- 본인 권한 사용자는 본인 리포트만 조회되는지 확인한다.
- 회계/전체 권한 사용자는 팀 리포트까지 조회되는지 확인한다.
- 영수증 1건 이상으로 리포트 생성 후 영수증이 `assigned` 상태로 바뀌는지 확인한다.
- 생성된 리포트의 line-item CSV/XLSX 다운로드가 열리는지 확인한다.

## 3. OCR / Duplicate
- OCR 성공 후 low confidence 또는 unreadable 케이스가 Review에서 바로 보이는지 확인한다.
- duplicate 표기된 영수증을 ignore 처리해도 저신뢰 경고가 유지되는지 확인한다.
- force 없는 OCR 재실행 차단 문구가 정책과 맞는지 확인한다.

## 4. Admin / Policy
- tenant admin이 자기 host 설정만 열 수 있고 다른 host는 차단되는지 확인한다.
- operator 계정은 cross-tenant 설정을 열 수 있는지 확인한다.
- user permissions 저장 후 다시 열었을 때 explicit/effective 권한이 예상대로 보이는지 확인한다.
- shared preset lock 상태에서 일반 사용자가 수정/삭제 못 하는지 확인한다.

## 5. Template / Export
- Template Info에서 shared default와 tenant override scope가 정확히 보이는지 확인한다.
- template upload 후 document override가 바로 preview/info에 반영되는지 확인한다.
- generate templates 실행 후 domestic/international 템플릿이 생성되는지 확인한다.
- audit log JSON/CSV export가 운영자가 읽을 수 있는 형태인지 확인한다.

## 릴리즈 게이트
- 자동 테스트 `python -m pytest` 통과
- 위 5개 섹션 중 blocker 없음
- UAT 결과 문서에 최종 PASS/FAIL 근거 기록
