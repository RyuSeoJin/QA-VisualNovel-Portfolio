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
    return page
