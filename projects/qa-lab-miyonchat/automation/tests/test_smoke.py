# -*- coding: utf-8 -*-
"""환경 스모크 — Playwright가 구동되고 SUT 테스트 인터페이스가 동작하는지만 확인한다.

무엇을 검증하는가
-----------------
  1. data-testid 셀렉터로 요소를 잡을 수 있다 (클래스·화면 문구로 찾지 않는다)
  2. window.__VN__ 상태 조회 훅으로 화면에 안 보이는 값을 읽을 수 있다
  3. 매 테스트 전 reset()이 앞 테스트의 상태를 지운다
  4. 실행 조건 파라미터(?seed=·?inject=)가 먹는다

기능을 검증하는 테스트가 아니다. 실패하면 환경·테스트 인터페이스 규약이 깨진 것이므로,
SUT나 TC를 의심하기 전에 여기부터 본다.

대역(STUB)에서 실제 SUT로 (2026-08-03)
--------------------------------------
  sut/ 가 없던 시절에는 최소 대역 HTML을 문자열로 두고 그것을 상대로 돌렸다. 이제 SUT가
  완성되어 conftest.py가 띄우는 실제 SUT를 상대로 돈다. 대역을 남겨 두면 "SUT가 둘"이
  되어, 실제 __VN__이 깨져도 스모크는 계속 통과하는 상태가 된다.

실행:
    .venv/Scripts/python.exe -m pytest projects/qa-lab-miyonchat/automation/tests -q
"""


def test_testid_selector(sut):
    """화면 문구가 아니라 testid로 찾는다 — 문구는 기획에 따라 바뀌지만 testid는 계약이다."""
    sut.click('[data-testid="g-nav-community"]')
    assert sut.is_visible('[data-testid="s7-stub"]')


def test_state_hook(sut):
    """화면에 나타나지 않는 값을 읽는 통로 — 격리 검증은 이 통로가 유일한 수단이다."""
    state = sut.evaluate("() => window.__VN__.getState()")
    assert state["screen"] == "s2"
    assert state["accountId"] is None
    assert state["seed"] == 1


def test_reset_isolates(sut):
    """앞 테스트의 상태가 남으면 격리 계열 검증이 무의미해지므로 reset을 확인한다."""
    sut.evaluate("() => { login('a'); addProfile({ name: '스모크' }); }")
    assert sut.evaluate("() => window.__VN__.getState().accountId") == "a"

    sut.evaluate("() => window.__VN__.reset()")
    after = sut.evaluate("() => window.__VN__.getState()")
    assert after["accountId"] is None
    assert after["account"] is None


def test_run_condition_params(sut, sut_url):
    """?seed= 로 응답 경로가 고정되고 ?inject= 로 결함이 켜진다 — 재현과 탐지력 증명의 축."""
    sut.goto(sut_url + "?seed=7&inject=gate-bypass")
    sut.wait_for_function("() => !!window.__VN__")
    state = sut.evaluate("() => window.__VN__.getState()")
    assert state["seed"] == 7
    assert state["inject"] == "gate-bypass"


def test_no_console_errors(page, sut_url):
    """콘솔 에러 0이 SUT의 기본 조건이다 — 에러가 나면 이후 테스트의 실패 원인이 흐려진다."""
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(sut_url + "?seed=1")
    page.wait_for_function("() => !!window.__VN__")
    page.click('[data-testid="g-nav-community"]')
    assert errors == []
