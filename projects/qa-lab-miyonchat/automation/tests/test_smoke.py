# -*- coding: utf-8 -*-
"""
환경 스모크 — Playwright가 구동되고 SUT 테스트 인터페이스 방식이 동작하는지만 확인한다.

무엇을 검증하는가
-----------------
  1. data-testid 셀렉터로 요소를 잡을 수 있다 (클래스·화면 문구로 찾지 않는다)
  2. window.__VN__ 상태 조회 훅으로 화면에 안 보이는 값을 읽을 수 있다
  3. 매 테스트 전 reset()이 앞 테스트의 상태를 지운다

기능을 검증하는 테스트가 아니다. 실패하면 환경·테스트 인터페이스 규약이 깨진 것이므로,
SUT나 TC를 의심하기 전에 여기부터 본다.

대역 HTML을 파일이 아니라 문자열로 두는 이유
------------------------------------------
  sut/ 가 아직 없어서 최소 대역이 필요하지만, 별도 파일로 두면 실제 SUT가
  생긴 뒤 "SUT가 둘"이 되어 설명 부담이 생긴다. sut/ 가 만들어지면 STUB를
  지우고 page.goto(SUT 경로)로 대상만 갈아탄다.

실행:
    .venv/Scripts/python.exe -m pytest projects/qa-lab-miyonchat/automation/tests -q
"""

import pytest

STUB = """
<!doctype html><meta charset="utf-8"><title>smoke stub</title>
<p data-testid="affection-value">0</p>
<button data-testid="choice-kind">친절한 선택</button>
<script>
  const state = { affection: 0 };
  document.querySelector('[data-testid="choice-kind"]').addEventListener('click', () => {
    state.affection += 5;
    document.querySelector('[data-testid="affection-value"]').textContent = state.affection;
  });
  window.__VN__ = {
    getState: () => ({ ...state }),
    reset: () => { state.affection = 0;
      document.querySelector('[data-testid="affection-value"]').textContent = 0; },
  };
</script>
"""


@pytest.fixture(autouse=True)
def fresh(page):
    """conftest.py가 매 테스트 전 reset()을 호출하는 실제 구조를 미리 흉내낸다."""
    page.set_content(STUB)
    page.evaluate("() => window.__VN__.reset()")


def test_testid_selector(page):
    page.click('[data-testid="choice-kind"]')
    assert page.text_content('[data-testid="affection-value"]') == "5"


def test_state_hook(page):
    page.click('[data-testid="choice-kind"]')
    page.click('[data-testid="choice-kind"]')
    assert page.evaluate("() => window.__VN__.getState()")["affection"] == 10


def test_reset_isolates(page):
    """앞 테스트의 상태가 남으면 격리 계열 검증이 무의미해지므로 reset을 확인한다."""
    assert page.evaluate("() => window.__VN__.getState()")["affection"] == 0
