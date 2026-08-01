# qa-lab-miyonchat — 남은 작업 (remaining-work)

할 일의 정본입니다(규칙: `rules/remaining-work.md`). 완료 항목은 삭제되며, 완료 기록은
change-log가 담당합니다. 갱신일: 2026-08-01 (골격 트리 v1.0 확정 직후 기준).

## 다음 작업 큐

1. **SUT 청사진(sut-blueprint) 개정** — 트리 v1.0과 동기화
   - 화면 맵: 화면 5개 → 상단 바 + 하단 내비 5탭(+스텁 탭) 구조로, 배치표를 트리 기준 재검증
   - 테스트 인터페이스 4갈래로 확장: 데이터 주입 신설(데이터 시트 4테이블 UI + `__VN__.setData()`), 상태 스위처, 갱신 버튼
   - 완료 시 문서 상태 "초안" → 확정
2. **design 명세 작성** — 입력: 트리 미확인 목록 13건 + 채택표 §12 수치 후보
   - `design/`: system-spec(관계 임계·호감도 가중치·엔딩 판정식·재화 요율·미션 보상·세이브 기획 규칙·집계 구간·섹션 선정식) · rubric
   - `sut-design/`: save-schema · mock-llm-spec · fault-injection
   - 병행: `rationale/…-addition-rationale.md` 적립 — §1 ADD 11건(목록은 tree-change-log v1.0), §2 수치 확정 근거
3. **TC 설계·산출** (playbook STEP 6)
   - 선행: `build_tc_template_xlsx.py`를 확정 서식과 3자 동기화, `design-template/tc-input-master.json` 생성, 대상 플랫폼 재확인(Web 단독 예상 → 시트 열 조정)
   - 산출: `…-tc-input-v1.0.json` → xlsx(기준 골격 v1.0 기록)
4. **SUT 구현** (`sut/`) — 청사진 준수, data-testid 전체 목록을 청사진에 확정 등재, 스모크의 STUB를 실제 SUT로 교체(test_smoke.py [주의] 참조)
5. **자동화** — conftest(reset)·thresholds·영역별 테스트 파일 → 결정적·금칙 격리부터 → 결함 주입 매트릭스(대각선만 FAIL) → 리포트(+"SUT 한계와 검증 범위")
6. **CI·묶기** — 워크플로(경로 필터, deploy-pages 금지), 추적 매트릭스, 프로젝트 허브·용어집 생성, README 실행 GIF, 저작권 게이트 → push

## 사용자 결정 대기

- **Issue 시트 포맷** — 사용자가 직접 제공 예정. tc-sheet-master.xlsx에 추가 후 명세서 시트 갱신 (3번 TC 산출 전까지 필요)
- **자동화 리포트 템플릿(Case C)** — 기본 리포트로 시작 권고 유지, 여유 시 재논의 (5번 리포트 단계 전까지)
- **`build_tc_xlsx.py` 존치** — 분석 문서를 HTML로 내기로 해 역할 중복, 보류 중
- **미push 커밋 push 시점** — f5bd6fe 이후 누적분, 저작권 게이트 걸릴 항목 없음

## 백로그

- CLAUDE.md에 `automation/` 하위 구조(`tests`·`report`·`result/history`)와 "정본과 파일 지위" 표 반영 (현재 정본은 change-log §확정된 결정)
- `scripts/gen_test_skeleton.py` — 시간 부족 시 버리는 순서 2번, 수동 작성으로 대체 가능
- 플레이툰 잔여 실측 소소 3건 — 내 작품 탭·홈 칩별 목록 구성·빈 검색 결과 UX (`analysis/…-plaitoon-inventory.md` B-3)
- 워크스페이스 잔재 파일 정리 — SKILL.md·feature-tree-ai-chat.md 제거(사용자 요청 대기)
