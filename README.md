# QA-VisualNovel-Portfolio

여러 **미연시 AI 서비스를 분석**해서, 미연시 AI 관련 앱을 개발하게 될 때 실제로 진행할 법한
**테스트 케이스를 만들어 내는 TC 자동 작성 포트폴리오**입니다.

한 번 만들고 끝나는 산출물이 아니라, 기능이 바뀔 때마다 골격을 갱신하고 그 이력을 추적하는
**살아있는 자산**으로 운영합니다. 이 저장소의 구조 자체가 그 운영 방식을 보여주도록 설계했습니다.

📄 **문서 미리보기** — https://ryuseojin.github.io/QA-VisualNovel-Portfolio/
(HTML 산출물은 GitHub에서 소스로 보이므로, 렌더링된 문서는 이 주소에서 확인하세요.)

> **현재 상태** — 첫 프로젝트 [`qa-lab-miyonchat`](projects/qa-lab-miyonchat/index.html)이
> 파이프라인을 완주했습니다. 역분석 → 기능 골격 → design 명세 → **SUT 직접 제작** → TC → 자동화
> → 결함 주입 매트릭스 → 리포트 → CI.

## 워크플로우

TC를 자동으로 작성하기 위해 세 단계를 거칩니다.

1. **레퍼런스 앱 분석** — 미연시 AI 서비스들을 수집·분해합니다. 확인되지 않은 값은 추측으로
   채우지 않고 `?`로 남겨 실측 대상으로 관리합니다.
2. **공통 기능 산출** — 분석한 서비스들이 공통으로 갖는 기능을 뽑아 Depth 계층의 기능 골격으로
   정규화하고, 노드마다 검증유형(결정적·확률적·루브릭·금칙)을 판정합니다.
3. **TC 산출** — 확정된 골격의 노드를 정상·경계·예외·우회로 전개해 실행용 TC 시트(xlsx)로 냅니다.

각 단계 사이에는 **확인 게이트**가 있습니다. 문서를 쓰기 전에 아웃라인과 템플릿을 먼저 확인받고,
**기능 골격이 최종 확정되기 전에는 TC 설계로 넘어가지 않습니다.** 골격이 흔들린 채 TC를 쓰면
그 뒤의 모든 산출물을 다시 만들어야 하기 때문입니다.

## 프로젝트

### qa-lab-miyonchat — 미연시 AI 챗

레퍼런스가 될 실제 서비스를 역분석해 공통 기능 골격을 세우고, **그 골격을 검증할 대상(SUT)을
직접 만들어** TC를 설계·자동화한 뒤, 결함을 일부러 심어 **탐지력까지 확인**했습니다.

| | |
|---|---|
| [프로젝트 허브](projects/qa-lab-miyonchat/index.html) | 파이프라인 8단계 · 문서 지도 · 정본과 파생물 |
| [QA 검증 리포트](projects/qa-lab-miyonchat/automation/report/qa-lab-miyonchat-report.html) | 검증유형별 집계 · 결함 주입 매트릭스 · SUT 한계와 검증 범위 |
| [기능 골격](projects/qa-lab-miyonchat/spec/qa-lab-miyonchat-feature-tree.html) | 구현 기능 단위 86개 · 노드마다 검증유형 판정 |
| [SUT](projects/qa-lab-miyonchat/sut/index.html) | 검증 대상을 직접 실행 — 디버그 콘솔로 상태를 만듭니다 |

**SUT를 직접 만든 이유**는 검증 방법 자체를 증명해야 했기 때문입니다. 남의 서비스로는 결함을
일부러 심을 수 없어서, 「내 TC가 이 결함을 실제로 잡는다」를 보일 방법이 없습니다.

**두 축으로 봅니다** — 커버리지는 *빠짐없이 봤는가*를, 결함 주입 매트릭스는 *봤을 때 알아채는가*를
말합니다. 통과 건수만으로는 뒤엣것을 알 수 없습니다.

## 구조

<img src="structure.svg" alt="저장소 구조와 관계 — 절차 기준은 모든 작업에, 형식 기준은 허브와 프로젝트 문서에, TC 생성 도구는 테스트 케이스에 연결된다" width="940">

관계는 세 종류로 묶여 있습니다. **절차 기준**(`qa-doc-playbook`·`rules/`)은 특정 산출물이 아니라
모든 작업 전에 확인하는 규칙이고, **형식 기준**(`master css·html`·`template-catalog`)은 중앙 허브부터
프로젝트 문서까지 모든 HTML 산출물의 형식을 결정하며, **TC 생성 도구**(`tc-sheet-master.xlsx`·`scripts/`)는
TC 엑셀 하나를 만들어 냅니다. 마지막 묶음은 폴더 위치가 서로 다르지만 역할이 한 쌍이라 함께 묶었습니다.

이 그림은 **무엇이 어디 있는가**를 말합니다. **무엇을 근거로 판정하는가**는 그림을 나눠
프로젝트 허브의 「검증 로직」 절에 두었습니다 — 커버리지 3축 대조 · 결함 주입 매트릭스 ·
자동화 실행과 격리. 정본은 [`diagrams/`](diagrams/)이며 허브 생성기가 읽어 넣습니다.

## 폴더 구조

최상위 구성은 아래와 같습니다. 각 폴더를 펼치면 안에 무엇이 들어 있는지 볼 수 있습니다.

- [`README.md`](README.md) — 저장소 소개 (이 문서)
- [`CLAUDE.md`](CLAUDE.md) — 작업 규칙 진입점. 정본 관리·참조 규칙·git 규칙이 여기 명문화되어 있습니다
- [`index.html`](index.html) — 중앙 허브. 워크스페이스 문서와 프로젝트 목록으로 가는 진입점

<details>
<summary><a href="design-guide/"><code>design-guide/</code></a> — 디자인 일관성의 기준</summary>

- [`design-guide-master.css`](design-guide/design-guide-master.css) — 색·타이포·컴포넌트 스타일의 정본
- [`design-guide-master.html`](design-guide/design-guide-master.html) — 그 스타일이 실제로 어떻게 보이는지 확인하는 시각 규칙서 ([렌더링 보기](https://ryuseojin.github.io/QA-VisualNovel-Portfolio/design-guide/design-guide-master.html))

새 디자인 요소가 필요하면 마스터를 임의로 고치지 않고, 판별 절차를 거쳐 버전을 올리는 방식으로만 추가합니다.

</details>

<details>
<summary><a href="design-template/"><code>design-template/</code></a> — 문서 서식과 판별 기준</summary>

- [`template-catalog.md`](design-template/template-catalog.md) — 템플릿 목록과 어떤 요청에 어떤 서식을 쓸지 판별하는 단일 소스
- [`01-feature-tree.html`](design-template/01-feature-tree.html) — 기능 골격 트리·관계도 문서 서식
- [`02-reverse-analysis.html`](design-template/02-reverse-analysis.html) — 출시 서비스 역분석 문서 서식
- [`03-spec-analysis.html`](design-template/03-spec-analysis.html) — 기획서 분석 문서 서식
- `tc-sheet-master.xlsx` — TC 시트 기준 서식. 내부 '명세서' 시트가 작성 규칙의 정본입니다 *(배치 예정)*

</details>

<details>
<summary><a href="project-process/"><code>project-process/</code></a> — 모든 작업이 따르는 절차·방법론</summary>

- [`qa-doc-playbook.md`](project-process/qa-doc-playbook.md) — 분석 → 골격 → TC 파이프라인 절차서. 확인 게이트와 체크리스트가 여기 있습니다
- [`qa-dictionary.md`](project-process/qa-dictionary.md) — 중앙 용어집. 정의를 새로 쓰지 않고 정본 문서를 가리키는 색인입니다
- [`rules/`](project-process/rules/) — 방법론·운영 규칙 정의
  - [`depth-and-tn.md`](project-process/rules/depth-and-tn.md) — Depth 계층·TN 번호·우선순위
  - [`verification-types.md`](project-process/rules/verification-types.md) — 검증유형과 PASS/FAIL 판정 규칙
  - [`case-expansion.md`](project-process/rules/case-expansion.md) — 노드 하나를 정상·경계·예외·우회로 전개하는 규칙
  - [`tc-relations.md`](project-process/rules/tc-relations.md) — 케이스 사이의 선행 관계와 실행 순서
  - [`tc-sheet-format.md`](project-process/rules/tc-sheet-format.md) — TC 시트 컬럼·문체·수식
  - [`html-report-guide.md`](project-process/rules/html-report-guide.md) — HTML 문서 디자인 규칙
  - [`qa-git-rules.md`](project-process/rules/qa-git-rules.md) — 커밋·push·브랜치 운영 규칙
- [`scripts/`](project-process/scripts/) — 정본에서 산출물을 찍어내는 도구
  - [`parse_feature_tree.py`](project-process/scripts/parse_feature_tree.py) — 기능 골격 정본(md)을 구조 데이터로 변환
  - [`build_tc_template_xlsx.py`](project-process/scripts/build_tc_template_xlsx.py) — TC 시트 생성
  - [`norm.py`](project-process/scripts/norm.py) — Test-Step·Expected-Result 문체 정규화

</details>

<details>
<summary><a href="projects/"><code>projects/{프로젝트}/</code></a> — 프로젝트별 산출물</summary>

프로젝트가 생기면 아래 구성으로 만들어집니다.

- `{프로젝트}-index.html` — 프로젝트 허브 (이 프로젝트의 문서 목록)
- `{프로젝트}-dictionary.html` — 프로젝트 용어집 (고유명사 허용)
- `{프로젝트}-change-log.md` — 문서 변경 이력. 작업 전 항상 먼저 읽는 파일
- `analysis/` — 조사 전량. 역분석 산출물과 원자료를 버리지 않고 모으는 곳
- `reference/` — 채택분. analysis에서 쓰기로 고른 것들의 구체 사양만 추린 자료집
- `spec/` — 확정 결정. TC의 기대값은 여기서만 가져옵니다
  - `{프로젝트}-feature-tree.md` — **정본.** 손으로 고치는 유일한 파일
  - `{프로젝트}-feature-tree.html` — 정본에서 재생성하는 트리 시각화 (직접 수정하지 않음)
  - `rationale/` — 레퍼런스에 없어 직접 세운 노드와 직접 정한 수치의 근거
  - `archive/` — 지나간 상태. 골격 변경 이력(`{프로젝트}-tree-change-log.md`)과 큰 개정 직전의 동결 스냅샷이 함께 있고, 평소에는 열지 않습니다
- `test-case/` — 산출된 TC 엑셀 (기준 골격 버전 기록 + 이슈 관리 시트 내장)
- `sut/` — 테스트 대상. 대상을 직접 만드는 프로젝트에만 둡니다
- `automation/` — 자동화 스크립트와 리포트. `sut/`가 있는 프로젝트에만 둡니다

</details>

## 왜 이렇게 설계했나

**단일 정본, 나머지는 파생.** 골격이 여러 파일에 따로 살면 수정 누락으로 반드시 어긋나기 때문에,
손으로 고치는 파일을 `spec/{프로젝트}-feature-tree.md` 하나로 고정했습니다. 트리 시각화 HTML과
TC xlsx는 전부 이 정본에서 재생성됩니다.

**구조도도 하나의 이미지로 관리합니다.** 구조도는 이 README와 중앙 허브(`index.html`) 두 곳에서
쓰이는데, 허브는 자기완결 단일 파일 규칙 때문에 파일을 참조하지 못하고 마크업을 직접 품어야 합니다.
손으로 맞추면 한쪽만 고쳤을 때 두 그림이 갈라지면서도 아무 에러가 나지 않아 오래 발견되지 않으므로,
`structure.svg`를 정본으로 두고 허브 쪽 사본은 `project-process/scripts/inline_structure_svg.py`로만
주입합니다. 커밋 전 `--check`로 동기를 확인하며, 그래서 두 곳의 구조도는 항상 같은 이미지입니다.

**change-log 이원화.** 삭제·수정된 옛 기능 정보가 현재 작업에 섞여 들어오지 않도록, 문서 이력
(`{프로젝트}-change-log.md`)과 골격 이력(`spec/archive/{프로젝트}-tree-change-log.md`)을 분리했습니다.
참조 규칙이 정반대인 두 기록을 한 파일에 두면 격리가 불가능하기 때문입니다. 그래서 문서 이력은 작업 전
항상 읽고, 골격 이력은 특정 기능의 행방을 물을 때만 엽니다.

**TC 시트 규칙의 이중화.** 시트 작성 규칙을 한 곳에서만 관리하면 잘못 수정됐을 때 설계 전체가
틀어지므로, md 문서(`rules/tc-sheet-format.md`)와 기준 xlsx의 '명세서' 시트 양쪽에 두고 교차 검증합니다.
불일치가 발견되면 임의로 판단하지 않고 어느 쪽을 기준으로 삼을지 확인합니다.

<details>
<summary>나머지 설계 결정 (archive · 이슈 시트 · 용어집 · 골격 재사용 · 디자인 갱신)</summary>

**archive/ 동결 스냅샷.** TC 시트에는 "기준 골격 v1.0"이 기록되는데 정본은 계속 진화합니다.
과거 TC를 검토하거나 롤백을 판단할 때 그 시점 골격 전체를 파일 하나로 대조할 수 있어야 하므로,
큰 개정 직전의 정본을 통째로 동결해 둡니다.

**`spec/` 하위를 참조 규칙으로 갈랐습니다.** 파일마다 열어도 되는지를 외우면 실수로 옛 정보를 끌어오게
되므로, 규칙이 같은 것끼리 폴더로 묶었습니다. 골격 이력과 동결 스냅샷은 둘 다 지나간 상태라
`archive/`에 모으고, 수시로 읽어야 하는 근거 문서는 `rationale/`로 분리했습니다. 그래서 `spec/`
아래에서는 폴더 이름만 보고 참조 여부를 판단할 수 있습니다.

**이슈 관리 시트 내장.** 실무 정석은 JIRA 같은 트래커를 분리해 운영하는 것이지만, 이 저장소는
포트폴리오 열람 편의를 위해 TC와 이슈 흐름을 한 파일에서 볼 수 있도록 xlsx 안에 이슈 관리 시트를
내장했습니다.

**용어집 이원화.** 범용 QA 용어와 프로젝트 고유명사가 한곳에 섞이면 다른 프로젝트에서 재사용할 수
없으므로, 중앙(`qa-dictionary.md`)과 프로젝트별(`{프로젝트}-dictionary.html`)로 분리했습니다.
중앙 용어집은 정의를 새로 쓰지 않는 색인이라 정의 중복과 어긋남도 함께 차단됩니다.

**골격 재사용, 시드 파일 없음.** 프로젝트 사이에 공유 파일을 두면 한쪽 수정이 다른 쪽을 오염시키므로,
새 프로젝트는 기존 골격에서 필요한 부분만 복사해 시작하고 복사된 순간부터 완전히 독립됩니다.

**디자인은 승인 갱신만.** 문서가 늘어도 디자인이 일관되도록, 새 디자인 요소는 템플릿 카탈로그의
판별 절차(Case A/B/C)를 거쳐 마스터를 버전 갱신하는 방식으로만 추가합니다.

</details>

## 방법론 핵심

- **검증유형이 기능 목록보다 먼저.** LLM이 응답을 만드는 서비스는 "기대 결과가 단일하다"는
  TC의 전제가 깨지므로, 결정적/확률적/루브릭/금칙 네 갈래로 먼저 나눕니다.
- **TN은 케이스 안의 스텝 번호.** 케이스 사이의 선행 관계는 별개 층위(TC 관계도)로 다룹니다.
- **상태는 Depth가 아니라 Pre-Condition으로.** 로그인·구독·플랫폼을 계층으로 쪼개면 트리가
  폭발합니다.
- **추측으로 기대값을 채우지 않는다.** 미확인 값은 `?`로 남기고 실측으로만 확정합니다.
- **커버리지는 세 축으로 대조한다.** 기능 단위 · 화면 요소 · 게이팅 상태. 한 축만 보면 반대쪽이
  통째로 샙니다 — 기능 단위만 보면 빈 상태 안내가 빠지고, 요소만 보면 집계·격리처럼 화면에 드러나지
  않는 규칙이 빠집니다.
- **결함을 일부러 심어 탐지력을 증명한다.** 담당 TC만 깨지는지 봅니다. 담당인데 통과하면 결함이
  아니라 그 TC가 부실한 것입니다.
- **판단은 낡으므로 기계가 검사하게 둔다.** 검증 제외 사유, 결함의 담당 TC, 생성된 산출물이
  최신인지 — 셋 다 「나중에 다시 보자」가 아니라 실행 시점 검사입니다.

자세한 규칙은 [`project-process/qa-doc-playbook.md`](project-process/qa-doc-playbook.md)와
[`project-process/rules/`](project-process/rules/)에서 시작하세요.
