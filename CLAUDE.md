# QA-VisualNovel-Portfolio

출시된 서비스·기획서를 QA 관점에서 분석해 **기능 골격(Depth 트리) → 테스트 케이스(xlsx)**까지 산출하는 워크스페이스입니다. 이 파일은 모든 작업이 따르는 규칙의 진입점입니다.

## 폴더 구조

- `project-process/` — 모든 작업이 따르는 절차·규칙. `qa-doc-playbook.md`(파이프라인 절차서), `qa-dictionary.md`(중앙 용어집 색인), `rules/`(방법론·운영 규칙 정의), `scripts/`(xlsx 생성 도구).
- `design-guide/` — 디자인 일관성의 기준. `design-guide-master.css`(스타일 정본) + `design-guide-master.html`(시각 규칙서).
- `design-template/` — 문서 포맷 템플릿(성장 영역). `template-catalog.md`(템플릿 목록+판별 기준의 단일 소스), `NN-{템플릿명}.html`, `tc-sheet-master.xlsx`(TC 시트 기준 서식 — '명세서' 시트가 규칙 정본).
- `projects/{프로젝트}/` — 프로젝트별 산출물. 허브(`{프로젝트}-index.html`)·용어집(`{프로젝트}-dictionary.html`)·이력(`{프로젝트}-change-log.md`)·`reference/`·`spec/`·`analysis/`·`test-case/`.

## 문서 제작 요청 시 (필수)

분석·역분석·TC 설계 등 **문서 제작 요청이 오면 반드시 `project-process/qa-doc-playbook.md`의 절차를 처음부터 끝까지 따릅니다.** 요약하면 이렇습니다.

1. 프로젝트 change-log를 먼저 읽어 최신 상태를 파악합니다.
2. **사용자 확인 ①(아웃라인)·②(템플릿 판별)를 받기 전에는 본문 작성을 시작하지 않습니다.**
3. 템플릿 판별은 `design-template/template-catalog.md` 기준으로 Case A(기존 템플릿) / B(마스터 갱신 필요) / C(신규 템플릿 필요)로 나눕니다. B·C는 승인 후에만 마스터·카탈로그를 갱신합니다.

## 정본과 파생 (필수)

- 기능 골격의 정본은 `analysis/{프로젝트}-feature-tree.md` **하나뿐입니다.** HTML 시각화와 TC xlsx는 전부 정본에서 재생성하는 파생물이므로 직접 수정하지 않습니다.
- **정본 수정 체크리스트(한 묶음으로 강제)**: ① 정본 md 수정 → ② HTML 재생성 → ③ analysis-change-log 기록(+프로젝트 change-log에 골격 버전 한 줄 포인터) → ④ 커밋 시점 제안.
- 미확인 값은 추측으로 채우지 않고 `?`로 표기하며, 정본의 "미확인 목록" 섹션에 모읍니다.

## change-log 참조 규칙 (필수)

| 파일 | 규칙 |
|---|---|
| `{프로젝트}-change-log.md` | 작업 전 **항상 먼저 읽습니다** (최신 문서 상태·골격 버전 파악) |
| `analysis/{프로젝트}-analysis-change-log.md` | **기본 참조 금지.** 사용자가 특정 기능의 행방·이력을 물을 때만 로드해 "언제 삭제/수정되어 현재 미사용" 형태로 답합니다 |
| `analysis/archive/` | **기본 참조 금지.** 과거 골격 버전과의 대조가 필요할 때만 엽니다 |

삭제·수정된 옛 기능 정보가 평상시 작업에 섞이는 것을 막기 위한 격리 장치입니다. 그래서 정본 트리에는 현재 상태만 남기고, 삭제 노드의 흔적(tombstone)을 두지 않습니다.

## TC 시트 규칙 (필수)

- 시트 규칙은 `rules/tc-sheet-format.md`(md)와 `design-template/tc-sheet-master.xlsx`의 **'명세서' 시트(정본)** 이중으로 관리합니다. 작업 시 md를 먼저 읽고 명세서 시트와 교차 검증하며, **불일치를 발견하면 임의로 판단하지 않고 사용자에게 어느 쪽 기준인지 질문합니다.**
- TC xlsx에는 기준 골격 버전을 기록하고, 이슈 관리 시트를 내장합니다.

## git 규칙 (필수)

`rules/qa-git-rules.md`를 따릅니다. 요약하면 커밋은 사용자 요청과 승인이 있을 때만 하고(제목·본문·브랜치 제시 후), push는 별도 승인과 저작권 게이트를 거치며, 브랜치는 혼합형(평상시 main, 큰 산출물만 PR), 태그는 버전 좌표로 씁니다.

## 표기·네이밍 규칙 (필수)

- 문서를 쓰거나 고칠 때는 `project-process/rules/doc-write-style.md`를 따릅니다(문체·문장 구조·예외).
- 폴더·파일은 전부 **kebab-case**로 쓰고, 프로젝트 산출물은 `{프로젝트}-{용도}-{이름}` 형식으로 씁니다.
- **개수 하드코딩 금지** — 문서가 늘어도 설명이 낡지 않도록, 구조 설명·다이어그램·README에서 "규칙 5종" 같은 개수 표기 대신 역할로 서술합니다("방법론·운영 규칙 정의").
- 용어집 이원화: 중앙 `qa-dictionary.md`에는 범용 QA 용어만 두고(색인이며 정의 정본은 rules/ 문서), 프로젝트 `{프로젝트}-dictionary.html`에는 해당 프로젝트 고유명사를 허용합니다. 배치 기준은 "정의 문장에서 프로젝트 이름을 지워도 성립하는가?"입니다.

## 산출물 출력 방식

- 단독 열람을 보장하기 위해, HTML 산출물(분석 문서·허브·용어집·feature-tree.html)은 생성 시점의 마스터 CSS를 `<style>`에 **inline한 자기완결 단일 파일**로 만듭니다. 기준 마스터 버전은 파일 상단 CHANGELOG 주석과 footer에 기록합니다.
- `<link>` 참조는 디자인 규칙서(design-guide-master.html, design-template의 템플릿)에만 허용합니다.
- **GitHub Pages 링크 규칙** — 이 저장소는 Pages로 공개됩니다(https://ryuseojin.github.io/QA-VisualNovel-Portfolio/). Pages에서 `.md`는 원본 텍스트로 뜨고 폴더 경로는 404가 되므로, HTML 문서 안에서 **md·폴더로 거는 링크는 GitHub 저장소 절대 URL**(`https://github.com/RyuSeoJin/QA-VisualNovel-Portfolio/blob|tree/main/…`)로, **HTML 문서 링크는 상대 경로**로 적습니다.
- HTML은 만들고 나서 렌더해 눈으로 확인합니다 — 콘솔 에러 0, 라벨 충돌·글자 깨짐 없음.

## 저작권 게이트 (필수)

역분석 대상 자료(스크린샷·원문 텍스트·상표)는 **처음 다루는 작업 시점부터** 저작권 점검 체크리스트(`qa-doc-playbook.md` 참조)를 적용합니다. 이 저장소는 public이므로 push 전 점검은 `qa-git-rules.md` §5를 따릅니다.

## 보관 상태

- 루트 `SKILL.md`와 `rules/feature-tree-ai-chat.md`는 초안 이전 자산의 보관본입니다. 작업 기준으로 참조하지 않으며, 사용자가 제거를 요청하면 삭제합니다.

## 트랙별 허브 갱신 (필수)

문서를 만들 때마다 중앙 허브 `index.html`에는 프로젝트·워크스페이스 문서 목록을, 프로젝트 허브 `{프로젝트}-index.html`에는 그 프로젝트 문서 목록을 갱신합니다(중앙 허브에는 프로젝트당 행 1개만 둡니다). 어려운 용어는 배치 기준에 맞는 용어집에 추가합니다.
