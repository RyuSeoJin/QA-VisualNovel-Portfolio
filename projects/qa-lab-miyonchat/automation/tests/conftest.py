# -*- coding: utf-8 -*-
"""테스트 공통 설비 — SUT를 띄우고, 매 테스트 전에 상태를 되돌린다.

SUT를 왜 서버로 띄우는가
------------------------
  `file://`로 열면 브라우저가 로컬 파일 스크립트를 막는 환경이 있어 `__VN__`이 아예
  생기지 않는다. 정적 서버 한 대면 그 차이가 사라지므로, 세션당 한 번 띄우고 끝낸다.

포트를 왜 0으로 여는가
----------------------
  개발자가 손으로 띄워 둔 서버(8848 등)와 부딪히면 테스트가 남의 SUT를 상대로 돌 수 있다.
  0을 주면 OS가 빈 포트를 골라 주므로 충돌하지 않고, 이 서버가 우리 것임이 보장된다.

reset을 왜 fixture로 두는가
---------------------------
  이 SUT는 상태를 메모리에만 두므로 앞 테스트가 남긴 방·재화·기억이 다음 테스트로 샌다.
  격리 계열 검증(계정 간·방 간·슬롯 간)은 시작점이 같아야 성립하므로 매 테스트 전에
  되돌린다. 페이지를 다시 여는 것보다 빠르고, 실제 conftest 규약과도 같다.
"""

import functools
import http.server
import os
import threading

import pytest

from thresholds import RUN

SUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "sut")


@pytest.fixture(scope="session")
def sut_url():
    """세션당 한 번 정적 서버를 띄우고 주소를 준다."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=os.path.abspath(SUT_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:%d/index.html" % server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(autouse=True)
def sut(page, sut_url):
    """SUT를 열고 상태를 초기값으로 되돌린 뒤 테스트에 넘긴다.

    시드는 기본값(1)로 고정한다 — mock 응답 경로가 시드로 정해지므로,
    시드를 명시하지 않으면 기대값이 실행마다 달라질 여지가 생긴다.
    """
    page.goto(sut_url + "?seed=1")
    page.wait_for_function("() => !!window.__VN__")
    page.evaluate("() => window.__VN__.reset()")
    page.set_default_timeout(RUN["wait_timeout_ms"])
    return page


# ── 상태 세팅 헬퍼 ────────────────────────────────────────────────────────────
# 게이팅 5상태를 만드는 길을 한 곳에 둔다. 케이스마다 다르게 세우면 「사전조건이 달라서 나는
# 실패」와 「기능 결함」이 구분되지 않는다. TC 시트의 상태 열 값과 인자가 1:1로 맞는다.

_GATE_SETUP = {
    "미로그인": "() => { logout(); }",
    "성인 인증": "() => { logout(); login('a'); setAdultVerified(true); }",
    "본인인증 미진행": "() => { logout(); login('a'); setAdultVerified(false); }",
    "미성년": "() => { logout(); login('b'); }",
    "세션 만료": "() => { logout(); login('a'); window.__VN__.expireSession(); }",
}


@pytest.fixture
def gate(sut):
    """TC의 상태 열 값을 그대로 받아 그 게이팅 상태를 만든다.

    상태를 바꾸는 API는 화면을 자동 갱신하지 않으므로(청사진 §3-2) 여기서 refresh까지
    한다 — 「데이터가 바뀌었는데 화면이 안 따라오는가」는 그 자체가 검증 대상이라
    화면 갱신을 확인하는 케이스는 이 헬퍼를 쓰지 않고 직접 조작한다.
    """
    def _set(state):
        if state not in _GATE_SETUP:
            raise ValueError(f"상태 열 값이 아닙니다: {state}")
        sut.evaluate(_GATE_SETUP[state])
        sut.evaluate("() => window.__VN__.refresh()")
        return sut
    return _set


@pytest.fixture
def room(sut):
    """대화방을 열어 그 방을 준다 — 대화방 계열 케이스의 공통 사전조건.

    프로필은 방에 사본으로 고정되므로(system-spec §2) 방마다 다른 이름을 줄 수 있습니다.
    """
    def _open(profile_name="자동화", char_id="c1"):
        return sut.evaluate("""([name, cid]) => {
            const p = addProfile({ name: name });
            const r = openRoom(cid, p || { name: name });
            VN.screen = 's4';
            window.__VN__.refresh();
            return r;
        }""", [profile_name, char_id])
    return _open


@pytest.fixture
def send(sut):
    """한 턴 보내고 **표시가 끝날 때까지** 기다린다 (§3 대기 규칙).

    고정 시간으로 기다리지 않습니다 — 스트리밍 연출의 길이는 응답 문자 수에 달렸고, 브라우저가
    타이머를 늦추면 그 길이가 환경마다 달라집니다. 표시 중 상태가 풀리는 것을 조건으로 삼습니다.
    """
    def _send(text="자동화 입력", choice=None):
        if choice is None:
            sut.evaluate("(t) => sendMessage(t)", text)
        else:
            sut.evaluate("(i) => { const b = document.querySelector"
                         "('[data-testid=\"s4-choice-' + i + '\"]'); if (b) b.click(); }", choice)
        # 표시 중 표식이 사라지는 것을 기다립니다 — 화면에서 읽히는 조건이라 내부 변수에
        # 기대지 않습니다(§3). 연출이 짧아 표식이 뜨기 전에 끝나도 그대로 통과합니다
        sut.wait_for_selector('[data-testid="s4-streaming"]', state="detached",
                              timeout=RUN["wait_timeout_ms"])
        sut.evaluate("() => window.__VN__.refresh()")
    return _send


@pytest.fixture
def wait_gone(sut):
    """표식이 사라질 때까지 기다린다 — 고정 대기 금지 규칙의 기본 수단(§3).

    타임아웃은 성공 판정이 아니라 실패 판정이다. 시간이 지나 조건이 성립하지 않으면
    통과가 아니라 예외로 끝난다.
    """
    def _wait(testid):
        sut.wait_for_selector(f'[data-testid="{testid}"]', state="detached",
                              timeout=RUN["wait_timeout_ms"])
    return _wait
