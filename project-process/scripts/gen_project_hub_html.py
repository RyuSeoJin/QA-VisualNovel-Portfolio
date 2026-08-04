# -*- coding: utf-8 -*-
"""프로젝트 허브 생성 — 한 프로젝트의 전체 구조를 한 장으로

리포트와 무엇이 다른가
---------------------
  리포트는 **결과**를 말합니다 — 얼마나 통과했고 무엇을 못 봤는가.
  허브는 **구조**를 말합니다 — 어떤 단계를 거쳤고, 각 단계의 정본이 어디 있으며,
  무엇이 파생물이라 손대면 안 되는가.

  둘을 한 문서에 담지 않는 이유는 읽는 시점이 다르기 때문입니다. 리포트는 「이번 실행이
  어땠나」를 볼 때, 허브는 「이 프로젝트에 처음 들어왔는데 어디부터 보나」를 볼 때 엽니다.

수치를 왜 읽어 오나
------------------
  허브에 「TC 153건」을 손으로 적어 두면 TC가 늘어도 허브는 옛 숫자를 계속 말합니다.
  숫자는 전부 정본에서 읽고, 이 스크립트에는 **구조와 설명만** 둡니다.

사용법
------
    python gen_project_hub_html.py --project-dir <프로젝트 디렉터리> --slug <프로젝트명> \
        --css <design-guide-master.css> -o <출력 html>
"""
import argparse
import html
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shell  # noqa: E402
from check_tc_coverage import tree_leaves, blueprint_testids  # noqa: E402

REPO = "https://github.com/RyuSeoJin/QA-VisualNovel-Portfolio/blob/main"


def esc(s):
    return html.escape(str(s if s is not None else ""))


def read_json(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def count_tests(junit):
    """자동화 건수 — junit 하나로 센다. 파일이 없으면 0."""
    if not os.path.exists(junit):
        return 0, 0
    root = ET.parse(junit).getroot()
    cases = list(root.iter("testcase"))
    failed = sum(1 for c in cases if any(x.tag in ("failure", "error") for x in c))
    return len(cases), failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--css", required=True)
    ap.add_argument("--js", help="동작 정본(생략 시 CSS 옆의 design-guide-master.js)")
    ap.add_argument("--diagrams", help="설명 다이어그램 SVG 폴더")
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    P, S = args.project_dir, args.slug
    rel = os.path.relpath(P, os.path.dirname(os.path.abspath(args.output))).replace("\\", "/")
    rel = "" if rel == "." else rel + "/"

    cfg = read_json(os.path.join(P, "test-case", "%s-tc-input-v1.0.json" % S))
    tcs = cfg["tcs"]
    leaves, tree_version = tree_leaves(os.path.join(P, "spec", "%s-feature-tree.md" % S))
    testids, _ = blueprint_testids(
        os.path.join(P, "spec", "sut-design", "%s-sut-blueprint.md" % S))
    issues = read_json(os.path.join(P, "test-case", "%s-issues.json" % S))["issues"]
    waivers = read_json(os.path.join(P, "test-case", "%s-coverage-waiver.json" % S))["waivers"]
    faults = read_json(os.path.join(P, "automation", "%s-fault-matrix.json" % S))["faults"]
    n_auto, n_fail = count_tests(
        os.path.join(P, "automation", "result", "matrix", "junit-none.xml"))

    build = ""
    dj = os.path.join(P, "sut", "js", "data.js")
    if os.path.exists(dj):
        m = re.search(r'SUT_BUILD\s*=\s*"([^"]+)"', io.open(dj, encoding="utf-8").read())
        build = m.group(1) if m else ""

    by_vt = {}
    for t in tcs:
        by_vt[t[6]] = by_vt.get(t[6], 0) + 1
    manual = sum(1 for t in tcs if t[7] == "사람 전용")

    css, js = shell.assets(args.css, args.js)
    O = []
    w = O.append

    TOC = (("pipe", "파이프라인"), ("logic", "검증 로직"), ("map", "문서 지도"),
           ("canon", "정본과 파생물"), ("rules", "이 프로젝트가 세운 규칙"))

    w(shell.head("%s — 프로젝트 허브" % S, css, js))
    w(shell.open_body(S, "hub", rel, "프로젝트 허브", TOC,
                      "골격 v%s%s" % (tree_version, " · " + build if build else "")))

    w('<div class="doc-header"><h1>%s — 프로젝트 허브</h1>' % esc(S))
    w('<p class="doc-lead">미연시 AI 챗 서비스를 역분석해 <strong>기능 골격</strong>을 세우고, '
      '그 골격을 검증할 <strong>SUT</strong>를 직접 만든 뒤, TC를 설계해 자동화하고 '
      '<strong>결함을 일부러 심어</strong> 탐지력까지 확인한 프로젝트입니다. '
      '이 문서는 그 단계와 산출물이 어디 있는지를 한 장에 모은 지도입니다.</p>')
    w('<div class="meta-row">')
    for k, v in (("SUT", build), ("기능 골격", "v" + tree_version),
                 ("TC", "%d건" % len(tcs)), ("자동화", "%d건" % n_auto),
                 ("결함 주입", "%d종" % len(faults))):
        w('<span class="badge">%s <b>%s</b></span>' % (esc(k), esc(v)))
    w('</div></div>')

    demo = os.path.join(P, "docs", "sut-demo.gif")
    if os.path.exists(demo):
        w('<div class="card" style="padding:12px">'
          '<img src="%sdocs/sut-demo.gif" alt="SUT 실행 — 미로그인에서 언세이프가 가려져 '
          '있고, 로그인하면 풀리고, 대화방에서 응답이 스트리밍되며 재화가 차감된다" '
          'style="width:100%%;height:auto;display:block;border-radius:8px">'
          '<p class="foot" style="margin:10px 2px 0">검증 대상을 직접 만들었습니다 — '
          '게이팅 한 갈래를 처음부터 끝까지. 이 GIF도 스크립트로 다시 만듭니다</p></div>' % rel)

    w('<div class="stats">')
    for num, lbl in ((len(leaves), "기능 단위"), (len(testids), "화면 요소"),
                     (len(tcs), "테스트 케이스"),
                     ("%d/%d" % (n_auto - n_fail, n_auto), "자동화 통과"),
                     (len(faults), "주입 결함"), (len(issues), "검출 이슈")):
        w('<div class="stat"><div class="num">%s</div><div class="lbl">%s</div></div>'
          % (esc(num), esc(lbl)))
    w('</div>')

    # ── 파이프라인
    w('<h2 id="pipe">파이프라인</h2>')
    w('<p>앞 단계의 산출물이 뒤 단계의 <strong>입력이자 기대값의 출처</strong>입니다. '
      '건너뛰면 뒤 단계가 근거 없이 만들어집니다 — 예를 들어 골격 없이 TC를 쓰면 '
      '「무엇을 다 봤는가」를 대조할 기준이 사라집니다.</p>')
    w('<div class="steps">')
    for title, desc, link in (
        ("역분석", "출시된 미연시 AI 서비스 셋을 분해해 행동 인벤토리와 공통 트리를 뽑습니다. "
                 "확인 못 한 값은 추측으로 채우지 않고 실측 대상으로 남깁니다.",
         "analysis/"),
        ("기능 골격", "공통 기능을 Depth 계층으로 정규화하고 노드마다 검증유형을 판정합니다. "
                   "<strong>TC 기대값의 출처는 여기와 design 명세뿐</strong>입니다.",
         "spec/%s-feature-tree.md" % S),
        ("design 명세", "골격이 「무엇을」이라면 여기는 「얼마나·어떤 규칙으로」입니다. "
                     "상한값·요율·임계·합격선이 확정됩니다.", "spec/design/"),
        ("SUT 제작", "검증 대상을 직접 만듭니다. 테스트 인터페이스 넷(testid · 상태 API · "
                   "실행 조건 파라미터 · 데이터 주입)을 함께 설계합니다.", "sut/"),
        ("TC 설계", "기능 단위를 정상·경계·예외·우회로 전개합니다. 케이스마다 무엇을 덮는지를 "
                  "좌표로 적어 두어 커버리지를 기계가 대조합니다.", "test-case/"),
        ("자동화", "케이스명이 곧 TC ID입니다 — 리포트만 보고 시트를 찾을 수 있습니다.",
         "automation/tests/"),
        ("결함 주입", "일부러 만든 고장을 하나씩 켜고 전체를 다시 돌려 <strong>담당 TC만 "
                   "깨지는지</strong> 봅니다. 커버리지가 「빠짐없이 봤다」라면 이쪽은 "
                   "「봤을 때 알아챈다」입니다.", "spec/sut-design/%s-fault-injection.md" % S),
        ("리포트", "검증유형별 집계를 분리하고, 매트릭스와 「SUT 한계와 검증 범위」를 싣습니다.",
         "automation/report/%s-report.html" % S),
    ):
        w('<div class="step"><div class="body"><b>%s</b> — %s '
          '<a href="%s%s">%s</a></div></div>'
          % (esc(title), desc, rel, esc(link), esc(link)))
    w('</div>')

    # ── 검증 로직 (설명 다이어그램)
    # 그림 파일이 정본이고 여기서 읽어 넣는다. 사본을 손으로 맞출 일이 없으므로
    # 「한쪽만 고쳐 두 그림이 갈라지는」 사고가 구조적으로 생기지 않는다.
    if args.diagrams and os.path.isdir(args.diagrams):
        w('<h2 id="logic">검증 로직</h2>')
        w('<p>위 파이프라인이 <strong>무엇을 거치는가</strong>라면, 여기는 '
          '<strong>무엇을 근거로 판정하는가</strong>입니다. 저장소 구조도에서 각각 '
          '<code>spec/</code>↔<code>test-case/</code> 구간과 <code>automation/</code> '
          '안쪽을 확대한 그림입니다.</p>')
        for fname, title, lead in (
            ("coverage-axes.svg", "① 커버리지 3축 — 「다 봤다」를 어떻게 판정하나",
             "기준선 셋을 정본에서 읽어 오고, TC가 신고한 좌표와 맞춰 <strong>덮이지 않은 "
             "것을 목록으로</strong> 냅니다. 그 목록이 빌 때까지가 TC 설계입니다."),
            ("fault-matrix.svg", "② 결함 주입 매트릭스 — 「봤을 때 알아챈다」를 어떻게 증명하나",
             "일부러 만든 고장을 하나씩 켜고 같은 스위트를 다시 돌려 <strong>담당 TC만 "
             "깨지는지</strong> 봅니다. 커버리지가 증명하지 못하는 것을 이쪽이 맡습니다."),
            ("automation-isolation.svg", "③ 자동화 실행과 격리 — 어떻게 오염 없이 도나",
             "테스트끼리 간섭하면 통과도 실패도 근거가 되지 않습니다. 시작점을 같게 만드는 "
             "일과 <strong>기다리는 방식</strong>이 그 근거를 지킵니다."),
        ):
            fp = os.path.join(args.diagrams, fname)
            if not os.path.exists(fp):
                continue
            w('<h3>%s</h3><p>%s</p>' % (esc(title), lead))
            w('<div class="card" style="padding:12px">%s</div>'
              % io.open(fp, encoding="utf-8").read().strip())

    # ── 문서 지도
    w('<h2 id="map">문서 지도</h2>')
    w('<p>작업을 이어받을 때는 <strong>change-log와 remaining-work를 먼저</strong> 읽습니다. '
      '그 둘이 「지금 어디까지 왔고 다음이 무엇인가」의 정본입니다.</p>')
    w('<div class="tbl-scroll"><table><thead><tr><th>폴더</th><th>무엇이 있나</th>'
      '<th>지위</th></tr></thead><tbody>')
    for folder, what, status in (
        ("<code>analysis/</code>", "역분석 조사 기록 — 행동 인벤토리 3종 + 공통 트리",
         "조사 자료 (TC 기대값 출처 아님)"),
        ("<code>reference/</code>", "조사에서 채택한 기능 목록", "판단 기록"),
        ("<code>spec/</code>", "기능 골격 · design 명세 · SUT 설계(청사진·결함 주입·mock·세이브 스키마)",
         "<strong>정본</strong>"),
        ("<code>spec/rationale/</code>", "왜 이렇게 정했나 — 추가·SUT 설계의 근거",
         "근거 기록 (기대값 출처 아님)"),
        ("<code>spec/archive/</code>", "골격 변경 이력", "기본 참조 금지 — 행방을 물을 때만"),
        ("<code>sut/</code>", "검증 대상 (단일 HTML + JS)", "<strong>구현</strong>"),
        ("<code>test-case/</code>", "TC 입력 · 제외 사유 · 이슈 · xlsx",
         "<strong>정본</strong>은 json, xlsx는 파생"),
        ("<code>automation/</code>", "테스트 · 매트릭스 기대표 · 실행 결과 · 리포트",
         "리포트·매트릭스 결과는 파생"),
    ):
        w('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (folder, what, status))
    w('</tbody></table></div>')

    # ── 정본과 파생물
    w('<h2 id="canon">정본과 파생물</h2>')
    w('<div class="callout warn"><strong>파생물은 손으로 고치지 않습니다.</strong> '
      '고치면 정본과 갈라지는데 아무 에러도 나지 않아 오래 발견되지 않습니다. '
      '정본을 고치고 다시 만드는 것이 유일한 경로이며, CI가 「커밋본이 최신인가」를 '
      '확인합니다.</div>')
    w('<div class="tbl-scroll"><table><thead><tr><th>파생물</th><th>정본</th>'
      '<th>만드는 도구</th></tr></thead><tbody>')
    for deriv, canon, tool in (
        ("%s-feature-tree.html" % S, "%s-feature-tree.md" % S, "gen_feature_tree_html.py"),
        ("%s-tc-v1.0.xlsx" % S, "%s-tc-input-v1.0.json" % S, "build_tc_template_xlsx.py"),
        ("%s-dictionary.html" % S, "%s-dictionary.md" % S, "gen_dictionary_html.py"),
        ("result/matrix/fault-matrix.md", "테스트 실행 + %s-fault-matrix.json" % S,
         "run_fault_matrix.py"),
        ("report/%s-report.html" % S, "위의 정본 전부", "gen_qa_report_html.py"),
        ("index.html (이 문서)", "위의 정본 전부", "gen_project_hub_html.py"),
    ):
        w('<tr><td><code>%s</code></td><td><code>%s</code></td><td><code>%s</code></td></tr>'
          % (esc(deriv), esc(canon), esc(tool)))
    w('</tbody></table></div>')

    w('<h3>현재 규모</h3>')
    w('<div class="tbl-scroll"><table><thead><tr><th>축</th><th class="num">값</th>'
      '<th>뜻</th></tr></thead><tbody>')
    vt_line = " · ".join("%s %d" % (k, v) for k, v in
                         sorted(by_vt.items(), key=lambda x: -x[1]))
    for k, v, meaning in (
        ("기능 단위", len(leaves), "골격에서 구현 범위로 확정된 검증 단위"),
        ("화면 요소", len(testids), "청사진에 등재된 조작 가능한 요소(testid)"),
        ("TC", len(tcs), vt_line),
        ("사람 전용 TC", manual, "자동화가 판정 기준을 세울 수 없는 것 — 루브릭 채점"),
        ("검증 제외", len(waivers), "누락이 아니라 판단. 사유와 근거를 기계가 확인"),
        ("검출 이슈", len(issues), "TC를 수행하다 나온 것"),
    ):
        w('<tr><td>%s</td><td class="num">%s</td><td>%s</td></tr>'
          % (esc(k), esc(v), esc(meaning)))
    w('</tbody></table></div>')

    # ── 이 프로젝트가 세운 규칙
    w('<h2 id="rules">이 프로젝트가 세운 규칙</h2>')
    w('<p>진행하다 막힌 자리에서 나온 것들입니다. 프로젝트 안에 묻어 두면 다음 프로젝트가 '
      '같은 자리에서 다시 막히므로, 워크스페이스 규칙(<code>project-process/rules/</code>)으로 '
      '올렸습니다.</p>')
    w('<div class="card-grid">')
    for title, body, doc in (
        ("TN은 연쇄에만", "스텝 하나를 떼어 내도 나머지가 성립하면 그건 나열입니다. "
                       "나열을 TN으로 묶으면 어느 대상이 깨졌는지 ID로 읽히지 않습니다.",
         "depth-and-tn.md"),
        ("케이스는 사전조건의 묶음", "뎁스 마지막 칸은 요약이 아닙니다. 「무엇을 보는가」를 "
                              "적으면 기대 결과와 중복되고, 값이 행마다 달라 뎁스 색이 "
                              "묶음이 아니라 소음이 됩니다.", "tc-sheet-format.md"),
        ("차단은 도달 경로마다", "판정 지점이 하나여도 그 상태를 만드는 코드가 경로마다 "
                          "다르면 케이스를 나눕니다.", "case-expansion.md"),
        ("기능 단위를 겸해 덮지 않음", "covers는 자기 신고라, 기능 단위 둘을 적고 하나만 검증해도 "
                          "대조기가 통과시킵니다. 빠진 것보다 나쁩니다.", "case-expansion.md"),
        ("판단은 낡습니다", "제외 사유에 기계가 확인할 조건을 붙입니다. 근거가 사라지면 "
                     "대조가 실패합니다.", "case-expansion.md"),
        ("담당은 주입 지점으로", "「돌려 보니 깨졌다」를 담당으로 삼으면 매트릭스는 항상 "
                          "통과하고 아무것도 증명하지 않습니다.", "sut-automation.md"),
        ("고정 대기 금지", "브라우저가 타이머를 늦추면 sleep 기반 대기가 환경에 따라 "
                      "깨집니다. 상태 표식이 바뀌는 것을 기다립니다.", "sut-automation.md"),
        ("내부 식별자 금지", "「계정 A」는 저장소 안에서만 통하는 이름입니다. 사전조건은 "
                       "그 밖에서도 읽힙니다.", "tc-sheet-format.md"),
    ):
        w('<div class="card"><h3>%s</h3><p>%s</p>'
          '<p class="foot"><a href="%s/project-process/rules/%s">%s</a></p></div>'
          % (esc(title), body, REPO, esc(doc), esc(doc)))
    w('</div>')

    w('<h2>산출물 바로 가기</h2><div class="card-grid">')
    for title, desc, link in (
        ("QA 검증 리포트", "검증유형별 집계 · 결함 주입 매트릭스 · SUT 한계",
         "%sautomation/report/%s-report.html" % (rel, S)),
        ("추적 매트릭스", "기능 단위 → TC → 자동화 함수 → 이슈를 한 줄로",
         "%sautomation/report/%s-traceability.html" % (rel, S)),
        ("기능 골격", "구현 기능 단위 %d개 · 검증유형 판정" % len(leaves),
         "%sspec/%s-feature-tree.html" % (rel, S)),
        ("SUT", "검증 대상을 직접 실행해 봅니다", "%ssut/index.html" % rel),
        ("TC 시트", "xlsx — GitHub에서는 내려받아 엽니다",
         "%s/projects/%s/test-case/%s-tc-v1.0.xlsx" % (REPO, S, S)),
    ):
        w('<div class="card"><h3><a href="%s">%s</a></h3><p>%s</p></div>'
          % (esc(link), esc(title), esc(desc)))
    w('</div>')

    w('<div class="doc-footer">이 문서는 파생물입니다 — <code>gen_project_hub_html.py</code>로 '
      '재생성합니다. 수치는 전부 정본에서 읽습니다.</div>')
    w(shell.close_body())

    with io.open(args.output, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(O))
    print("saved %s | 기능 단위 %d · testid %d · TC %d · 자동화 %d"
          % (args.output, len(leaves), len(testids), len(tcs), n_auto))
    return 0


if __name__ == "__main__":
    sys.exit(main())
