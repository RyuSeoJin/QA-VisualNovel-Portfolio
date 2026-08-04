# -*- coding: utf-8 -*-
"""shell.py — 산출물 공통 셸(사이드바·상단 바·테마 토글)을 한 곳에서 발행

왜 모듈인가
-----------
  사이드바 항목을 생성기마다 적어 두면 문서마다 메뉴가 갈라집니다. 리포트에는 있는
  항목이 매트릭스에는 없는 식입니다. 항목은 여기 한 곳에 두고, 생성기는 「지금 어느
  문서인가」와 「이 문서의 절 목록」만 넘깁니다.

  스타일 정본은 `design-guide/design-guide-master.css`, 동작 정본은 같은 폴더의
  `design-guide-master.js`입니다. 산출물은 그 둘을 생성 시점 사본으로 inline해
  네트워크 요청 0건인 단일 파일이 됩니다.

쓰는 곳
-------
  셸을 입히는 문서는 **여러 장이 서로를 참조하는 산출물**입니다 — 프로젝트 허브 ·
  QA 리포트 · 추적 매트릭스. 한 장으로 끝나는 문서(기능 골격 트리 등)는 셸 없이
  `head()`만 쓰고 테마 토글은 문서 머리말에 답니다(`header_toggle()`).
"""
import html
import io
import os

REPO = "https://github.com/RyuSeoJin/QA-VisualNovel-Portfolio"
BLOB = REPO + "/blob/main"

#: 사이드바 「산출물」 묶음 — (키, 라벨, 프로젝트 폴더 기준 경로)
NAV = (
    ("hub", "프로젝트 허브", "index.html"),
    ("report", "QA 리포트", "automation/report/{S}-report.html"),
    ("trace", "추적 매트릭스", "automation/report/{S}-traceability.html"),
    ("tree", "기능 골격", "spec/{S}-feature-tree.html"),
    ("sut", "SUT 실행", "sut/index.html"),
)

#: 사이드바 「저장소」 묶음 — Pages에서 404가 나는 md·폴더·xlsx는 절대 URL로 건다
OUT = (
    ("TC 시트", BLOB + "/projects/{S}/test-case/{S}-tc-v1.0.xlsx", "xlsx"),
    ("기능 골격 정본", BLOB + "/projects/{S}/spec/{S}-feature-tree.md", "md"),
    ("저장소", REPO, "git"),
)

#: 사이드바 「소개」 묶음 — (키, 라벨, 저장소 루트 기준 경로)
#: 랜딩에서 갈라지는 읽기 순서 그대로이며, 아직 없는 페이지는 링크 없이 회색으로 남는다
INTRO = (
    ("landing", "포트폴리오 홈", "index.html"),
    ("structure", "저장소 구조", "intro/repo-structure.html"),
    ("foundation", "토대 — 작업 규칙", "intro/foundation.html"),
    ("making", "제작 과정", "intro/miyonchat-making.html"),
    ("tc", "TC 설계 규칙", "intro/tc-design.html"),
    ("auto", "자동화 설계와 결과", "intro/automation.html"),
)


def esc(s):
    return html.escape(str(s if s is not None else ""))


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def assets(css_path, js_path=None):
    """마스터 CSS·JS를 읽어 온다. JS 경로를 안 주면 CSS 옆에서 찾는다."""
    css = read(css_path)
    if js_path is None:
        js_path = os.path.join(os.path.dirname(os.path.abspath(css_path)),
                               "design-guide-master.js")
    js = read(js_path) if os.path.exists(js_path) else ""
    return css, js


def head(title, css, js, extra_style=""):
    """<head>까지. JS는 <head>에서 동기로 돌아 첫 페인트 전에 테마를 정한다."""
    return (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>%s</title><style>%s%s</style><script>%s</script></head>'
        % (esc(title), css, extra_style, js))


def header_toggle():
    """셸이 없는 문서용 — .doc-header 안에 넣으면 오른쪽 위에 붙는다."""
    return '<button class="icon-btn" data-theme-toggle>다크</button>'


def nav_group(title, items):
    """items: (라벨, href 또는 None, 활성 여부, 태그). href가 None이면 링크 없이 회색으로."""
    o = ['<div class="nav-sec">%s</div>' % esc(title)]
    for label, href, active, tag in items:
        tag_html = ('<span class="tag">%s</span>' % esc(tag)) if tag else ""
        if href:
            o.append('<a class="nav-i%s" href="%s">%s%s</a>'
                     % (" on" if active else "", esc(href), esc(label), tag_html))
        else:
            o.append('<span class="nav-i nav-off">%s%s</span>' % (esc(label), tag_html))
    return "".join(o)


def sidebar_from(groups, head_href, head_title, head_sub, toc=(), foot=""):
    """묶음을 그대로 받아 사이드바를 만든다. groups: (제목, items) 목록."""
    o = ['<aside class="side">']
    o.append('<div class="side-head"><a href="%s">%s</a><span class="sub">%s</span></div>'
             % (esc(head_href), esc(head_title), esc(head_sub)))
    o.append('<nav class="side-nav">')
    for title, items in groups:
        o.append(nav_group(title, items))
    if toc:
        o.append('<div class="nav-sec">이 문서</div>')
        for anchor, label in toc:
            o.append('<a class="nav-sub" href="#%s">%s</a>' % (esc(anchor), esc(label)))
    o.append('</nav>')
    if foot:
        o.append('<div class="side-foot">%s</div>' % esc(foot))
    o.append('</aside>')
    return "".join(o)


def intro_group(current, root, exists=None):
    """소개 묶음. root = 저장소 루트로 가는 상대 경로 접두("" 또는 "../").
    exists(경로)가 False면 링크 없이 회색으로 남긴다 — 아직 안 만든 페이지."""
    items = []
    for key, label, path in INTRO:
        # 지금 만들고 있는 페이지는 아직 파일이 없다 — 자기 자신은 항상 있는 것으로 본다
        ok = key == current or exists is None or bool(exists(path))
        items.append((label, (root + path) if ok else None, key == current, ""))
    return ("소개", items)


def sidebar(slug, current, rel, toc=(), foot=""):
    """산출물 문서용 — rel = 출력 파일에서 프로젝트 폴더로 가는 상대 경로 접두."""
    out_items = [(label, rel + path.format(S=slug), key == current, "")
                 for key, label, path in NAV]
    repo_items = [(label, url.format(S=slug), False, tag) for label, url, tag in OUT]
    return sidebar_from((("산출물", out_items), ("저장소", repo_items)),
                        rel + "index.html", slug, "QA 검증 워크스페이스", toc, foot)


def topbar(crumb_root, crumb_doc):
    return (
        '<header class="topbar">'
        '<button class="icon-btn side-toggle" aria-label="메뉴 열기">☰</button>'
        '<div class="crumb">%s · <b>%s</b></div><span class="sp"></span>'
        '<button class="icon-btn" data-theme-toggle>다크</button></header>'
        % (esc(crumb_root), esc(crumb_doc)))


def open_body(slug, current, rel, crumb_doc, toc=(), foot=""):
    """<body>부터 본문 시작(.wrap 열림)까지."""
    return ('<body><div class="app">%s<div class="main">%s<div class="wrap">'
            % (sidebar(slug, current, rel, toc, foot), topbar(slug, crumb_doc)))


def close_body():
    return '</div></div></div><div class="backdrop"></div></body></html>'


def table_tools(table_id, placeholder="검색", buttons=()):
    """표 도구 한 줄 — 검색 · 필터 칩 · 건수.

    buttons: (라벨, 종류, 값, 값2) 목록.
      ("결정적", "col", 2, "결정적")  → 2번 열 텍스트에 값이 있으면 표시
      ("이슈 있음", "attr", "issue", "1") → 행의 data-issue 가 "1"이면 표시
    """
    o = ['<div class="tbl-tools" data-table="%s">' % esc(table_id)]
    o.append('<input class="tbl-search" type="search" placeholder="%s">' % esc(placeholder))
    for label, kind, key, val in buttons:
        attr = ('data-col="%s"' % esc(key)) if kind == "col" else ('data-attr="%s"' % esc(key))
        o.append('<button class="fbtn" %s data-val="%s">%s</button>'
                 % (attr, esc(val), esc(label)))
    o.append('<span class="tbl-count"></span></div>')
    return "".join(o)
