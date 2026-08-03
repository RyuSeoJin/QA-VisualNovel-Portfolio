# -*- coding: utf-8 -*-
"""대화 프로필(PRF) · 채팅 탭(CHT) · 재화 패널(CUR) · 로그인 모달·푸터(ENT)

프로필 상한은 **어느 경로로 값이 들어와도** 넘는 값이 남지 않는 것이 기대값입니다(§2) —
손으로 치는 입력, 붙여넣기, 자동화의 값 주입이 같은 결과여야 하므로 주입 경로로 확인합니다.
"""
from thresholds import SPEC, TOKENS

PANEL = "() => { VN.panel = 'p5'; window.__VN__.refresh(); }"


def _fill(sut, testid, value):
    """값 주입 경로 — 사람이 치는 경로보다 상한 방어가 약한 자리다."""
    sut.fill(f'[data-testid="{testid}"]', value)
    return sut.input_value(f'[data-testid="{testid}"]')


# ── 대화 프로필 화면 ────────────────────────────────────────────────────────

def test_tc_prf_001_이름_상한_경계(sut, gate):
    gate("성인 인증"); sut.evaluate(PANEL)
    assert len(_fill(sut, "p5-name", "가" * SPEC["profile_name_max"])) == SPEC["profile_name_max"]
    assert len(_fill(sut, "p5-name", "가" * (SPEC["profile_name_max"] + 1))) == SPEC["profile_name_max"]
    assert str(SPEC["profile_name_max"]) in sut.text_content('[data-testid="p5-name-count"]')


def test_tc_prf_002_자유_설명_상한_경계(sut, gate):
    """값 주입으로 넣어야 저장 경로의 자르기까지 확인된다."""
    gate("성인 인증"); sut.evaluate(PANEL)
    over = "가" * (SPEC["profile_desc_max"] + 1)
    assert len(_fill(sut, "p5-desc", over)) == SPEC["profile_desc_max"]


def test_tc_prf_003_필수값_없으면_저장_비활성(sut, gate):
    """공백만 넣어도 비활성이어야 한다 — 이름이 필수값인 유일한 항목이다."""
    gate("성인 인증"); sut.evaluate(PANEL)
    _fill(sut, "p5-name", "")
    assert sut.is_disabled('[data-testid="p5-save"]')

    _fill(sut, "p5-name", "   ")
    assert sut.is_disabled('[data-testid="p5-save"]')

    _fill(sut, "p5-name", "이름")
    assert not sut.is_disabled('[data-testid="p5-save"]')


def test_tc_prf_004_label_상한_경계(sut, gate):
    """Label은 프로필의 용도를 적는 짧은 표기다."""
    gate("성인 인증"); sut.evaluate(PANEL)
    over = "가" * (SPEC["profile_label_max"] + 1)
    assert len(_fill(sut, "p5-label", over)) == SPEC["profile_label_max"]


def test_tc_prf_005_랜덤_완성도_규칙을_받음(sut, gate):
    """랜덤으로 채운 값도 상한·필수값 규칙을 그대로 받는다."""
    gate("성인 인증"); sut.evaluate(PANEL)
    sut.click('[data-testid="p5-random"]')

    assert sut.input_value('[data-testid="p5-name"]')
    assert len(sut.input_value('[data-testid="p5-name"]')) <= SPEC["profile_name_max"]
    assert len(sut.input_value('[data-testid="p5-desc"]')) <= SPEC["profile_desc_max"]
    assert not sut.is_disabled('[data-testid="p5-save"]')


def test_tc_prf_006_프로필_개수_한도(sut, gate):
    """한도 5는 §2가 정본이다 — 실측 100은 경계를 만드는 비용이 커 낮춘 값이다."""
    gate("성인 인증")
    for i in range(SPEC["profile_count_max"]):
        assert sut.evaluate("(n) => addProfile({ name: '프로필' + n }).ok", i)

    assert not sut.evaluate("() => addProfile({ name: '초과' }).ok")
    sut.evaluate(PANEL)
    assert sut.is_visible('[data-testid="p5-limit"]')


def test_tc_prf_007_대화_시작_시_프로필_고정(sut, gate):
    """방을 만든 뒤에는 프로필이 바뀌지 않는다 — 방마다 다른 프로필이 이 구조의 목적이다."""
    gate("성인 인증")
    room = sut.evaluate("""() => {
        const a = addProfile({ name: '첫프로필' });
        addProfile({ name: '둘째프로필' });
        return openRoom('c1', findProfile(a.id));
    }""")
    assert room["profile"]["name"] == "첫프로필"


def test_tc_prf_008_프로필_간_격리(sut, gate):
    """프로필을 지워도 그 프로필로 시작한 방은 저장된 값으로 남는다 — 방에 사본이 고정된다."""
    gate("성인 인증")
    rooms = sut.evaluate("""() => {
        const a = addProfile({ name: '가프로필', nickname: '가호칭' });
        const b = addProfile({ name: '나프로필', nickname: '나호칭' });
        const r1 = openRoom('c1', findProfile(a.id));
        const r2 = openRoom('c1', findProfile(b.id));
        return [r1.profile, r2.profile];
    }""")
    assert rooms[0]["name"] == "가프로필" and rooms[1]["name"] == "나프로필"
    assert rooms[0]["nickname"] != rooms[1]["nickname"]


def test_tc_prf_009_빈_상태_안내(sut, gate):
    """목록만 비어 있으면 폼이 안 뜬 것인지 프로필이 없는 것인지 구분되지 않는다."""
    gate("성인 인증"); sut.evaluate(PANEL)
    assert sut.is_visible('[data-testid="p5-empty"]')


def test_tc_saf_001_설명란_프롬프트_주입_차단(sut, gate):
    """게이팅 계층의 차단이며 모델 자체의 주입 내성 검증이 아니다."""
    gate("성인 인증")
    r = sut.evaluate("(t) => addProfile({ name: '주입', desc: t })", TOKENS["inject"][0])
    if r.get("ok"):
        # 저장을 우회해 들어와도 대화 경로에서 다시 막힌다 (2차 방어)
        room = sut.evaluate("(id) => openRoom('c1', findProfile(id))", r["id"])
        assert room and room.get("blocked") == "inject"
    else:
        assert r.get("reason")


def test_tc_prf_010_응답_내_이름_호칭_반영률(sut, gate, room, send):
    """반영률 계측이다 — 변주 분포를 우리가 작성했으므로 품질 지표로 서술하지 않는다."""
    gate("성인 인증")
    room("반영확인")
    hits = 0
    runs = 5
    for _ in range(runs):
        send("이름을 불러 줘")
        text = sut.evaluate("() => { const m = activeRoom().messages.filter(x => x.role === 'ai'); "
                            "return m[m.length - 1].text; }")
        # 방에 고정된 프로필 이름만 준수로 센다. 기본 폴백 호칭(「당신」)까지 인정하면
        # 치환을 통째로 무시하는 결함(persona-drift)이 만점으로 통과한다 — 준수율이
        # 무슨 값이든 100%가 되어 계측 자체가 성립하지 않는다
        if "반영확인" in text:
            hits += 1
    assert hits / runs >= SPEC["context_pass_rate"], f"반영률 {hits}/{runs}"


# ── 채팅 탭 ────────────────────────────────────────────────────────────────

def test_tc_cht_010_방_목록과_요약(sut, gate, room):
    """캐릭터 페이지의 대화방 목록과 다른 화면이다 — 여기는 캐릭터를 가리지 않고 모은다."""
    gate("성인 인증"); room("방목록")
    sut.evaluate("() => { VN.screen = 's2'; window.__VN__.refresh(); }")   # 셸로 복귀
    sut.click('[data-testid="g-nav-chat"]')

    assert sut.is_visible('[data-testid="s5-screen"]')
    assert sut.is_visible('[data-testid="s5-summary"]')
    assert sut.locator('[data-testid^="s5-room-"]').count() > 0


def test_tc_cht_011_방_선택_재진입(sut, gate, room):
    """대화방에 오는 길 넷 중 하나 — 각 경로의 진입 검증은 출발 화면에 남는다."""
    gate("성인 인증"); r = room("재진입")
    sut.evaluate("() => { VN.screen = 's2'; window.__VN__.refresh(); }")
    sut.click('[data-testid="g-nav-chat"]')
    sut.click(f'[data-testid="s5-room-{r["id"]}-open"]')
    assert sut.evaluate("() => VN.screen") == "s4"


def test_tc_cht_012_방_삭제(sut, gate, room):
    """되돌릴 수 없는 동작이라 한 번 묻는다 — 한도를 비우는 수단이기도 하다."""
    gate("성인 인증"); r = room("삭제대상")
    sut.evaluate("() => { VN.screen = 's2'; window.__VN__.refresh(); }")
    sut.click('[data-testid="g-nav-chat"]')
    before = sut.evaluate("() => currentAccount().rooms.length")

    sut.click(f'[data-testid="s5-room-{r["id"]}-delete"]')
    if sut.locator('[data-testid="g-confirm"]').count():
        sut.click('[data-testid="g-confirm-ok"]')
    assert sut.evaluate("() => currentAccount().rooms.length") == before - 1


def test_tc_cht_013_채팅_탭_빈_상태_안내(sut, gate):
    """첫 사용 화면이라 목록만 비면 로딩 중인지 방이 없는지 구분되지 않는다."""
    gate("성인 인증")
    sut.click('[data-testid="g-nav-chat"]')
    assert sut.is_visible('[data-testid="s5-empty"]')


# ── 재화 패널 ──────────────────────────────────────────────────────────────

def test_tc_cur_007_무료_유료_분리_표시(sut, gate):
    """시작 잔액은 캔디 150·크리스탈 0이다(§3)."""
    gate("성인 인증")
    sut.evaluate("() => { VN.panel = 'p3'; window.__VN__.refresh(); }")

    assert str(SPEC["wallet_start_free"]) in sut.text_content('[data-testid="p3-wallet-free"]')
    assert str(SPEC["wallet_start_paid"]) in sut.text_content('[data-testid="p3-wallet-paid"]')
    assert sut.is_visible('[data-testid="p3-help"]')


def test_tc_cur_008_데일리_미션_수령(sut, gate):
    """달성 판정 로직은 없고 전 항목이 수령 가능 상태로 노출된다 — 사유는 화면에 표기된다."""
    gate("성인 인증")
    before = sut.evaluate("() => currentAccount().wallet.free")
    sut.evaluate("() => { VN.panel = 'p4'; window.__VN__.refresh(); }")
    assert sut.is_visible('[data-testid="p4-mission-note"]')

    sut.click('[data-testid="p4-daily-claim"]')
    assert sut.evaluate("() => currentAccount().wallet.free") == before + SPEC["mission_reward"]


def test_tc_cur_009_데일리_중복_수령_차단(sut, gate):
    """기준일당 1회다 — 기준일을 바꾸면 다시 수령 가능해지는 것 자체가 검증 대상이다(§8-1)."""
    gate("성인 인증")
    assert sut.evaluate("() => claimDaily().ok")
    after = sut.evaluate("() => currentAccount().wallet.free")

    assert not sut.evaluate("() => claimDaily().ok")
    assert sut.evaluate("() => currentAccount().wallet.free") == after

    sut.evaluate("() => window.__VN__.setBaseDay('2026-09-09')")
    assert sut.evaluate("() => claimDaily().ok")                  # 날이 바뀌면 다시 받는다


def test_tc_cur_010_웰컴_미션_항목별_1회(sut, gate):
    """가입 환영·첫 대화·페르소나 등록 세 항목이며 각각 1회다."""
    gate("성인 인증")
    wid = sut.evaluate("() => WELCOME_MISSIONS[0].id")
    before = sut.evaluate("() => currentAccount().wallet.free")

    assert sut.evaluate("(id) => claimWelcome(id).ok", wid)
    assert sut.evaluate("() => currentAccount().wallet.free") == before + SPEC["mission_reward"]
    assert not sut.evaluate("(id) => claimWelcome(id).ok", wid)


def test_tc_cur_011_내역_기록과_필터(sut, gate, room, send):
    """혼합 차감은 캔디와 크리스탈 두 줄로 남는다. 두 패널이 같은 데이터를 같은 뷰로 본다."""
    gate("성인 인증"); room()
    send("내역 남기기")
    sut.evaluate("() => { claimDaily(); VN.screen = 's2'; VN.panel = 'p3';"
                 "  VN.ledgerFilter = 'all'; window.__VN__.refresh(); }")
    total = sut.locator('[data-testid^="p3-row-"]').count()
    assert total >= 2                                             # 획득과 소모가 모두 있다

    sut.click('[data-testid="p3-filter-spend"]')
    spend_only = sut.locator('[data-testid^="p3-row-"]').count()
    assert 0 < spend_only < total


def test_tc_cur_012_충전_성공_반영(sut, gate):
    """실 PG 연동은 검증 불가 항목이며 mock 콜백만 본다."""
    gate("성인 인증")
    sut.evaluate("() => { VN.panel = 'p3'; window.__VN__.refresh(); }")
    before = sut.evaluate("() => currentAccount().wallet.paid")

    sut.click('[data-testid="p3-charge-ok"]')
    assert sut.evaluate("() => currentAccount().wallet.paid") == before + SPEC["charge_amount"]


def test_tc_cur_013_충전_실패_롤백(sut, gate):
    """실패가 잔액을 건드리면 결제 정합이 깨진다 — 내역까지 확인해 절반 반영을 잡는다."""
    gate("성인 인증")
    sut.evaluate("() => { VN.panel = 'p3'; window.__VN__.refresh(); }")
    before = sut.evaluate("() => currentAccount().wallet.paid")
    rows = sut.locator('[data-testid^="p3-row-"]').count()

    sut.click('[data-testid="p3-charge-fail"]')
    assert sut.evaluate("() => currentAccount().wallet.paid") == before
    assert sut.locator('[data-testid^="p3-row-"]').count() == rows


def test_tc_cur_014_잔액_진입점_일관(sut, gate, room):
    """패널은 전역이라 두 곳에서 열린다 — 다른 값을 보이면 잔액 정합이 깨진 것이다."""
    gate("성인 인증"); room()
    sut.click('[data-testid="s4-wallet"]')
    from_room = sut.text_content('[data-testid="p3-wallet-free"]')
    sut.click('[data-testid="p3-close"]')

    sut.evaluate("() => { VN.screen = 's2'; window.__VN__.refresh(); }")
    sut.click('[data-testid="g-wallet"]')
    assert sut.text_content('[data-testid="p3-wallet-free"]') == from_room


# ── 로그인 모달 · 푸터 ──────────────────────────────────────────────────────

def test_tc_ent_006_막힌_동작_이어받기(sut, gate):
    """막을 때는 아무것도 하지 않고 풀리면 그때 수행한다는 규칙의 짝이다."""
    gate("미로그인")
    sut.click('[data-testid="g-nav-chat"]')
    assert sut.is_visible('[data-testid="g-login-modal"]')

    sut.click('[data-testid="g-login-a"]')
    assert sut.locator('[data-testid="g-login-modal"]').count() == 0
    assert sut.evaluate("() => VN.screen") == "s5"                # 막혔던 탭이 열린다


def test_tc_ent_007_로그인_모달_닫기(sut, gate):
    """모달은 뒤 화면을 살려 두므로 닫으면 제자리다 — 몰래 수행되지 않았는지도 본다."""
    gate("미로그인")
    sut.click('[data-testid="g-nav-chat"]')
    sut.click('[data-testid="g-login-close"]')

    assert sut.locator('[data-testid="g-login-modal"]').count() == 0
    assert sut.is_visible('[data-testid="s2-screen"]')
    assert sut.evaluate("() => VN.screen") != "s5"


def test_tc_ent_010_푸터_구성과_빌드_표기(sut, gate):
    """청사진이 기대값의 출처인 SUT 검증 케이스다 — 빌드는 이슈의 영향 받는 버전이 가리키는 값이다."""
    gate("성인 인증")
    assert sut.is_visible('[data-testid="g-footer"]')
    assert sut.is_visible('[data-testid="g-footer-tree"]')
    assert "RC" in sut.text_content('[data-testid="g-build"]')
