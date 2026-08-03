# -*- coding: utf-8 -*-
"""대화방 — 송수신(CHT) · 서사(NAR) · 되돌림 · 소모(CUR) · 세이프티(SAF) · 만료 차단(ENT)

되돌림의 축은 **화면에서 사라진 메시지는 점수와 기억에서도 사라진다**입니다(§5-1). 그래서
되돌림 케이스는 화면만이 아니라 호감도·대화수까지 함께 봅니다.

재계산은 「지운 만큼 빼기」가 아니라 **남은 기록으로 다시 세기**입니다 — 호감도 하한이 0이라
뺄셈으로 되돌리면 없던 점수가 생깁니다. 전송도 같은 계산을 쓰므로 두 경로가 같은 값을 냅니다.
"""
from thresholds import SPEC, TOKENS, bypass_variants

STAGE = SPEC["stage_bounds"]


def _room_state(sut):
    return sut.evaluate("() => { const r = activeRoom(); return "
                        "{ turn: r.turn, affection: r.affection, msgs: r.messages.length }; }")


def _wallet(sut):
    return sut.evaluate("() => currentAccount().wallet.free")


# ── 송수신 ──────────────────────────────────────────────────────────────────

def test_tc_cht_001_전송과_스트리밍_표시(sut, gate, room, send):
    """대기는 고정 시간이 아니라 표시 중 표식이 사라지는 것으로 판정한다(§3)."""
    gate("성인 인증"); room()
    assert sut.is_visible('[data-testid="s4-msg-0-ai"]')      # 첫 메시지

    send("안녕")
    assert sut.is_visible('[data-testid="s4-msg-1-user"]')
    assert sut.is_visible('[data-testid="s4-msg-1-ai"]')
    assert sut.locator('[data-testid="s4-streaming"]').count() == 0


def test_tc_cht_002_자유_입력_상한_경계(sut, gate, room):
    """어느 경로로 들어와도 상한을 넘는 값이 남지 않는 것이 기대값이다."""
    gate("성인 인증"); room()
    sut.fill('[data-testid="s4-input"]', "가" * (SPEC["input_max"] + 1))
    assert len(sut.input_value('[data-testid="s4-input"]')) == SPEC["input_max"]
    assert str(SPEC["input_max"]) in sut.text_content('[data-testid="s4-input-count"]')


def test_tc_cht_009_방_없을_때_안내(sut, gate):
    """주소로 들어왔으나 열 방이 없는 경우 — 로그인 여부와는 다른 층의 빈 상태다."""
    gate("성인 인증")
    sut.evaluate("() => { VN.screen = 's4'; window.__VN__.refresh(); }")
    assert sut.is_visible('[data-testid="s4-noroom"]')


def test_tc_cht_008_대화수_표시_정합(sut, gate, room, send):
    """대화수는 유저+AI 턴 합산이고 첫 메시지를 포함한다."""
    gate("성인 인증"); room()
    before = sut.evaluate("() => roomMessageCount(activeRoom())")
    send("한 턴")
    assert sut.evaluate("() => roomMessageCount(activeRoom())") == before + 2


# ── 서사 ────────────────────────────────────────────────────────────────────

def test_tc_nar_001_선택지_진행과_가중치(sut, gate, room, send):
    """가중치는 호감형 +2 · 중립 +1 · 비호감 −1이다(§4-1)."""
    gate("성인 인증"); room()
    weight = SPEC["affection_choice"]["호감형"]
    sut.evaluate("(w) => sendMessage('선택', w)", weight)
    sut.wait_for_selector('[data-testid="s4-streaming"]', state="detached")

    # 한 턴에는 선택지 기여분과 AI 응답의 기여분이 함께 실린다. 「가중치 반영」의 검증
    # 대상은 선택지 쪽이므로 그 메시지의 기여분을 직접 본다
    user_delta = sut.evaluate("() => activeRoom().messages.find(m => m.turn === 1 && m.role === 'user').delta")
    assert user_delta == weight
    assert sut.is_visible('[data-testid="s4-msg-1-user"]')


def test_tc_nar_002_호감도_하한_0(sut, gate, room):
    """하한 0은 되돌림의 「다시 세기」 방식을 정한 근거이기도 하다(§5-1)."""
    gate("성인 인증"); room()
    sut.evaluate("() => { const r = activeRoom();"
                 "  r.affection = 0; r.affectionBase = 0; r.affectionBaseTurn = r.turn; }")
    sut.evaluate("() => sendMessage('비호감', -1)")
    sut.wait_for_selector('[data-testid="s4-streaming"]', state="detached")
    assert sut.evaluate("() => activeRoom().affection") >= 0


def test_tc_nar_003_관계_단계_임계_전이(sut, gate, room):
    """구간은 경계 0~19 · 호기심 20~59 · 애착 60~119 · 운명 120+."""
    gate("성인 인증"); room()
    assert sut.evaluate("(v) => stageOf(v).name", STAGE["호기심"] - 1) == "경계"
    assert sut.evaluate("(v) => stageOf(v).name", STAGE["호기심"]) == "호기심"
    assert sut.evaluate("(v) => stageOf(v).name", STAGE["애착"]) == "애착"
    assert sut.evaluate("(v) => stageOf(v).name", STAGE["운명"]) == "운명"


def test_tc_nar_004_단계_도달_표시(sut, gate, room):
    """패널의 ⓘ에 단계 구간표가 있어 화면 안에서 기준을 읽을 수 있다."""
    gate("성인 인증"); room()
    sut.evaluate("() => { activeRoom().affection = 60; VN.panel = 'p2'; window.__VN__.refresh(); }")
    assert "애착" in sut.text_content('[data-testid="p2-stage"]')

    sut.click('[data-testid="p2-help"]')
    assert sut.is_visible('[data-testid="p2-help-body"]')


def test_tc_nar_005_검사_시점_굿_엔딩_판정(sut, gate, room, send):
    """검사 시점의 판정은 굿만 나온다 — 배드는 종점 판정에서만(§4-2)."""
    gate("성인 인증"); room()
    # 호감도는 base에서 다시 세어지므로 base를 운명 구간 위로 올려 둔다
    check = SPEC["ending_check_from"]
    sut.evaluate("(t) => { const r = activeRoom();"
                 "  r.affectionBase = 130; r.affectionBaseTurn = t - 1; r.turn = t - 1; }", check)
    send("검사 시점")

    assert sut.evaluate("() => activeRoom().ending") == "굿"
    assert sut.is_visible('[data-testid="s4-ending"]')
    assert "굿" in sut.text_content('[data-testid="s4-ending-kind"]')


def test_tc_nar_006_종점_배드_엔딩_판정(sut, gate, room, send):
    """종점 판정은 120 이상 굿 / 20 미만 배드 / 그 외 노멀이다."""
    gate("성인 인증"); room()
    # 기준점을 종점 직전으로 당겨 호감도가 쌓이지 않게 한다 — 종점에서 경계 구간이라야
    # 배드가 나온다(자유 입력 턴도 mock 델타로 오르는 구조라 그냥 두면 노멀이 된다)
    sut.evaluate("""() => {
        const r = activeRoom();
        const set = mockSetFor(r.charId, r.scenarioId);
        r.affectionBase = 0; r.affectionBaseTurn = set.endTurn - 1; r.turn = set.endTurn - 1;
    }""")
    send("종점")

    assert sut.evaluate("() => activeRoom().ended")
    assert sut.evaluate("() => activeRoom().affection") < SPEC["stage_bounds"]["호기심"]
    assert sut.is_visible('[data-testid="s4-ending"]')
    assert "배드" in sut.text_content('[data-testid="s4-ending-kind"]')


# ── 되돌림 ──────────────────────────────────────────────────────────────────

def test_tc_cht_003_액션_노출_범위(sut, gate, room, send):
    """과거 턴에서 되돌림 셀렉터가 잡히면 실패다 — 과거 개입은 분기가 맡는다."""
    gate("성인 인증"); room()
    send("첫 턴"); send("둘째 턴")

    for act in ("edit", "delete", "regen"):                     # 최신 교환에만
        assert sut.locator(f'[data-testid="s4-msg-2-{act}"]').count() == 1
        assert sut.locator(f'[data-testid="s4-msg-1-{act}"]').count() == 0
    assert sut.locator('[data-testid="s4-msg-1-branch"]').count() == 1


def test_tc_cht_004_교환_삭제와_재계산(sut, gate, room, send):
    """삭제 단위는 교환 통째이고, 되돌린 뒤 상태는 처음부터 그렇게 대화했을 때와 같다."""
    gate("성인 인증"); room()
    send("첫 턴")
    base = _room_state(sut)
    send("둘째 턴")

    sut.click('[data-testid="s4-msg-2-delete"]')
    assert sut.is_visible('[data-testid="g-confirm"]')
    sut.click('[data-testid="g-confirm-ok"]')

    after = _room_state(sut)
    assert after["msgs"] == base["msgs"]
    assert after["affection"] == base["affection"]              # 기여분이 정확히 취소된다


def test_tc_cht_005_메시지_편집_후_재생성(sut, gate, room, send):
    """편집된 유저 메시지의 AI 응답은 무효가 되어 재생성되고 상태가 재계산된다."""
    gate("성인 인증"); room()
    send("원본")
    old = sut.text_content('[data-testid="s4-msg-1-ai"]')

    sut.click('[data-testid="s4-msg-1-edit"]')
    assert sut.is_visible('[data-testid="s4-edit-input"]')
    sut.fill('[data-testid="s4-edit-input"]', "고친 내용")
    sut.click('[data-testid="s4-edit-save"]')
    sut.wait_for_selector('[data-testid="s4-streaming"]', state="detached")

    assert "고친 내용" in sut.text_content('[data-testid="s4-msg-1-user"]')
    assert sut.evaluate("() => activeRoom().messages.filter(m => m.role === 'user').length") == 1


def test_tc_cht_006_ai_응답_재생성과_맥락_격리(sut, gate, room, send):
    """재생성은 후보를 한 칸 미는 것이라 난수가 없다 — 몇 번째인지가 정해지면 결과도 정해진다."""
    gate("성인 인증"); room()
    send("원본")
    before = sut.evaluate("() => activeRoom().messages.find(m => m.turn === 1 && m.role === 'ai').variant")

    sut.click('[data-testid="s4-msg-1-regen"]')
    sut.wait_for_selector('[data-testid="s4-streaming"]', state="detached")
    after = sut.evaluate("() => activeRoom().messages.find(m => m.turn === 1 && m.role === 'ai').variant")
    assert after != before
    assert sut.evaluate("() => activeRoom().messages.filter(m => m.turn === 1 && m.role === 'ai').length") == 1


def test_tc_cur_001_재생성_재차감(sut, gate, room, send):
    """새 응답을 만드는 모든 경로가 차감한다 — 되돌림으로 재화가 환급되지는 않는다."""
    gate("성인 인증"); room()
    send("원본")
    before = _wallet(sut)

    sut.click('[data-testid="s4-msg-1-regen"]')
    sut.wait_for_selector('[data-testid="s4-streaming"]', state="detached")
    assert _wallet(sut) == before - SPEC["send_cost"]


def test_tc_cht_007_과거_턴_분기_생성(sut, gate, room, send):
    """타임머신형 — 원본 방은 그대로 남고 이후 두 방은 서로를 참조하지 않는다."""
    gate("성인 인증"); room()
    send("첫 턴"); send("둘째 턴")
    rooms_before = sut.evaluate("() => currentAccount().rooms.length")
    wallet_before = _wallet(sut)

    sut.click('[data-testid="s4-msg-1-branch"]')
    sut.click('[data-testid="g-confirm-ok"]')

    assert sut.evaluate("() => currentAccount().rooms.length") == rooms_before + 1
    assert _wallet(sut) == wallet_before                        # 분기는 무료다


# ── 세이브/로드 ─────────────────────────────────────────────────────────────

def test_tc_sav_001_슬롯_저장과_복원(sut, gate, room, send):
    """슬롯은 대화방마다 4개이며 저장·로드 모두 무료다."""
    gate("성인 인증"); room()
    send("저장 시점")
    saved = _room_state(sut)

    sut.evaluate("() => { saveSlot(activeRoom(), 1); }")
    send("저장 뒤 진행")
    assert _room_state(sut)["turn"] != saved["turn"]

    sut.evaluate("() => { loadSlotHere(activeRoom(), 1); window.__VN__.refresh(); }")
    assert _room_state(sut)["turn"] == saved["turn"]
    assert _room_state(sut)["affection"] == saved["affection"]


def test_tc_sav_002_빈_슬롯_로드_불가(sut, gate, room):
    """빈 슬롯을 눌러 아무 일도 안 일어나는 것과 비활성은 다르다."""
    gate("성인 인증"); room()
    sut.evaluate("() => { VN.panel = 'p1'; window.__VN__.refresh(); }")
    assert "비어" in sut.text_content('[data-testid="p1-slot-2-info"]')
    assert sut.is_disabled('[data-testid="p1-slot-2-load"]')


def test_tc_sav_003_덮어쓰기_저장_확인(sut, gate, room, send):
    """되돌릴 수 없는 동작이라 한 번 묻는다."""
    gate("성인 인증"); room()
    send("첫 저장")
    sut.evaluate("() => { saveSlot(activeRoom(), 1); }")
    send("두 번째")

    sut.evaluate("() => { VN.panel = 'p1'; window.__VN__.refresh(); }")
    sut.click('[data-testid="p1-slot-1-save"]')
    assert sut.is_visible('[data-testid="g-confirm"]')
    sut.click('[data-testid="g-confirm-ok"]')
    assert sut.evaluate("() => window.__VN__.getSave(1).room.messages.length") == _room_state(sut)["msgs"]


def test_tc_sav_004_덮어쓰기_로드_복원(sut, gate, room, send):
    """저장 시점 이후의 대화·상태 변화가 남지 않아야 한다."""
    gate("성인 인증"); room()
    send("저장 시점")
    sut.evaluate("() => { saveSlot(activeRoom(), 1); }")
    saved = _room_state(sut)
    send("이후 진행")

    sut.evaluate("() => { VN.panel = 'p1'; window.__VN__.refresh(); }")
    sut.click('[data-testid="p1-slot-1-load"]')
    assert sut.is_visible('[data-testid="p1-load-pick"]')
    sut.click('[data-testid="p1-load-here"]')

    assert _room_state(sut)["msgs"] == saved["msgs"]


def test_tc_sav_005_새_방으로_로드(sut, gate, room, send):
    """새 방 갈래가 곧 분기 생성이며 원본 방은 그대로 남는다."""
    gate("성인 인증"); room()
    send("저장 시점")
    sut.evaluate("() => { saveSlot(activeRoom(), 1); }")
    rooms_before = sut.evaluate("() => currentAccount().rooms.length")

    sut.evaluate("() => { VN.panel = 'p1'; window.__VN__.refresh(); }")
    sut.click('[data-testid="p1-slot-1-load"]')
    sut.click('[data-testid="p1-load-new"]')
    assert sut.evaluate("() => currentAccount().rooms.length") == rooms_before + 1


def test_tc_sav_006_슬롯_간_격리(sut, gate, room, send):
    """화면만 봐서는 혼입을 판정할 수 없어 상태 훅으로 확인한다 — 자동화 전용이다."""
    gate("성인 인증"); room()
    send("첫 시점")
    sut.evaluate("() => { saveSlot(activeRoom(), 1); }")
    first = sut.evaluate("() => window.__VN__.getSave(1).room.messages.length")

    send("둘째 시점")
    sut.evaluate("() => { saveSlot(activeRoom(), 2); }")
    second = sut.evaluate("() => window.__VN__.getSave(2).room.messages.length")

    assert first != second
    assert sut.evaluate("() => window.__VN__.getSave(1).room.messages.length") == first   # 1번이 안 흔들린다


def test_tc_sav_007_한도_찼을_때_새_방_차단(sut, gate, room, send):
    """묻기만 하고 지우지 않으면 아무 방도 만들어지지 않아야 한다(§6)."""
    gate("성인 인증"); room()
    send("저장 시점")
    sut.evaluate("() => { saveSlot(activeRoom(), 1); }")
    sut.evaluate("(n) => { const acc = currentAccount(); const c = activeRoom().charId;"
                 "  while (acc.rooms.filter(r => r.charId === c).length < n)"
                 "    acc.rooms.push(Object.assign({}, activeRoom(), { id: 'pad' + acc.rooms.length })); }",
                 SPEC["rooms_per_char"])
    rooms_before = sut.evaluate("() => currentAccount().rooms.length")

    assert sut.evaluate("() => loadSlotToNewRoom(activeRoom(), 1)") is None
    assert sut.evaluate("() => currentAccount().rooms.length") == rooms_before


# ── 메모리/컨텍스트 ─────────────────────────────────────────────────────────

def test_tc_mem_001_현재_상태_대시보드(sut, gate, room):
    """패널은 대화방 하위 오버레이라 대화방 소속이다."""
    gate("성인 인증"); room()
    sut.evaluate("() => { VN.panel = 'p2'; window.__VN__.refresh(); }")
    for tid in ("p2-stage", "p2-affection", "p2-temp", "p2-nickname"):
        assert sut.is_visible(f'[data-testid="{tid}"]'), tid


def test_tc_mem_002_상태_값_고정_우선(sut, gate, room, send):
    """유저가 정한 것이 AI 판단보다 우선이다 — 관계 단계·호감도는 엔딩 근거라 고정 불가."""
    gate("성인 인증"); room()
    sut.evaluate("() => { VN.panel = 'p2'; window.__VN__.refresh(); }")
    sut.fill('[data-testid="p2-nickname-input"]', "고정호칭")
    sut.click('[data-testid="p2-nickname-fix"]')
    assert "고정" in sut.text_content('[data-testid="p2-nickname-state"]')

    send("몇 턴 더")
    sut.evaluate("() => { VN.panel = 'p2'; window.__VN__.refresh(); }")
    assert "고정호칭" in sut.text_content('[data-testid="p2-nickname"]')
    assert sut.is_visible('[data-testid="p2-fix-help"]')


def test_tc_mem_003_대화에서_기억_등록(sut, gate, room, send):
    """기억하기는 과거 턴에도 붙는다 — 되돌림 액션과 노출 범위가 다르다."""
    gate("성인 인증"); room()
    send("기억할 내용")
    sut.click('[data-testid="s4-msg-1-user-remember"]')

    sut.evaluate("() => { VN.panel = 'p2'; window.__VN__.refresh(); }")
    assert sut.locator('[data-testid^="p2-memory-"]').count() > 0


def test_tc_mem_004_고정한_기억은_간략화_제외(sut, gate, room, send):
    """간략화는 장면이 끝날 때 오는, 기억이 저절로 바뀌는 유일한 사건이다."""
    gate("성인 인증"); room()
    send("기억 대상")
    sut.click('[data-testid="s4-msg-1-user-remember"]')
    sut.evaluate("() => { VN.panel = 'p2'; window.__VN__.refresh(); }")

    mid = sut.evaluate("() => activeRoom().memories[0].id")
    sut.evaluate("(id) => toggleMemoryPin(activeRoom(), id)", mid)
    assert sut.evaluate("(id) => activeRoom().memories.find(m => m.id === id).pinned", mid)


def test_tc_mem_005_기억_삭제와_재등장_차단(sut, gate, room, send):
    """참조 차단은 삭제뿐 아니라 되돌림·분기·로드로 없어진 경우에도 적용된다."""
    gate("성인 인증"); room()
    send("지울 기억")
    sut.click('[data-testid="s4-msg-1-user-remember"]')
    sut.evaluate("() => { VN.panel = 'p2'; window.__VN__.refresh(); }")

    mid = sut.evaluate("() => activeRoom().memories[0].id")
    sut.evaluate("(id) => deleteMemory(activeRoom(), id)", mid)
    assert sut.evaluate("(id) => !activeRoom().memories.some(m => m.id === id)", mid)
    assert sut.evaluate("() => (activeRoom().forgotten || []).length") > 0


def test_tc_mem_006_단기_맥락_창_경계(sut, gate, room):
    """창은 최근 N턴이고 합격선은 계측이다 — 창 경계 자체는 결정적으로 본다."""
    gate("성인 인증"); room()
    win = SPEC["context_window_turns"]
    sut.evaluate("(n) => { activeRoom().turn = n + 5; }", win)
    span = sut.evaluate("() => contextRange(activeRoom())")
    assert span["to"] - span["from"] + 1 <= win


# ── 소모 ────────────────────────────────────────────────────────────────────

def test_tc_cur_002_전송_차감(sut, gate, room, send):
    """요율은 §3이 정본이며 겸용 소모 시 무료분이 먼저 나간다."""
    gate("성인 인증"); room()
    before = _wallet(sut)
    send("한 턴")
    assert _wallet(sut) == before - SPEC["send_cost"]


def test_tc_cur_003_소모_우선순위(sut, gate, room, send):
    """캔디 우선, 부족분은 크리스탈에서 혼합 차감한다."""
    gate("성인 인증"); room()
    sut.evaluate("() => { const w = currentAccount().wallet; w.free = 4; w.paid = 50; }")
    send("혼합 차감")

    w = sut.evaluate("() => currentAccount().wallet")
    assert w["free"] == 0
    assert w["paid"] == 50 - (SPEC["send_cost"] - 4)


def test_tc_cur_004_잔액_0_차단(sut, gate, room):
    """차단된 전송은 재화·턴·대화수 어디에도 흔적이 없어야 한다."""
    gate("성인 인증"); room()
    sut.evaluate("() => { const w = currentAccount().wallet; w.free = 0; w.paid = 0; }")
    before = _room_state(sut)

    sut.evaluate("() => sendMessage('부족')")
    assert sut.is_visible('[data-testid="g-nofund-modal"]')
    assert _room_state(sut)["msgs"] == before["msgs"]
    assert sut.is_visible('[data-testid="g-nofund-charge"]')


def test_tc_cur_005_연타_이중_차감_방지(sut, gate, room):
    """사람 손으로는 간격이 매번 달라 조건이 흔들린다 — 자동화가 간격을 고정해야 성립한다."""
    gate("성인 인증"); room()
    before = _wallet(sut)
    sut.evaluate("() => { sendMessage('연타'); sendMessage('연타'); }")
    sut.wait_for_selector('[data-testid="s4-streaming"]', state="detached")

    assert _wallet(sut) == before - SPEC["send_cost"]
    assert sut.evaluate("() => activeRoom().messages.filter(m => m.role === 'user').length") == 1


def test_tc_cur_006_생성_실패_시_미차감(sut, gate, room):
    """두 실패는 결과가 같고 알림만 다르다 — 어느 쪽도 잔액·내역·대화를 건드리지 않는다."""
    gate("성인 인증"); room()
    before_wallet, before_room = _wallet(sut), _room_state(sut)

    sut.evaluate("() => { window.__VN__.failNext(true); sendMessage('실패할 전송'); }")
    sut.wait_for_selector('[data-testid="s4-streaming"]', state="detached")

    assert _wallet(sut) == before_wallet
    assert _room_state(sut)["msgs"] == before_room["msgs"]
    assert sut.is_visible('[data-testid="g-toast"]')


# ── 세이프티 ────────────────────────────────────────────────────────────────

def test_tc_saf_002_금칙_입력_차단(sut, gate, room):
    """입력 차단은 치는 동안이 아니라 전송할 때 한다 — 주입 경로와 같은 지점에서 걸린다."""
    gate("성인 인증"); room()
    before = _wallet(sut)

    sut.evaluate("(t) => sendMessage(t)", TOKENS["blocked"][0])
    assert sut.is_visible('[data-testid="g-blocked-modal"]')
    assert _wallet(sut) == before                                # 아무것도 소비하지 않는다
    assert sut.input_value('[data-testid="s4-input"]') == TOKENS["blocked"][0]


def test_tc_saf_003_우회_시도_정규화_방어(sut, gate, room):
    """대조 전에 공백·특수문자를 지운다 — 쪼개 넣는 것이 우회의 형태다."""
    gate("성인 인증"); room()
    for variant in bypass_variants(TOKENS["blocked"][0]):
        assert not sut.evaluate("(t) => screenInput(t).ok", variant), variant


def test_tc_saf_004_금칙_후보_대체(sut, gate, room, send):
    """마스킹이 아니라 대체다 — 걸러졌다는 사실은 화면에 표기한다."""
    gate("성인 인증"); room()
    # 금칙 토큰이 든 후보만 남은 턴을 만들고, 그 후보가 쓰이지 않는지 본다
    sut.evaluate("""(token) => {
        const r = activeRoom();
        const set = mockSetFor(r.charId, r.scenarioId);
        set.turns[r.turn].candidates.forEach((c, i) => { if (i > 0) c.text = token; });
    }""", TOKENS["blocked"][0])
    send("금칙 후보 턴")

    text = sut.text_content('[data-testid="s4-msg-1-ai"]')
    assert TOKENS["blocked"][0] not in text


def test_tc_saf_005_프롬프트_누출_차단(sut, gate, room):
    """게이팅 계층의 검증이며 모델 자체의 안전성 검증이 아니다."""
    gate("성인 인증"); room()
    sut.evaluate("(t) => sendMessage(t)", TOKENS["leak"][0])
    sut.wait_for_selector('[data-testid="s4-streaming"]', state="detached")
    sut.evaluate("() => window.__VN__.refresh()")
    assert sut.locator('[data-testid="s4-msg-1-leak"]').count() == 1


# ── 만료 상태 차단 (뎁스는 대화방, 영역은 앱 진입/세션) ──────────────────────

def test_tc_ent_004_만료_상태_전송_차단(sut, gate, room):
    """명세 §1-1의 만료 행이 차단한다고 적은 것은 전송·저장·수령이다."""
    gate("성인 인증"); room()
    before = _room_state(sut)
    sut.evaluate("() => { window.__VN__.expireSession(); window.__VN__.refresh(); }")

    sut.evaluate("() => sendMessage('만료 상태 전송')")
    assert _room_state(sut)["msgs"] == before["msgs"]
    assert sut.is_visible('[data-testid="g-expired-modal"]')
