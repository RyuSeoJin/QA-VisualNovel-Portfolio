# -*- coding: utf-8 -*-
"""탐색/발견 (DSC) — 전역 셸 · 홈 화면

목록의 **순서 자체가 기대값**인 케이스가 많습니다(§8-5). 순서를 눈으로 확인하는 대신 상태
훅으로 목록을 읽어 비교합니다 — 화면의 카드 순서와 내부 계산이 갈리면 그것이 결함입니다.

경계는 디버그 콘솔이 아니라 `setData()`로 만듭니다. 두 경로는 같은 저장소를 쓰므로(청사진
§1) 결과가 같고, 자동화는 조건을 세우는 비용이 낮은 쪽을 씁니다.
"""
from thresholds import SPEC

LOGIN_A = "() => { logout(); login('a'); setAdultVerified(true); window.__VN__.refresh(); }"


def _chars(sut):
    return sut.evaluate("() => VN.sheet.characters.map(c => c.id)")


# ── 전역 셸 · 상단 바 ────────────────────────────────────────────────────────

def test_tc_dsc_001_로고로_홈_복귀(gate):
    sut = gate("성인 인증")
    sut.evaluate("() => { VN.pageCharId = 'c1'; VN.screen = 's3'; window.__VN__.refresh(); }")
    sut.click('[data-testid="g-logo"]')
    assert sut.is_visible('[data-testid="s2-screen"]')


def test_tc_dsc_002_홈에서_로고_재선택(gate):
    """같은 버튼이 화면에 따라 다르게 동작하는 자리라 TC-DSC-001과 나눴다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="g-logo"]')
    assert sut.is_visible('[data-testid="s2-screen"]')
    assert sut.evaluate("() => window.scrollY") == 0


def test_tc_dsc_003_페이지_제목_부분일치_검색(gate):
    """검색 결과는 별도 화면이 아니라 홈에 표시된다."""
    sut = gate("성인 인증")
    sut.fill('[data-testid="g-search"]', "우산")
    sut.click('[data-testid="g-search-submit"]')

    assert sut.is_visible('[data-testid="s2-search-list"]')
    assert sut.is_visible('[data-testid="s2-card-c1"]')          # 비 오는 날의 우산


def test_tc_dsc_004_페이지_카테고리_부분일치_검색(gate):
    """제목과 카테고리 두 축이 모두 검색 대상이라 TC-DSC-003과 나눴다."""
    sut = gate("성인 인증")
    sut.fill('[data-testid="g-search"]', "로맨스")
    sut.click('[data-testid="g-search-submit"]')

    for cid in ("c1", "c4", "c7"):                               # 로맨스를 가진 셋
        assert sut.is_visible(f'[data-testid="s2-card-{cid}"]')


def test_tc_dsc_005_검색_결과_0건_안내(gate):
    """목록만 비고 안내가 없으면 검색이 안 걸린 것인지 결과가 없는 것인지 구분되지 않는다."""
    sut = gate("성인 인증")
    sut.fill('[data-testid="g-search"]', "겹치지않는문자열zzz")
    sut.click('[data-testid="g-search-submit"]')

    assert sut.is_visible('[data-testid="s2-search-info"]')
    assert sut.locator('[data-testid^="s2-card-"]').count() == 0
    sut.click('[data-testid="s2-search-clear"]')
    assert sut.locator('[data-testid^="s2-card-"]').count() > 0


def test_tc_dsc_006_알림_목록이_데이터_시트를_반영(gate):
    """발생 로직은 없고 표시 반영만 검증한다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="g-noti"]')
    assert sut.is_visible('[data-testid="g-noti-list"]')
    assert sut.locator('[data-testid^="g-noti-n"]').count() > 0


def test_tc_dsc_007_알림_빈_상태_안내(gate):
    sut = gate("성인 인증")
    sut.evaluate("() => { window.__VN__.setData('notifications', []); window.__VN__.refresh(); }")
    sut.click('[data-testid="g-noti"]')
    assert sut.is_visible('[data-testid="g-noti-empty"]')


# ── 전역 셸 · 하단 내비 ──────────────────────────────────────────────────────

def test_tc_dsc_008_홈_탭_재선택(gate):
    """칩이 기본값으로 돌아가면 「돌아왔을 때 그대로인가」를 확인할 수 없다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-랭킹"]')
    sut.click('[data-testid="g-nav-home"]')

    assert sut.evaluate("() => VN.homeChip") == "랭킹"           # 활성 칩 유지
    assert sut.evaluate("() => window.scrollY") == 0


def test_tc_dsc_009_미로그인_커뮤니티_탭_통과(gate):
    """차단이 미로그인 열람 탭까지 과하게 걸리지 않는지 본다."""
    sut = gate("미로그인")
    sut.click('[data-testid="g-nav-community"]')
    assert sut.is_visible('[data-testid="s7-stub"]')
    assert sut.locator('[data-testid="g-login-modal"]').count() == 0


# ── 홈 화면 · 필터 칩 ───────────────────────────────────────────────────────

def test_tc_dsc_010_칩_구성과_기본_선택(gate):
    """카테고리는 3종 고정이며 작품 카테고리 배열의 첫 항목이 대표다(§8-6)."""
    sut = gate("성인 인증")
    for chip in ("추천", "랭킹", "신작", "로맨스", "판타지", "일상"):
        assert sut.is_visible(f'[data-testid="s2-chip-{chip}"]')
    assert sut.evaluate("() => VN.homeChip") == "추천"


# ── 홈 화면 · 추천 탭 ───────────────────────────────────────────────────────

def test_tc_dsc_011_추천_캐러셀_상한(gate):
    """데이터가 넘쳐도 상한까지만 — 동률은 §8-4 체인이 가른다."""
    sut = gate("성인 인증")
    sut.evaluate("""() => {
        const base = VN.sheet.characters;
        const extra = Array.from({ length: 6 }, (_, i) => Object.assign({}, base[0], {
            id: 'x' + i, name: '추가' + i, pageTitle: '추가 작품 ' + i
        }));
        window.__VN__.setData('characters', base.concat(extra));
    }""")
    n = sut.evaluate("() => carouselList().length")
    assert n <= SPEC["carousel_max"]


def test_tc_dsc_012_최근_대화_섹션_조건부_노출(gate):
    """이력이 없으면 섹션 자체가 없어야 한다 — 빈 섹션이 남으면 결함이다."""
    sut = gate("성인 인증")
    assert sut.locator('[data-testid="s2-sec-recent"]').count() == 0


def test_tc_dsc_013_떠오르는_신작_선정식(gate):
    """월간이 모수를 거르고 주간이 순서를 만든다(§8-5)."""
    sut = gate("성인 인증")
    listed = sut.evaluate("() => risingList().map(c => c.id)")
    assert len(listed) <= SPEC["section_top"]
    for cid in listed:                                            # 모수 조건 — 월간 1건 이상
        assert sut.evaluate("(id) => monthUsage(findCharacter(id))", cid) >= 1


def test_tc_dsc_014_떠오르는_신작_창_경계(gate):
    """60일이 경계라 61일은 밖이다."""
    sut = gate("성인 인증")
    before = sut.evaluate("() => risingList().map(c => c.id)")
    assert before, "경계를 볼 대상이 있어야 한다"

    target = before[0]
    sut.evaluate("""(id) => {
        const rows = VN.sheet.characters.map(c =>
            c.id === id ? Object.assign({}, c, { createdDay: '2020-01-01' }) : c);
        window.__VN__.setData('characters', rows);
    }""", target)
    assert target not in sut.evaluate("() => risingList().map(c => c.id)")


def test_tc_dsc_015_지금_뜨거운_선정식(gate):
    """떠오르는 신작과 달리 생성일 조건이 없다."""
    sut = gate("성인 인증")
    listed = sut.evaluate("() => hotList().map(c => c.id)")
    assert len(listed) <= SPEC["section_top"]
    for cid in listed:
        assert sut.evaluate("(id) => weekUsage(findCharacter(id))", cid) >= 1


def test_tc_dsc_016_섹션_모수_0건_안내(gate):
    """이용수를 전부 비우면 두 섹션의 모수가 빈다."""
    sut = gate("성인 인증")
    sut.evaluate("() => { window.__VN__.setData('events', []); window.__VN__.refresh(); }")
    assert sut.evaluate("() => risingList().length") == 0
    assert sut.evaluate("() => hotList().length") == 0
    assert sut.is_visible('[data-testid="s2-sec-rising-empty"]')
    assert sut.is_visible('[data-testid="s2-sec-hot-empty"]')


# ── 홈 화면 · 랭킹 탭 ───────────────────────────────────────────────────────

def test_tc_dsc_017_랭킹_진입_기본값(gate):
    """기간 버튼 배열(일→주→월)의 첫 값과 같다(§8-3)."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-랭킹"]')
    assert sut.evaluate("() => VN.rankPeriod") == "daily"
    assert sut.evaluate("() => VN.rankSort") == "usage"


def test_tc_dsc_018_기간_필터_전환(gate):
    """기간은 이용수 기준에만 걸린다 — 좋아요·리뷰는 누적값이다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-랭킹"]')
    sut.click('[data-testid="s2-rank-period-weekly"]')
    assert sut.evaluate("() => VN.rankPeriod") == "weekly"
    sut.click('[data-testid="s2-rank-period-monthly"]')
    assert sut.evaluate("() => VN.rankPeriod") == "monthly"

    # 좋아요 순은 기간을 바꿔도 순서가 그대로여야 한다
    sut.click('[data-testid="s2-rank-sort-likes"]')
    monthly = sut.evaluate("() => rankList().map(c => c.id)")
    sut.click('[data-testid="s2-rank-period-daily"]')
    assert sut.evaluate("() => rankList().map(c => c.id)") == monthly


def test_tc_dsc_019_이용수_중복_제거(gate):
    """유저×작품×날짜 조합으로 센다(§8-2)."""
    sut = gate("성인 인증")
    sut.evaluate("""() => {
        const day = VN.sheet.baseDay;
        window.__VN__.setData('events', [
            { user: 'u1', charId: 'c1', day: day },
            { user: 'u1', charId: 'c1', day: day },   // 같은 조합 — 1로 센다
            { user: 'u2', charId: 'c1', day: day }
        ]);
    }""")
    assert sut.evaluate("() => usageCount('c1', recentDays(1))") == 2


def test_tc_dsc_020_미래_이벤트_집계_제외(gate):
    """주입 데이터 방어다(§8-1)."""
    sut = gate("성인 인증")
    sut.evaluate("""() => {
        window.__VN__.setBaseDay('2026-08-02');
        window.__VN__.setData('events', [
            { user: 'u1', charId: 'c1', day: '2026-08-02' },
            { user: 'u2', charId: 'c1', day: '2026-12-31' }   // 미래
        ]);
    }""")
    assert sut.evaluate("() => usageCount('c1', null)") == 1


def test_tc_dsc_021_이용수_0건_제외(gate):
    """0건 제외는 이용수 순위에만 걸린다 — 좋아요 순에서는 빠지지 않는다."""
    sut = gate("성인 인증")
    sut.evaluate("""() => {
        const day = VN.sheet.baseDay;
        window.__VN__.setData('events', [{ user: 'u1', charId: 'c1', day: day }]);
        VN.homeChip = '랭킹'; VN.rankPeriod = 'daily'; VN.rankSort = 'usage';
    }""")
    assert sut.evaluate("() => rankList().map(c => c.id)") == ["c1"]

    sut.evaluate("() => { VN.rankSort = 'likes'; }")
    assert len(sut.evaluate("() => rankList().map(c => c.id)")) > 1


def test_tc_dsc_022_정렬_기준_전환(gate):
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-랭킹"]')
    sut.click('[data-testid="s2-rank-sort-likes"]')
    likes = sut.evaluate("() => rankList().map(c => likeCount(c))")
    assert likes == sorted(likes, reverse=True)

    sut.click('[data-testid="s2-rank-sort-reviews"]')
    reviews = sut.evaluate("() => rankList().map(c => c.reviews)")
    assert reviews == sorted(reviews, reverse=True)


def test_tc_dsc_023_리뷰_점수순_최소_표본(gate):
    """임계 미만은 점수 순위에서 제외된다(§8-3)."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-랭킹"]')
    sut.click('[data-testid="s2-rank-sort-score"]')
    for reviews in sut.evaluate("() => rankList().map(c => c.reviews)"):
        assert reviews >= SPEC["review_min_sample"]


def test_tc_dsc_024_랭킹_도움말_표시(gate):
    """화면 안에서 기준을 읽을 수 있어야 정렬 결과를 판단할 수 있다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-랭킹"]')
    sut.click('[data-testid="s2-rank-help"]')
    body = sut.text_content('[data-testid="s2-rank-help-body"]')
    assert str(SPEC["review_min_sample"]) in body


# ── 홈 화면 · 신작/카테고리 탭 ───────────────────────────────────────────────

def test_tc_dsc_025_출시일_최신순_정렬(gate):
    """이용수 조건 없이 전량을 출시일로만 줄 세운다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-신작"]')
    days = sut.evaluate("() => newestList().map(c => c.createdDay)")
    assert days == sorted(days, reverse=True)


def test_tc_dsc_026_칩_선택_시_모수_제한(gate):
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-로맨스"]')
    for cid in sut.evaluate("() => categoryList('로맨스').map(c => c.id)"):
        assert sut.evaluate("(id) => hasCategory(findCharacter(id), '로맨스')", cid)


def test_tc_dsc_027_카테고리_인기_신작(gate):
    """떠오르는 신작과 식이 같고 모수만 카테고리로 좁힌 것이다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-로맨스"]')
    for cid in sut.evaluate("() => risingList('로맨스').map(c => c.id)"):
        assert sut.evaluate("(id) => hasCategory(findCharacter(id), '로맨스')", cid)


def test_tc_dsc_028_함께_보는_카테고리_and_필터(gate):
    """OR가 아니라 AND다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-로맨스"]')
    sut.click('[data-testid="s2-cat-tag-후회"]')
    listed = sut.evaluate("() => categoryList('로맨스').map(c => c.id)")
    assert listed
    for cid in listed:
        assert sut.evaluate("(id) => hasCategory(findCharacter(id), '로맨스')", cid)
        assert sut.evaluate("(id) => hasCategory(findCharacter(id), '후회')", cid)


def test_tc_dsc_029_and_필터_결과_0건_안내(gate):
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-로맨스"]')
    sut.click('[data-testid="s2-cat-tag-계약연애"]')
    sut.evaluate("""() => {
        const rows = VN.sheet.characters.map(c =>
            Object.assign({}, c, { pageCategories: ['로맨스'] }));   // 겹치는 짝을 없앤다
        window.__VN__.setData('characters', rows);
        window.__VN__.refresh();
    }""")
    assert sut.evaluate("() => categoryList('로맨스').length") == 0
    assert sut.is_visible('[data-testid="s2-cat-list-empty"]')


def test_tc_dsc_030_전체_목록_정렬_전환(gate):
    """대화순은 기간 창이 없는 누적 이용수다 — 랭킹의 기간 필터와 다른 축이다."""
    sut = gate("성인 인증")
    sut.click('[data-testid="s2-chip-로맨스"]')
    sut.click('[data-testid="s2-cat-sort-new"]')
    days = sut.evaluate("() => categoryList('로맨스').map(c => c.createdDay)")
    assert days == sorted(days, reverse=True)

    sut.click('[data-testid="s2-cat-sort-chat"]')
    used = sut.evaluate("() => categoryList('로맨스').map(c => usageCount(c.id, null))")
    assert used == sorted(used, reverse=True)


# ── 홈 화면 · 카드 구성 ─────────────────────────────────────────────────────

def test_tc_dsc_031_카드_구성_네_줄(gate):
    """지표를 카드에 두지 않는 것이 스펙이다(§8-4-1)."""
    sut = gate("성인 인증")
    assert sut.is_visible('[data-testid="s2-card-c1"]')
    assert sut.is_visible('[data-testid="s2-card-c1-thumb"]')
    assert sut.locator('[data-testid="s2-card-c1-metric"]').count() == 0


def test_tc_dsc_032_지표_표시_토글_반영(gate):
    """정렬 근거를 눈으로 확인할 때만 켠다."""
    sut = gate("성인 인증")
    sut.evaluate("() => { VN.showMetrics = true; window.__VN__.refresh(); }")
    assert sut.is_visible('[data-testid="s2-card-c1-metric"]')
