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
from parse_feature_tree import parse as parse_tree  # noqa: E402

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
      '무엇을 중점적으로 봐야 할까」</strong>를 고민했습니다. 레퍼런스로 삼은 서비스의 공통점이나, '
      '핵심으로 가져올 만한 기능을 골라 AI 캐릭터와 대화하는 서비스 '
      '<strong><a href="%ssut/index.html">MiyonChat</a></strong>을 설계해 만들었고, '
      '그 위에서 테스트 케이스를 설계해 <strong>자동화 테스트까지 돌려 검증했습니다.</strong></p>' % P)
    # 응답을 만드는 층은 실제 모델이 아니다 — 첫 화면에서 밝힌다. 자세한 것은 자동화 소개가 담는다
    w('<div class="callout"><strong>MiyonChat은 AI 캐릭터와 대화가 진행되는 과정과 규칙을 '
      '파악하려고 만든 포트폴리오용 서비스입니다.</strong> 그래서 응답을 만드는 영역은 실제 AI 모델을 '
      '쓰지 않고, <strong>미리 정해 둔 대화 세트</strong>로 구성했습니다 — 같은 조건에서는 같은 응답이 '
      '나오도록 고정했고, 그 덕에 실패한 테스트를 그대로 다시 만들어 볼 수 있습니다.</div>')
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
    w('<h2 id="what">무엇을 만들었나요?</h2>')
    w('<p>아래와 같이 AI 채팅 사이트를 만들었습니다. 해당 GIF는 손으로 녹화한 것이 아니라 '
      '스크립트가 브라우저를 조작해 만들었습니다.</p>')
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
    w(card("어떤 서비스인가요?",
           "웹 진입부터 시작하여, 캐릭터를 고르고 대화하는 과정에서 재화가 차감됩니다. "
           "대화가 쌓이면 <strong>호감도에 따라 관계 단계와 결말이 갈리고</strong>, 대화 내용을 "
           "저장했다가 되돌릴 수 있으며, 성인 콘텐츠는 인증 상태에 따라 가려집니다.",
           "화면 조작 지점 %d개 · 검증 영역 %d개" % (n_tid, n_area)))
    w(card("왜 직접 만들었나요?",
           "다른 레퍼런스 사이트를 기반으로 어떤 것들이 구성되는지 보려고 했습니다. 하지만 특정 "
           "프로세스에서는 재화가 부족해 확인이 힘들었고, <strong>고장을 일부러 심어 테스트가 그것을 "
           "잡아내는지 보는 것</strong>은 다른 서비스에서 불가능하다고 판단했습니다. 그래서 진입부터 "
           "끝까지 조건을 직접 만들어 검증할 수 있는 대상을 만들고자 했습니다.",
           "테스트가 붙잡을 접점을 처음부터 심어 만들었습니다"))
    w(card("무엇을 근거로 기능을 정했나요?",
           "혼자 상상해서 만들면 「테스트를 위해 만든 장난감」이 됩니다. 그래서 출시된 서비스 6개를 "
           "조사하여 「처음 켰을 때부터 사용자가 할 수 있는 행동」 순서로 조사해 공통적으로 사용하는 "
           "기능을 선정하고, 추가로 필요한 기능들을 포함시켜 기능을 결정했습니다.",
           "조사 대상: AI 챗 3종 · AI 챗+비주얼노벨 1종 · 미연시 2종"))
    w('</div>')

    # ── ② 중앙 규칙과 프로젝트 규칙 — 앞선 작업에서 부딪힌 문제와 그 해결
    paths = dict((k, p) for k, _l, p in shell.INTRO)

    def intro_link(key, label):
        path = paths[key]
        if os.path.exists(os.path.join(args.repo_root, path)):
            return '<a href="%s%s">%s</a>' % (rel["root"], esc(path), esc(label))
        return "<b>%s</b>" % esc(label)

    w('<h2 id="why">중앙 규칙과 프로젝트 규칙 설계</h2>')
    w('<p>이전에 Claude를 이용해 공부하는 사이트를 만드는 과정에서 <strong>두 가지 문제를 '
      '반복해서 겪었습니다.</strong> 이에 대한 문제를 풀고 시작했습니다.</p>')
    w('<div class="steps">')
    for title, body in (
        ("한 프로젝트의 스펙이 다른 프로젝트로 새어 들어갑니다",
         "AI에게 디자인 가이드와 지켜야 할 규칙을 설명하고, 대화하면서 그 규칙이 자라는 구조로 "
         "설계했습니다. 그런데 프로젝트가 여럿이 되자 <b>A 프로젝트의 작업에 B 프로젝트의 스펙이 "
         "섞여 들어왔습니다.</b> 규칙과 결정이 한자리에 뒤엉켜 있으니 어느 프로젝트 것인지 "
         "가려낼 방법이 없었습니다."),
        ("산출물마다 완성도 차이가 존재했습니다",
         "디자인 가이드가 없다 보니 문서에 대해 작성을 요청할 때마다 가독성이나 구조가 매번 "
         "달라져서 보기가 힘들었습니다. <b>모든 문서가 공유하는 디자인 가이드</b>를 먼저 세우고, "
         "새로 만드는 화면도 그 가이드 안에서 해결하도록 제어했습니다."),
    ):
        w('<div class="step"><div class="body"><b>%s</b> — %s</div></div>' % (esc(title), body))
    w('</div>')

    w('<p>이러한 병목을 없애려고 <strong>폴더 규칙을 두 갈래로 정의했습니다.</strong></p>')
    w('<div class="card-grid">')
    w(card("중앙 규칙 — 모든 프로젝트가 따라야 하는 규칙",
           "무엇을 어떤 순서로 할지(<code>project-process/</code>), 산출물이 어떤 모양이어야 "
           "하는지(<code>design-guide/</code> · <code>design-template/</code>), 저장소를 어떻게 "
           "소개할지(<code>intro/</code>)를 담습니다. <b>어떤 프로젝트가 작업을 시작해도 "
           "일관성 있는 작업을 유지합니다.</b>",
           intro_link("central", "자세한 구조는 중앙 규칙 구조에서 다룹니다. →")))
    w(card("프로젝트 규칙 — 프로젝트마다 개별로 기억하는 것",
           "중앙 규칙에 의거하여 해당 프로젝트 안에서만 다루어야 하는 문서나 규칙이 쌓입니다 — 조사 기록, 채택한 것, "
           "확정 사양, 테스트 케이스, 그리고 내린 결정과 남은 작업. <b>다른 프로젝트가 참조하지 "
           "않으므로 한쪽의 결정이 다른 쪽으로 새지 않습니다.</b>",
           intro_link("project", "자세한 구조는 프로젝트 규칙 구조에서 다룹니다. →")))
    w('</div>')
    w('<p>이 둘을 기반으로, 앞으로 여러 테스트 사이트를 만들어도 <strong>일관성이 유지되고 '
      '이야기를 나누면서 「모든 프로젝트가 따라야 하는 규칙」이 자라는 형태</strong>로 저장소의 '
      '구조를 설계했습니다.</p>')

    # ── ③ MiyonChat 작업 과정
    w('<h2 id="how">MiyonChat 작업 과정</h2>')
    w('<p>AI 서비스를 검증하려면 어떤 것이 필요한지 이해하기 위해 다음과 같은 작업 과정을 '
      '거쳤습니다.</p>')
    w('<div class="steps">')
    for title, body, link, link_label in (
        ("서비스 중인 AI 서비스 사이트를 분석했습니다",
         "실제 서비스 중인 AI 채팅 서비스 사이트나 프로그램을 6개 분석하였습니다.",
         None, None),
        ("공통 기능의 기준을 세웠습니다",
         "AI 채팅 서비스 프로그램에서 겹치는 행동을 정리하였습니다.",
         None, None),
        ("그 외에 필요한 기능을 임시로 판단하여 추가하였습니다",
         "공통 기능을 제외하고 AI 채팅 서비스에 기본적으로 필요하다고 판단한 기능들을 "
         "추가하였습니다.",
         None, None),
        ("위 내용을 기반으로 검증할 대상인 「MiyonChat」을 설계하였습니다",
         "화면 요소마다 테스트 환경이 확인할 수 있는 이름표를 달고, 특정 상태를 판정할 수 있도록 "
         "디버그 환경을 만들어서 테스트 환경을 설계하였습니다.",
         "%ssut/index.html" % P, "직접 실행해보기"),
        ("테스트 케이스를 설계했습니다",
         "기능마다 확인해야 할 TC를 자동으로 설계하였습니다.",
         None, None),
        ("자동화 테스트 진행",
         "테스트 케이스를 기반으로 한 자동화 테스트를 진행하였습니다.",
         None, None),
    ):
        link_html = (' <a href="%s">%s →</a>' % (esc(link), esc(link_label))) if link else ""
        w('<div class="step"><div class="body"><b>%s</b> — %s%s</div></div>'
          % (esc(title), body, link_html))
    w('</div>')

    # ── ④ 검출한 결함
    w('<h2 id="issue">검출한 결함</h2>')
    w('<p>개발 과정에서 정해놓은 시스템 규칙과 다르게 동작하는 현상들에 대해 자동으로 결함을 '
      '검출하도록 하였습니다. <a href="%s%s">자동화 QA 리포트</a>에서도 '
      '어떤 결함이 검출되었는지 확인할 수 있습니다.</p>'
      % (rel["root"], dict((k, p) for k, _l, p in shell.INTRO)["report"]))
    w('<div class="tbl-scroll"><table><thead><tr><th>증상</th><th>원인</th>'
      '<th>조치</th></tr></thead><tbody>')
    for iss in d["issues"]:
        sym, cause, fix = issue_parts(iss)
        w('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
          % (esc(sym), esc(cause) or '<span class="foot">—</span>',
             ('%s에서 수정' % esc(fix)) if fix else esc(iss.get("resolution", ""))))
    w('</tbody></table></div>')

    # ── ⑤ 문서 요약 — 저장소가 어떻게 생겼는가와 이 프로젝트가 무엇을 냈는가를
    # 좌우로 가른다. 사이드바의 두 묶음(소개 · 문서)과 같은 갈래이고 이름도 같게 쓴다
    w('<h2 id="more">문서 요약</h2>')
    w('<div class="card-grid">')
    paths = dict((k, p) for k, _l, p in shell.INTRO)

    w('<div class="card"><h3>깃허브 폴더 구조</h3><div class="item-grid">')
    for key, title, desc in (
        ("central", "중앙 규칙",
         "절차서·규칙 문서·형식 기준을 프로젝트 밖에 두고, 프로젝트가 늘어도 같은 방식으로 "
         "일하게 했습니다."),
        ("project", "프로젝트 규칙",
         "한 프로젝트의 결정이 다른 프로젝트로 새지 않도록, 프로젝트 폴더와 중앙 규칙만 "
         "보게 했습니다."),
    ):
        exists = os.path.exists(os.path.join(args.repo_root, paths[key]))
        link = ('<a href="%s%s">%s</a>' % (rel["root"], esc(paths[key]), esc(title))
                if exists else '<b>%s</b> <span class="chip chip-unk">준비 중</span>' % esc(title))
        # 아직 없는 장은 누를 곳이 없으므로 강조도 걷는다(.item-off)
        w('<div class="item%s">%s<span class="foot">%s</span></div>'
          % ("" if exists else " item-off", link, esc(desc)))
    # 저장소 밖으로 나가는 둘은 실재 판정을 하지 않습니다 — 소개 페이지가 아니라
    # 언제나 거기 있는 자리입니다. 이름은 사이드바와 같은 자리에서 가져옵니다
    for title, desc, link in (
        ("깃허브 링크", "저장소 전체를 GitHub에서 봅니다", shell.REPO),
        ("%s 웹 링크" % shell.PROJECT_LABEL.get(S, S),
         "임시로 만든 AI 채팅 서비스로 이동하는 링크입니다.", "%ssut/index.html" % P),
    ):
        w('<div class="item"><a href="%s">%s</a>'
          '<span class="foot">%s</span></div>'
          % (esc(link), esc(title), esc(desc)))
    w('</div></div>')

    w('<div class="card"><h3>%s 관련</h3><div class="item-grid">'
      % esc(shell.PROJECT_LABEL.get(S, S)))
    for key, title, desc in (
        ("making", "프로젝트 개요", "프로젝트 MiyonChat에 대한 구조를 설명합니다."),
        ("tc", "TC 설계 규칙", "TC를 설계한 방식에 대해 정리했습니다."),
        ("tcsheet", "TC 시트 구성", "설계 규칙에 따른 시트의 구성을 정리했습니다."),
        ("auto", "자동화 설계와 결과",
         "자동화 설계 과정과 그에 따른 결과를 정리했습니다."),
        ("report", "자동화 QA 리포트", "자동화 테스트를 결과물로 보여줍니다."),
        ("trace", "추적 매트릭스",
         "기능 하나가 어떤 케이스·어떤 테스트 함수·어떤 결함으로 이어지는지 정리했습니다."),
        ("tree", "기능 골격",
         "MiyonChat을 구현하기 위해 사용된 전체 기능 구조에 대해 정리했습니다."),
        ("dict", "용어집",
         "MiyonChat을 구현하면서 사용된 프로젝트만의 용어를 정리했습니다."),
    ):
        exists = os.path.exists(os.path.join(args.repo_root, paths[key]))
        link = ('<a href="%s%s">%s</a>' % (rel["root"], esc(paths[key]), esc(title))
                if exists else '<b>%s</b> <span class="chip chip-unk">준비 중</span>' % esc(title))
        # 아직 없는 장은 누를 곳이 없으므로 강조도 걷는다(.item-off)
        w('<div class="item%s">%s<span class="foot">%s</span></div>'
          % ("" if exists else " item-off", link, esc(desc)))
    w('</div></div>')

    w('</div>')

    w('<div class="doc-footer">이 문서는 파생물입니다 — <code>gen_intro_html.py --page landing</code>으로 '
      '재생성합니다. 수치는 전부 정본에서 읽고, 자동화 결과는 커밋된 매트릭스 표에서 읽습니다.</div>')

    return "".join(o), "포트폴리오 홈"


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


def page_central(d, args, rel):
    """중앙 규칙 구조 — 모든 프로젝트가 따르는 절차·형식·소개가 어디 있고 무엇을 정하는지.

    목록은 폴더를 훑어 만들고 설명은 각 파일의 첫 문단·첫 줄에서 읽습니다. 여기에 요약을
    옮겨 적으면 규칙이 바뀔 때 이 페이지만 옛말을 하게 됩니다.
    """
    R = rel["root"]
    proc = os.path.join(args.repo_root, "project-process")
    rules_dir = os.path.join(proc, "rules")
    scripts_dir = os.path.join(proc, "scripts")
    o = []
    w = o.append

    rule_files = sorted(n for n in os.listdir(rules_dir) if n.endswith(".md"))
    scripts = sorted(n for n in os.listdir(scripts_dir)
                     if n.endswith(".py") and not n.startswith("_"))
    proj_path = dict((k, p) for k, _l, p in shell.INTRO)["project"]
    proj_link = ('<a href="%s%s">프로젝트 규칙 구조</a>' % (R, esc(proj_path))
                 if os.path.exists(os.path.join(args.repo_root, proj_path))
                 else "<b>프로젝트 규칙 구조</b>")

    w('<div class="doc-header"><h1>중앙 규칙: 모든 프로젝트가 따라야 하는 규칙</h1>')
    w('<p class="doc-lead">프로젝트를 시작하기 전, <strong>절차와 판단 기준과 형식부터 '
      '세웠습니다.</strong> 작업을 진행하는 도중 중앙 규칙 단위로 바뀌어야 하는 규칙이 있다면 '
      '유저에게 추가·편집할 것인지 제안하고, 유저는 그에 대한 결정을 내립니다. 이를 기반으로 '
      '어긋나는 규칙이 있다면 한쪽으로 일치시킴으로써, <strong>프로젝트를 진행할수록 자라는 '
      '구조</strong>로 설계하였습니다.</p>')
    w('<div class="meta-row"><span class="badge">규칙 문서 <b>%d편</b></span>'
      '<span class="badge">생성 도구 <b>%d개</b></span>'
      '<span class="badge">확인 게이트 <b>2곳</b></span></div></div>' % (len(rule_files), len(scripts)))

    # ── 전체 그림
    w('<h2 id="map">중앙 규칙 워크플로우</h2>')
    w('<p>중앙 규칙은 <strong>모든 작업 앞에</strong> 있고, 프로젝트는 그 규칙을 기반으로 삼아 '
      '자신만의 프로젝트에 필요한 규칙이나 문서를 추가로 작성해 나갑니다. 아래 그림은 중앙 규칙의 '
      '워크플로우를 도식화한 이미지입니다.</p>')
    svg = os.path.join(args.repo_root, "structure.svg")
    if os.path.exists(svg):
        body = io.open(svg, encoding="utf-8").read()
        body = body[body.index("<svg"):]
        w('<div class="card" style="padding:14px">%s</div>' % body)

    # ── 왜 중앙에 모았나
    w('<h2 id="why">왜 중앙 규칙을 분리했나요?</h2>')
    w('<div class="card-grid">')
    w(card("한 프로젝트의 결정이 다른 프로젝트에 유입되지 않도록 사전 차단",
           "규칙을 프로젝트 안에 두고 대화로 키우면, 프로젝트가 늘었을 때 <strong>A의 스펙이 B에 "
           "섞여 들어옵니다.</strong> 규칙을 밖으로 빼면 프로젝트는 서로를 참조할 일이 없어지고, "
           "공유되는 것은 「따라야 하는 기준」뿐입니다."))
    w(card("매번 같은 판단을 참조",
           "규칙이 늘어남에 따라 여러 문서에 담길 수 있는 규칙들의 중복을 제거하고, "
           "<strong>하나의 규칙을 기반으로 동일한 판단을 참조</strong>할 수 있도록 의도하였습니다."))
    w('</div>')

    # ── 무엇이 중앙 규칙인가
    w('<h2 id="what">무엇이 중앙 규칙에 포함되나요?</h2>')
    w('<p>판별 기준은 <strong>「문장에서 프로젝트 이름을 지워도 성립하는가」</strong>입니다. '
      '성립하면 중앙 규칙이고, 아니면 %s입니다.</p>' % proj_link)
    w('<div class="card-grid">')
    w(card("<code>project-process/</code> — 절차와 판단 기준",
           "프로젝트의 진행 절차의 규칙을 사전에 정의함으로써, <strong>프로젝트가 늘어도 같은 방식으로 "
           "일하도록</strong> 유도합니다.",
           "파이프라인 절차서 · 규칙 문서 %d편 · 중앙 용어집 · 생성 도구" % len(rule_files)))
    w(card("<code>design-guide/</code> — 형식의 정본",
           "색·타이포·컴포넌트의 정본이 하나라, 문서마다 스타일을 다시 정하지 않습니다. "
           "산출물은 만들 때마다 그 사본을 품어 네트워크 요청 없이 혼자 열립니다.",
           '<a href="%sdesign-guide/design-guide-master.html">시각 규칙서 열기</a>' % R))
    w(card("<code>design-template/</code> — 새 문서를 만들 때의 틀",
           "새 문서가 <strong>기존 템플릿으로 되는지, 기준을 고쳐야 하는지, 새로 만들어야 하는지</strong>를 "
           "세 갈래로 판별합니다. 문서의 목적과 다른 템플릿을 사용하지 않도록 <strong>일관적인 "
           "템플릿을 유도</strong>합니다.",
           "TC 시트 서식의 정본은 tc-sheet-master.xlsx의 명세서 시트"))
    w(card("<code>intro/</code> — 저장소를 소개하는 층",
           "지금 읽고 계신 문서들입니다. 「프로젝트를 만들기 전에 세운 규칙」처럼 특정 프로젝트 "
           "소유가 아닌 이야기가 섞이므로 프로젝트 밖에 둡니다.",
           "전부 생성기가 만드는 파생물입니다"))
    w('</div>')

    # ── 절차 (playbook의 STEP 제목을 읽어 온다)
    w('<h2 id="step">중앙 규칙의 작업 절차</h2>')
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
    w('<div class="callout warn">규칙을 파악하는 과정에서 <strong>중앙 규칙과 다른 상태가 '
      '들어오면 그 자리에서 맞추지 않고 유저에게 되묻습니다</strong> — 이 프로젝트의 예외로 '
      '둘 것인지, 중앙 규칙을 고칠 것인지. 임의로 한쪽에 맞추면 어느 것이 기준인지 알 수 없게 '
      '되고, 다음 프로젝트가 그 상태를 물려받습니다.</div>')

    # ── 규칙 문서 (폴더를 훑고 첫 문단을 읽는다)
    w('<h2 id="doc">규칙 문서</h2>')
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
    w('<p class="foot">md 문서와 폴더 링크는 GitHub 저장소에서 열리고, HTML 문서는 이 사이트에서 '
      '바로 렌더링됩니다 — GitHub Pages에서는 md가 원본 텍스트로 뜨기 때문입니다.</p>')

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
      '<code>gen_intro_html.py --page central</code>로 재생성합니다. 규칙 목록·절차 단계·'
      '도구 설명은 전부 실제 파일에서 읽고, 구조도는 <code>structure.svg</code>를 읽습니다.</div>')

    return "".join(o), "중앙 규칙 구조"


def doc_intro(path, limit=230):
    """md 본문의 첫 문단 — 그 문서가 스스로 밝힌 존재 이유를 그대로 가져온다.

    길면 줄이되 **문장 도중에는 자르지 않는다.** 문장 중간에서 끊긴 설명은 무슨 말인지
    알 수 없어, 설명을 싣지 않은 것과 다르지 않다.
    """
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
    if len(text) <= limit:
        return text
    # 한도 안에서 마지막으로 끝난 문장까지만 남긴다. 한 문장도 못 담으면 그때만 말줄임한다
    cut = max(text.rfind(m, 0, limit + 1) for m in ("다.", "요.", "다!", "다?"))
    if cut > 0:
        return text[:cut + 2]
    return text[:limit].rstrip() + "…"


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
# 페이지 ③ 프로젝트 규칙 구조 — 프로젝트 안에 무엇이 쌓이는가
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


def page_project(d, args, rel):
    """프로젝트 규칙 구조 — 프로젝트 안에 무엇이 쌓이고, 폴더마다 참조 규칙이 어떻게 다른지.

    폴더 목록과 참조 규칙은 이 저장소가 실제로 쓰는 구조 그대로이며, 수치는 정본에서 읽습니다.
    """
    S = d["slug"]
    R = rel["root"]
    o = []
    w = o.append

    central_path = dict((k, p) for k, _l, p in shell.INTRO)["central"]
    central_link = ('<a href="%s%s">중앙 규칙</a>' % (R, esc(central_path))
                    if os.path.exists(os.path.join(args.repo_root, central_path))
                    else "<b>중앙 규칙</b>")

    w('<div class="doc-header"><h1>프로젝트 규칙: 프로젝트마다 따로 쌓이는 규칙</h1>')
    w('<p class="doc-lead">%s에 의거하여 <strong>프로젝트마다 실제 작업이 쌓이는 공간</strong>입니다. '
      '여기서 정한 것은 해당 프로젝트 안에서만 유효하여, 다른 프로젝트가 참조하지 않습니다.</p>'
      % central_link)
    w('<div class="meta-row"><span class="badge">현재 프로젝트 <b>%d개</b></span>'
      '<span class="badge">기능 <b>%d개</b></span>'
      '<span class="badge">TC <b>%d건</b></span></div></div>'
      % (1, len(d["leaves"]), len(d["tcs"])))

    # ── 왜 분리하나
    w('<h2 id="why">왜 프로젝트마다 분리하나요?</h2>')
    w('<div class="card-grid">')
    w(card("다른 프로젝트의 규칙 확인 차단",
           "프로젝트는 본인 프로젝트 폴더와 중앙 규칙만을 확인하게 하여, <strong>다른 프로젝트의 "
           "규칙을 확인하는 과정 자체를 차단</strong>합니다."))
    w('</div>')
    w('<p>폴더를 어떻게 나누고 무엇을 따로 기억하는지는 <strong>프로젝트마다 다를 수 '
      '있습니다.</strong> 각 프로젝트의 규칙이 어떻게 설계되었는지는 각 프로젝트에서 확인하실 수 '
      '있습니다.</p>')

    # ── 프로젝트 목록 — 카드 하나가 프로젝트 하나다. 구성과 규칙은 그 프로젝트가
    #    스스로 설명하므로 여기서는 어디로 가면 되는지만 가리킨다
    #    2026-08-05: 허브를 폐지해 「프로젝트 개요」로 잇는다. 허브가 갖고 있던
    #    파이프라인·문서 지도가 그리로 옮겨 갔으므로 누르는 사람이 기대하던 내용이 나온다
    w('<h2 id="proj">프로젝트 목록</h2>')
    w('<div class="card">')
    w('<h3><a href="%s%s">%s</a></h3>'
      % (R, esc(shell.intro_path("making")), esc(S)))
    w('<p>출시 서비스 역분석 → 기능 목록 → 확정 사양 → 검증 대상 제작 → 테스트 케이스 → '
      '자동화 → 고장 주입 → 리포트 → CI까지 한 바퀴를 완주한 프로젝트입니다.</p>')
    w('<p class="foot">기능 %d개 · TC %d건 · 자동화 %d건 · 빌드 %s</p>'
      % (len(d["leaves"]), len(d["tcs"]), d["auto"], esc(d["build"])))

    w('</div>')

    w('<div class="doc-footer">이 문서는 파생물입니다 — '
      '<code>gen_intro_html.py --page project</code>로 재생성합니다. 수치는 기능 골격 정본과 '
      'TC 설계 원본에서 읽습니다.</div>')

    return "".join(o), "프로젝트 규칙 구조"


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


def tree_outline(md_path, max_depth=2):
    """골격 정본에서 얕은 개요만 뽑는다 — 이름과 뎁스뿐이고 칩·비고는 버린다.

    전부 실으면 「기능 골격」 문서와 같아지므로, 여기서는 「어떤 영역에 어떤 묶음이
    있나」까지만 보입니다. 더 볼 사람은 기능 골격으로 갑니다.
    """
    try:
        data = parse_tree(io.open(md_path, encoding="utf-8").read())
    except (OSError, ValueError):
        return []
    return [(n["depth"], n["name"]) for n in data["nodes"] if n["depth"] <= max_depth]


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
    """프로젝트 개요 — 왜 직접 만들었고, 조사에서 무엇을 넣고 뺐는지, 값은 왜 그 숫자인지.

    근거 표는 판단 기록(rationale)에서 그대로 읽습니다. 이 페이지에 옮겨 적으면
    근거가 바뀔 때 여기만 옛말을 하게 됩니다.
    """
    S = d["slug"]
    P, R = rel["project"], rel["root"]
    PJ = args.project_dir
    o = []
    w = o.append

    tree_md = os.path.join(PJ, "spec", "%s-feature-tree.md" % S)
    counts, excluded = tree_scope(tree_md)
    n_leaf = len(d["leaves"])

    w('<div class="doc-header"><h1>MiyonChat 프로젝트 개요</h1>')
    w('<p class="doc-lead">출시된 AI 챗·미연시 서비스를 분석하며 <strong>「이런 서비스를 검증하려면 '
      '무엇을 중점적으로 봐야 할까」</strong>를 고민했습니다. 레퍼런스로 삼은 서비스의 공통점이나, '
      '핵심으로 가져올 만한 기능을 골라 AI 캐릭터와 대화하는 서비스 '
      '<strong><a href="%ssut/index.html">MiyonChat</a></strong>을 설계해 만들었고, '
      '그 위에서 테스트 케이스를 설계해 '
      '<strong>자동화 테스트까지 돌려 검증했습니다.</strong></p>' % P)
    w('<div class="meta-row">'
      '<span class="badge">조사에서 채택 <b>%d개</b></span>'
      '<span class="badge">직접 세움 <b>%d개</b></span>'
      '<span class="badge">범위에서 제외 <b>%d개</b></span>'
      '<span class="badge">빌드 <b>%s</b></span></div></div>'
      % (counts["REF"], counts["ADD"], len(excluded), esc(d["build"])))

    # ── 왜 이 프로젝트인가 — 검증 대상을 직접 만들기로 한 경위.
    #    제목 없이 문장만 세운다. 세 항목이 하나의 판단으로 이어지므로 쪼개면 흐름이 끊긴다
    w('<h2 id="why">왜 해당 프로젝트를 진행했나요?</h2>')
    w('<div class="steps">')
    for body in (
        "출시된 AI 챗·미연시 서비스를 분석하며 <strong>「이런 서비스를 검증하려면 무엇을 "
        "중점적으로 봐야 할까」</strong>를 고민했습니다.",

        "AI 캐릭터 기반 채팅은 캐릭터마다 검증 범위가 모호하다고 보았고, 서비스의 전체 플로우는 "
        "어느 서비스든 비슷할 것이라 판단하여, <strong>AI 채팅 기반 서비스의 전체 흐름도를 "
        "이해하고자</strong> 조사하기로 했습니다.",

        "서비스 중인 사이트에서는 이미 대부분의 결함이 수정된 뒤라 다양한 예외 처리 사항을 "
        "확인하게 되면 <strong>긍정적인 결과만 확인할 수 있었습니다.</strong> 그 과정을 직접 "
        "겪어 보며 워크플로우를 더 깊이 이해하고, 그것을 QA의 작업물로 남기기 위해 "
        "<strong>임시 서비스 사이트를 직접 만들고 그 위에서 테스트하기로</strong> "
        "결정했습니다.",
    ):
        w('<div class="step"><div class="body">%s</div></div>' % body)
    w('</div>')

    # ── 조사
    w('<h2 id="ref">첫 시작 작업: 레퍼런스 조사</h2>')
    w('<p>AI 채팅 기반 서비스가 <strong>어떤 방식으로 운영되는지</strong> 조사했습니다. 회사마다 '
      '추구하는 핵심 경험은 다르겠지만 서비스가 돌아가는 전체 플로우는 비슷할 것이라 판단하여, '
      '총 <strong>6개의 레퍼런스</strong>를 조사했습니다.</p>')
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
    w('<div class="callout">AI가 레퍼런스를 조사하는 과정에서 <strong>실제로 확인하지 못하거나 '
      '저작권에 영향을 받을 만한 내용은 임의로 채우지 못하도록</strong> 설정했습니다 — 성인 인증 '
      '게이트 안쪽처럼 진입하지 않기로 한 자리, 그리고 각 사이트의 AI 캐릭터 정보처럼 옮겨 적으면 '
      '안 되는 것입니다. 확인하지 못한 것은 추측으로 채우지 않고 미확인으로 남겼습니다.</div>')

    # ── 좁히기
    w('<h2 id="narrow">조사한 레퍼런스는 그대로 사용하지 못하게 설정했습니다</h2>')
    w('<p>타 서비스에서 확인한 내용을 곧바로 테스트 환경으로 구현하게 되면, <strong>여러 규칙이 '
      '섞여 혼란을 일으킬 수도 있다</strong>고 판단했습니다. 그래서 다음과 같은 단계로 테스트 환경을 '
      '구축하기로 결정했습니다.</p>')
    w('<div class="steps">')
    for title, body in (
        ("<code>analysis/</code> 폴더",
         "조사한 레퍼런스에서 확인한 것들을 <b>전부 모아 놓습니다.</b>"),
        ("<code>reference/</code> 폴더",
         "그중 <b>테스트 환경에 적용할 기능을 확정</b>합니다."),
        ("<code>spec/</code> 폴더",
         "reference에서 확정한 기능과 추가해야 할 기능에 대한 <b>구조나 규칙을 설계</b>합니다."),
        ("테스트 환경 설계",
         "<b><code>spec/</code> 폴더의 문서만 바라보며</b> 테스트 환경을 설계합니다."),
    ):
        w('<div class="step"><div class="body"><b>%s</b> — %s</div></div>' % (title, body))
    w('</div>')
    w('<p>다음과 같은 구조를 통해 테스트 환경에 들어가야 할 기능에, <strong>기존의 조사한 레퍼런스 '
      '데이터가 혼용되지 않도록</strong> 설계하였습니다.</p>')
    w('<div class="stats">')
    w(stat(counts["REF"], "조사에서 채택", "본 것을 근거로 세운 항목"))
    w(stat('<em>%d</em>' % counts["ADD"], "직접 세움", "조사에 없어 판단으로 채운 항목"))
    w(stat(n_leaf, "검증 대상 기능", "이번 범위에서 만든 것"))
    w(stat(counts["보류"], "보류", "트리에만 두고 만들지 않음"))
    w('</div>')

    # ── 플로우 구조 설계 · 문서 지도 (프로젝트 허브에서 옮겨 옴 — 2026-08-05)
    w('<h2 id="pipe">플로우 구조 설계</h2>')
    w('<p>테스트 환경에 필요한 구조를 다음과 같이 설계하였습니다.</p>')
    outline = tree_outline(tree_md)
    tree_html = ""
    if outline:
        rows = "".join(
            '<div class="body" style="padding-left:%dpx">%s%s</div>'
            % (14 * (depth - 1), '<span class="depth-tag">D%d</span> ' % depth, esc(name))
            for depth, name in outline)
        tree_html = ('<details class="fold"><summary>기능 골격 요약 보기 — 상위 두 단계 '
                     '%d줄</summary><div class="fold-body">%s</div></details>'
                     % (len(outline), rows))

    paths = dict((k, p) for k, _l, p in shell.INTRO)

    def doc_link(key, label):
        return '<a href="%s%s">%s</a>' % (R, esc(paths[key]), esc(label))

    w('<div class="steps">')
    for body, extra in (
        ("<b>기능 골격</b> — 테스트 환경에 들어갈 기능을 Depth 계층으로 정리합니다.", tree_html),
        ("<b>design 명세</b> — 기능 골격이 <b>어떤 기능이 들어갈 것인가</b>에 대한 정의라면, "
         "design 명세는 <b>얼마나, 어떤 규칙으로</b> 진행될 것인지 상세 규칙을 설계합니다.", ""),
        ("<b>테스트 환경(SUT) 제작</b> — 기능 골격과 design 명세를 기반으로 검증 대상을 직접 "
         "만듭니다. <a href=\"%ssut/index.html\">%s 웹 링크 →</a>"
         % (P, shell.PROJECT_LABEL.get(S, S)), ""),
        ("<b>TC 설계</b> — 기능 골격과 design 명세를 기반으로 TC를 설계합니다. TC 설계 규칙은 "
         "%s 페이지를 참고합니다." % doc_link("tc", "TC 설계 규칙"), ""),
        ("<b>자동화</b> — 설계된 TC를 기반으로 SUT가 정상적으로 실행되는지 확인합니다.", ""),
        ("<b>결함 주입</b> — 고의로 결함을 설정했을 때 실제로 깨지는지 확인하여, 실제로 결함 "
         "발생 시 정상적으로 차단되는지 확인합니다.", ""),
        ("<b>리포트</b> — 자동화 실행 결과에 대해 정리합니다. %s"
         % doc_link("report", "QA 리포트 →"), ""),
    ):
        w('<div class="step"><div class="body">%s%s</div></div>' % (body, extra))
    w('</div>')

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

    # ── 뺀 것
    if excluded:
        w('<h2 id="drop">검증 범위 제외 영역</h2>')
        w('<p>다음과 같은 기능은 검증 범위에서 제외했습니다.</p>')
        w('<div class="tbl-scroll"><table><thead><tr><th>뺀 것</th><th>이유</th>'
          '</tr></thead><tbody>')
        for name, why in excluded:
            w('<tr><td>%s</td><td>%s</td></tr>' % (esc(name), md_inline(why)))
        w('</tbody></table></div>')

    # ── 만들 때 지킨 조건
    w('<h2 id="make">만들 때 지킨 조건</h2>')
    w('<div class="card-grid">')
    w(card("명세를 먼저 고칩니다",
           "코드가 확정 사양과 어긋나면 코드를 슬쩍 맞추지 않고 <strong>명세를 먼저 고치고 그 변경을 "
           "기록</strong>했습니다. 반대로 하면 테스트의 기대값이 코드를 따라가게 되어, "
           "무엇이 옳은지 아무도 모르게 됩니다."))
    w(card("테스트가 잡을 이름표를 먼저 정합니다",
           "화면 요소를 무엇으로 찾을지(<code>data-testid</code> 명명 규칙)를 코드 첫 줄 전에 확정했습니다. "
           "나중에 붙이면 테스트가 화면 생김새나 문구에 매달리게 되고, 디자인이 바뀔 때마다 깨집니다."))
    w(card("기능 목록에 없는 것은 만들지 않습니다",
           "만들다 보면 「이것도 있으면 좋겠다」가 계속 생깁니다. 목록에 없는 기능은 검증 대상이 아니므로, "
           "넣고 싶으면 <strong>목록을 먼저 고치고</strong> 그 이력을 남겼습니다."))
    w('</div>')

    w('<div class="stats">')
    w(stat(esc(d["build"]), "지금 빌드", "화면 단위로 끊어 올린 결과"))
    w(stat(n_leaf, "만든 기능", "목록의 검증 대상 전부"))
    w(stat(len(d["testids"]), "테스트가 잡는 요소", "이름표를 달아 둔 화면 조작 지점"))
    w('</div>')

    w('<div class="doc-footer">이 문서는 파생물입니다 — '
      '<code>gen_intro_html.py --page making</code>으로 재생성합니다. 수치와 제외 사유는 '
      '기능 목록 정본에서 그대로 읽습니다.</div>')

    return "".join(o), "프로젝트 개요"


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

    w('<div class="doc-header"><h1>테스트 케이스 설계 규칙</h1>')
    w('<p class="doc-lead">테스트 환경에서 <strong>Happy path</strong>(계획대로 완벽히 돌아가는 최상의 '
      '상황)만 체크하면 <strong>결함을 놓칠 가능성이 높습니다.</strong> 그래서 테스트 항목의 기준을 '
      '어떻게 판정할지, 무엇을 확인해야 할지를 정의하였습니다.</p>')
    w('<div class="meta-row">'
      '<span class="badge">케이스 <b>%d건</b></span>'
      '<span class="badge">영역 <b>%d개</b></span>'
      '<span class="badge">사람이 직접 <b>%d건</b></span>'
      '<span class="badge">규칙 정본 <b>rules/</b></span></div></div>'
      % (len(tcs), len(areas), n_manual))

    # ── 네 갈래 전개
    w('<h2 id="expand">테스트 항목의 기준 분류</h2>')
    w('<p>테스트 항목의 기준에 따라 다음과 같이 테스트하도록 유도했습니다.</p>')
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
    w('<h2 id="vt">테스트 판정 방식 결정</h2>')
    w('<p>테스트 항목에 따라 <strong>무엇을 기준으로 통과 처리할 것인지</strong> 정해집니다.</p>')
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
    w('<p>대조하는 과정에서 아래 대상은 검증 대상에서 제외하였습니다.</p>')
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
    w(card("결함 시트를 함께 넣습니다",
           "발견한 결함을 다른 도구에 적으면 케이스와 끊깁니다. 같은 파일 안에 두고 케이스 번호로 "
           "이으면 <strong>어떤 케이스가 어떤 결함을 잡았는지</strong>가 남습니다."))
    w('</div>')
    w('<p class="foot">서식 규칙의 정본은 <a href="%s/project-process/rules/tc-sheet-format.md">'
      '<code>rules/tc-sheet-format.md</code></a>와 시트 안의 명세서 탭입니다 — 둘을 교차 '
      '검증합니다.</p>' % BLOB)

    w('<div class="doc-footer">이 문서는 파생물입니다 — '
      '<code>gen_intro_html.py --page tc</code>로 재생성합니다. 건수·영역·제외 사유는 TC 설계 '
      '원본에서, 커버리지 그림은 <code>diagrams/coverage-axes.svg</code>에서 읽습니다.</div>')

    return "".join(o), "TC 설계 규칙"


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
    w('<p class="doc-lead">테스트는 <strong>아무것도 확인하지 않았을 때도 통과하게 됩니다.</strong> '
      '그래서 자동화를 짤 때 두 가지를 기반으로 설계했습니다.</p>')
    w('<div class="steps">')
    for body in (
        "고의로 결함을 설정했을 때 <strong>실제로 깨지는지 확인</strong>하여, 실제로 결함 발생 시 "
        "정상적으로 차단되는지 확인",
        "<strong>화면이 바뀌어도 자동으로 화면을 읽고 확인</strong>할 수 있도록 설정",
    ):
        w('<div class="step"><div class="body">%s</div></div>' % body)
    w('</div>')
    w('<div class="meta-row">'
      '<span class="badge">자동화 <b>%d건</b></span>'
      '<span class="badge">자동화 대상 케이스 <b>%d건</b></span>'
      '<span class="badge">심은 고장 <b>%d종</b></span>'
      '<span class="badge">빌드 <b>%s</b></span></div></div>'
      % (d["auto"], n_auto_tc, len(faults), esc(d["build"])))

    # ── 접점
    w('<h2 id="iface">테스트가 붙잡을 접점을 먼저 심었습니다</h2>')
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
    w('<h2 id="fault">고장을 심어 탐지력을 증명합니다</h2>')
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
      '<a href="%s%s">자동화 QA 리포트</a>입니다.</p>'
      % (rel["root"], dict((k, p) for k, _l, p in shell.INTRO)["report"]))

    w('<div class="doc-footer">이 문서는 파생물입니다 — '
      '<code>gen_intro_html.py --page auto</code>로 재생성합니다. 접점 규칙은 '
      '<code>rules/sut-automation.md</code>에서, 담당 근거는 결함 기대표에서, 실행 결과는 커밋된 '
      '매트릭스 표에서, CI 단계는 워크플로 파일에서 읽습니다.</div>')

    return "".join(o), "자동화 설계와 결과"


PAGES = {"landing": page_landing, "central": page_central,
         "project": page_project, "making": page_making,
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
    body, crumb = PAGES[args.page](d, args, rel)

    css, js = shell.assets(args.css, args.js)
    # 사이드바는 모든 문서가 같은 것을 씁니다 — 정본은 shell.sidebar 하나입니다
    # (만든 사람 정보는 넣지 않습니다 — 2026-08-04 사용자 확정)
    # 회색 처리는 「아무도 만들지 않는 페이지」에만 씁니다. 판정은 둘 중 하나면 통과입니다 —
    # ① 이 생성기가 만들 수 있다(--page 키가 있다) ② 파일이 이미 있다(다른 생성기가 만든다).
    # 디스크만 보면 여러 장을 한꺼번에 다시 만들 때 아직 안 만든 장이 회색으로 굳고,
    # 키만 보면 리포트·용어집처럼 남이 만드는 문서가 회색이 됩니다. 둘 다 실제로 겪었습니다
    planned = set(path for key, _l, path in shell.INTRO if key in PAGES)
    side = shell.sidebar(
        args.slug, args.page, rel["project"],
        "골격 v%s%s" % (d["tree_version"], " · " + d["build"] if d["build"] else ""),
        out_path=args.output,
        exists=lambda p: p in planned or os.path.exists(os.path.join(args.repo_root, p)))

    html_out = "".join([
        shell.head("QA-VisualNovel-Portfolio — %s" % crumb, css, js),
        '<body><div class="app">', side, '<div class="main">',
        shell.topbar("QA-VisualNovel-Portfolio", crumb),
        '<div class="wrap">', body, shell.close_body(),
    ])
    shell.save(args.output, html_out)
    print("saved %s | 기능 단위 %d · TC %d · 자동화 %d · 결함 %d종"
          % (args.output, len(d["leaves"]), len(d["tcs"]), d["auto"], len(d["faults"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
