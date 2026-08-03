# -*- coding: utf-8 -*-
"""임계·반복 값의 단일 출처 (rules/sut-automation.md §4 임계·반복 관리)

케이스마다 숫자를 흩어 두면 리포트의 표기와 코드의 실제 값이 조용히 어긋납니다. 여기 한 곳에
모으고, 리포트는 이 모듈을 읽어 표기합니다 — 리포트에 수치를 하드코딩하지 않습니다.

**임계값 변경은 스펙 변경입니다.** 커밋 [스펙 변경]과 change-log에 함께 적습니다.

기획 확정값(SPEC_*)과 실행 설정(RUN_*)을 갈라 둡니다 — 앞은 system-spec이 정본이라 코드가
따라가는 값이고, 뒤는 자동화가 정하는 값입니다. 섞으면 SUT 명세가 바뀌었는지 테스트 사정이
바뀌었는지 커밋에서 구분되지 않습니다.
"""

# ── 기획 확정값 — 정본은 spec/design/qa-lab-miyonchat-system-spec.md ────────────
SPEC = {
    # §2 유저 페르소나
    "profile_name_max": 12,          # 이름 상한
    "profile_nickname_max": 12,      # 호칭 상한
    "profile_desc_max": 1000,        # 자유 설명 상한
    "profile_label_max": 30,         # Label 상한
    "profile_count_max": 5,          # 프로필 개수 상한
    # §3 재화
    "wallet_start_free": 150,        # 시작 캔디
    "wallet_start_paid": 0,          # 시작 크리스탈
    "send_cost": 10,                 # 전송 1회 요율(캔디)
    "mission_reward": 50,            # 미션 1건 보상
    "charge_amount": 100,            # mock 충전량(크리스탈)
    # §4 서사
    "affection_choice": {"호감형": 2, "중립": 1, "비호감": -1},
    "stage_bounds": {"경계": 0, "호기심": 20, "애착": 60, "운명": 120},
    "ending_check_from": 10,         # 엔딩 검사 시작 턴
    "ending_check_every": 5,         # 이후 검사 주기
    # §5 대화 세션
    "input_max": 500,                # 자유 입력 상한
    # §6 세이브/로드
    "rooms_per_char": 4,             # 캐릭터당 대화방
    "slots_per_room": 4,             # 대화방당 시점 슬롯
    # §7 메모리
    "context_window_turns": 10,      # 단기 맥락 창
    "context_pass_rate": 0.80,       # 반영률 합격선 — 계측 표기
    # §8 탐색·집계
    "new_window_days": 60,           # 신작 창
    "review_min_sample": 50,         # 리뷰 점수순 최소 표본
    "carousel_max": 7,               # 추천 캐러셀 상한
    "section_top": 5,                # 떠오르는 신작·지금 뜨거운 상한
    "related_like_min": 10,          # 그 외 작품 추천 좋아요 임계
    "related_max": 5,                # 그 외 작품 추천 노출 상한
}

# ── 실행 설정 — 자동화가 정하는 값 ─────────────────────────────────────────────
RUN = {
    # 확률적 케이스의 반복 — 반복은 테스트 함수 안에서 돌립니다(§2). parametrize로
    # 쪼개면 반복이 독립 케이스로 집계되어 성공률을 계산할 수 없습니다
    "probabilistic_runs": 20,
    # 금칙 케이스의 우회 변형 수 — 정규화 방어를 확인하는 변형 목록의 크기
    "bypass_variants": 6,
    # 조건 대기의 상한(ms). 지나면 성공이 아니라 **실패**입니다(§3 대기 규칙)
    "wait_timeout_ms": 5000,
}

# 금칙 코퍼스는 추상 토큰만 씁니다 — 실제 탈옥 문자열을 저장소에 넣지 않습니다(§9-1)
TOKENS = {
    "blocked": ["[BLOCKED_TERM_A]", "[BLOCKED_TERM_B]", "[BLOCKED_TERM_C]"],
    "jailbreak": ["[JAILBREAK_A]", "[JAILBREAK_B]"],
    "inject": ["[INJECT_A]", "[INJECT_B]"],
    "leak": ["[LEAK_PROMPT]"],
}


def bypass_variants(token):
    """정규화 방어 확인용 변형 — 공백·특수문자를 끼워 넣어 같은 토큰으로 읽히는지 본다.

    대조 전에 공백·특수문자를 지우는 것이 방어 방식이므로(§9-1), 쪼개 넣은 것도 같은 것으로
    판정되어야 한다. 변형 수는 RUN["bypass_variants"]가 정한다.
    """
    body = token.strip("[]")
    out = [
        token,
        f"[{body[:3]} {body[3:]}]",
        f"[{'-'.join(body)}]",
        f"[{body[:4]}_{body[4:]}]",
        f"[ {body} ]",
        f"[{body.replace('_', ' _ ')}]",
    ]
    return out[: RUN["bypass_variants"]]
