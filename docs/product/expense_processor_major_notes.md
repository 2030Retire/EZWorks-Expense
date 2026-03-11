# EZWorks Expense Major Notes

## 목적
- 이 파일은 최근 구현하면서 누적된 핵심 정책, UX 결정, 운영 포인트를 빠르게 다시 보기 위한 기록이다.
- 세부 구현은 코드와 기존 문서에 남기고, 여기에는 "왜 이렇게 했는지"와 "어디를 먼저 봐야 하는지"를 남긴다.

## Wizard 구조
- Step 1은 업로드/OCR 중심으로 정리하고, 실제 리포트 성격은 영수증 통화와 OCR 결과를 기준으로 추정한다.
- Step 2 Review는 단순 검토 화면이 아니라, OCR 결과 보정 + FX 준비 + Finalize 사전점검 역할을 맡는다.
- Step 3 Finalize는 문서정책에 따라 필요한 메타데이터를 채우는 단계이며, 현재는 문서별 required field 정책을 따른다.

## FX 정책
- 테넌트별 FX 정책은 `date_based`, `company_average`, `user_select`를 지원한다.
- `date_based`일 때는 Review에서 날짜별 환율이 준비되지 않으면 다음 단계로 진행하지 못하게 막는다.
- `company_average`일 때는 예상 환율로 동작하며, 실제 회계 반영값과 차이가 있을 수 있다는 안내를 유지한다.

## Document Type 정책
- Document Type은 단순 표시값이 아니라 아래 항목들과 연결된다.
  - Finalize 추천 제목
  - Trip Purpose/Notes placeholder
  - Finalize guidance 문구
  - Required field 정책
  - 템플릿 override 선택
- Admin에서 문서별 preset과 required fields를 직접 관리한다.

## Template 관리 원칙
- Base template는 모든 문서의 기본 fallback이다.
- Document-type override template는 해당 문서 종류와 mode에만 적용된다.
- Template Preview는 resolved template와 base template를 비교해서 차이를 보여준다.
- Admin Templates 화면에는 현재 준비 상태를 빠르게 읽을 수 있도록 overview 카드와 매핑 표를 같이 둔다.

## Profile / MS365
- Microsoft 365 로그인 시 사용자 프로필에서 Employee Name, Department, Employee ID, Manager 정보를 최대한 자동으로 채운다.
- Finalize 상단의 Profile Context는 값의 출처와 누락 이유를 설명하는 보조 패널이다.
- tenant field visibility가 꺼진 항목은 Profile Context와 Finalize readiness에서도 제외한다.

## Finalize UX 원칙
- `Required summary`는 현재 생성이 막히는 이유를 보여주는 차단 경고다.
- `Finalize readiness`는 문서정책 기준 입력 진행 상태를 보여주는 체크리스트다.
- Finalize 상단 패널은 길게 늘어지기보다, readiness 요약과 receipt/period/review sync 상태를 압축해서 보여주는 방향을 유지한다.
- Finalize의 설명 문구와 카드/섹션 간격은 최대한 압축해, 첫 화면에서 핵심 입력 필드가 바로 보이도록 유지한다.
- Finalize의 저장/생성 액션은 스크롤 중에도 찾기 쉽도록 하단 액션 바를 유지하는 방향이 좋다.
- Finalize 내부 필드 폭은 같은 섹션 안에서 `핵심 입력은 넓게, 보조 입력은 좁게` 배치해 시선 흐름을 안정적으로 유지한다.
- Finalize의 `Basic Info`와 `Report Details`는 이름/제목/메모처럼 길게 읽는 필드를 더 넓히고, 부가 필드는 줄여서 한 줄당 의미 밀도를 높이는 방향을 유지한다.
- Finalize 성공 패널은 하단 액션 바와 시각적으로 이어지게 해, 생성 직후 다음 행동이 자연스럽게 보이도록 유지한다.
- Review의 `Still missing`과 `Finalize Inputs`는 Finalize 해당 필드로 바로 이동할 수 있어야 한다.
- Finalize에서 보고서를 만든 뒤 다시 값을 수정하기 시작하면, 이전 성공 상태 배너/강조는 즉시 내려서 `이미 생성된 상태`와 `다시 편집 중인 상태`가 섞여 보이지 않게 유지한다.
- Finalize 상단은 `Document Settings`와 `Basic Info`를 가능한 한 같은 화면 높이 안에서 소화하도록 압축 배치하고, `Report Details`를 아래 독립 구역으로 두는 방향을 유지한다.
- Finalize 상단 overview strip에도 `Required / Review sync` 상태를 짧은 pill로 같이 보여줘, Review에서 본 상태 언어가 Step 3 첫 화면에서도 끊기지 않게 유지한다.

## Review UX 원칙
- Review 상단 KPI는 단순 통계가 아니라 사용자의 다음 행동을 유도해야 한다.
- Review 상단 KPI는 `읽기 전용 요약`과 `즉시 행동 카드`를 시각적으로 구분해, 클릭 대상을 헷갈리지 않게 유지한다.
- `Finalize Inputs`는 Step 3 준비 상태를 뜻하고, 클릭 시 Finalize로 바로 이동한다.
- Review의 `Finalize Inputs`와 하단 상태 pill은 `remaining / ready` 기준 문구를 함께 써서, Step 3 준비 상태가 다른 말로 보이지 않게 유지한다.
- `FX Pending`도 단순 카운트가 아니라 FX 편집 영역으로 바로 이동하는 액션 카드로 유지한다.
- `Required Fixes`, `Unsaved Edits`도 KPI 카드에서 바로 attention filter를 켜는 액션 카드로 유지한다.
- `Focus action-needed rows`는 required/fx/retry/dirty 기준으로 예외행만 빠르게 보는 운영 도구다.
- Review 상단 편집 도구는 `Bulk Currency`와 `View Options`처럼 목적별 그룹으로 묶어, 화면이 넓어져도 흩어져 보이지 않게 유지한다.
- Review FX 영역도 별도 작업 공간으로 묶어, 정책 선택/기본 환율/날짜별 환율 입력 흐름이 한눈에 보이도록 유지한다.
- Review의 FX Workspace 앞뒤 안내 문구는 `행 수정 -> FX 확인 -> Finalize 이동` 순서를 짧게 설명해, 테이블과 환율 편집이 끊겨 보이지 않게 유지한다.
- Review 하단의 다음 단계 액션도 화면 끝에서 다시 찾지 않도록, 테이블 편집 흐름과 이어지는 하단 액션 바 형태를 유지한다.
- Review 하단 액션 바에는 `Required / FX / Save / Finalize`처럼 다음 단계 진입에 직접 영향을 주는 상태만 pill 형태로 압축 노출해, 사용자가 막히는 이유를 즉시 읽게 유지한다.

## Admin 운영 원칙
- Accounting의 Document Type 카드는 단순 설정폼이 아니라, 템플릿 override 유무와 Finalize 정책 준비상태를 함께 보여주는 운영 카드로 유지한다.
- Templates 탭의 상세 매핑표를 보기 전에, Accounting 카드 단계에서도 각 문서 타입의 준비 정도를 빠르게 판단할 수 있어야 한다.
- Accounting는 `quick readiness`, Templates는 `file-level detail and preview` 역할로 구분해, 같은 정보를 두 탭에서 과하게 반복하지 않도록 유지한다.
- Admin 문구는 `정책 설정 -> 파일 업로드/비교` 순서를 짧게 안내해, 운영자가 탭 역할을 바로 이해하도록 유지한다.
- Templates 탭 overview는 운영 순서를 짧은 체크포인트 형태로 보여줘, 관리자가 어떤 순서로 점검해야 하는지 바로 이해할 수 있게 유지한다.
- Templates preview는 상세 비교 전에도 `무엇을 보고 있는지`와 `빠른 확인 포인트`를 먼저 보여줘, 긴 표보다 맥락을 먼저 읽게 유지한다.
- Templates preview에는 현재 `mode / base or document override / scope`를 chip 형태로 먼저 보여줘, 표를 읽기 전에 지금 보고 있는 템플릿의 위치를 바로 이해하게 유지한다.
- Templates preview 비교 화면은 표 자체보다 먼저 `sheet 수 / preview 범위 / diff cell 규모`를 요약해, 운영자가 롤아웃 전 위험도를 빠르게 판단하게 유지한다.
- Templates preview compare 모드는 `resolved -> base` 읽기 순서를 짧게 안내해, 긴 비교표를 보기 전에 해석 규칙부터 이해하게 유지한다.

## 필드 이동 UX 원칙
- Review나 Finalize checklist에서 특정 입력칸으로 이동시키는 경우, 도착한 필드를 잠깐 강조해 사용자가 현재 포커스 위치를 즉시 인지하게 유지한다.
- Finalize 경고/체크리스트에는 `다음으로 채워야 할 첫 필드`로 바로 이동하는 액션을 유지해, 사용자가 목록을 읽고 다시 찾는 비용을 줄인다.
- Template Preview compare 화면은 `resolved(주요 화면)`과 `base(reference)` 역할을 헤더에서 바로 구분해, 좌우 비교 순서를 한눈에 이해하게 유지한다.
- Finalize 하단 액션 바에도 `Required / Review sync / Receipts / Period` 상태를 압축 노출해, Review와의 연결 상태를 아래에서도 즉시 읽게 유지한다.
- Finalize 하단 액션 바의 본문 문구는 상단 카드의 상세 설명을 반복하지 말고, `지금 막히는 이유 / 바로 가능한 행동`만 짧게 안내하는 방향을 유지한다.
- Template Preview diff 요약은 긴 문장보다 `diff cell 수 / 영향 시트 수 / 상위 변경 시트` 중심으로 압축해 읽게 유지한다.
- Template Preview compare의 diff 요약은 긴 설명 문장보다 chip과 짧은 상위 변경 시트 목록 중심으로 압축해, override 영향 범위를 빠르게 읽게 유지한다.
- Template Preview compare의 상위 변경 시트는 `Top changes` 레이블과 chip 조합으로 보여줘, 숫자 목록의 의미를 다시 해석하지 않게 유지한다.
- Template Preview compare의 요약 chip에는 `Left resolved / Right base` 같은 방향성 힌트도 포함해, 비교 축을 바로 읽게 유지한다.

## 주의할 점
- wizard 설정은 localStorage에 저장되므로, 서로 다른 브라우저/기기 간에는 자동 동기화되지 않는다.
- 테넌트가 이미 커스텀 템플릿을 올려둔 경우 기본 템플릿 변경만으로는 바로 결과가 바뀌지 않을 수 있다.
- Finalize required field 정책과 field visibility 정책이 서로 충돌하지 않도록 항상 함께 확인해야 한다.

## 다음에 우선 보기 좋은 파일
- `templates/report_wizard_upload.html`
- `templates/report_wizard_review.html`
- `templates/report_wizard_generate.html`
- `templates/admin.html`
- `app.py`
