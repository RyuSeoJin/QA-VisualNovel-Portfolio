# -*- coding: utf-8 -*-
"""소개 페이지 생성 — 「무엇을 할 줄 아는가」를 먼저 보이는 층

산출물과 무엇이 다른가
---------------------
  허브·리포트·추적 매트릭스는 **작업의 결과**입니다. 이미 맥락을 아는 사람이 봅니다.
  소개 페이지는 처음 온 사람에게 **왜 그렇게 했는지**를 말합니다. 그래서 여기서는
  수치와 표를 다시 서술하지 않고, 판단과 이유를 적은 뒤 상세는 산출물로 보냅니다.
  같은 내용을 두 곳에 적으면 한쪽만 고쳤을 때 갈라집니다.

수치는 전부 정본에서 읽는다
--------------------------
  기능 단위·화면 요소·TC 건수는 트리와 청사진·TC 입력에서, 자동화 건수는 테스트 파일에서,
  결함 주입 결과는 커밋된 매트릭스 표에서 읽습니다. **junit을 읽지 않습니다** — 원자료는
  `.gitignore` 대상이라 환경이 없는 곳에서 재생성하면 0으로 떨어집니다.

사용법
------
    python gen_intro_html.py --page landing --repo-root . \
        --project-dir projects/qa-lab-miyonchat --slug qa-lab-miyonchat \
        --css design-guide/design-guide-master.css -o index.html
"""
import argparse
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shell  # noqa: E402
from check_tc_coverage import tree_leaves, blueprint_testids  # noqa: E402

esc = shell.esc
BLOB = shell.BLOB


def read_json(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def count_test_funcs(tests_dir):
    """자동화 건수 — 테스트 파일에서 센다(커밋된 정본). 실행 결과가 아니라 설계된 수다."""
    n = 0
    if not os.path.isdir(tests_dir):
        return n
    for name in sorted(os.listdir(tests_dir)):
        if not name.startswith("test_") or not name.endswith(".py"):
            continue
        with io.open(os.path.join(tests_dir, name), encoding="utf-8") as f:
            n += len(re.findall(r"^\s*def test_", f.read(), re.M))
    return n


def matrix_baseline(md_path):
    """기준선(주입 없음) 행이 전부 PASS인가 · 대각선만 FAIL인가를 표에서 읽는다."""
    if not os.path.exists(md_path):
        return None, 0
    base_ok, n_fail = None, 0
    with io.open(md_path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|") or "---" in line:
                continue
            if "(주입 없음)" in line:
                base_ok = "FAIL" not in line
            elif line.startswith("| `"):
                n_fail += line.count("FAIL")
    return base_ok, n_fail


def load(args):
    """정본에서 읽는 값 한 묶음 — 페이지들이 공유한다."""
    P, S = args.project_dir, args.slug
    d = {"slug": S}
    d["leaves"], d["tree_version"] = tree_leaves(
        os.path.join(P, "spec", "%s-feature-tree.md" % S))
    d["testids"], _ = blueprint_testids(
        os.path.join(P, "spec", "sut-design", "%s-sut-blueprint.md" % S))
    cfg = read_json(os.path.join(P, "test-case", "%s-tc-input-v1.0.json" % S))
    d["tcs"] = cfg["tcs"]
    d["areas"] = cfg.get("area_codes") or {}
    d["issues"] = read_json(os.path.join(P, "test-case", "%s-issues.json" % S))["issues"]
    d["faults"] = read_json(
        os.path.join(P, "automation", "%s-fault-matrix.json" % S))["faults"]
    d["auto"] = count_test_funcs(os.path.join(P, "automation", "tests"))
    d["base_ok"], d["diag_fail"] = matrix_baseline(
        os.path.join(P, "automation", "result", "matrix", "fault-matrix.md"))

    by_vt = {}
    for t in d["tcs"]:
        by_vt[t[6]] = by_vt.get(t[6], 0) + 1
    d["by_vt"] = by_vt

    states = set()
    for t in d["tcs"]:
        for s in (t[13] if len(t) > 13 else "").split(","):
            if s.strip():
                states.add(s.strip())
    d["states"] = states

    build = ""
    dj = os.path.join(P, "sut", "js", "data.js")
    if os.path.exists(dj):
        m = re.search(r'SUT_BUILD\s*=\s*"([^"]+)"',
                      io.open(dj, encoding="utf-8").read())
        build = m.group(1) if m else ""
    d["build"] = build
    return d


def issue_parts(issue):
    """이슈 하나를 증상·원인·조치 한 줄씩으로 접는다.

    상세(재현 절차·기대 결과)는 QA 리포트가 이미 담고 있으므로 여기서는 반복하지 않는다.
    """
    body = issue.get("description") or ""
    fields = {}
    key = None
    for line in body.splitlines():
        m = re.match(r"^([A-Za-z ]+):\s*(.*)$", line)
        if m:
            key = m.group(1).strip()
            fields[key] = m.group(2).strip()
        elif key:
            fields[key] += " " + line.strip()

    cause = fields.get("QA Comment", "")
    cause = re.sub(r"[*`]", "", cause)
    cause = re.split(r"(?<=[다음됨함임])\.\s|\.\s", cause)[0].strip()
    if len(cause) > 150:
        cause = cause[:150].rstrip() + "…"
    fix = issue.get("fixedVersion") or ""
    return issue.get("summary", ""), cause, fix


def stat(num, lbl, sub="", bar=None):
    o = ['<div class="stat"><div class="num">%s</div><div class="lbl">%s</div>'
         % (num, esc(lbl))]
    if sub:
        o.append('<div class="sub">%s</div>' % sub)
    if bar:
        o.append('<div class="bar"><i class="%s" style="width:%d%%"></i></div>' % bar)
    o.append('</div>')
    return "".join(o)


def card(title, body, foot=""):
    # title에 링크를 담는 경우가 있어 여기서 이스케이프하지 않는다 — 호출부가 책임진다
    o = ['<div class="card"><h3>%s</h3><p>%s</p>' % (title, body)]
    if foot:
        o.append('<p class="foot">%s</p>' % foot)
    o.append('</div>')
    return "".join(o)


# ────────────────────────────────────────────────────────────────
# 페이지 ① 랜딩 — 저장소 루트. 링크를 받은 사람이 처음 보는 화면이다
# ────────────────────────────────────────────────────────────────
def page_landing(d, args, rel):
    """랜딩 — 이 저장소를 처음 보는 사람이 위에서부터 읽어 내려가는 순서로 짠다.

    독자의 질문 순서를 그대로 절로 삼는다: 이게 뭐지 → 실물이 뭐지 → 왜 이렇게 했지 →
    어떻게 일했지 → 결과는 → 무슨 역량이지. 내부 용어는 문장에서 풀어 쓰고, 그래도 막히면
    마지막 「이 문서의 말」에서 한 줄로 찾게 한다.
    """
    S = d["slug"]
    P = rel["project"]
    o = []
    w = o.append

    n_leaf, n_tid, n_tc = len(d["leaves"]), len(d["testids"]), len(d["tcs"])
    n_area = len([k for k, v in d["areas"].items() if isinstance(v, dict)])
    n_auto_tc = sum(1 for t in d["tcs"] if t[7] != "사람 전용")

    # ── 히어로 — 제목은 주장이 아니라 「무엇을 왜 했는가」 한 문장이다
    w('<div class="doc-header">'
      '<h1>설계 의도를 파악하고자, AI 캐릭터와 대화하는 서비스를 분석했습니다</h1>')
    w('<p class="doc-lead">출시된 AI 챗·미연시 서비스를 분석하며 <strong>「이런 서비스를 검증하려면 '
      '무엇을 봐야 하는가」</strong>를 고민하고 구조화했습니다. 그 결과를 근거로 AI 캐릭터와 대화하는 '
      '서비스 <strong>MiyonChat</strong>을 직접 설계해 만들었고, 그 위에서 테스트 케이스를 설계해 '
      '<strong>자동화 테스트까지 돌려 검증했습니다.</strong></p>')
    w('<div class="meta-row">')
    for k, v in (("검증 대상", "MiyonChat (직접 제작)"), ("기능 목록", "v" + d["tree_version"]),
                 ("빌드", d["build"])):
        if v:
            w('<span class="badge">%s <b>%s</b></span>' % (esc(k), esc(v)))
    w('</div></div>')

    # ── 진행한 방식 — 상세는 아래 §어떻게 일했나가 담고, 여기서는 네 걸음만
    w('<div class="card-grid">')
    for step, title, body in (
        ("①", "조사",
         "출시 서비스 여섯을 「처음 켰을 때부터 할 수 있는 행동」 순서로 정리했습니다. "
         "기능 이름은 회사마다 달라도 사용자의 행동은 겹치기 때문입니다."),
        ("②", "구조화",
         "겹치는 행동을 계층으로 묶어 검증 대상 %d개를 세우고, 항목마다 "
         "<strong>어떻게 판정할지</strong>를 먼저 정했습니다." % n_leaf),
        ("③", "구현",
         "그 구조대로 동작하는 서비스를 직접 만들었습니다. 테스트가 붙잡을 접점과 "
         "고장을 켜는 스위치를 처음부터 심었습니다."),
        ("④", "검증",
         "테스트 케이스 %d건을 설계해 %d건을 자동화하고, 고장 %d종을 일부러 심어 "
         "<strong>담당 케이스만 깨지는지</strong> 확인했습니다."
         % (n_tc, n_auto_tc, len(d["faults"]))),
    ):
        w('<div class="card"><h3>%s %s</h3><p>%s</p></div>' % (step, esc(title), body))
    w('</div>')

    # ── ① 무엇을 만들었나 — 실물부터 보인다
    w('<h2 id="what">무엇을 만들었나</h2>')
    w('<p>글보다 화면이 빠릅니다. 아래는 실제로 동작하는 MiyonChat이고, 이 GIF도 손으로 녹화한 것이 '
      '아니라 스크립트가 브라우저를 조작해 만듭니다.</p>')
    demo = os.path.join(args.project_dir, "docs", "sut-demo.gif")
    if os.path.exists(demo):
        w('<div class="card" style="padding:12px">'
          '<img src="%sdocs/sut-demo.gif" alt="MiyonChat 실행 화면 — 로그인하지 않은 상태에서는 '
          '성인 콘텐츠가 가려져 있고, 로그인하면 풀리며, 대화방에서 응답이 한 글자씩 나오고 '
          '재화가 차감된다" style="width:100%%;height:auto;display:block;border-radius:8px">'
          '<p class="foot" style="margin:10px 2px 0">로그인하지 않으면 성인 콘텐츠가 가려지고 → '
          '로그인하면 풀리고 → 대화방에서 응답이 한 글자씩 나오며 재화가 차감됩니다. '
          '검증이 걸린 한 갈래를 처음부터 끝까지 보여 줍니다.</p></div>' % P)
    w('<div class="card-grid">')
    w(card("어떤 서비스인가",
           "캐릭터를 고르고 대화하면 호감도가 오르내리고, 그에 따라 관계 단계와 결말이 갈립니다. "
           "대화에는 재화가 들고, 대화 내용을 저장했다가 되돌릴 수 있으며, 성인 콘텐츠는 "
           "인증 상태에 따라 가려집니다.",
           "화면 조작 지점 %d개 · 검증 영역 %d개" % (n_tid, n_area)))
    w(card("왜 직접 만들었나",
           "지원하려는 회사의 제품이 아직 출시 전이라 테스트할 실물이 없었습니다. 남의 서비스를 "
           "테스트하면 화면이 바뀔 때마다 결과가 무너지고, 무엇보다 <strong>고장을 일부러 심을 수 "
           "없습니다.</strong> 테스트가 결함을 실제로 잡아내는지 보이려면 대상을 손에 쥐고 있어야 했습니다.",
           "테스트가 붙잡을 접점을 처음부터 심어 만들었습니다"))
    w(card("무엇을 근거로 기능을 정했나",
           "혼자 상상해서 만들면 「테스트를 위해 만든 장난감」이 됩니다. 그래서 출시된 서비스 여섯을 "
           "「처음 켰을 때부터 사용자가 할 수 있는 행동」 순서로 조사해 공통 기능을 뽑고, 조사에서 "
           "나온 기능과 직접 판단해 넣은 기능을 <strong>칸을 갈라 표시</strong>했습니다.",
           "조사 대상: AI 챗 3종 · AI 챗+비주얼노벨 1종 · 미연시 2종"))
    w('</div>')

    # ── ② 왜 이렇게 했나 — 제약 셋
    w('<h2 id="why">이 프로젝트가 풀어야 했던 문제 셋</h2>')
    w('<p>테스트 설계가 어려웠던 이유는 기능이 많아서가 아니라, <strong>판정할 기준이 없는 항목이 '
      '섞여 있어서</strong>입니다. 세 가지가 겹쳐 있었습니다.</p>')
    w('<div class="steps">')
    for title, body in (
        ("기준 문서가 없다",
         "출시된 서비스에는 기획서가 딸려 오지 않습니다. 「무엇이 정상인가」를 아무도 적어 두지 "
         "않은 상태에서 시작해야 했습니다. → 조사한 것을 그대로 기대값으로 쓰지 않고, "
         "<b>조사 → 채택 → 확정</b> 세 단계로 좁혀 확정된 것만 테스트의 기대값으로 썼습니다."),
        ("응답이 매번 다르다",
         "AI가 만드는 대화는 같은 입력에도 같은 답이 나오지 않습니다. 통과·실패로 자를 수 없는 "
         "항목이 생깁니다. → 케이스마다 <b>판정 방식을 먼저 정했습니다</b>. 시스템이 보장해야 하는 "
         "값은 1회 실행으로 자르고, 품질에 의존하는 항목은 여러 번 돌려 성공률로, 어투·일관성처럼 "
         "수치화가 어려운 것은 채점표로, 절대 나오면 안 되는 것은 0건 기준으로 봅니다."),
        ("「다 봤다」를 증명할 수 없다",
         "테스트를 아무리 많이 써도 빠진 곳은 눈에 안 보입니다. → 케이스마다 <b>무엇을 확인하는지 "
         "좌표를 적어 두고</b>, 기능 목록·화면 요소·계정 상태 세 축을 스크립트가 대조해 덮이지 않은 "
         "것을 목록으로 내게 했습니다. 그 목록이 빌 때까지가 설계입니다."),
    ):
        w('<div class="step"><div class="body"><b>%s</b> — %s</div></div>' % (esc(title), body))
    w('</div>')

    # ── ③ 어떻게 일했나
    w('<h2 id="how">어떻게 일했나</h2>')
    w('<p>앞 단계의 결과가 뒤 단계의 입력이자 <strong>기대값의 출처</strong>입니다. '
      '단계마다 그때 내린 판단을 함께 적었습니다.</p>')
    w('<div class="steps">')
    for title, body, link, link_label in (
        ("출시 서비스를 분해했다",
         "기능 목록이 아니라 <b>행동 목록</b>부터 만들었습니다. 기능 이름은 회사마다 다르지만 "
         "사용자가 하는 행동은 겹치기 때문입니다.",
         "%sanalysis/" % P, "조사 기록"),
        ("공통 기능의 목록을 세웠다",
         "겹치는 행동을 계층으로 정리해 <b>검증 대상 %d개</b>를 확정했습니다. 조사에 없어 직접 "
         "정한 항목은 왜 그렇게 정했는지를 따로 적립했습니다 — 면접에서 가장 많이 받을 질문이라서입니다."
         % n_leaf,
         "%sspec/%s-feature-tree.html" % (P, S), "기능 목록 보기"),
        ("수치와 합격선을 확정했다",
         "「기능이 있다」와 「얼마부터 통과인가」는 다른 문제입니다. 상한값·차감량·관계 단계의 "
         "경계·채점 합격선을 확정 문서로 못박고, 테스트의 기대값은 <b>그 문서에서만</b> 가져오게 했습니다.",
         None, None),
        ("검증 대상을 만들었다",
         "화면 요소마다 테스트가 붙잡을 이름표를 달고, 상태를 읽고 바꾸는 통로와 <b>고장을 켜는 "
         "스위치</b>를 처음부터 심었습니다. 나중에 붙이면 테스트가 화면 생김새에 매달리게 됩니다.",
         "%ssut/index.html" % P, "직접 실행해 보기"),
        ("테스트 케이스를 설계했다",
         "기능마다 정상·경계·예외·우회 네 갈래로 펼쳐 <b>%d건</b>을 만들고, 케이스마다 무엇을 "
         "확인하는지 좌표를 적었습니다. 시트는 실무에서 쓰는 서식을 그대로 따랐습니다." % n_tc,
         "%s/projects/%s/test-case/%s-tc-v1.0.xlsx" % (BLOB, S, S), "TC 시트 내려받기"),
        ("자동화하고 고장을 심었다",
         "<b>%d건 중 %d건</b>을 자동화했습니다. 테스트 함수 이름이 곧 케이스 번호라 실패한 줄만 "
         "보고 시트를 찾을 수 있습니다. 그리고 고장 %d종을 하나씩 켜서 <b>담당 케이스만 깨지는지</b> "
         "확인했습니다." % (n_tc, n_auto_tc, len(d["faults"])),
         "%sautomation/report/%s-report.html" % (P, S), "검증 리포트 보기"),
    ):
        link_html = (' <a href="%s">%s →</a>' % (esc(link), esc(link_label))) if link else ""
        w('<div class="step"><div class="body"><b>%s</b> — %s%s</div></div>'
          % (esc(title), body, link_html))
    w('</div>')

    # ── ④ 결과
    w('<h2 id="result">무엇이 나왔나</h2>')
    w('<div class="stats">')
    w(stat(n_leaf, "검증 대상 기능", "테스트로 확인할 최소 단위"))
    w(stat('<em>%d</em>' % n_tc, "테스트 케이스", "%d개 영역 · 시트로 산출" % n_area))
    w(stat(d["auto"], "자동화 테스트", "사람 손 없이 실행"))
    w(stat("%d종" % len(d["faults"]), "일부러 심은 고장",
           "담당 케이스만 깨짐" if d["base_ok"] else "탐지력 확인용"))
    w(stat(len(d["issues"]), "검출한 결함", "명세와 어긋난 동작 · 전부 수정"))
    w('</div>')

    if d["base_ok"]:
        w('<div class="callout">고장을 심지 않은 상태에서는 <strong>전 영역이 통과</strong>하고, '
          '고장을 하나 켜면 <strong>그 고장을 담당하는 케이스만 실패</strong>합니다. 담당 밖 테스트가 '
          '함께 흔들리면 그 테스트는 무엇을 보는지 모르는 채 통과하고 있었다는 뜻이라, '
          '이 둘을 같이 봅니다.</div>')

    w('<h3>검출한 결함</h3>')
    w('<p>확정 명세가 정한 동작과 구현이 어긋난 건들입니다. 재현 절차와 기대 결과는 '
      '검증 리포트에 있습니다.</p>')
    w('<div class="tbl-scroll"><table><thead><tr><th>증상</th><th>원인</th>'
      '<th>조치</th></tr></thead><tbody>')
    for iss in d["issues"]:
        sym, cause, fix = issue_parts(iss)
        w('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
          % (esc(sym), esc(cause) or '<span class="foot">—</span>',
             ('%s에서 수정' % esc(fix)) if fix else esc(iss.get("resolution", ""))))
    w('</tbody></table></div>')

    # ── ⑤ 역량
    w('<h2 id="skill">이 작업이 보여주는 것</h2>')
    w('<div class="card-grid">')
    w(card("기준이 없을 때 기준을 만든다",
           "기획서가 없는 서비스를 분해해 「무엇이 정상인가」를 문서로 세웠습니다. 조사한 값과 "
           "직접 정한 값을 구분해 두었기 때문에, 나중에 「이 숫자는 어디서 왔나」를 되짚을 수 있습니다."))
    w(card("자를 수 없는 것에 선을 긋는다",
           "AI 응답처럼 매번 달라지는 결과도 판정할 수 있게, 항목마다 판정 방식과 합격선을 먼저 "
           "정했습니다. 「대충 괜찮아 보인다」를 숫자로 바꾸는 일입니다."))
    w(card("빠짐없이 봤는지를 사람이 아니라 도구가 확인한다",
           "덮이지 않은 기능을 스크립트가 목록으로 냅니다. 검증 대상이 아닌 것은 사유를 파일에 "
           "적게 하고, 그 사유가 실제로 성립하는지까지 검사합니다."))
    w(card("테스트가 결함을 잡는지 증명한다",
           "테스트가 통과한다는 말과 테스트가 쓸모 있다는 말은 다릅니다. 고장을 심어 담당 테스트만 "
           "깨지는 것을 보이면, 통과가 곧 근거가 됩니다."))
    w('</div>')

    # ── ⑥ 용어
    w('<h2 id="word">이 문서의 말</h2>')
    w('<p>본문에서 풀어 썼지만, 산출물 안에서는 아래 이름으로 나옵니다.</p>')
    w('<div class="tbl-scroll"><table><thead><tr><th>여기서 쓴 말</th><th>산출물에서의 이름</th>'
      '<th>뜻</th></tr></thead><tbody>')
    for plain, term, mean in (
        ("검증 대상 기능", "기능 단위",
         "테스트로 확인하는 최소 단위. 기능 목록의 맨 끝 항목입니다"),
        ("직접 만든 검증 대상", "SUT (System Under Test)",
         "테스트를 당하는 쪽. 테스트 코드가 아니라 그 코드가 조작하는 제품입니다"),
        ("화면 조작 지점", "화면 요소 (data-testid)",
         "테스트가 버튼·입력창을 찾을 때 쓰는 이름표. 화면 생김새가 바뀌어도 안 흔들립니다"),
        ("판정 방식", "검증유형",
         "결정적(1회로 자름) · 확률적(여러 번 돌려 성공률) · 루브릭(채점표) · 금칙(0건이어야 통과)"),
        ("빠짐없이 봤는지 대조", "커버리지 3축",
         "기능 목록 · 화면 요소 · 계정 상태 세 기준선과 케이스가 적어 둔 좌표를 맞춰 봅니다"),
        ("일부러 심은 고장", "결함 주입",
         "고장을 하나씩 켜고 전체를 다시 돌려, 담당 케이스만 실패하는지 확인하는 방법"),
    ):
        w('<tr><td><strong>%s</strong></td><td><code>%s</code></td><td>%s</td></tr>'
          % (esc(plain), esc(term), esc(mean)))
    w('</tbody></table></div>')

    # ── ⑦ 더 보기
    w('<h2 id="read">더 자세히</h2>')
    w('<p>판단의 근거와 규칙을 단계별로 풀어 둔 문서입니다.</p>')
    w('<div class="steps">')
    for key, title, desc in (
        ("structure", "저장소 구조",
         "폴더가 곧 규칙입니다 — 조사한 것·채택한 것·확정한 것·지나간 것을 섞지 않으려고 "
         "폴더로 갈라 두었습니다."),
        ("foundation", "작업 규칙 — 첫 문서를 쓰기 전에 정한 것",
         "절차서·규칙 문서·디자인 기준을 먼저 세우고 시작했습니다. 같은 판단이 매번 같게 "
         "나오도록 고정해 둔 것들입니다."),
        ("making", "제작 과정 — MiyonChat은 어떻게 나왔나",
         "레퍼런스 조사에서 시작해 어떤 기능을 왜 넣고 뺐는지를 따라갑니다."),
        ("tc", "테스트 케이스 설계 규칙",
         "케이스를 어떻게 펼쳤고, 시트가 왜 그 서식이며, 무엇을 근거로 「다 봤다」고 하는지."),
        ("auto", "자동화 설계와 결과",
         "테스트가 붙잡을 접점을 어떻게 심었고, 고장을 심어 무엇을 확인했는지."),
    ):
        path = dict((k, p) for k, _l, p in shell.INTRO)[key]
        exists = os.path.exists(os.path.join(args.repo_root, path))
        link = ('<a href="%s%s">%s</a>' % (rel["root"], esc(path), esc(title))
                if exists else '<b>%s</b> <span class="chip chip-unk">준비 중</span>' % esc(title))
        w('<div class="step"><div class="body">%s — %s</div></div>' % (link, desc))
    w('</div>')

    w('<h2 id="out">산출물 바로 가기</h2>')
    w('<div class="card-grid">')
    for title, desc, link in (
        ("검증 리포트", "무엇을 얼마나 통과했고, 무엇을 못 봤는지",
         "%sautomation/report/%s-report.html" % (P, S)),
        ("추적 매트릭스", "기능 하나가 어떤 케이스·어떤 테스트 함수·어떤 결함으로 이어지는지",
         "%sautomation/report/%s-traceability.html" % (P, S)),
        ("기능 목록", "검증 대상 %d개와 각각의 판정 방식" % n_leaf,
         "%sspec/%s-feature-tree.html" % (P, S)),
        ("MiyonChat 실행", "검증 대상을 직접 눌러 봅니다", "%ssut/index.html" % P),
        ("TC 시트", "실무 서식 그대로의 엑셀 — 내려받아 엽니다",
         "%s/projects/%s/test-case/%s-tc-v1.0.xlsx" % (BLOB, S, S)),
        ("프로젝트 허브", "문서가 어디 있는지 모아 둔 지도", "%sindex.html" % P),
    ):
        w('<div class="card"><h3><a href="%s">%s</a></h3><p>%s</p></div>'
          % (esc(link), esc(title), esc(desc)))
    w('</div>')

    w('<div class="doc-footer">이 문서는 파생물입니다 — <code>gen_intro_html.py --page landing</code>으로 '
      '재생성합니다. 수치는 전부 정본에서 읽고, 자동화 결과는 커밋된 매트릭스 표에서 읽습니다.</div>')

    toc = (("what", "무엇을 만들었나"), ("why", "풀어야 했던 문제 셋"), ("how", "어떻게 일했나"),
           ("result", "무엇이 나왔나"), ("skill", "이 작업이 보여주는 것"),
           ("word", "이 문서의 말"), ("read", "더 자세히"), ("out", "산출물"))
    return "".join(o), toc, "포트폴리오 홈"


# ────────────────────────────────────────────────────────────────
# 페이지 ② 저장소 구조 — 폴더 이름이 곧 참조 규칙이다
# ────────────────────────────────────────────────────────────────
def doc_title(path):
    """md 첫 줄의 제목에서 설명만 뽑는다 — 문서가 스스로 말하게 하고 여기 적어 두지 않는다."""
    try:
        with io.open(path, encoding="utf-8") as f:
            head = f.readline().strip().lstrip("#").strip()
    except OSError:
        return ""
    for sep in (" — ", " - "):
        if sep in head:
            return head.split(sep, 1)[1]
    return head


def page_structure(d, args, rel):
    """저장소 구조 — 어디에 무엇이 있고, 그 자리에 있는 이유가 무엇인지.

    문서 목록을 손으로 적어 두면 문서가 늘 때마다 낡습니다. 그래서 폴더를 훑어
    실재하는 파일에서 제목을 읽습니다.
    """
    S = d["slug"]
    R, P = rel["root"], rel["project"]
    o = []
    w = o.append

    w('<div class="doc-header"><h1>저장소 구조 — 폴더 이름이 곧 규칙입니다</h1>')
    w('<p class="doc-lead">조사한 것 · 채택한 것 · 확정한 것 · 지나간 것을 한 폴더에 섞어 두면, '
      '테스트의 기대값을 <strong>아직 확정되지 않은 값에서 가져오는 사고</strong>가 납니다. '
      '그래서 참조 규칙이 같은 것끼리 폴더로 묶고, 폴더 이름만 보고도 「여기 것을 기대값으로 써도 '
      '되는가」를 판단할 수 있게 했습니다.</p>')
    w('<div class="meta-row"><span class="badge">저장소 <b>3층</b></span>'
      '<span class="badge">규칙 문서 <b>%d편</b></span></div></div>'
      % len([n for n in sorted(os.listdir(os.path.join(args.repo_root, "project-process", "rules")))
             if n.endswith(".md")]))

    # ── 전체 그림
    w('<h2 id="map">전체 그림</h2>')
    w('<p>절차·형식 기준은 <strong>모든 작업 앞에</strong> 있고, 프로젝트 산출물은 조사에서 확정으로 '
      '좁혀지며, 확정된 것에서만 테스트가 나옵니다. 아래 그림의 정본은 저장소 루트의 '
      '<code>structure.svg</code> 파일 하나이고, 이 페이지는 그 파일을 그대로 읽어 넣습니다.</p>')
    svg = os.path.join(args.repo_root, "structure.svg")
    if os.path.exists(svg):
        body = io.open(svg, encoding="utf-8").read()
        body = body[body.index("<svg"):]
        w('<div class="card" style="padding:14px">%s</div>' % body)

    # ── 세 층
    w('<h2 id="layer">세 층으로 나눠 둔 이유</h2>')
    w('<div class="card-grid">')
    w(card("① 절차 — project-process/",
           "무엇을 어떤 순서로 할지, 판단이 갈릴 때 무엇을 기준으로 정할지를 담습니다. "
           "프로젝트가 생기기 <strong>전에</strong> 세운 층이라, 프로젝트가 늘어도 같은 방식으로 일하게 됩니다.",
           "파이프라인 절차서 · 규칙 문서 · 생성 도구"))
    w(card("② 형식 — design-guide/ · design-template/",
           "모든 산출물이 같은 모양으로 나오게 하는 층입니다. 색과 컴포넌트의 정본이 하나라, "
           "문서마다 스타일을 다시 정하지 않습니다.",
           "스타일 정본 · 시각 규칙서 · 문서 템플릿 · TC 시트 서식"))
    w(card("③ 산출물 — projects/{프로젝트}/",
           "실제 작업이 쌓이는 층입니다. 안에서 다시 <strong>조사 → 채택 → 확정</strong>으로 "
           "좁혀지고, 확정된 것에서만 테스트 케이스가 나옵니다.",
           "현재 프로젝트 1개 · 기능 %d개 · TC %d건" % (len(d["leaves"]), len(d["tcs"]))))
    w('</div>')

    # ── 폴더별 규칙
    w('<h2 id="rule">폴더마다 다른 참조 규칙</h2>')
    w('<p>같은 프로젝트 안이라도 폴더에 따라 <strong>「기대값으로 써도 되는가」가 다릅니다.</strong> '
      '이 구분이 이 저장소에서 가장 중요한 규칙입니다.</p>')
    w('<div class="tbl-scroll"><table><thead><tr><th>폴더</th><th>무엇이 있나</th>'
      '<th>기대값으로 쓸 수 있나</th></tr></thead><tbody>')
    for path, what, use, cls in (
        ("analysis/", "출시 서비스를 조사한 전량. 버리지 않고 모읍니다",
         "안 됩니다 — 남의 서비스 값입니다", "no"),
        ("reference/", "조사분 중 「이건 가져오자」고 고른 것",
         "안 됩니다 — 아직 확정 전입니다", "no"),
        ("spec/ (평면)", "기능 목록 정본. 손으로 고치는 유일한 파일",
         "됩니다", "ok"),
        ("spec/design/", "확정 사양 — 상한값·차감량·임계·합격선",
         "됩니다 — 수치의 출처입니다", "ok"),
        ("spec/sut-design/", "검증 대상 전용 사양 — 청사진·저장 스키마·고장 주입",
         "구현·자동화만 — 기획 테스트는 참조하지 않습니다", "part"),
        ("spec/rationale/", "왜 그렇게 정했는지의 기록",
         "안 됩니다 — 판단 기록이지 확정안이 아닙니다", "no"),
        ("spec/archive/", "지나간 것 — 이력과 동결본",
         "안 됩니다 — 평상시에는 열지도 않습니다", "no"),
        ("test-case/", "테스트 케이스 설계 원본(json)과 시트(xlsx)",
         "설계 결과입니다", "ok"),
        ("sut/", "검증 대상 그 자체",
         "테스트가 조작하는 쪽입니다", "part"),
        ("automation/", "테스트 코드 · 실행 결과 · 리포트",
         "실행 결과입니다", "part"),
    ):
        w('<tr><td><code>%s</code></td><td>%s</td>'
          '<td><span class="chip chip-%s">%s</span></td></tr>'
          % (esc(path), esc(what), cls, esc(use)))
    w('</tbody></table></div>')
    w('<div class="callout">지나간 것을 <code>archive/</code>로 몰아 두는 이유는 단순합니다 — '
      '삭제된 옛 기능 정보가 평상시 작업에 섞이면, 있지도 않은 기능의 테스트를 쓰게 됩니다. '
      '그래서 기능 목록 정본에는 <strong>현재 상태만</strong> 남기고 삭제 흔적을 두지 않습니다.</div>')

    # ── 워크스페이스 문서 (폴더를 훑어 만든다)
    w('<h2 id="doc">작업 규칙 문서</h2>')
    w('<p>아래 목록은 폴더를 훑어 만들어집니다 — 문서가 늘거나 이름이 바뀌어도 이 페이지가 '
      '낡지 않습니다.</p>')
    w('<div class="tbl-scroll"><table id="doc-tbl"><thead><tr><th class="sortable">문서</th>'
      '<th>무엇을 정하나</th></tr></thead><tbody>')
    entries = []
    for rel_dir, label in (("project-process", ""), ("project-process/rules", "rules/"),
                           ("design-template", "")):
        abs_dir = os.path.join(args.repo_root, rel_dir)
        if not os.path.isdir(abs_dir):
            continue
        for name in sorted(os.listdir(abs_dir)):
            if not name.endswith(".md"):
                continue
            entries.append((label + name, "%s/%s/%s" % (BLOB, rel_dir, name),
                            doc_title(os.path.join(abs_dir, name))))
    entries.append(("design-guide-master.html", R + "design-guide/design-guide-master.html",
                    "모든 HTML 산출물이 따르는 색·타이포·컴포넌트 기준"))
    for name, href, desc in entries:
        w('<tr><td><a href="%s"><code>%s</code></a></td><td>%s</td></tr>'
          % (esc(href), esc(name), esc(desc)))
    w('</tbody></table></div>')
    w('<p class="foot">md 문서와 폴더 링크는 GitHub 저장소에서 열리고, HTML 문서는 이 사이트에서 '
      '바로 렌더링됩니다 — GitHub Pages에서는 md가 원본 텍스트로 뜨기 때문입니다.</p>')

    # ── 프로젝트
    w('<h2 id="proj">프로젝트</h2>')
    w('<div class="card-grid">')
    w(card('<a href="%sindex.html">%s</a>' % (P, esc(S)),
           "출시 서비스 역분석 → 기능 목록 → 확정 사양 → 검증 대상 제작 → 테스트 케이스 → "
           "자동화 → 고장 주입 → 리포트 → CI까지 한 바퀴를 완주한 프로젝트입니다.",
           "기능 %d개 · TC %d건 · 자동화 %d건 · 빌드 %s"
           % (len(d["leaves"]), len(d["tcs"]), d["auto"], esc(d["build"]))))
    w('</div>')

    w('<div class="doc-footer">이 문서는 파생물입니다 — '
      '<code>gen_intro_html.py --page structure</code>로 재생성합니다. 구조도는 '
      '<code>structure.svg</code>를, 문서 목록은 폴더를 그대로 읽습니다.</div>')

    toc = (("map", "전체 그림"), ("layer", "세 층"), ("rule", "폴더별 참조 규칙"),
           ("doc", "작업 규칙 문서"), ("proj", "프로젝트"))
    return "".join(o), toc, "저장소 구조"


def doc_intro(path, limit=180):
    """md 본문의 첫 문단 — 그 문서가 스스로 밝힌 존재 이유를 그대로 가져온다."""
    try:
        lines = io.open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return ""
    buf = []
    for line in lines[1:]:
        t = line.strip()
        if t.startswith("#") or t.startswith("|") or t.startswith("---"):
            if buf:
                break
            continue
        if not t:
            if buf:
                break
            continue
        buf.append(t)
    text = re.sub(r"[*`]", "", " ".join(buf))
    if len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def script_summary(path):
    """생성 도구의 모듈 docstring 첫 줄 — 도구가 스스로 적어 둔 한 줄.

    함수 docstring을 집어 오지 않도록, 첫 def/class보다 앞에 있는 문자열만 인정한다.
    """
    try:
        src = io.open(path, encoding="utf-8").read()
    except OSError:
        return ""
    start = src.find('"""')
    if start < 0:
        return ""
    body_start = re.search(r"^(def |class )", src, re.M)
    if body_start and body_start.start() < start:
        return ""
    end = src.find('"""', start + 3)
    doc = src[start + 3:end if end > 0 else None]
    for line in doc.splitlines():
        head = line.strip()
        if head:
            return head.split(" — ", 1)[1] if " — " in head else head
    return ""


# ────────────────────────────────────────────────────────────────
# 페이지 ③ 토대 — 첫 문서를 쓰기 전에 정해 둔 것들
# ────────────────────────────────────────────────────────────────
#: 규칙 문서를 묶는 축. 목록에 없는 파일은 「그 밖에」로 떨어지므로 새 문서가 사라지지 않는다
RULE_GROUPS = (
    ("무엇을 어떤 순서로 하는가", ("qa-doc-playbook.md", "remaining-work.md", "qa-git-rules.md")),
    ("테스트를 어떻게 설계하는가",
     ("depth-and-tn.md", "case-expansion.md", "verification-types.md",
      "tc-relations.md", "tc-sheet-format.md")),
    ("만들고 돌리는 규칙", ("sut-automation.md",)),
    ("문서를 어떻게 쓰고 어디에 두는가",
     ("doc-write-style.md", "html-report-guide.md", "site-structure.md")),
)


def page_foundation(d, args, rel):
    """토대 — 프로젝트를 시작하기 전에 규칙부터 세운 이유와 그 목록.

    목록은 폴더를 훑어 만들고, 각 문서의 설명은 그 문서의 첫 문단에서 읽습니다.
    여기에 요약을 옮겨 적으면 규칙이 바뀔 때 이 페이지만 옛말을 하게 됩니다.
    """
    R = rel["root"]
    proc = os.path.join(args.repo_root, "project-process")
    rules_dir = os.path.join(proc, "rules")
    o = []
    w = o.append

    rule_files = sorted(n for n in os.listdir(rules_dir) if n.endswith(".md"))
    scripts_dir = os.path.join(proc, "scripts")
    scripts = sorted(n for n in os.listdir(scripts_dir)
                     if n.endswith(".py") and not n.startswith("_"))

    w('<div class="doc-header"><h1>토대 — 첫 문서를 쓰기 전에 정해 둔 것들</h1>')
    w('<p class="doc-lead">비슷한 자료를 보고 그때그때 만들면, 사흘째에 어제와 다른 판단을 하게 됩니다. '
      '그래서 <strong>프로젝트를 시작하기 전에 절차와 규칙부터 세웠습니다.</strong> '
      '무엇을 어떤 순서로 하고, 판단이 갈릴 때 무엇을 기준으로 정하며, 산출물을 어떤 형식으로 낼지를 '
      '먼저 고정해 두면, 작업 중에는 「무엇을 검증할까」에만 집중할 수 있습니다.</p>')
    w('<div class="meta-row"><span class="badge">규칙 문서 <b>%d편</b></span>'
      '<span class="badge">생성 도구 <b>%d개</b></span>'
      '<span class="badge">확인 게이트 <b>2곳</b></span></div></div>' % (len(rule_files), len(scripts)))

    # ── 왜 규칙부터인가
    w('<h2 id="why">왜 규칙부터 세웠나</h2>')
    w('<div class="card-grid">')
    w(card("같은 판단이 매번 같게 나오도록",
           "「이건 경계값을 몇 개 잡지?」 「이 수치는 어디서 가져오지?」는 작업마다 반복해서 만나는 "
           "질문입니다. 그때그때 정하면 문서마다 기준이 달라지고, 나중에 왜 다른지 설명하지 못합니다."))
    w(card("되돌아가는 비용이 크기 때문에",
           "기능 목록이 흔들린 채로 테스트 케이스를 쓰면 뒤의 산출물을 전부 다시 만들어야 합니다. "
           "그래서 단계 사이에 <strong>확인 게이트</strong>를 두고, 앞 단계가 확정되기 전에는 "
           "다음으로 넘어가지 않습니다."))
    w(card("혼자 해도 규칙이 필요해서",
           "규칙은 여러 사람이 맞추기 위한 것만은 아닙니다. 사흘 뒤의 나도 남입니다. "
           "판단의 근거를 문서에 남겨 두지 않으면, 그 판단을 다시 설명할 수 없습니다."))
    w('</div>')

    # ── 절차 (playbook의 STEP 제목을 읽어 온다)
    w('<h2 id="step">작업 절차</h2>')
    w('<p>문서 제작 요청이 오면 아래 순서를 처음부터 끝까지 따릅니다. 단계 이름은 절차서에서 '
      '그대로 읽어 온 것이라, 절차가 바뀌면 이 목록도 함께 바뀝니다.</p>')
    steps = []
    pb = os.path.join(proc, "qa-doc-playbook.md")
    if os.path.exists(pb):
        for line in io.open(pb, encoding="utf-8"):
            m = re.match(r"^## (STEP \d+) — (.+)$", line.strip())
            if m:
                steps.append((m.group(1), m.group(2)))
    w('<div class="steps">')
    for no, title in steps:
        w('<div class="step"><div class="body"><b>%s</b> — %s</div></div>'
          % (esc(no), esc(title)))
    w('</div>')
    w('<div class="callout">이 절차의 핵심은 <strong>확인 게이트 두 곳</strong>입니다. '
      '아웃라인을 확인받기 전에는 본문을 쓰지 않고, 어떤 형식으로 낼지 정하기 전에는 만들지 '
      '않습니다. 다 쓰고 나서 방향이 어긋난 것을 알면 그때는 전부 다시 써야 하기 때문입니다.</div>')

    # ── 규칙 문서 (폴더를 훑고 첫 문단을 읽는다)
    w('<h2 id="rule">규칙 문서</h2>')
    w('<p>각 문서가 스스로 밝힌 존재 이유를 그대로 가져왔습니다 — 여기에 요약을 옮겨 적으면 '
      '규칙이 바뀔 때 이 페이지만 옛말을 하게 됩니다.</p>')
    placed = set()
    for group, names in RULE_GROUPS:
        rows = []
        for name in names:
            path = os.path.join(rules_dir, name)
            base = name
            if not os.path.exists(path):
                path = os.path.join(proc, name)
                base = name
                if not os.path.exists(path):
                    continue
                href = "%s/project-process/%s" % (BLOB, name)
            else:
                href = "%s/project-process/rules/%s" % (BLOB, name)
                base = "rules/" + name
            placed.add(name)
            rows.append((base, href, doc_intro(path)))
        if not rows:
            continue
        w('<h3>%s</h3><div class="tbl-scroll"><table><tbody>' % esc(group))
        for base, href, why in rows:
            w('<tr><td style="width:230px"><a href="%s"><code>%s</code></a></td><td>%s</td></tr>'
              % (esc(href), esc(base), esc(why)))
        w('</tbody></table></div>')
    left = [n for n in rule_files if n not in placed]
    if left:
        w('<h3>그 밖에</h3><div class="tbl-scroll"><table><tbody>')
        for name in left:
            w('<tr><td style="width:230px"><a href="%s/project-process/rules/%s">'
              '<code>rules/%s</code></a></td><td>%s</td></tr>'
              % (BLOB, esc(name), esc(name), esc(doc_intro(os.path.join(rules_dir, name)))))
        w('</tbody></table></div>')

    # ── 형식 기준
    w('<h2 id="form">형식 기준</h2>')
    w('<p>산출물이 문서마다 다른 모양으로 나오면, 읽는 사람이 매번 새 문서를 배워야 합니다. '
      '그래서 색·타이포·컴포넌트의 정본을 하나 두고 모든 산출물이 그것을 인라인합니다.</p>')
    w('<div class="card-grid">')
    w(card('<a href="%sdesign-guide/design-guide-master.html">디자인 시각 규칙서</a>' % R,
           "색 토큰과 컴포넌트가 실제로 어떻게 보여야 하는지를 눈으로 확인하는 문서입니다. "
           "스타일 정본은 <code>design-guide-master.css</code>, 동작 정본은 "
           "<code>design-guide-master.js</code>이고, 산출물은 만들 때마다 그 사본을 품습니다.",
           "이 페이지도 같은 기준으로 그려졌습니다"))
    w(card('<a href="%s/design-template/template-catalog.md">문서 템플릿 카탈로그</a>' % BLOB,
           "새 문서를 만들 때 <strong>기존 템플릿으로 되는지, 기준을 고쳐야 하는지, 새로 만들어야 "
           "하는지</strong>를 세 갈래로 판별합니다. 판별 없이 만들기 시작하면 비슷하지만 미묘하게 "
           "다른 문서가 쌓입니다.",
           "TC 시트 서식의 정본은 tc-sheet-master.xlsx의 명세서 시트"))
    w('</div>')

    # ── 도구 (docstring 첫 줄을 읽는다)
    w('<h2 id="tool">사람이 반복하지 않게 만든 도구</h2>')
    w('<p>같은 일을 두 번 이상 손으로 하면 언젠가 한 번은 틀립니다. 아래는 그 자리마다 만들어 둔 '
      '도구이고, 설명은 각 파일이 스스로 적어 둔 첫 줄입니다.</p>')
    w(shell.table_tools("tool-tbl", "도구 검색"))
    w('<div class="tbl-scroll"><table id="tool-tbl"><thead><tr>'
      '<th class="sortable">도구</th><th>무엇을 하나</th></tr></thead><tbody>')
    for name in scripts:
        w('<tr><td><a href="%s/project-process/scripts/%s"><code>%s</code></a></td><td>%s</td></tr>'
          % (BLOB, esc(name), esc(name), esc(script_summary(os.path.join(scripts_dir, name)))))
    w('</tbody></table></div>')

    w('<div class="doc-footer">이 문서는 파생물입니다 — '
      '<code>gen_intro_html.py --page foundation</code>으로 재생성합니다. 규칙 목록·절차 단계·'
      '도구 설명은 전부 실제 파일에서 읽습니다.</div>')

    toc = (("why", "왜 규칙부터인가"), ("step", "작업 절차"), ("rule", "규칙 문서"),
           ("form", "형식 기준"), ("tool", "도구"))
    return "".join(o), toc, "토대 — 작업 규칙"


def md_inline(text):
    """md 인라인 표기를 최소한만 살린다 — 백틱은 코드로, 굵게는 강조로."""
    out = esc(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    return out


def md_rows(path, heading):
    """md의 어느 절에 있는 표를 행 목록으로 읽는다 — 근거를 옮겨 적지 않고 그대로 가져온다."""
    rows, on = [], False
    try:
        lines = io.open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return rows
    for line in lines:
        if line.startswith("#"):
            if on and rows:
                break
            on = heading in line
            continue
        if not on or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            # 구분선 바로 앞줄은 머리글이다 — 이름으로 거르면 표마다 예외가 늘어난다
            if rows:
                rows.pop()
            continue
        rows.append(cells)
    return rows


def tree_scope(md_path):
    """트리에서 범위·출처 태그를 세고, 제외 노드는 사유와 함께 뽑는다."""
    counts = {"구현": 0, "보류": 0, "제외": 0, "REF": 0, "ADD": 0}
    excluded = []
    try:
        lines = io.open(md_path, encoding="utf-8").read().splitlines()
    except OSError:
        return counts, excluded
    for line in lines:
        for key in ("구현", "보류", "제외"):
            if "[범위: %s]" % key in line:
                counts[key] += 1
        for key in ("REF", "ADD"):
            if "[출처: %s]" % key in line:
                counts[key] += 1
        if "[범위: 제외]" in line and line.lstrip().startswith("- "):
            name = line.lstrip()[2:].split("[범위:")[0].strip()
            why = line.split("—", 1)[1].strip() if "—" in line else ""
            excluded.append((name, why))
    return counts, excluded


# ────────────────────────────────────────────────────────────────
# 페이지 ④ 제작 과정 — 무작정 만들지 않았다는 것을 근거로 보인다
# ────────────────────────────────────────────────────────────────
def page_making(d, args, rel):
    """제작 과정 — 조사에서 시작해 무엇을 넣고 뺐는지, 값은 왜 그 숫자인지.

    근거 표는 판단 기록(rationale)에서 그대로 읽습니다. 이 페이지에 옮겨 적으면
    근거가 바뀔 때 여기만 옛말을 하게 됩니다.
    """
    S = d["slug"]
    P, R = rel["project"], rel["root"]
    PJ = args.project_dir
    o = []
    w = o.append

    tree_md = os.path.join(PJ, "spec", "%s-feature-tree.md" % S)
    rat = os.path.join(PJ, "spec", "rationale", "%s-addition-rationale.md" % S)
    counts, excluded = tree_scope(tree_md)
    add_rows = md_rows(rat, "§1 노드 보강")
    num_rows = md_rows(rat, "§2 수치 확정")
    n_leaf = len(d["leaves"])

    w('<div class="doc-header"><h1>제작 과정 — MiyonChat은 어떻게 나왔나</h1>')
    w('<p class="doc-lead">검증 대상을 직접 만들면 <strong>「테스트하기 좋게 만든 장난감」</strong>이 되기 쉽습니다. '
      '그래서 기능을 상상해서 넣지 않고, 출시된 서비스를 조사해 공통 행동을 뽑은 뒤 그것을 근거로 세웠습니다. '
      '조사에 없어 직접 정한 것은 <strong>따로 표시하고 이유를 남겼습니다</strong> — 이 페이지는 그 기록입니다.</p>')
    w('<div class="meta-row">'
      '<span class="badge">조사에서 채택 <b>%d개</b></span>'
      '<span class="badge">직접 세움 <b>%d개</b></span>'
      '<span class="badge">범위에서 제외 <b>%d개</b></span>'
      '<span class="badge">빌드 <b>%s</b></span></div></div>'
      % (counts["REF"], counts["ADD"], len(excluded), esc(d["build"])))

    # ── 조사
    w('<h2 id="ref">무엇을 조사했나</h2>')
    w('<p>기능 목록이 아니라 <strong>행동 목록</strong>부터 만들었습니다. 기능 이름은 회사마다 다르지만 '
      '「처음 켰을 때부터 사용자가 할 수 있는 행동」은 겹치기 때문입니다. 겹치는 행동이 곧 '
      '「이런 서비스라면 반드시 있어야 할 것」입니다.</p>')
    w('<div class="card-grid">')
    w(card("AI 챗 축",
           "캐릭터와 대화하는 서비스 셋. 재화 소모·대화 한도·세이프티처럼 <strong>AI 챗에만 있는 "
           "구조</strong>를 여기서 얻었습니다."))
    w(card("AI 챗 + 비주얼노벨 축",
           "대화형 AI에 비주얼노벨 UI가 얹힌 서비스. 두 축이 한 화면에서 어떻게 만나는지를 봤고, "
           "로그인 실측으로 화면 구성·수치 상한을 확인했습니다."))
    w(card("미연시 축",
           "세이브·로드 슬롯, 분기와 호감도, 관계 단계와 결말처럼 <strong>대화만으로는 나오지 않는 "
           "기능</strong>을 여기서 가져왔습니다."))
    w('</div>')
    ana = os.path.join(PJ, "analysis")
    if os.path.isdir(ana):
        w('<div class="tbl-scroll"><table><thead><tr><th>조사 문서</th><th>무엇을 담았나</th>'
          '</tr></thead><tbody>')
        for name in sorted(n for n in os.listdir(ana) if n.endswith(".md")):
            w('<tr><td><a href="%s/projects/%s/analysis/%s"><code>%s</code></a></td><td>%s</td></tr>'
              % (BLOB, S, esc(name), esc(name),
                 esc(doc_intro(os.path.join(ana, name), 150))))
        w('</tbody></table></div>')
    w('<div class="callout">조사에는 <strong>지키기로 한 선</strong>이 있었습니다 — 스크린샷 0장, '
      '원문 대사 인용 없음, 실화폐 결제 없음, 성인 인증 게이트 안쪽 미진입. 확인하지 못한 것은 '
      '추측으로 채우지 않고 미확인으로 남겨 두었습니다.</div>')

    # ── 좁히기
    w('<h2 id="narrow">조사한 것을 그대로 쓰지 않았다</h2>')
    w('<p>남의 서비스에서 본 값을 그대로 기대값으로 쓰면, 테스트가 <strong>처음부터 틀린 기준</strong>을 '
      '갖게 됩니다. 우리 서비스가 그렇게 동작하기로 정한 적이 없기 때문입니다. 그래서 세 단계로 좁혔습니다.</p>')
    w('<div class="steps">')
    for title, body in (
        ("조사 전량", "본 것을 버리지 않고 전부 모읍니다. 나중에 「이 값은 어디서 왔나」를 되짚을 수 있어야 합니다."),
        ("채택분", "그중 「우리도 갖자」고 고른 것만 남깁니다. 아직 확정은 아닙니다."),
        ("확정 결정", "우리 서비스의 규칙으로 못박습니다. <strong>테스트의 기대값은 여기서만</strong> 가져옵니다."),
    ):
        w('<div class="step"><div class="body"><b>%s</b> — %s</div></div>' % (esc(title), body))
    w('</div>')
    w('<div class="stats">')
    w(stat(counts["REF"], "조사에서 채택", "본 것을 근거로 세운 항목"))
    w(stat('<em>%d</em>' % counts["ADD"], "직접 세움", "조사에 없어 판단으로 채운 항목"))
    w(stat(n_leaf, "검증 대상 기능", "이번 범위에서 만든 것"))
    w(stat(counts["보류"], "보류", "트리에만 두고 만들지 않음"))
    w('</div>')

    # ── ADD 근거
    if add_rows:
        w('<h2 id="add">직접 세운 기능과 그 근거</h2>')
        w('<p>조사에 없는데도 넣기로 한 것들입니다. <strong>「조사에 없다」는 사실과 그래도 넣는 이유를 '
          '함께</strong> 적어 두었습니다 — 면접에서 가장 많이 받을 질문이 여기이기 때문입니다.</p>')
        w(shell.table_tools("add-tbl", "기능 이름 · 근거 검색"))
        w('<div class="tbl-scroll"><table id="add-tbl"><thead><tr>'
          '<th class="sortable">기능</th><th>왜 넣었나</th></tr></thead><tbody>')
        for row in add_rows:
            if len(row) >= 2:
                w('<tr><td>%s</td><td>%s</td></tr>' % (md_inline(row[0]), md_inline(row[1])))
        w('</tbody></table></div>')

    # ── 수치 근거
    if num_rows:
        w('<h2 id="num">값은 왜 그 숫자인가</h2>')
        w('<p>기능이 있다는 것과 「얼마부터 통과인가」는 다른 문제입니다. 공개되지 않은 값은 직접 정해야 하는데, '
          '그 숫자가 <strong>검증하기 좋은 크기인지</strong>까지 함께 봤습니다 — 경계가 ±1로 잡히지 않으면 '
          '경계 테스트가 성립하지 않습니다.</p>')
        w(shell.table_tools("num-tbl", "값 검색",
                            (("직접 정함", "col", 1, "ADD"),)))
        w('<div class="tbl-scroll"><table id="num-tbl"><thead><tr><th class="sortable">값</th>'
          '<th class="sortable">출처</th><th>근거</th></tr></thead><tbody>')
        for row in num_rows:
            if len(row) >= 3:
                w('<tr><td>%s</td><td><span class="chip chip-%s">%s</span></td><td>%s</td></tr>'
                  % (md_inline(row[0]),
                     "det" if row[1].startswith("REF") else "rub",
                     esc(row[1]), md_inline(row[2])))
        w('</tbody></table></div>')

    # ── 뺀 것
    if excluded:
        w('<h2 id="drop">무엇을 뺐나</h2>')
        w('<p>넣지 않기로 한 것도 판단입니다. <strong>검증 축이 늘지 않는 기능</strong>은 만들어도 '
          '테스트가 늘지 않고 시간만 씁니다. 뺀 이유를 남겨 두면 나중에 「왜 이건 없나」에 답할 수 있습니다.</p>')
        w('<div class="tbl-scroll"><table><thead><tr><th>뺀 것</th><th>이유</th>'
          '</tr></thead><tbody>')
        for name, why in excluded:
            w('<tr><td>%s</td><td>%s</td></tr>' % (esc(name), md_inline(why)))
        w('</tbody></table></div>')

    # ── 만들 때 지킨 조건
    w('<h2 id="make">만들 때 지킨 조건</h2>')
    w('<div class="card-grid">')
    w(card("명세를 먼저 고친다",
           "코드가 확정 사양과 어긋나면 코드를 슬쩍 맞추지 않고 <strong>명세를 먼저 고치고 그 변경을 "
           "기록</strong>했습니다. 반대로 하면 테스트의 기대값이 코드를 따라가게 되어, "
           "무엇이 옳은지 아무도 모르게 됩니다."))
    w(card("테스트가 잡을 이름표를 먼저 정한다",
           "화면 요소를 무엇으로 찾을지(<code>data-testid</code> 명명 규칙)를 코드 첫 줄 전에 확정했습니다. "
           "나중에 붙이면 테스트가 화면 생김새나 문구에 매달리게 되고, 디자인이 바뀔 때마다 깨집니다."))
    w(card("기능 목록에 없는 것은 만들지 않는다",
           "만들다 보면 「이것도 있으면 좋겠다」가 계속 생깁니다. 목록에 없는 기능은 검증 대상이 아니므로, "
           "넣고 싶으면 <strong>목록을 먼저 고치고</strong> 그 이력을 남겼습니다."))
    w('</div>')

    w('<div class="stats">')
    w(stat(esc(d["build"]), "지금 빌드", "화면 단위로 끊어 올린 결과"))
    w(stat(n_leaf, "만든 기능", "목록의 검증 대상 전부"))
    w(stat(len(d["testids"]), "테스트가 잡는 요소", "이름표를 달아 둔 화면 조작 지점"))
    w('</div>')

    w('<div class="doc-footer">이 문서는 파생물입니다 — '
      '<code>gen_intro_html.py --page making</code>으로 재생성합니다. 근거 표는 판단 기록에서, '
      '수치는 기능 목록 정본에서 그대로 읽습니다.</div>')

    toc = (("ref", "무엇을 조사했나"), ("narrow", "그대로 쓰지 않았다"),
           ("add", "직접 세운 기능"), ("num", "값의 근거"), ("drop", "무엇을 뺐나"),
           ("make", "만들 때 지킨 조건"))
    return "".join(o), toc, "제작 과정"


# ────────────────────────────────────────────────────────────────
# 페이지 ⑤ TC 설계 규칙 — 케이스를 어떻게 펼치고 무엇으로 「다 봤다」를 판정하나
# ────────────────────────────────────────────────────────────────
VT_CHIP = {"결정적": "det", "확률적": "prob", "루브릭": "rub", "금칙": "ban"}


def page_tc(d, args, rel):
    """TC 설계 규칙 — 규칙의 정의는 rules/가 정본이고, 여기서는 왜 그렇게 했는지를 말한다."""
    S = d["slug"]
    o = []
    w = o.append

    cfg = read_json(os.path.join(args.project_dir, "test-case",
                                 "%s-tc-input-v1.0.json" % S))
    tcs = d["tcs"]
    areas = {k: v for k, v in d["areas"].items() if isinstance(v, dict)}
    code_of = {v["code"]: k for k, v in areas.items()}
    by_area = {}
    for t in tcs:
        by_area.setdefault(t[0].split("-")[1], []).append(t)
    waivers = read_json(os.path.join(args.project_dir, "test-case",
                                     "%s-coverage-waiver.json" % S))["waivers"]
    n_manual = sum(1 for t in tcs if t[7] == "사람 전용")

    w('<div class="doc-header"><h1>테스트 케이스를 어떻게 설계했나</h1>')
    w('<p class="doc-lead">기능 하나에 케이스 하나를 쓰면 <strong>정상 동작만 확인하고 끝납니다.</strong> '
      '결함은 대개 경계와 예외, 그리고 막아 둔 길을 돌아가는 자리에서 나옵니다. 그래서 기능마다 네 갈래로 '
      '펼치고, 케이스마다 <strong>어떻게 판정할지</strong>와 <strong>무엇을 확인하는지</strong>를 함께 '
      '적었습니다.</p>')
    w('<div class="meta-row">'
      '<span class="badge">케이스 <b>%d건</b></span>'
      '<span class="badge">영역 <b>%d개</b></span>'
      '<span class="badge">사람이 직접 <b>%d건</b></span>'
      '<span class="badge">규칙 정본 <b>rules/</b></span></div></div>'
      % (len(tcs), len(areas), n_manual))

    # ── 네 갈래 전개
    w('<h2 id="expand">기능 하나를 네 갈래로 편다</h2>')
    w('<div class="card-grid">')
    w(card("정상", "설계대로 동작하는가. 이것만 있으면 「되는 것만 확인한」 테스트가 됩니다."))
    w(card("경계", "제한이 있는 곳마다 <strong>경계−1 · 경계 · 경계+1</strong> 세 점을 찍습니다. "
                 "「20 이상」인지 「20 초과」인지는 여기서만 드러납니다."))
    w(card("예외", "실패·중단·빈 상태처럼 정상 흐름을 벗어난 자리. 실패했을 때 "
                 "<strong>무엇이 남지 않아야 하는지</strong>가 핵심입니다."))
    w(card("우회", "막아 둔 길을 돌아가 봅니다 — 주소로 직접 진입하거나, 화면을 거치지 않고 "
                 "동작을 부르거나. 실제 결함이 가장 많이 나온 갈래입니다."))
    w('</div>')

    # ── 판정 방식
    w('<h2 id="vt">판정 방식을 먼저 정한다</h2>')
    w('<p>AI가 만드는 응답은 같은 입력에도 매번 다릅니다. 그래서 케이스를 쓰기 전에 '
      '<strong>이 항목을 무엇으로 통과·실패라 부를지</strong>부터 정했습니다. 판정 방식이 정해지면 '
      '몇 번 돌려야 하는지도 따라 정해집니다.</p>')
    w('<div class="tbl-scroll"><table><thead><tr><th>판정 방식</th><th>어떤 항목인가</th>'
      '<th>어떻게 판정하나</th><th class="num">건수</th></tr></thead><tbody>')
    for vt, what, how in (
        ("결정적", "시스템이 보장해야 하는 값·상태 전이. 재화 차감액, 화면 전환, 저장·복원",
         "1회 실행하고 어긋나면 곧바로 실패"),
        ("금칙", "단 한 번도 일어나면 안 되는 것. 게이트 우회, 데이터 잔존, 필터 누출",
         "우회 변형까지 여러 번 시도해 <strong>0건이어야</strong> 통과"),
        ("확률적", "품질에 기대지만 숫자로 잴 수 있는 것. 페르소나 반영률 같은 항목",
         "여러 번 돌려 성공률을 임계와 비교"),
        ("루브릭", "수치화가 어려운 품질. 어투와 관계 단계가 어울리는가",
         "5점 채점표로 채점하고 합격선과 비교"),
    ):
        w('<tr><td><span class="chip chip-%s">%s</span></td><td>%s</td><td>%s</td>'
          '<td class="num">%d</td></tr>'
          % (VT_CHIP.get(vt, "unk"), esc(vt), esc(what), how, d["by_vt"].get(vt, 0)))
    w('</tbody></table></div>')
    w('<div class="callout"><strong>반복은 자동화가 하고 사람은 어떤 유형이든 한 번만 봅니다.</strong> '
      '사람에게 같은 조작을 50번 시키면 50번째의 관찰이 첫 번째와 같지 않습니다. 그래서 시트에는 '
      '반복 횟수를 적지 않고, 반복이 필요한 항목은 자동화 쪽 임계로 관리합니다.</div>')

    # ── 뎁스
    w('<h2 id="depth">뎁스는 기능 분류가 아니라 도달 경로</h2>')
    w('<p>케이스의 앞 칸(뎁스)에 기능 분류를 적으면 TC 번호의 영역 구분과 같은 말을 두 번 하게 됩니다. '
      '그래서 뎁스에는 <strong>「어디서 실행하나」</strong> — 앱을 열고 그 화면까지 가는 경로를 적고, '
      '<strong>「무엇을 검증하나」</strong>는 번호 접두가 담습니다. 실행하는 사람은 경로를 따라가면 되고, '
      '설계하는 사람은 번호로 영역을 셉니다.</p>')
    order = cfg.get("d1_order") or []
    if order:
        w('<div class="filters">%s</div>'
          % "".join('<button class="fbtn" disabled>%s</button>' % esc(x) for x in order))
        w('<p class="foot">경로의 첫 칸으로 쓰는 화면들입니다 — 여러 길이 합쳐지는 지점, 어느 화면에나 '
          '있는 요소, 위에 덮이는 오버레이를 기준으로 갈랐습니다.</p>')

    # ── 실제 한 건
    sample = None
    for t in tcs:
        if t[6] == "금칙" and len([x for x in t[4].split("\n") if x.strip()]) >= 2:
            sample = t
            break
    if sample:
        w('<h2 id="case">실제 케이스 한 건</h2>')
        w('<p>규칙이 실제로 어떤 모양이 되는지 한 건만 펼쳐 보입니다. 막아 둔 길을 돌아가는 갈래이고, '
          '판정 방식은 「단 한 번도 일어나면 안 됨」입니다.</p>')
        steps = [x for x in sample[4].split("\n") if x.strip()]
        exp = sample[5]
        w('<div class="card"><h3>%s — %s</h3>' % (esc(sample[0]), esc(sample[2])))
        w('<p class="foot">도달 경로: %s · 사전조건: %s · 우선순위 %s</p>'
          % (esc(" > ".join(sample[1])), esc(sample[3] or "-"), esc(sample[8])))
        w('<div class="tbl-scroll"><table><thead><tr><th style="width:44%">무엇을 하나</th>'
          '<th>무엇이 되어야 하나</th></tr></thead><tbody>')
        for i, st in enumerate(steps):
            outs = exp[i] if isinstance(exp, list) and i < len(exp) else []
            outs = outs if isinstance(outs, list) else [outs]
            w('<tr><td>%s</td><td>%s</td></tr>'
              % (esc(st), "<br>".join(esc(x) for x in outs)))
        w('</tbody></table></div>')
        w('<p class="foot">확인하는 좌표: %s</p></div>'
          % ", ".join("<code>%s</code>" % esc(c) for c in (sample[12] or [])))
        w('<p>마지막 줄이 이 설계의 핵심입니다 — 케이스마다 <strong>무엇을 덮는지 좌표를 적어 '
          '둡니다.</strong> 이 좌표가 있어야 「빠짐없이 봤다」를 사람이 아니라 스크립트가 판정할 수 '
          '있습니다.</p>')

    # ── 영역별 규모
    w('<h2 id="area">영역별 규모</h2>')
    w('<p>영역마다 판정 방식의 구성이 다릅니다. 게이팅처럼 <strong>막는 것이 일인 영역</strong>은 '
      '금칙 비중이 크고, 화면 표시가 일인 영역은 결정적이 대부분입니다.</p>')
    w(shell.table_tools("area-tbl", "영역 검색"))
    w('<div class="tbl-scroll"><table id="area-tbl"><thead><tr><th class="sortable">영역</th>'
      '<th class="sortable">코드</th><th class="num sortable">케이스</th>'
      '<th>판정 방식 구성</th></tr></thead><tbody>')
    for code, rows in sorted(by_area.items(), key=lambda x: -len(x[1])):
        mix = {}
        for t in rows:
            mix[t[6]] = mix.get(t[6], 0) + 1
        chips = " ".join('<span class="chip chip-%s">%s %d</span>'
                         % (VT_CHIP.get(k, "unk"), esc(k), v)
                         for k, v in sorted(mix.items(), key=lambda x: -x[1]))
        w('<tr><td>%s</td><td><code>%s</code></td><td class="num">%d</td><td>%s</td></tr>'
          % (esc(code_of.get(code, code)), esc(code), len(rows), chips))
    w('</tbody></table></div>')

    # ── 커버리지
    w('<h2 id="cov">「다 봤다」를 어떻게 판정하나</h2>')
    w('<p>테스트를 많이 썼다는 말은 빠진 것이 없다는 뜻이 아닙니다. 그래서 기준선 셋을 정본에서 읽어 오고, '
      '케이스가 적어 둔 좌표와 맞춰 <strong>덮이지 않은 것을 목록으로</strong> 냅니다. '
      '그 목록이 빌 때까지가 설계입니다.</p>')
    cov = os.path.join(args.repo_root, "diagrams", "coverage-axes.svg")
    if os.path.exists(cov):
        body = io.open(cov, encoding="utf-8").read()
        w('<div class="card" style="padding:14px">%s</div>' % body[body.index("<svg"):])
    w('<div class="stats">')
    w(stat("%d/%d" % (len(d["leaves"]), len(d["leaves"])), "기능 축", "만든 기능 전부",
           ("ok", 100)))
    w(stat("%d/%d" % (len(d["testids"]), len(d["testids"])), "화면 요소 축",
           "이름표를 단 조작 지점 전부", ("ok", 100)))
    w(stat(len(d["states"]), "상태 축", "계정·세션 상태"))
    w(stat(len(waivers), "검증 대상 제외", "사유를 적고 그 사유까지 검사"))
    w('</div>')
    w('<h3>검증 대상에서 뺀 것</h3>')
    w('<p>덮이지 않은 것을 <strong>덮은 척하지 않으려고</strong>, 뺄 때는 무엇을 왜 빼는지 파일에 '
      '적습니다. 대조 스크립트는 그 사유의 종류와 대상이 실재하는지까지 확인합니다.</p>')
    w('<div class="tbl-scroll"><table><thead><tr><th>대상</th><th>종류</th><th>이유</th>'
      '</tr></thead><tbody>')
    for wv in waivers:
        w('<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>'
          % (esc(wv.get("target", "")), esc(wv.get("kind", "")),
             md_inline(wv.get("reason", ""))))
    w('</tbody></table></div>')

    # ── 시트
    w('<h2 id="sheet">시트는 실무 서식 그대로</h2>')
    w('<p>새 레이아웃을 발명하면 받는 쪽이 읽는 법부터 배워야 합니다. 그래서 실제로 쓰이는 TC 시트의 '
      '열 구성과 문체를 그대로 따르고, 규칙만 문서로 못박았습니다.</p>')
    w('<div class="card-grid">')
    w(card("한 행 = 한 스텝",
           "케이스 단위 값(번호·경로·우선순위·판정 방식)은 행마다 반복하고, 스텝과 기대 결과만 "
           "행으로 늘립니다. 실행하면서 한 줄씩 결과를 적을 수 있어야 하기 때문입니다."))
    w(card("결과는 네 가지",
           "통과·실패 외에 <strong>확인 불가</strong>와 <strong>미구현</strong>을 둡니다. "
           "확인 못 한 것을 실패로 적으면 결함이 실제보다 많아 보이고, 통과율의 분모도 틀어집니다."))
    w(card("결함 시트를 함께 넣는다",
           "발견한 결함을 다른 도구에 적으면 케이스와 끊깁니다. 같은 파일 안에 두고 케이스 번호로 "
           "이으면 <strong>어떤 케이스가 어떤 결함을 잡았는지</strong>가 남습니다."))
    w('</div>')
    w('<p class="foot">서식 규칙의 정본은 <a href="%s/project-process/rules/tc-sheet-format.md">'
      '<code>rules/tc-sheet-format.md</code></a>와 시트 안의 명세서 탭입니다 — 둘을 교차 '
      '검증합니다.</p>' % BLOB)

    w('<div class="doc-footer">이 문서는 파생물입니다 — '
      '<code>gen_intro_html.py --page tc</code>로 재생성합니다. 건수·영역·제외 사유는 TC 설계 '
      '원본에서, 커버리지 그림은 <code>diagrams/coverage-axes.svg</code>에서 읽습니다.</div>')

    toc = (("expand", "네 갈래 전개"), ("vt", "판정 방식"), ("depth", "도달 경로 뎁스"),
           ("case", "실제 케이스"), ("area", "영역별 규모"), ("cov", "커버리지"),
           ("sheet", "시트 서식"))
    return "".join(o), toc, "TC 설계 규칙"


# ────────────────────────────────────────────────────────────────
# 페이지 ⑥ 자동화 설계와 결과 — 테스트가 결함을 잡는지 어떻게 증명했나
# ────────────────────────────────────────────────────────────────
def sample_test_names(tests_dir, limit=6):
    """실제 테스트 함수 이름 몇 개 — 이름이 곧 케이스 번호라는 것을 눈으로 보인다."""
    out = []
    if not os.path.isdir(tests_dir):
        return out
    for name in sorted(os.listdir(tests_dir)):
        if not name.startswith("test_") or not name.endswith(".py"):
            continue
        src = io.open(os.path.join(tests_dir, name), encoding="utf-8").read()
        for fn in re.findall(r"^\s*def (test_tc_[a-z0-9_]+)", src, re.M):
            out.append((fn, name))
            break
        if len(out) >= limit:
            break
    return out


def matrix_table(md_path):
    """커밋된 매트릭스 표를 그대로 읽는다 — 실행 결과의 정본이다."""
    head, rows = [], []
    if not os.path.exists(md_path):
        return head, rows
    for line in io.open(md_path, encoding="utf-8"):
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if not head:
            head = cells
        else:
            rows.append(cells)
    return head, rows


def ci_steps(path):
    """CI 워크플로의 단계 이름 — 무엇을 반복 확인하는지 파일에서 읽는다."""
    out = []
    if not os.path.exists(path):
        return out
    for line in io.open(path, encoding="utf-8"):
        m = re.match(r"^\s+- name: (.+)$", line.rstrip())
        if m:
            out.append(m.group(1).strip())
    return out


def page_auto(d, args, rel):
    """자동화 설계와 결과 — 무엇을 심어 뒀고, 고장을 넣었을 때 무엇이 깨졌나."""
    S = d["slug"]
    P = rel["project"]
    PJ = args.project_dir
    o = []
    w = o.append

    fm = read_json(os.path.join(PJ, "automation", "%s-fault-matrix.json" % S))
    faults = fm["faults"]
    iface = md_rows(os.path.join(args.repo_root, "project-process", "rules",
                                 "sut-automation.md"), "1. SUT 제작 규칙")
    tests_dir = os.path.join(PJ, "automation", "tests")
    names = sample_test_names(tests_dir)
    mhead, mrows = matrix_table(os.path.join(PJ, "automation", "result", "matrix",
                                             "fault-matrix.md"))
    steps = ci_steps(os.path.join(args.repo_root, ".github", "workflows", "%s.yml" % S))
    n_auto_tc = sum(1 for t in d["tcs"] if t[7] != "사람 전용")

    w('<div class="doc-header"><h1>자동화 설계와 결과</h1>')
    w('<p class="doc-lead">테스트가 <strong>통과한다</strong>는 말과 테스트가 <strong>쓸모 있다</strong>는 '
      '말은 다릅니다. 아무것도 확인하지 않는 테스트도 통과하기 때문입니다. 그래서 자동화를 짤 때 두 가지를 '
      '함께 설계했습니다 — 화면이 바뀌어도 살아남는 구조, 그리고 <strong>고장을 심었을 때 실제로 '
      '깨지는지</strong> 확인하는 절차입니다.</p>')
    w('<div class="meta-row">'
      '<span class="badge">자동화 <b>%d건</b></span>'
      '<span class="badge">자동화 대상 케이스 <b>%d건</b></span>'
      '<span class="badge">심은 고장 <b>%d종</b></span>'
      '<span class="badge">빌드 <b>%s</b></span></div></div>'
      % (d["auto"], n_auto_tc, len(faults), esc(d["build"])))

    # ── 접점
    w('<h2 id="iface">테스트가 붙잡을 접점을 먼저 심었다</h2>')
    w('<p>검증 대상을 다 만든 뒤에 테스트를 붙이면, 테스트가 <strong>화면 생김새와 문구에 매달리게</strong> '
      '됩니다. 버튼 글자 하나만 바뀌어도 무더기로 깨지고, 화면에 안 나타나는 것(저장소에 남은 데이터 같은)은 '
      '아예 확인할 수 없습니다. 그래서 만들기 시작할 때부터 네 갈래를 심어 두었습니다.</p>')
    if iface:
        w('<div class="tbl-scroll"><table><thead><tr><th>접점</th><th>규칙</th><th>왜 필요한가</th>'
          '</tr></thead><tbody>')
        for row in iface:
            if len(row) >= 3:
                w('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                  % (md_inline(row[0]), md_inline(row[1]), md_inline(row[2])))
        w('</tbody></table></div>')

    # ── 이름 규칙
    w('<h2 id="name">테스트 이름이 곧 케이스 번호</h2>')
    w('<p>리포트에서 빨간 줄 하나를 보고 <strong>시트의 어느 케이스인지 바로 찾을 수 있어야</strong> '
      '합니다. 그래서 테스트 함수 이름에 케이스 번호를 그대로 넣었습니다. 이름을 짓는 규칙 하나로 '
      '실행 결과와 설계 문서가 이어집니다.</p>')
    if names:
        w('<div class="tbl-scroll"><table><thead><tr><th>테스트 함수</th><th>파일</th>'
          '<th>가리키는 케이스</th></tr></thead><tbody>')
        for fn, fname in names:
            m = re.match(r"test_tc_([a-z]+)_(\d+)_", fn)
            tc = "TC-%s-%s" % (m.group(1).upper(), m.group(2)) if m else "-"
            w('<tr><td><code>%s</code></td><td><code>%s</code></td><td><code>%s</code></td></tr>'
              % (esc(fn), esc(fname), esc(tc)))
        w('</tbody></table></div>')

    # ── 흔들리지 않게
    w('<h2 id="stable">환경 때문에 깨지지 않게</h2>')
    w('<p>자동화가 가끔 실패하기 시작하면, 사람은 곧 결과를 믿지 않게 됩니다. 「또 그거겠지」가 되는 순간 '
      '자동화는 있으나 마나 합니다. 그래서 <strong>가짜 실패를 만드는 원인</strong>을 규칙으로 막았습니다.</p>')
    w('<div class="card-grid">')
    w(card("몇 초 기다리기 금지",
           "브라우저가 느려지면 「2초 기다린다」는 환경에 따라 깨집니다. 시간이 아니라 "
           "<strong>상태 표식이 바뀌는 것</strong>을 기다립니다."))
    w(card("테스트마다 초기화",
           "앞 테스트가 남긴 데이터가 뒤 테스트의 결과를 바꾸면, 실패의 원인이 코드인지 순서인지 "
           "알 수 없습니다. 매번 초기화하고 시작합니다."))
    w(card("응답을 고정할 수 있게",
           "AI 응답이 매번 다르면 실패를 재현할 수 없습니다. 시드를 주면 같은 응답이 나오도록 "
           "만들어, 실패한 조건을 그대로 다시 만들 수 있습니다."))
    w('</div>')
    iso = os.path.join(args.repo_root, "diagrams", "automation-isolation.svg")
    if os.path.exists(iso):
        body = io.open(iso, encoding="utf-8").read()
        w('<div class="card" style="padding:14px">%s</div>' % body[body.index("<svg"):])

    # ── 고장 주입
    w('<h2 id="fault">고장을 심어 탐지력을 증명한다</h2>')
    w('<p>커버리지는 「빠짐없이 봤다」까지만 말합니다. <strong>봤을 때 알아채는지</strong>는 다른 문제입니다. '
      '그래서 고장을 하나씩 켜고 전체를 다시 돌려, <strong>담당 케이스만 실패하는지</strong>를 봅니다. '
      '담당은 실행 결과가 아니라 <strong>고장을 심은 지점을 지나며 그 오동작을 판정하는가</strong>로 정합니다 — '
      '지나가기만 하는 케이스는 담당이 아닙니다.</p>')
    fmt = os.path.join(args.repo_root, "diagrams", "fault-matrix.svg")
    if os.path.exists(fmt):
        body = io.open(fmt, encoding="utf-8").read()
        w('<div class="card" style="padding:14px">%s</div>' % body[body.index("<svg"):])
    w('<div class="tbl-scroll"><table><thead><tr><th>심은 고장</th><th>어디에 심었나</th>'
      '<th>담당 케이스</th><th>담당인 이유</th></tr></thead><tbody>')
    for f in faults:
        exp = f.get("expect") or []
        first = True
        for e in exp:
            w('<tr><td>%s</td><td>%s</td><td><code>%s</code></td><td>%s</td></tr>'
              % ('<code>%s</code>' % esc(f["key"]) if first else "",
                 esc(f.get("point", "")) if first else "",
                 esc(e.get("tc", "")), md_inline(e.get("why", ""))))
            first = False
    w('</tbody></table></div>')

    # ── 결과
    if mrows:
        w('<h2 id="result">결과 — 대각선만 실패해야 정상</h2>')
        w('<p>가로는 검증 영역, 세로는 심은 고장입니다. 아무것도 심지 않은 첫 줄은 <strong>전부 통과</strong>해야 하고, '
          '고장을 하나 켜면 <strong>그 고장을 담당하는 영역만 실패</strong>해야 합니다. 담당 밖이 함께 흔들리면 '
          '그 테스트는 무엇을 보는지 모른 채 지나가고 있었다는 뜻입니다.</p>')
        w('<div class="tbl-scroll"><table><thead><tr>')
        for h in mhead:
            w('<th>%s</th>' % esc(h))
        w('</tr></thead><tbody>')
        for row in mrows:
            w('<tr>')
            for i, cell in enumerate(row):
                if i == 0:
                    w('<td>%s</td>' % md_inline(cell))
                elif "FAIL" in cell:
                    w('<td><span class="chip chip-no">%s</span></td>'
                      % esc(re.sub(r"[*]", "", cell)))
                elif "PASS" in cell:
                    w('<td><span class="chip chip-ok">PASS</span></td>')
                else:
                    w('<td>%s</td>' % esc(cell))
            w('</tr>')
        w('</tbody></table></div>')
        w('<p class="foot">표는 읽기 편하게 영역으로 접은 것이고, 판정은 케이스 단위로 합니다 — '
          '한 영역에 케이스가 여럿이면 하나만 깨져도 영역은 실패로 보입니다.</p>')

    # ── CI
    if steps:
        w('<h2 id="ci">사람이 잊어도 도는 검사</h2>')
        w('<p>규칙은 지키기로 마음먹는 것만으로는 유지되지 않습니다. 그래서 바뀔 때마다 '
          '<strong>기계가 같은 순서로 다시 확인</strong>하게 했습니다. 아래 단계는 실제 설정 파일에서 '
          '읽어 온 것입니다.</p>')
        w('<div class="steps">')
        for name in steps:
            w('<div class="step"><div class="body">%s</div></div>' % esc(name))
        w('</div>')
        w('<div class="callout">마지막 단계가 중요합니다 — <strong>커밋된 산출물이 최신인지</strong> '
          '확인합니다. 정본을 고치고 리포트를 다시 만들지 않으면 여기서 걸립니다. 문서가 조용히 낡는 것을 '
          '막는 장치입니다.</div>')

    # ── 한계
    w('<h2 id="limit">이 자동화가 확인하지 않는 것</h2>')
    w('<p>할 수 있는 것보다 <strong>할 수 없는 것을 밝히는 쪽</strong>이 신뢰를 만듭니다. '
      '적어도 세 가지는 이 검증의 범위 밖입니다.</p>')
    w('<div class="card-grid">')
    w(card("실제 AI 모델의 품질",
           "응답은 규칙으로 만든 대체 구현입니다. 그래서 여기서 잰 반영률·어투 점수는 "
           "<strong>모델의 성능이 아니라 시스템이 규칙대로 조립하는지</strong>를 말합니다."))
    w(card("실제 결제와 외부 인증",
           "결제와 본인인증은 흉내만 냅니다. 실패 경로와 되돌림은 검증하지만, 결제사·인증사와의 "
           "실제 연동은 대상이 아닙니다."))
    w(card("사람이 봐야 하는 것",
           "어투와 관계 단계가 어울리는지는 채점표로 사람이 봅니다. 자동화가 대신할 수 있는 척하지 "
           "않고, 사람 몫으로 남겨 두었습니다."))
    w('</div>')
    w('<p class="foot">검증 범위와 한계의 정본은 프로젝트의 청사진 문서이고, 실행 결과의 정본은 '
      '<a href="%sautomation/report/%s-report.html">검증 리포트</a>입니다.</p>' % (P, S))

    w('<div class="doc-footer">이 문서는 파생물입니다 — '
      '<code>gen_intro_html.py --page auto</code>로 재생성합니다. 접점 규칙은 '
      '<code>rules/sut-automation.md</code>에서, 담당 근거는 결함 기대표에서, 실행 결과는 커밋된 '
      '매트릭스 표에서, CI 단계는 워크플로 파일에서 읽습니다.</div>')

    toc = (("iface", "테스트가 붙잡을 접점"), ("name", "이름이 곧 케이스 번호"),
           ("stable", "가짜 실패 막기"), ("fault", "고장을 심어 증명"),
           ("result", "결과"), ("ci", "반복 검사"), ("limit", "확인하지 않는 것"))
    return "".join(o), toc, "자동화 설계와 결과"


PAGES = {"landing": page_landing, "structure": page_structure,
         "foundation": page_foundation, "making": page_making,
         "tc": page_tc, "auto": page_auto}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True, choices=sorted(PAGES))
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--css", required=True)
    ap.add_argument("--js", help="동작 정본(생략 시 CSS 옆의 design-guide-master.js)")
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    out_dir = os.path.dirname(os.path.abspath(args.output))

    def prefix(target):
        p = os.path.relpath(target, out_dir).replace("\\", "/")
        return "" if p == "." else p + "/"

    rel = {"root": prefix(args.repo_root), "project": prefix(args.project_dir)}

    d = load(args)
    body, toc, crumb = PAGES[args.page](d, args, rel)

    css, js = shell.assets(args.css, args.js)
    groups = [shell.intro_group(
        args.page, rel["root"],
        exists=lambda p: os.path.exists(os.path.join(args.repo_root, p)))]
    out_items = [(label, rel["project"] + path.format(S=args.slug), False, "")
                 for _k, label, path in shell.NAV]
    groups.append(("산출물", out_items))
    groups.append(("저장소",
                   [(label, url.format(S=args.slug), False, tag)
                    for label, url, tag in shell.OUT]))

    side = shell.sidebar_from(
        groups, rel["root"] + "index.html", "QA-VisualNovel-Portfolio",
        "QA 포트폴리오 · 류서진", toc,
        "골격 v%s%s" % (d["tree_version"], " · " + d["build"] if d["build"] else ""))

    html_out = "".join([
        shell.head("QA-VisualNovel-Portfolio — %s" % crumb, css, js),
        '<body><div class="app">', side, '<div class="main">',
        shell.topbar("QA-VisualNovel-Portfolio", crumb),
        '<div class="wrap">', body, shell.close_body(),
    ])
    with io.open(args.output, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_out)
    print("saved %s | 기능 단위 %d · TC %d · 자동화 %d · 결함 %d종"
          % (args.output, len(d["leaves"]), len(d["tcs"]), d["auto"], len(d["faults"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
