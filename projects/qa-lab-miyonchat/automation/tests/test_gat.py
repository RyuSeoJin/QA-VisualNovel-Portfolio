# -*- coding: utf-8 -*-
"""계정/게이팅 (GAT) — 로그인 필요 화면 차단 · 언세이프 게이트 · 세이프티 필터 · 계정 전환

이 파일이 상태 축의 본무대입니다. 언세이프 게이트는 네 상태에서 각각, 세이프티 필터는 세
상태에서 각각 확인해야 하며(트리의 `[상태:]` 선언), 그 조합이 커버리지 대조의 요구입니다.

**차단 셋과 통과 하나를 짝으로 읽습니다.** 게이트가 과하게 걸려 성인에게도 가려지면 그것도
결함이라, positive 케이스(TC-GAT-015)가 차단 케이스들과 같은 무게로 있습니다.
"""

PROTECTED_SCREENS = {"s4": "대화방", "s5": "채팅 탭", "s6": "MY 탭", "s8": "내 작품 탭"}


def _direct(sut, sut_url, screen):
    """주소로 화면을 직접 연다 — 가드는 페이지가 열리는 순간 판정한다."""
    sut.goto(f"{sut_url}?seed=1&screen={screen}")
    sut.wait_for_function("() => !!window.__VN__")
    return sut


# ── 로그인 필요 화면 직접 접근 차단 ────────────────────────────────────────────

def test_tc_gat_001_대화방_차단과_로그인_후_복귀(sut, sut_url):
    """뒤에 깔 화면이 없는 경우라 모달이 아니라 로그인 화면으로 받고, 로그인하면 이어진다."""
    _direct(sut, sut_url, "s4")
    assert sut.locator('[data-testid="s4-screen"]').count() == 0
    assert sut.is_visible('[data-testid="s1-notice"]')
    assert sut.locator('[data-testid="g-login-modal"]').count() == 0   # 모달이 아니다

    sut.click('[data-testid="s1-account-a"]')
    assert sut.evaluate("() => VN.screen") == "s4"


def test_tc_gat_002_채팅_탭_차단(sut, sut_url):
    _direct(sut, sut_url, "s5")
    assert sut.locator('[data-testid="s5-screen"]').count() == 0
    assert sut.is_visible('[data-testid="s1-notice"]')


def test_tc_gat_003_my_탭_차단(sut, sut_url):
    _direct(sut, sut_url, "s6")
    assert sut.locator('[data-testid="s6-screen"]').count() == 0
    assert sut.is_visible('[data-testid="s1-notice"]')


def test_tc_gat_004_내_작품_탭_차단(sut, sut_url):
    """스텁 화면이지만 로그인 필요 화면이라 차단은 걸린다."""
    _direct(sut, sut_url, "s8")
    assert sut.locator('[data-testid="s8-stub"]').count() == 0
    assert sut.is_visible('[data-testid="s1-notice"]')


def test_tc_gat_005_홈_화면_통과(sut, sut_url):
    """차단이 미로그인 열람 화면까지 과하게 걸리지 않는지 — 차단 케이스들과 짝으로 읽는다."""
    _direct(sut, sut_url, "s2")
    assert sut.is_visible('[data-testid="s2-screen"]')
    assert sut.locator('[data-testid="s1-notice"]').count() == 0


def test_tc_gat_006_커뮤니티_탭_통과(sut, sut_url):
    _direct(sut, sut_url, "s7")
    assert sut.is_visible('[data-testid="s7-stub"]')
    assert sut.locator('[data-testid="s1-notice"]').count() == 0


def test_tc_gat_011_만료_상태_보호_화면_직접_진입(sut, sut_url):
    """구현의 판정은 로그인 여부 하나라 만료도 미로그인과 같은 차단을 받는다."""
    sut.evaluate("() => { login('a'); window.__VN__.expireSession(); }")
    _direct(sut, sut_url, "s6")
    assert sut.locator('[data-testid="s6-screen"]').count() == 0
    assert sut.is_visible('[data-testid="s1-notice"]')


# ── 셸 안에서 막히는 경우 — 모달이고 뒤 화면은 남는다 ─────────────────────────

def test_tc_gat_007_미로그인_알림_열람_차단(gate):
    """알림 열람은 명세 §1-1의 로그인 필요 동작이다."""
    sut = gate("미로그인")
    sut.click('[data-testid="g-noti"]')
    assert sut.locator('[data-testid="g-noti-list"]').count() == 0
    assert sut.is_visible('[data-testid="g-login-modal"]')


def test_tc_gat_008_미로그인_채팅_탭_차단(gate):
    sut = gate("미로그인")
    sut.click('[data-testid="g-nav-chat"]')
    assert sut.locator('[data-testid="s5-screen"]').count() == 0
    assert sut.is_visible('[data-testid="g-login-modal"]')
    assert sut.is_visible('[data-testid="s2-screen"]')      # 뒤 화면은 그대로 남는다


def test_tc_gat_009_미로그인_my_탭_차단(gate):
    sut = gate("미로그인")
    sut.click('[data-testid="g-nav-my"]')
    assert sut.locator('[data-testid="s6-screen"]').count() == 0
    assert sut.is_visible('[data-testid="g-login-modal"]')


def test_tc_gat_010_미로그인_내_작품_탭_차단(gate):
    sut = gate("미로그인")
    sut.click('[data-testid="g-nav-works"]')
    assert sut.locator('[data-testid="s8-stub"]').count() == 0
    assert sut.is_visible('[data-testid="g-login-modal"]')


# ── 언세이프 게이트 — 상태 넷 (차단 셋 + 통과 하나) ───────────────────────────
# 기본 데이터의 언세이프는 카일(c4)이다

def test_tc_gat_012_미로그인_언세이프_블러(gate):
    """미로그인은 로그인·본인인증으로 해제할 수 있어 미성년과 대비된다."""
    sut = gate("미로그인")
    assert sut.is_visible('[data-testid="s2-card-c4-blur"]')


def test_tc_gat_013_본인인증_미진행_언세이프_블러(gate):
    """인증을 하지 않아 나이를 모르는 상태 — 인증하면 풀린다."""
    sut = gate("본인인증 미진행")
    assert sut.is_visible('[data-testid="s2-card-c4-blur"]')


def test_tc_gat_014_미성년_언세이프_차단(gate):
    """화면은 미인증과 같아 보이나 해제 가능성이 정반대다 — 이 대비가 게이팅 검증의 축이다."""
    sut = gate("미성년")
    assert sut.is_visible('[data-testid="s2-card-c4-blur"]')


def test_tc_gat_015_성인_인증_언세이프_정상_노출(gate):
    """게이트가 과하게 걸리는 것도 결함이라 통과를 따로 세운다(positive)."""
    sut = gate("성인 인증")
    assert sut.is_visible('[data-testid="s2-card-c4"]')
    assert sut.locator('[data-testid="s2-card-c4-blur"]').count() == 0


def test_tc_gat_016_언세이프_페이지_상세_숨김(gate):
    """홈의 카드 블러와 층이 다르다 — 여기는 페이지 안의 상세 숨김이다."""
    sut = gate("미성년")
    sut.evaluate("() => { VN.pageCharId = 'c4'; VN.screen = 's3'; window.__VN__.refresh(); }")
    assert sut.is_visible('[data-testid="s3-locked"]')
    assert sut.locator('[data-testid="s3-first"]').count() == 0
    assert sut.locator('[data-testid="s3-situation"]').count() == 0


# ── MY 탭 — 게이팅 상태 표시와 세이프티 필터 ─────────────────────────────────

def test_tc_gat_017_게이팅_상태_표시(gate):
    """언세이프가 왜 가려졌는지 판단하려면 지금 어느 상태인지 화면에서 읽혀야 한다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="g-nav-my"]')
    assert sut.is_visible('[data-testid="s6-gate"]')
    assert "성인 인증" in sut.text_content('[data-testid="s6-gate"]')


def test_tc_gat_018_세이프티_필터_노출과_동작(gate):
    """필터는 숨기고 게이팅은 가린 채 남긴다 — 층이 다르다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="g-nav-my"]')
    sut.click('[data-testid="s6-safety-toggle"]')

    sut.click('[data-testid="g-nav-home"]')
    assert sut.locator('[data-testid="s2-card-c4"]').count() == 0      # 목록에서 아예 빠진다
    assert sut.locator('[data-testid="s2-card-c4-blur"]').count() == 0


def test_tc_gat_019_본인인증_미진행_토글_비노출(gate):
    """성인 인증 계정에만 노출되는 것이 스펙이다 — 미인증에게 보이면 결함이다."""
    sut = gate("본인인증 미진행")
    sut.evaluate("() => { VN.screen = 's6'; window.__VN__.refresh(); }")
    assert sut.locator('[data-testid="s6-safety-toggle"]').count() == 0
    assert sut.is_visible('[data-testid="s6-safety-hidden"]')


def test_tc_gat_020_미성년_토글_비노출(gate):
    """미성년은 언세이프가 원천 차단이라 필터를 켤 이유 자체가 없다."""
    sut = gate("미성년")
    sut.evaluate("() => { VN.screen = 's6'; window.__VN__.refresh(); }")
    assert sut.locator('[data-testid="s6-safety-toggle"]').count() == 0
    assert sut.is_visible('[data-testid="s6-safety-hidden"]')


# ── 계정 전환 격리 — 자동화 전용(화면만 봐서는 혼입을 판정할 수 없다) ─────────

def _seed_account(sut, account, profile_name, candy):
    """그 계정에 흔적을 남긴다 — 전환 뒤 그 흔적이 넘어오는지가 검증 대상이다."""
    sut.evaluate("""([acc, name, candy]) => {
        logout(); login(acc);
        addProfile({ name: name });
        currentAccount().wallet.free = candy;
    }""", [account, profile_name, candy])


def test_tc_gat_021_계정_전환_격리_성인_계정(sut):
    """B로 쓰다 A로 전환하면 A의 데이터만 보여야 한다."""
    _seed_account(sut, "b", "미성년프로필", 11)
    _seed_account(sut, "a", "성인프로필", 22)

    state = sut.evaluate("() => window.__VN__.getState()")
    names = [p["name"] for p in state["account"]["profiles"]]
    assert names == ["성인프로필"]
    assert state["account"]["wallet"]["free"] == 22


def test_tc_gat_022_계정_전환_격리_미성년_계정(sut):
    """반대 방향도 본다 — 한 방향만 보면 복사가 한쪽으로만 새는 결함을 놓친다."""
    _seed_account(sut, "a", "성인프로필", 22)
    _seed_account(sut, "b", "미성년프로필", 11)

    state = sut.evaluate("() => window.__VN__.getState()")
    names = [p["name"] for p in state["account"]["profiles"]]
    assert names == ["미성년프로필"]
    assert state["account"]["wallet"]["free"] == 11
