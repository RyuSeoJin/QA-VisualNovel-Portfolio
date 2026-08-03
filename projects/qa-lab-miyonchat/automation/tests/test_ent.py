# -*- coding: utf-8 -*-
"""앱 진입/세션 (ENT) — 웹 진입 영역

케이스명은 TC ID를 그대로 씁니다(rules/sut-automation.md §2) — 리포트만 보고 TC 시트와
대조되게 하기 위해서입니다. 파일은 기능 트리 1-Depth 영역 단위로 나눕니다.

기대값의 출처는 TC 시트이고, 그 시트의 기대값은 트리와 spec/design/에서만 왔습니다.
여기서 기대값을 새로 만들지 않습니다 — 코드가 명세와 어긋나면 명세를 먼저 고칩니다.

대기는 고정 시간이 아니라 조건으로 합니다(§3) — 이 파일의 검증은 화면 전환뿐이라
Playwright의 액션 대기가 그 역할을 하고, 별도 `sleep`은 쓰지 않습니다.
"""


def test_tc_ent_001_미로그인_첫_진입(gate):
    """미로그인 진입은 로그인 화면 없이 홈이고, 상단 바에 로그인 버튼이 놓인다."""
    sut = gate("미로그인")
    assert sut.is_visible('[data-testid="s2-screen"]')
    assert sut.locator('[data-testid="s1-notice"]').count() == 0
    assert sut.is_visible('[data-testid="g-login"]')
    assert sut.locator('[data-testid="g-wallet"]').count() == 0


def test_tc_ent_002_로그인_상태_진입_분기(gate):
    """로그인 상태이면 홈 직행이고 잔액·간편 프로필이 보인다.

    새로고침을 견디는지는 이 케이스가 아니라 TC-ENT-011이 본다.
    """
    sut = gate("성인 인증")
    assert sut.is_visible('[data-testid="s2-screen"]')
    assert sut.locator('[data-testid="s1-notice"]').count() == 0
    assert sut.is_visible('[data-testid="g-wallet"]')
    assert sut.is_visible('[data-testid="g-profile"]')


def test_tc_ent_003_세션_만료_후_재진입(gate):
    """만료 안내가 뜨고, 확인하면 미로그인 홈으로 복귀한다."""
    sut = gate("세션 만료")
    assert sut.is_visible('[data-testid="g-expired-modal"]')

    sut.click('[data-testid="g-expired-ok"]')
    assert sut.is_visible('[data-testid="s2-screen"]')
    assert sut.locator('[data-testid="g-wallet"]').count() == 0
    assert sut.is_visible('[data-testid="g-login"]')


def test_tc_ent_005_로그인_상태_보호_화면_직접_진입(sut, sut_url):
    """세션 지속으로 계정이 복원되므로 가드가 통과시킨다 — 가드의 positive 경로."""
    sut.evaluate("() => { login('a'); setAdultVerified(true); window.__VN__.refresh(); }")

    sut.goto(sut_url + "?seed=1&screen=s6")
    sut.wait_for_function("() => !!window.__VN__")
    assert sut.is_visible('[data-testid="s6-screen"]')
    assert sut.locator('[data-testid="s1-notice"]').count() == 0


def test_tc_ent_011_새로고침_후_세션_지속(sut):
    """계정 스코프가 복원되고, 보기 상태는 담지 않아 홈에서 시작한다."""
    sut.evaluate("() => { login('a'); setAdultVerified(true); window.__VN__.refresh(); }")
    sut.click('[data-testid="g-nav-community"]')          # 보기 상태를 홈이 아닌 곳으로

    sut.reload()
    sut.wait_for_function("() => !!window.__VN__")
    assert sut.is_visible('[data-testid="s2-screen"]')     # 보기 상태는 복원되지 않는다
    assert sut.is_visible('[data-testid="g-wallet"]')
    assert sut.evaluate("() => window.__VN__.getState().accountId") == "a"


def test_tc_ent_012_시트_데이터는_지속되지_않음(sut):
    """시트는 테스트 조건이라 저장하지 않는다 — 남으면 앞사람의 조건 위에서 돌게 된다."""
    sut.evaluate("() => { login('a'); window.__VN__.setBaseDay('2026-01-01'); }")
    assert sut.evaluate("() => VN.sheet.baseDay") == "2026-01-01"

    sut.reload()
    sut.wait_for_function("() => !!window.__VN__")
    assert sut.evaluate("() => window.__VN__.getState().accountId") == "a"   # 계정은 남고
    assert sut.evaluate("() => VN.sheet.baseDay") != "2026-01-01"            # 시트는 안 남는다


def test_tc_ent_008_로그아웃_수행(gate):
    """로그인 화면이 아니라 미로그인 홈으로 복귀한다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="g-nav-my"]')
    sut.click('[data-testid="s6-logout"]')

    assert sut.is_visible('[data-testid="s2-screen"]')
    assert sut.is_visible('[data-testid="g-login"]')


def test_tc_ent_009_로그아웃_후_데이터_잔존_차단(gate):
    """화면뿐 아니라 저장소에도 남지 않아야 한다 — 상태 훅으로만 판정된다."""
    sut = gate("성인 인증")
    sut.evaluate("() => { addProfile({ name: '잔존확인' }); }")
    assert sut.evaluate("() => localStorage.getItem('miyonchat.session')") is not None

    sut.evaluate("() => { logout(); window.__VN__.refresh(); }")
    state = sut.evaluate("() => window.__VN__.getState()")
    assert state["accountId"] is None
    assert state["account"] is None
    assert sut.evaluate("() => localStorage.getItem('miyonchat.session')") is None
