# Receipt Inbox SaaS 적용 리뷰 (보안/분리 기준)

기준 문서: `receipt_inbox_saa_s_프로젝트_핵심정리.md`

## 1) 핵심 이슈 대응 결과

- 스텝별 페이지 분리: 완료
  - `/inbox/upload`, `/inbox/review`, `/inbox/reports`, `/inbox/settings`로 분리
- 히스토리 노출 통제: 완료
  - report 권한(`report.view_own`/`report.view_all`) 기반 노출
  - host 스코프 + 작성자 스코프 강제
- 다운로드 보안 통제: 완료
  - report metadata(호스트/작성자/권한) 검증 후 다운로드 허용

## 2) 정의서 항목별 적용 상태

### 완료
- Receipt Inbox 중심 흐름(Upload -> OCR -> Inbox -> Report)
- Receipt Status(processed/needs_review/duplicate)
- Report Status(assigned/unassigned)
- Search/Filter(date/vendor/category/amount/status/report status)
- Category -> Account Mapping(기본값 + 고객사 override)
- Vendor Auto Classification(vendor mapping 기반)
- Duplicate Detection(merchant+amount+date)
- Review 후 수동 생성(자동 생성 없음)
- 멀티테넌트 host 분리 + 사용자별 권한 기반 데이터 제한

### 부분 적용
- Settings 영역 중 Report Templates/Branding은 기존 Admin 경로와 연동
- Step UI는 분리했으나 화면 디자인/상세 UX는 경량 구현

### 미적용(향후)
- Object Storage(S3/R2/B2) 전환
- Retention/Storage 정책 자동 집계
- 이메일/푸시 알림 워크플로우
- 개인 사용자 모드(Personal Mode)

## 3) 보안 체크 요약

- cross-tenant report history 노출: 차단됨
- 타 사용자 report download: 차단됨
- own/all 권한 분리: 적용됨
- superuser(운영자) 전체 접근: 유지됨

## 4) 이번 반영 파일

- `app.py`
- `user_db.py`
- `receipt_inbox_db.py`
- `excel_filler.py`
- `templates/inbox_upload.html`
- `templates/inbox_review.html`
- `templates/inbox_reports.html`
- `templates/inbox_settings.html`
