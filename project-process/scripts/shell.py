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
  **사이드바에서 열리는 문서에는 전부 입힙니다**(2026-08-05 개정). 메뉴로 들어간 페이지에
  그 메뉴가 없으면 돌아갈 길이 사라지기 때문입니다. 예외는 SUT 하나로, 검증 대상은 문서가
  아니라 테스트가 조작하는 제품이라 화면 구조를 건드리지 않습니다.
"""
import html
import io
import os

REPO = "https://github.com/RyuSeoJin/QA-VisualNovel-Portfolio"
BLOB = REPO + "/blob/main"

#: 검증 대상 자체로 가는 링크 — (키, 라벨, 프로젝트 폴더 기준 경로).
#: 문서가 아니라 조작해 보는 제품이라 「문서」 묶음 끝에 붙되 새 탭으로 연다
SUT_LINK = ("sut", "서비스 웹 링크", "sut/index.html")

#: 새 탭에서 여는 항목. 기준은 **사이트 밖으로 나가는가**이다 — SUT는 읽는 문서가 아니라
#: 조작해 보는 제품이고, 내려받기·GitHub은 저장소 밖으로 나간다. 둘 다 읽던 문서를 덮지 않는다
NEW_TAB = ("sut",)

#: 사이드바 「내려받기」 묶음 — 열어 보는 문서가 아니라 받아 가는 파일이다.
#: Pages에서 404가 나므로 절대 URL로 걸고, 저장소를 벗어나므로 새 탭이다
OUT = (
    ("TC 시트", BLOB + "/projects/{S}/test-case/{S}-tc-v1.0.xlsx", "xlsx"),
)

#: 저장소 자체로 가는 링크. 프로젝트가 아니라 **워크스페이스 전체**를 가리키므로
#: 프로젝트 묶음이 아니라 「소개」 끝에 붙인다
REPO_LINK = ("포트폴리오 깃허브 링크", REPO, "git")

#: 사이드바에서 워크스페이스 이야기와 프로젝트 이야기를 가르는 기준.
#: 앞은 프로젝트가 늘어도 그대로이고, 뒤는 프로젝트마다 한 벌씩 생긴다
WORKSPACE_INTRO = ("landing", "central", "project")
PROJECT_INTRO = ("making", "tc", "auto", "report", "trace", "tree", "dict")

#: 프로젝트 카테고리에 표시할 이름. 없으면 slug를 그대로 쓴다
PROJECT_LABEL = {"qa-lab-miyonchat": "MiyonChat"}

#: 프로젝트를 파일명에서 부르는 짧은 이름. 폴더는 slug(qa-lab-miyonchat)를 쓰지만
#: 파일 접두는 짧게 간다 — 이름이 길어지면 파일 목록에서 뒤쪽 구분이 안 보인다
PROJECT_PREFIX = {"qa-lab-miyonchat": "miyonchat"}

#: 사이드바 「소개」 묶음 — (키, 라벨, 저장소 루트 기준 경로)
#: 파일명 규칙: 워크스페이스 문서는 `main-`, 프로젝트 문서는 `{프로젝트}-` 접두.
#: 프로젝트가 늘었을 때 같은 이름이 부딪히지 않게 하려는 것이다.
#: 루트 `index.html`만 예외 — Pages의 진입점이라 이름을 바꿀 수 없다
INTRO = (
    ("landing", "포트폴리오 홈", "index.html"),
    ("central", "중앙 규칙 구조", "intro/main-central-rules.html"),
    ("project", "프로젝트 규칙 구조", "intro/main-project-rules.html"),
    ("making", "프로젝트 개요", "intro/miyonchat-overview.html"),
    ("tc", "TC 설계 규칙", "intro/miyonchat-tc-design.html"),
    ("auto", "자동화 설계와 결과", "intro/miyonchat-automation.html"),
    ("report", "자동화 QA 리포트", "intro/miyonchat-report.html"),
    ("trace", "추적 매트릭스", "intro/miyonchat-traceability.html"),
    ("tree", "기능 골격", "intro/miyonchat-feature-tree.html"),
    ("dict", "용어집", "intro/miyonchat-dictionary.html"),
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
    """items: (라벨, href 또는 None, 활성 여부, 태그[, 새 탭 여부]).

    href가 None이면 링크 없이 회색으로 남습니다. 다섯 번째 값이 참이면 새 탭에서 엽니다.
    """
    o = ['<div class="nav-sec">%s</div>' % esc(title)]
    for item in items:
        label, href, active, tag = item[:4]
        blank = bool(item[4]) if len(item) > 4 else False
        tag_html = ('<span class="tag">%s</span>' % esc(tag)) if tag else ""
        if href:
            o.append('<a class="nav-i%s" href="%s"%s>%s%s</a>'
                     % (" on" if active else "", esc(href),
                        ' target="_blank" rel="noopener"' if blank else "",
                        esc(label), tag_html))
        else:
            o.append('<span class="nav-i nav-off">%s%s</span>' % (esc(label), tag_html))
    return "".join(o)


def sidebar_from(groups, head_href, head_title, head_sub, foot=""):
    """묶음을 그대로 받아 사이드바를 만든다.

    groups: (제목, items) 목록. 제목 앞에 "@"를 붙이면 **카테고리 머리말**로 나가고,
    그 아래 묶음들이 그 카테고리에 속한 것으로 읽힙니다.

    문서 안의 절 목록(「이 문서」)은 넣지 않습니다 — 본문 제목이 이미 그 역할을 하고,
    사이드바에 겹쳐 두면 항목이 두 배로 늘어 메뉴가 읽히지 않습니다.
    """
    o = ['<aside class="side">']
    o.append('<div class="side-head"><a href="%s">%s</a><span class="sub">%s</span></div>'
             % (esc(head_href), esc(head_title), esc(head_sub)))
    o.append('<nav class="side-nav">')
    for title, items in groups:
        if title.startswith("@"):
            o.append('<div class="nav-cat">%s</div>' % esc(title[1:]))
            continue
        o.append(nav_group(title, items))
    o.append('</nav>')
    if foot:
        o.append('<div class="side-foot">%s</div>' % esc(foot))
    o.append('</aside>')
    return "".join(o)


def intro_group(current, root, exists=None, keys=None, title="소개"):
    """소개 묶음. root = 저장소 루트로 가는 상대 경로 접두("" 또는 "../").

    keys를 주면 그 키만 순서대로 뽑는다 — 워크스페이스 문서와 프로젝트 문서를 갈라
    두기 위해서다. exists(경로)가 False면 링크 없이 회색으로 남긴다(아직 안 만든 페이지).
    """
    picked = [(k, l, p) for k, l, p in INTRO if keys is None or k in keys]
    if keys is not None:
        picked.sort(key=lambda t: list(keys).index(t[0]))
    items = []
    for key, label, path in picked:
        # 지금 만들고 있는 페이지는 아직 파일이 없다 — 자기 자신은 항상 있는 것으로 본다
        ok = key == current or exists is None or bool(exists(path))
        items.append((label, (root + path) if ok else None, key == current, ""))
    return (title, items)


def repo_root():
    """shell.py 자리에서 저장소 루트를 되짚는다 — project-process/scripts/shell.py 기준."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def root_rel(out_path):
    """출력 파일에서 저장소 루트로 가는 상대 경로 접두."""
    r = os.path.relpath(repo_root(), os.path.dirname(os.path.abspath(out_path)))
    r = r.replace(os.sep, "/")
    return "" if r == "." else r + "/"


def intro_path(key):
    """소개 묶음 한 장의 저장소 루트 기준 경로. 정본은 INTRO 하나다 —
    본문에서 링크를 손으로 적으면 파일명이 바뀔 때 사이드바만 따라오고 본문은 남는다."""
    for k, _l, p in INTRO:
        if k == key:
            return p
    raise KeyError(key)


def intro_href(key, out_path):
    """출력 파일에서 소개 페이지 한 장으로 가는 상대 경로."""
    return root_rel(out_path) + intro_path(key)


def sidebar(slug, current, rel, foot="", out_path=None, exists=None):
    """모든 문서가 쓰는 사이드바 — rel = 출력 파일에서 프로젝트 폴더로 가는 상대 경로 접두.

    구성은 두 덩어리다. 위는 **워크스페이스**(포트폴리오 홈과 규칙 구조), 아래는
    **프로젝트 하나**(그 프로젝트를 설명하는 문서 · 산출물 · 원본 파일)이다. 프로젝트가
    늘면 아래 덩어리가 하나 더 붙는 형태라, 지금 구조가 그대로 자란다.

    out_path를 주면 소개 묶음까지 붙어 어느 문서에서나 같은 메뉴가 나온다. 사이드바에서
    들어간 페이지에 사이드바가 없으면 돌아갈 길이 사라지므로, 새 문서는 반드시 준다.

    exists(경로)는 「그 소개 페이지가 있는가」의 판정이다. 기본값은 디스크 확인인데,
    소개 페이지를 여러 장 한꺼번에 다시 만들 때는 **아직 안 만든 장이 회색으로 굳으므로**
    생성기가 「만들 수 있는 페이지」 기준을 대신 넘긴다.
    """
    groups = []
    head_href, head_title, head_sub = rel + "index.html", slug, "QA 검증 워크스페이스"
    if out_path is not None:
        root = root_rel(out_path)
        if exists is None:
            # 소개 층은 여러 생성기가 나눠 만든다. 디스크만 보면 「아직 안 만든 장」이 회색으로
            # 굳으므로, 목록에 있는 문서는 있는 것으로 본다 — 목록 자체가 만들겠다는 선언이다
            planned = set(path for _k, _l, path in INTRO)
            exists = lambda p: p in planned  # noqa: E731
        ws_title, ws_items = intro_group(current, root, exists=exists, keys=WORKSPACE_INTRO)
        # 저장소 링크는 워크스페이스 전체를 가리키므로 소개 묶음의 끝에 붙는다
        ws_items.append((REPO_LINK[0], REPO_LINK[1], False, REPO_LINK[2], True))
        groups.append((ws_title, ws_items))
        head_href = root + "index.html"
        head_title, head_sub = "QA-VisualNovel-Portfolio", "QA 포트폴리오"
        groups.append(("@프로젝트: %s" % PROJECT_LABEL.get(slug, slug), ()))
        doc_title, doc_items = intro_group(current, root, exists=exists,
                                           keys=PROJECT_INTRO, title="문서")
        # 검증 대상은 문서가 아니지만 이 프로젝트의 것이므로 문서 묶음 끝에 둔다
        key, label, path = SUT_LINK
        doc_items.append((label, rel + path.format(S=slug), key == current, "", True))
        groups.append((doc_title, doc_items))
    # 「내려받기」는 GitHub으로 나가므로 전부 새 탭이다
    repo_items = [(label, url.format(S=slug), False, tag, True) for label, url, tag in OUT]
    groups.append(("내려받기", repo_items))
    return sidebar_from(groups, head_href, head_title, head_sub, foot)


def topbar(crumb_root, crumb_doc):
    return (
        '<header class="topbar">'
        '<button class="icon-btn side-toggle" aria-label="메뉴 열기">☰</button>'
        '<div class="crumb">%s · <b>%s</b></div><span class="sp"></span>'
        '<button class="icon-btn" data-theme-toggle>다크</button></header>'
        % (esc(crumb_root), esc(crumb_doc)))


def open_body(slug, current, rel, crumb_doc, foot="", out_path=None):
    """<body>부터 본문 시작(.wrap 열림)까지."""
    crumb_root = "QA-VisualNovel-Portfolio" if out_path is not None else slug
    return ('<body><div class="app">%s<div class="main">%s<div class="wrap">'
            % (sidebar(slug, current, rel, foot, out_path),
               topbar(crumb_root, crumb_doc)))


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
