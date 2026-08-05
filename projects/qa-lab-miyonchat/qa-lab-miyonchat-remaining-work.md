# qa-lab-miyonchat — 남은 작업 (remaining-work)

할 일의 정본입니다(규칙: `rules/remaining-work.md`). 완료 항목은 삭제되며, 완료 기록은
change-log가 담당합니다. 갱신일: 2026-08-05 (`gen_project_hub_html.py` 폐지 + 허브 표기 정리 — 소개의 도구 목록에서 빠졌고, 규칙 문서에 남아 있던 허브 설명과 **404였던 링크 둘**을 「프로젝트 개요」로 맞췄습니다. 산출물 층의 자리 표기도 실제(`intro/`)에 맞췄습니다. 소개↔리포트 표 중복은 **그대로 두기로 확정**했습니다. **남은 판단은 하나뿐입니다**).

## 지금 상태 (이어받기용 요약)

| 항목 | 값 |
|---|---|
| SUT 빌드 | `PC웹_Ver1.0_Dev_RC25` (`sut/js/data.js`의 `SUT_BUILD`) |
| 캐시 무효화 번호 | `sut/index.html`의 `?v=63` |
| 골격 | **v1.14** — 내부 식별자 제거(표기만, 기능 단위 86개·128노드) |
| git | **push 완료 · 미push 없음.** 좌표는 `git log --oneline -1`·`git status -sb`로 확인합니다 |
| TC·자동화 | TC **153건**(루브릭 1건은 사람 전용) · 자동화 **157건 통과** · 커버리지 3축 통과 · **결함 주입 매트릭스 통과**(담당 14건 전부 잡음·담당 밖 0) |
| 리포트 | `intro/miyonchat-report.html` — 단일 파일·외부 요청 0건. `gen_qa_report_html.py`로 재생성만 합니다(`-o` 경로가 바뀌었습니다) |
| CI | `.github/workflows/qa-lab-miyonchat.yml` — 커버리지 대조 → 매트릭스 → 리포트 재생성 → **커밋본이 최신인지** |
| 산출물 | 전부 `intro/`에 있습니다(2026-08-05 이동) — [자동화 QA 리포트](../../intro/miyonchat-report.html) · [추적 매트릭스](../../intro/miyonchat-traceability.html) · [기능 골격](../../intro/miyonchat-feature-tree.html) · [용어집](../../intro/miyonchat-dictionary.html). **프로젝트 허브는 폐지했습니다** |
| 설명 다이어그램 | `structure.svg`(전체 구조) + `diagrams/` 3종(커버리지 3축 · 결함 주입 · 자동화 격리) |
| 문서 구조 | 읽는 문서는 **전부 `intro/`** 입니다. 파일명은 워크스페이스 `main-` · 프로젝트 `miyonchat-` 접두(규칙: `rules/site-structure.md` §소개 층의 파일명). 사이드바 정본은 `scripts/shell.py`의 `INTRO`·`WORKSPACE_INTRO`·`PROJECT_INTRO` |
| 소개 층 문구 | **동결입니다** — 고쳐 달라는 지시가 있을 때만 손댑니다. 문구는 `gen_intro_html.py` 안에 있으므로 그 문자열을 고치는 것이 곧 문구 변경입니다(CLAUDE.md §소개 층 문구는 동결) |
| 다음 착수 지점 | **작업 큐가 비었습니다.** 남은 판단 하나(§사용자 결정 대기 — 그림 안 텍스트)는 사용자 요청 대기이므로, 다음은 §백로그에서 고릅니다 |

**매트릭스를 다시 돌리는 법** (SUT나 자동화를 고쳤을 때 반드시 함께 돌립니다)

```
python project-process/scripts/run_fault_matrix.py \
  --tests projects/qa-lab-miyonchat/automation/tests \
  --map projects/qa-lab-miyonchat/automation/qa-lab-miyonchat-fault-matrix.json \
  --out projects/qa-lab-miyonchat/automation/result/matrix
```

담당은 관측이 아니라 **주입 지점**으로 정합니다 — 기대표(`…-fault-matrix.json`)의 `why`가
그 근거이고, 판정은 TC 단위 양방향입니다(담당인데 안 깨짐 / 담당 밖인데 깨짐 둘 다 실패).

**세션을 새로 열었다면 이 순서로 읽습니다.** ① 이 파일 → ② `qa-lab-miyonchat-change-log.md`
(§확정된 결정이 규칙 정본) → ③ 착수할 영역의 `spec/design/…-system-spec.md` 해당 절 →
④ `spec/sut-design/…-sut-blueprint.md` §3-1(testid)·§4-2(디버그 콘솔). `spec/archive/`는 기본 참조하지
않습니다.

**TC를 쓰기 전에는 이 셋을 더 읽습니다** (2026-08-03 규칙 개정 — 예전 방식과 다릅니다):
`rules/depth-and-tn.md` §도달 경로 뎁스 · `rules/tc-sheet-format.md` §셀 병합 규칙·§실행
주체·§검증유형과 반복 · 이 파일의 §착수 전 정할 것.

## 다음 작업 큐

1. **SUT 구현** (`sut/`) — **완료(RC21)**
   - **완료**: 전역 셸(상단 바·하단 내비·푸터) · 로그인 화면 · 라우팅 가드(미로그인 열람: 홈·캐릭터 페이지·커뮤니티 /
     로그인 필요: 대화방·채팅·MY·내 작품) · 로그인 모달(막힌 동작 이어받기) · 간편 프로필 패널 · 디버그 콘솔 ·
     가상 시계 · `__VN__` API · 홈 화면 · 상단 바 검색·알림(**탐색/발견 전부**) · 캐릭터 페이지(작품·캐릭터 2층) · 대화 프로필 화면(복수·한도) · 대화방 한도 · 디버그 콘솔 초안 구조(저장·
     재확인·닫기)와 생성 실패 스위치 · **재화 영역 전부**(차감·연타·잔액 0 차단·생성 실패
     미차감·재화/충전 패널 mock 충전·간편 프로필 패널 미션 수령·내역 필터) · **서사 전부**(고정 선택지 가중치·호감도·
     관계 단계·검사 시점/종점 엔딩 판정·현재 상태 패널, mock 전용 100턴·공통 30턴) ·
     **되돌림 전부**(편집·삭제·재생성 재계산, 과거 턴 분기, 확인 모달) · **세이브/로드 전부**
     (세이브/로드 패널 시점 슬롯 4·저장/덮어쓰기·로드 갈래·방 목록) · **메모리 전부**(기억 목록·핀·삭제·
     재등장 차단·장면 간략화·단기 맥락 창·상태 값 고정·대화에서 기억 등록) · **세이프티 전부**(입력·출력
     필터·우회 방어·누출 차단·설명란 주입) · **채팅 탭** · **MY 탭** · **커뮤니티·내 작품 탭 스텁** · **결함 주입 4종**
   - **다음 단위 — 대화방 확장**: ~~① 재화~~(RC10) → ~~② 서사~~(RC13) → ~~③ 되돌림~~(RC14) →
     ~~④ 세이브/로드~~(RC15) → ~~⑤ 메모리~~(RC16) → ~~⑥ 세이프티~~(RC18) — **대화방 확장 완료**
   - **SUT 구현 완료(RC20).** 마무리 둘(testid 확정 등재 · 스모크를 실제 SUT로)도 끝났습니다
   - 지켜야 할 조건: ① 코드가 명세와 어긋나면 **명세를 먼저 고치고** 스펙 변경으로 기록
     ② 기능 트리 노드 구현 외 작업 금지(시간 도둑 1번) ③ data-testid 명명 규칙은 코드 첫 줄
     전에 확정
   - **RC21 완료** — system-spec §8-8 두 값을 코드가 따라갔습니다(콘솔 표의 출시일·최종
     업데이트일·버전 칸 · 버전 입력 정규화 · 추천 선정식 교체 · 후보 0건 안내 · 임계·상한 조절).
     신설 testid는 청사진 §3-1에 등재했습니다
   - 작업 요령: 정적 서버로 확인 · **CSS·JS 수정 시 `index.html`의 `?v=` 숫자 올리기** ·
     슬라이스 완료 시 `data.js`의 `SUT_BUILD`를 다음 RC로 · 슬라이스 끝에 트리·트리 HTML·
     tree-change-log·system-spec·청사진·change-log·이 파일을 함께 갱신
2. **TC 본문 작성** (playbook STEP 6) — **완료(2026-08-04)**
   - 선행 완료: 스크립트 3자 동기화 · `tc-input-master.json` · 이슈 관리 시트 편입 ·
     **플랫폼 Web 단독** · `test-case/…-tc-input-v1.0.json`(목록 값·`vt_note`·진입축
     `d1_order` 반영, `tcs`만 비어 있음) · 케이스 전개 축 판정(청사진 §4-1) ·
     **시트 서식·뎁스 규칙 확정**(2026-08-03)
   - **완료(2026-08-04)** — ~~① 웹 진입~~ → ~~② 나머지 9영역~~ → ~~③ xlsx 생성~~ →
     ~~④ Excel 오픈 검증~~. 10영역 147건 285행이며 커버리지 3축이 전부 통과합니다
   - 첫 영역에서 확정된 것: **TN은 연쇄에만** 쓰고 나열은 케이스로 나눕니다 · 기대결과는
     **스텝별 배열**로 적습니다 · 영역코드는 `area_codes`가 정본입니다 · **상태(14번째 필드)를
     명시**합니다(생략 시 성인 인증) · covers의 testid는 청사진 §3-1 등재 표에서 골라 적습니다
     (지어내면 오타 검사에 걸립니다)
   - **커버리지 대조를 영역 끝날 때마다 돌립니다** — `check_tc_coverage.py`가 기능 단위·testid·
     기능 단위×상태 세 축을 요구합니다. 이미 잡혀 있는 것: 「로그인 필요 화면 직접 접근 차단 ×
     세션 만료」(만료 상태 URL 직접 진입 케이스가 아직 없음 — 웹 진입 영역에 추가 필요)
   - 규모는 영역 10개 × (정상 흐름 + 경계 + 금칙 + 격리)로 **90~130건** 안팎 예상
   - 한 줄 쓸 때 지켜야 할 것
     - 기대값은 **트리와 `spec/design/`에서만** 가져옵니다 (analysis·reference·rationale 금지)
     - Test-Step은 **구현으로 확정된 화면 용어**로 씁니다 (약어 아님 — 「대화방」·「캐릭터 페이지」)
     - 뎁스 경로는 **도달 경로**입니다. 영역은 TC ID 접두가 담습니다
     - 실행 주체는 **「공통」이 기본값**이고 나머지 둘은 사유가 있을 때만
     - Note에는 **사람이 읽을 안내만** — 케이스 메타는 열이 가집니다
     - 반복 횟수는 시트에 적지 않습니다
   - 생성·검증
     ```
     python project-process/scripts/build_tc_template_xlsx.py \
       projects/qa-lab-miyonchat/test-case/qa-lab-miyonchat-tc-input-v1.0.json \
       -o projects/qa-lab-miyonchat/test-case/qa-lab-miyonchat-tc-v1.0.xlsx \
       --issues projects/qa-lab-miyonchat/test-case/qa-lab-miyonchat-issues.json
     ```
     생성 뒤 Excel에서 '복구' 프롬프트 없이 열리는지 확인합니다(`verify_xlsx_opens.ps1`)
3. **자동화 + 결함 주입 매트릭스** — **완료.** 157건 통과(스모크 5 + TC 152), 매트릭스 대각선만 FAIL
   - 케이스명이 TC ID입니다(`test_tc_{영역코드}_{번호}_{요약}`) — 리포트만 보고 시트를 찾습니다
   - 매트릭스 실행법과 담당의 기준은 위 §지금 상태에 있습니다
   - 남은 개선: 상태 열을 pytest 마커로 옮기면 `-m 미성년` 식의 부분 실행이 됩니다(미착수)

4. **리포트** — **완료(2026-08-04)**
   - `automation/report/…-report.html` · 생성기 `project-process/scripts/gen_qa_report_html.py`
   - 재생성
     ```
     python project-process/scripts/gen_qa_report_html.py \n       --project-dir projects/qa-lab-miyonchat --slug qa-lab-miyonchat \n       --css design-guide/design-guide-master.css \n       -o intro/miyonchat-report.html
     ```
   - 파생물이라 손으로 고치지 않습니다. 수치는 전부 정본에서 읽으므로 정본을 고치고 다시 만듭니다
   - 남은 개선: 계열이 늘어 표로 읽기 어려워지면 그때 Chart.js를 인라인합니다(지금은 표+CSS 막대)

5. **CI** — **완료(2026-08-04)** · `.github/workflows/qa-lab-miyonchat.yml`
   - 경로 필터로 SUT·자동화·TC 입력·명세가 바뀔 때만 돕니다
   - 순서: 커버리지 3축 → 결함 주입 매트릭스 → 리포트 재생성 → **커밋본이 최신인지**
   - `deploy-pages`를 쓰지 않습니다(§7). 리포트는 커밋본이 Pages로 서빙되고 CI는 검증만 합니다
   - **자동 커밋하지 않습니다.** 산출물을 고쳤으면 재생성해 함께 커밋해야 4번이 통과합니다

6. **묶기** — **진행 중**
   - **완료**: 추적 매트릭스(기능 단위↔TC↔자동화↔이슈) · 프로젝트 허브 · 중앙 허브 갱신 · README
   - **완료(2026-08-04)**: 구조도 분리 — `structure.svg` v1.5(automation 안쪽 + CI) +
     `diagrams/` 3종. ①은 `inline_structure_svg.py`로 주입, ②③④는 허브 생성기가 읽어 넣음
   - **완료(2026-08-04)**: 실행 GIF — `docs/sut-demo.gif`, 생성기 `gen_sut_demo_gif.py`
     (Pillow 필요. 문서 자산 도구라 `automation/requirements.txt`에는 넣지 않습니다)
   - **완료(2026-08-04)**: 프로젝트 용어집 — 정본 `…-dictionary.md` + 생성기
     `gen_dictionary_html.py`. 고유명사만 담고 정의는 정본 자리를 가리킵니다.
     `shell.py`에 사이드바 항목을 넣어 셸이 붙은 문서와 소개 층을 함께 재생성했습니다
   - **묶기 완료** — 다음 착수 지점은 §백로그에서 고릅니다
   - 재생성
     ```
     python project-process/scripts/gen_traceability_html.py \n       --project-dir projects/qa-lab-miyonchat --slug qa-lab-miyonchat \n       --css design-guide/design-guide-master.css \n       -o intro/miyonchat-traceability.html
     ```

7. **산출물 디자인 개편 v2.0** — **완료(2026-08-04)** · 재생성까지 끝났습니다
   - 사용자 결정: Gentelella v4의 **디자인 언어만 차용**(코드 미복제 — MIT 고지 불필요) ·
     **라이트 기본 + 다크 토글** · 토글은 **모든 문서**에 · 셸(사이드바·상단 바)은
     **허브·QA 리포트·추적 매트릭스** 셋에만 · 표 도구는 **경량 자작 JS**
   - **완료(렌더 확인함)**: `design-guide-master.css` **v2.0**(토큰 두 벌·셸·표 도구·
     스탯 막대·`--on-accent`·`.sd` 다크 전용 덮기) · `design-guide-master.js` **v2.0 신설**
     (테마 토글·서랍·목차 표시·표 검색/필터/정렬) · 시각 규칙서 v2.0 ·
     `scripts/shell.py` 신설(사이드바 항목의 정본) · 생성기 4종 개편(허브·리포트·
     추적 매트릭스·기능 트리) · `rules/html-report-guide.md` 반영
   - **완료(2026-08-04)**: 리포트·추적 매트릭스·프로젝트 허브·기능 골격 HTML 재생성 + **TC 시트
     재빌드**(생성기 문구·이슈 요약이 시트에 안 실려 있었습니다). 라이트·다크 두 벌 렌더 확인,
     콘솔 오류 0·외부 요청 0. junit이 남아 있고 SUT·테스트가 그보다 오래돼 매트릭스는 다시
     돌리지 않았고, 수치는 `157/157`로 살아 있습니다. **재생성 순서와 의존 관계의 정본은
     `rules/site-structure.md` §파생물과 재생성 순서**입니다
   - CI의 「커밋본이 최신인지」 검사는 아직 **리포트와 매트릭스 표 둘만** 봅니다. 파생물이 늘었으므로
     검사 대상 확대(또는 재생성 스크립트 신설) 여지가 있으나, 2026-08-04 사용자 판단으로
     **문서에 순서만 적어 두는 쪽**을 택했습니다
   - **옛 남음 ②는 사라졌습니다** — 중앙 `index.html`의 CSS 스냅샷이 v1.1에 멈춰 있다는
     항목이었는데, 8번에서 루트를 생성물 랜딩으로 바꾸면서 v2.0과 토글이 함께 들어갔습니다.
     손으로 고칠 스냅샷 자체가 없어져 (a)/(b) 갈래가 성립하지 않습니다
   - 이 프로젝트의 `structure.svg`·`diagrams/*.svg`는 원래 밝은 배경 기준이라 손댈 것이 없습니다

8. **소개 층(`intro/`) 신설** — **6/6 완료 · 커밋됨** (2026-08-04)
   - 사용자 결정: 루트 `index.html`을 **포트폴리오 랜딩으로 교체** · 소개 페이지는 **루트 `intro/`**
     한 곳 · **단일 생성기**(`gen_intro_html.py --page …`) · 랜딩부터 한 장씩
   - 랜딩의 서술 기준(사용자 확정): 만든 사람 정보는 넣지 않음 · 검출 결함은 **히어로에서 빼고
     결과 절에서** 증상·원인·조치로 · 내부 용어는 문장에서 풀고 「이 문서의 말」 절에 한 줄 사전 ·
     「자기가 만든 걸 자기가 찾았다」에 대한 변론 문단은 넣지 않음
   - **완료**: ①랜딩(`index.html`) · ②중앙 규칙 구조(`intro/main-central-rules.html`) ·
     ③프로젝트 규칙 구조(`intro/main-project-rules.html` — 절차 단계는 playbook의 STEP 제목을, 규칙 설명은 각 md의
     첫 문단을, 도구 설명은 각 스크립트의 모듈 docstring 첫 줄을 읽습니다) ·
     ④제작 과정(`intro/miyonchat-overview.html` — REF/ADD·제외 노드는 트리 태그에서 세고,
     ADD 근거 16건과 수치 근거 25건은 `rationale/…-addition-rationale.md`의 표를 그대로 읽습니다)
     ⑤TC 설계 규칙(`intro/miyonchat-tc-design.html` — 영역별 규모·판정 방식 건수는 TC 원본에서,
     제외 7건은 waiver 파일에서, 커버리지 그림은 `diagrams/coverage-axes.svg`에서 읽고,
     실제 케이스 한 건을 시트 모양으로 펼쳐 보입니다)
     ⑥자동화 설계와 결과(`intro/miyonchat-automation.html` — 접점 4갈래는 `rules/sut-automation.md` §1 표,
     담당 근거 16건은 결함 기대표, 실행 결과는 커밋된 `fault-matrix.md`, CI 단계는 워크플로
     파일에서 읽습니다)
   - **소개 층 6페이지 완료.** 사이드바에 회색으로 자리만 잡혀 있고,
     파일이 생기면 생성기가 자동으로 링크로 바꿉니다
   - 수치는 junit을 읽지 않습니다 — 자동화 건수는 `automation/tests/*.py`의 테스트 함수를 세고,
     매트릭스 결과는 커밋된 `result/matrix/fault-matrix.md`에서 읽습니다(환경 없이도 살아 있음)
   - **딸린 정리 완료(2026-08-04)**: `inline_structure_svg.py` 삭제(사본이 사라져 할 일이 없어짐) ·
     규칙 이관 — CLAUDE.md의 §산출물 출력 방식·§트랙별 허브 갱신을 **포인터 두 절로 줄이고**
     정의는 `rules/html-report-guide.md`(출력 방식·Pages 링크)와 **`rules/site-structure.md` 신설**
     (세 층·목록 자동화·셸·용어집 배치)로 옮김. SUT 예외는 `rules/sut-automation.md` §1
   - 재생성
     ```
     python project-process/scripts/gen_intro_html.py --page landing \n       --repo-root . --project-dir projects/qa-lab-miyonchat --slug qa-lab-miyonchat \n       --css design-guide/design-guide-master.css -o index.html
     python project-process/scripts/gen_intro_html.py --page central \n       --repo-root . --project-dir projects/qa-lab-miyonchat --slug qa-lab-miyonchat \n       --css design-guide/design-guide-master.css -o intro/main-central-rules.html
     ```

## TC 입력 형식 (참조)

`tcs` 한 줄이 **14필드**이고 두 번째 값이 **뎁스 경로 배열**입니다. 케이스명은 경로 다음
칸에 놓이며(→ `tc-sheet-format.md` §케이스), 생성 시 **실제로 쓰인 깊이까지만** 뎁스 열이 만들어집니다. 13번째가 `covers`
(커버리지 좌표), 14번째가 상태 열입니다.

```json
["TC-GAT-003", ["MY 탭","세이프티 필터"], "필터 ON 반영",
 "1. 성인 계정으로 로그인\n2. 필터 꺼짐 상태", "1. 필터 토글 선택한다\n2. 홈 탭 이동한다",
 [["켜짐 표시된다"], ["언세이프 제외 모수로 노출된다", "필터 상태 유지된다"]],
 "결정적|확률적|루브릭|금칙", "자동화 전용|공통|사람 전용", "High|Medium|Low",
 "선행 TC 또는 -", "대상 서비스", "Note(수행 안내)",
 ["트리 경로 또는 testid", "..."], "상태(쉼표 복수, 생략 시 성인 인증)"]
```

- 기대결과는 **스텝별 배열**입니다(2026-08-03 개정) — 안쪽 배열 하나가 그 스텝의 판정 목록이고,
  판정이 여럿이면 그 스텝의 행이 그만큼 늘며 TN·Test-Step이 병합됩니다. 문장을 이어 쓴 문자열도
  읽히지만 판정의 소속 정보가 없어 개수가 다르면 전부 마지막 스텝에 실립니다

- 뎁스 경로는 **도달 경로**입니다(기능 영역 아님). 영역은 TC ID 접두가 담습니다
- 8번째 **실행 주체**가 신설이며 생략하면 「공통」으로 읽힙니다
- 마지막 값은 이제 **Note(사람이 읽을 안내)** 입니다 — 케이스 메타는 각자 열을 가집니다

- 옛 형식(13필드·`d1`·`d2`·`d3`)도 읽히지만 새 형식으로 씁니다
- 규칙 정본은 `project-process/rules/tc-sheet-format.md`

### 착수 전 정할 것 — 모두 확정 (2026-08-03)

| 항목 | 확정 |
|---|---|
| 뎁스 축 | **도달 경로 뎁스** — 경계 기준 셋(합류점·전역·오버레이) + 소속 규칙(트리거 화면). 1-Depth 10개는 `tc-input`의 `d1_order` |
| 영역 구분 | **TC ID 접두**가 담습니다. 뎁스는 「어디서 실행하나」, ID는 「무엇을 검증하나」 |
| 커버리지 보증 | 구현 기능 단위 85개 ↔ TC 대조를 스크립트로 — 미매핑 기능 단위를 목록으로 출력 |
| 시트 서식 | 병합은 스텝 범위 하나 · Total Result 행 단위 · 머리 영역 재구성 · 뎁스 채움 색 |
| 신설 열 | 실행 주체(자동화 전용/공통/사람 전용) · TC ID · 검증유형 (뒤 둘은 Note 우측 참조 블록) |
| 실행 배분 | **공통은 자동화가 돌리고 사람은 생략.** 현재 프로젝트는 자동화만 수행 |
| 결함 주입 매트릭스 열 | TC 비고(Note)가 아니라 **자동화 단계에서 매핑** — 위 커버리지 대조 스크립트가 같은 자리에서 처리 |

### 첫 영역 — 웹 진입

플로우 시작점이라 형식 확인용으로 읽기 쉽고, 게이팅 결함(`gate-bypass`)이 여기서 걸립니다.
①에서 한 번 멈춰 형식·밀도를 확인받은 뒤 나머지 9영역으로 갑니다.

### 이번 설계에서 제외한 것 (사유 기록 — 리포트 「SUT 한계와 검증 범위」 재료)

- **오조작·중단 전개 축** (2026-08-03 사용자 확정 제외) — 연타·순서 역행·진행 중 이탈·입력
  실수를 케이스로 세우는 축입니다. 케이스가 20~30건 늘고 설계가 복잡해져 이번 범위에서
  뺐습니다. 예측 못 한 조작은 **탐색적 테스트**가 맡고, 거기서 나온 결함은 이슈 시트에
  「조인에 걸리지 않는 이슈」로 기록된 뒤 리그레션 TC 세트로 편입됩니다.
  (연타는 트리의 「연타 이중 차감 방지」 노드로 일부 이미 덮입니다)
- **산출물 대상별 분리** — 한 시트를 유지하고 실행 주체 열의 자동 필터로 자릅니다. 첫 영역을
  써 본 뒤 세 분류의 실제 비율을 보고 필요하면 그때 착수합니다

## 사용자 결정 대기

1. **그림 안 텍스트 30곳을 언제 고칠까요?** (2026-08-04 보류 → 대기 중)
   `diagrams/` 3종과 `structure.svg`의 라벨이 아직 평서형입니다(「시작점을 같게 만든다」 등).
   문서 본문은 모두 경어체로 통일했으므로 그림만 남았습니다. 좌표와 줄바꿈이 글자 수에
   맞춰져 있어 문장을 늘리면 배치가 밀립니다 — **사용자가 「포트폴리오 페이지 전체 수정 후에
   요청하겠다」고 하여 대기 중입니다.**

닫힌 결정과 그 사유는 change-log
§확정된 결정 > 결정 대기 항목 정리에 있습니다 — 이슈·TC 연결 구조, 트리 미확인 2건,
트리의 조사 후보 수치, `build_tc_xlsx.py` 삭제, 자동화 리포트 템플릿(기본 리포트로 시작).

## 백로그

- **「정본과 파일 지위」 표를 중앙으로 올릴지 — 두 번째 프로젝트를 시작할 때 판단합니다**
  (2026-08-05 개정). 원래는 「CLAUDE.md에 반영」이라고 적혀 있었으나 그 뒤에 방향이 둘 갈렸습니다 —
  ① CLAUDE.md는 **포인터만** 두기로 확정(2026-08-04)했으므로 표 본문이 들어갈 자리가 아니고,
  ② `rules/site-structure.md`가 「정본이 무엇인지는 **프로젝트마다** change-log의 표가 정한다」로
  확정했습니다. 표의 내용은 전부 중앙 성격이지만(프로젝트 이름이 안 들어감), 프로젝트가 하나뿐이라
  복사가 아직 일어나지 않았습니다. **실제로 복사가 필요해지는 시점**에 옮길지 정합니다.
  옮긴다면 자리는 `rules/` 아래 문서이고 CLAUDE.md는 가리키기만 합니다. 커밋 여부 열은
  성격상 `qa-git-rules.md` 쪽입니다.
  (`automation/` 하위 구조는 2026-08-05 CLAUDE.md에 반영 완료)
- `scripts/gen_test_skeleton.py` — 시간 부족 시 버리는 순서 2번, 수동 작성으로 대체 가능
- 플레이툰 잔여 실측 소소 2건 — 내 작품 탭·빈 검색 결과 UX (`analysis/…-plaitoon-inventory.md`
  B-3. 홈 칩별 목록 구성은 2026-08-02 실측 완료)
- MY 프로필 편집 — 2026-08-02 미편입 확정, 추후 편입 가능성 있음(사용자 의향). 편입 시 트리
  개정 필요
- **리그레션 TC 세트** — 결함에서 출발하는 케이스는 기능 TC와 섞지 않고 별도 세트로 만들어
  진행합니다(2026-08-02 사용자 확정). 결함이 쌓인 뒤 착수하며, 기능 TC(v1.0)와 파일·번호
  체계를 어떻게 가를지는 착수 시점에 결정
