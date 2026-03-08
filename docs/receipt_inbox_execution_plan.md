# Receipt Inbox SaaS 실행 계획 (Phase 1)

## Goal
- 기존 멀티테넌트 코어(호스트 분리/권한 분리/MS365+로컬 로그인)는 유지한다.
- 업로드 흐름을 `Upload -> OCR -> Inbox -> Review -> Report`로 확장한다.
- 기존 `/api/upload-receipts`, `/api/ocr`, `/api/generate`는 레거시 호환 경로로 유지한다.

## In Scope
- Receipt Inbox 데이터 모델(SQLite)
- 테넌트(Host) 스코프 강제 API
- Inbox UI(업로드/리뷰/리포트 생성) 최소 기능
- 리포트 생성 시 Inbox receipt 선택 기반 생성

## Out of Scope (Phase 1 제외)
- Object Storage(S3/R2/B2) 전환
- 이메일/푸시 스케줄 알림
- 고급 중복 탐지(이미지 해시 + 유사도)
- Personal Mode(organization_id 없는 독립 모드)

## Constraints
- 비운영자 계정은 현재 Host 외 데이터 접근 불가
- 기존 Admin/Platform 권한 경계 절대 유지
- 기존 리포트 생성 기능 동작 보존
- 기본 저장은 로컬 파일시스템 + SQLite

## Proposed Architecture
- Auth/Session: 기존 세션 유지(`user_id`, `user_email`, `is_admin`)
- Tenant Boundary: 모든 inbox row에 `host` 저장, 조회/수정 시 request host로 강제 필터
- Data Layer: `receipt_inbox.db`
  - receipts: OCR 결과/상태/리포트 연결
  - reports: 생성 이력(호스트/생성자/결과파일)
- File Layer:
  - 원본 이미지: `uploads/inbox/<host_key>/<stored_name>`
  - 결과 파일: 기존 `outputs/<session_id>/<file>` 재사용
- API Layer:
  - POST `/api/inbox/upload`
  - POST `/api/inbox/ocr/<receipt_id>`
  - GET `/api/inbox/receipts`
  - PATCH `/api/inbox/receipts/<receipt_id>`
  - POST `/api/inbox/reports/generate`
  - GET `/api/inbox/reports`
- UI Layer:
  - 신규 `/inbox` 페이지(Upload/Inbox/Reports 3구역)

## Decision Log
1. 단일 repo 확장 채택
- 이유: 인증/테넌트/운영자 경계를 중복 구현하지 않고 속도/리스크 최적화

2. Flask 모놀리식 유지 + 모듈 분리
- 이유: 배포 복잡도 증가 없이 receipt 도메인만 분리 가능

3. SQLite 별도 DB 파일 사용
- 이유: 기존 users.db 영향 최소화, 마이그레이션 단순화

4. 레거시 API 유지
- 이유: 기존 index 워크플로우 즉시 사용 가능(회귀 리스크 절감)

## Delivery Phases

### Phase 1 (이번 구현)
- Receipt Inbox DB/CRUD/OCR/리포트 생성 연결
- Host 스코프 필터 + 최소 UI
- 수동 smoke 검증

### Phase 2
- 중복 탐지 고도화(vendor+amount+date + 이미지 fingerprint)
- 카테고리/벤더 매핑 테이블 및 자동 분류 개선
- 리포트 템플릿별 파라미터 세분화

### Phase 3
- Object Storage 전환 + 보관 정책
- 이메일 알림 배치
- 운영/감사 로그

## Risks & Mitigations
- Risk: OCR 실패/불완전 데이터 증가
- Mitigation: `needs_review` 기본 상태 + 필수 필드 검증

- Risk: Host 경계 누락으로 데이터 노출
- Mitigation: 모든 select/update에 `host` 강제 조건, API 단위 재검증

- Risk: 레거시 화면과 신규 화면 간 기능 중복 혼선
- Mitigation: `/`는 legacy, `/inbox`는 신형으로 명확히 분리

## Acceptance Criteria (Phase 1)
- 같은 DB에 다중 host 데이터가 있어도 요청 host 기준으로만 조회된다.
- 업로드된 파일이 inbox row로 저장되고 OCR 결과가 row에 반영된다.
- `needs_review`/`processed`/`duplicate`/`assigned` 상태 필터 조회가 가능하다.
- 선택한 receipt들로 리포트 생성 후 report 이력이 저장된다.
- 생성된 receipt는 `report_status=assigned`, `report_id`가 설정된다.
- 기존 `/api/upload-receipts` 기반 레거시 흐름은 계속 동작한다.
