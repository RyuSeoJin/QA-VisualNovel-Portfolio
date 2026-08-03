# -*- coding: utf-8 -*-
"""탐색/발견 (DSC) — 캐릭터 페이지 · MY 탭 · 스텁

캐릭터 페이지는 **작품 층과 캐릭터 층**이 구분선으로 나뉘는 2층 구조이고(§8-8), 그 구조가
곧 기대값입니다. MY는 다른 화면의 값이 모이는 곳이라 정합 검증이 많습니다 — 합계가 어긋나면
방 쪽인지 합계 쪽인지 갈라야 하므로 방별 값과 함께 읽습니다.
"""
from thresholds import SPEC

ROOM = """(profileName) => {
    const p = addProfile({ name: profileName });
    return openRoom('c1', p || { name: profileName });
}"""


def _open_page(sut, char_id="c1"):
    sut.evaluate("(id) => { VN.pageCharId = id; VN.screen = 's3'; window.__VN__.refresh(); }", char_id)
    return sut


# ── 캐릭터 페이지 · 2층 구성 ────────────────────────────────────────────────

def test_tc_dsc_033_페이지_진입과_2층_구성(gate):
    """카드에서 페이지로 넘어가는 진입과, 작품 층·캐릭터 층이 나뉘는 구성을 함께 본다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-card-c1"]')
    assert sut.is_visible('[data-testid="s3-screen"]')

    for tid in ("s3-page-title", "s3-page-subtitle", "s3-categories", "s3-stories"):
        assert sut.is_visible(f'[data-testid="{tid}"]'), tid          # 작품 층
    for tid in ("s3-char-block", "s3-name", "s3-tagline", "s3-char-desc",
                "s3-situation", "s3-first"):
        assert sut.is_visible(f'[data-testid="{tid}"]'), tid          # 캐릭터 층


def test_tc_dsc_034_제작자_표시만(gate):
    """소셜은 제외 영역이라 표시만 한다 — 팔로우 동작이 없어야 한다."""
    sut = _open_page(gate("성인 인증"))
    assert sut.is_visible('[data-testid="s3-creator"]')
    assert sut.locator('[data-testid="s3-follow"]').count() == 0


def test_tc_dsc_035_현황_표시_정합(gate):
    """좋아요 수는 시트 기본값 + 계정 토글이다(§8-7) — 내가 누른 것이 반영돼야 한다."""
    sut = _open_page(gate("성인 인증"))
    before = sut.evaluate("() => likeCount(findCharacter('c1'))")
    sut.click('[data-testid="s3-like"]')
    assert sut.evaluate("() => likeCount(findCharacter('c1'))") == before + 1


def test_tc_dsc_036_출시일_최종_업데이트_표기(gate):
    """저장은 숫자로 하고 표시할 때 v를 붙인다(§8-8)."""
    sut = _open_page(gate("성인 인증"))
    text = sut.text_content('[data-testid="s3-updated"]')
    assert "출시" in text and "최종 업데이트" in text
    assert "(v" in text


def test_tc_dsc_037_버전_입력_정규화(gate):
    """v를 직접 적어도 접두가 겹치지 않는 것이 기대값이다."""
    sut = gate("성인 인증")
    assert sut.evaluate("() => versionInput('v2.5a')") == "2.5"
    assert sut.evaluate("() => versionLabel('v2.5a')") == "v2.5"

    sut.evaluate("""() => {
        const rows = VN.sheet.characters.map(c =>
            c.id === 'c1' ? Object.assign({}, c, { version: versionInput('v2.5a') }) : c);
        window.__VN__.setData('characters', rows);
    }""")
    _open_page(sut)
    assert "(v2.5)" in sut.text_content('[data-testid="s3-updated"]')


# ── 캐릭터 페이지 · 그 외 작품 추천 ─────────────────────────────────────────

def test_tc_dsc_038_그_외_작품_선정식과_정렬(gate):
    """카테고리 공유 + 좋아요 임계 이상을 상한까지, 자기 자신은 뺀다(§8-8)."""
    sut = _open_page(gate("성인 인증"))
    listed = sut.evaluate("() => relatedList(findCharacter('c1')).map(c => c.id)")

    assert "c1" not in listed
    assert len(listed) <= SPEC["related_max"]
    for cid in listed:
        assert sut.evaluate("(id) => likeCount(findCharacter(id))", cid) >= SPEC["related_like_min"]
        shared = sut.evaluate("""(id) => {
            const a = findCharacter('c1').pageCategories || [];
            return (findCharacter(id).pageCategories || []).some(n => a.includes(n));
        }""", cid)
        assert shared


def test_tc_dsc_039_그_외_작품_후보_0건_안내(gate):
    """섹션을 감추면 안 뜬 것과 없는 것이 구분되지 않는다."""
    sut = gate("성인 인증")
    sut.evaluate("() => { VN.relatedLikeMin = 99999; }")          # 후보를 전멸시킨다
    _open_page(sut)
    assert sut.is_visible('[data-testid="s3-related-empty"]')
    assert sut.locator('[data-testid="s3-related"]').count() == 0


def test_tc_dsc_040_시작_상황_표시만(gate):
    """캐릭터당 하나이며 유저는 고르지 못한다 — 그 id가 mock 세트의 좌표다."""
    sut = _open_page(gate("성인 인증"))
    assert sut.is_visible('[data-testid="s3-situation"]')
    assert sut.locator('[data-testid="s3-situation-select"]').count() == 0


# ── 캐릭터 페이지 · 좋아요/스크랩 ───────────────────────────────────────────

def test_tc_dsc_041_좋아요_토글_반영(gate):
    sut = _open_page(gate("성인 인증"))
    sut.click('[data-testid="s3-like"]')
    assert sut.evaluate("() => isLiked('c1')")

    _open_page(sut)                                               # 다시 열어도 유지
    assert sut.evaluate("() => isLiked('c1')")


def test_tc_dsc_042_스크랩_토글_반영(gate):
    """스크랩은 정렬에 쓰이지 않고 MY 활동 목록에만 반영된다."""
    sut = _open_page(gate("성인 인증"))
    sut.click('[data-testid="s3-scrap"]')
    assert sut.evaluate("() => isScrapped('c1')")

    _open_page(sut)
    assert sut.evaluate("() => isScrapped('c1')")


# ── 캐릭터 페이지 · 하단 버튼 ───────────────────────────────────────────────

def test_tc_dsc_043_대화방_없을_때_버튼_구성(gate):
    sut = _open_page(gate("성인 인증"))
    assert sut.is_visible('[data-testid="s3-pick-profile"]')
    assert sut.is_visible('[data-testid="s3-start"]')
    assert sut.locator('[data-testid="s3-rooms"]').count() == 0


def test_tc_dsc_044_대화방_있을_때_버튼_구성(gate):
    """방 유무로 구성이 갈리는 자리라 없는 경우와 나눴다."""
    sut = gate("성인 인증")
    sut.evaluate(ROOM, "테스트프로필")
    _open_page(sut)
    assert sut.is_visible('[data-testid="s3-rooms"]')
    assert sut.is_visible('[data-testid="s3-start"]')


def test_tc_dsc_045_대화방_이어하기(gate):
    """대화방 1-Depth는 진입한 상태를 사전조건으로 시작하므로 진입 경로 검증은 여기 남는다."""
    sut = gate("성인 인증")
    room = sut.evaluate(ROOM, "이어하기")
    _open_page(sut)
    sut.click(f'[data-testid="s3-room-{room["id"]}"]')
    assert sut.evaluate("() => VN.screen") == "s4"


def test_tc_dsc_046_대화방_한도_차단(gate):
    """한도 값은 §6이 정본이며 세이브 로드의 새 방 갈래도 같은 한도를 받는다."""
    sut = gate("성인 인증")
    for i in range(SPEC["rooms_per_char"]):
        sut.evaluate(ROOM, f"방{i}")
    assert sut.evaluate("() => roomLimitReached('c1')")

    _open_page(sut)
    assert sut.is_visible('[data-testid="s3-room-limit"]')
    assert sut.evaluate(ROOM, "초과") is None                     # 새 방이 만들어지지 않는다


def test_tc_dsc_054_없는_캐릭터_주소_폴백(gate):
    """빈 화면이 뜨면 결함인지 데이터 문제인지 구분되지 않는다."""
    sut = _open_page(gate("성인 인증"), "존재하지않는id")
    assert sut.is_visible('[data-testid="s3-missing"]')


# ── MY 탭 ──────────────────────────────────────────────────────────────────

def test_tc_dsc_047_대화수_합계_정합(gate):
    """합계가 어긋나면 방 쪽인지 합계 쪽인지 갈라야 하므로 방별 값과 함께 읽는다."""
    sut = gate("성인 인증")
    sut.evaluate(ROOM, "합계확인")
    sut.click('[data-testid="g-nav-my"]')

    total = int(sut.text_content('[data-testid="s6-total-count"]').strip().rstrip("개"))
    rooms = sut.evaluate("() => currentAccount().rooms.reduce((n, r) => n + roomMessageCount(r), 0)")
    assert total == rooms
    assert sut.is_visible('[data-testid="s6-room-count"]')


def test_tc_dsc_048_팔로워_팔로잉_표시만(gate):
    """소셜은 제외 영역이라 로직 없이 표시만 한다."""
    sut = gate("성인 인증")
    sut.evaluate("() => { window.__VN__.setData('accountStats', { followers: 77, following: 33 }); }")
    sut.click('[data-testid="g-nav-my"]')
    assert "77" in sut.text_content('[data-testid="s6-followers"]')
    assert "33" in sut.text_content('[data-testid="s6-following"]')


def test_tc_dsc_049_좋아요_스크랩_정합(gate):
    """캐릭터 페이지의 토글과 짝이다 — 토글이 여기 반영되는지가 검증 대상이다."""
    sut = _open_page(gate("성인 인증"))
    sut.click('[data-testid="s3-like"]')
    sut.click('[data-testid="s3-scrap"]')

    sut.click('[data-testid="g-nav-my"]')
    assert sut.is_visible('[data-testid="s6-activity-like-c1"]')
    assert sut.is_visible('[data-testid="s6-activity-scrap-c1"]')

    sut.click('[data-testid="s6-activity-like-c1"]')
    assert sut.evaluate("() => VN.screen") == "s3"


def test_tc_dsc_050_활동_빈_상태(gate):
    """좋아요와 스크랩이 각자 목록을 가지므로 둘 다 확인한다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="g-nav-my"]')
    assert sut.is_visible('[data-testid="s6-activity-like-empty"]')
    assert sut.is_visible('[data-testid="s6-activity-scrap-empty"]')


def test_tc_dsc_051_제외_영역_사유_안내(gate):
    """트리가 제외 사유의 정본임을 화면에서 읽히게 하는 자리다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="g-nav-my"]')
    assert sut.is_visible('[data-testid="s6-stubs"]')
    sut.click('[data-testid="s6-stub-library"]')
    assert sut.is_visible('[data-testid="g-toast"]')


# ── 스텁·정적 ──────────────────────────────────────────────────────────────

def test_tc_dsc_052_커뮤니티_전시용_정적(gate):
    """데이터 표시만 있고 발생·조작 로직이 없다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="g-nav-community"]')
    assert sut.is_visible('[data-testid="s7-stub"]')
    assert sut.locator('[data-testid="s7-write"]').count() == 0


def test_tc_dsc_053_내_작품_스텁_사유와_트리_항목명(gate):
    """스텁이 빈 화면이 아니라 판단의 결과임을 보이는 자리다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="g-nav-works"]')
    assert sut.is_visible('[data-testid="s8-stub"]')
    assert sut.is_visible('[data-testid="s8-stub-reason"]')
    assert sut.is_visible('[data-testid="s8-stub-node"]')
