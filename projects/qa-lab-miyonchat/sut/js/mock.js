/* mock 응답 세트 — 정적 데이터 (mock-llm-spec)
 *
 * 캐릭터는 대답을 생성하지 않습니다. 턴 순서대로 깔아 둔 후보 중 하나를 **시드가** 고릅니다.
 * 그래서 같은 시드·같은 입력 순서면 언제나 같은 응답열이 나오고, 실패한 테스트는 시드와
 * 입력만 적어 두면 재현됩니다. 무작위 함수는 쓰지 않습니다(mock-llm-spec §1).
 *
 * 유저가 친 내용은 응답 선택에 관여하지 않습니다 — 관여하는 곳은 입력 필터(금칙 토큰)·
 * 길이 상한·페르소나 슬롯 치환 셋뿐입니다.
 *
 * **긴 경로를 조립으로 만듭니다.** 전용 100턴·공통 30턴 분량의 대사를 한 줄씩 적으면 파일이
 * 검증과 무관한 분량으로 불어나므로, 서사를 구간으로 나누고 구간별 대사 풀에서 **턴 번호로**
 * 뽑아 조립합니다. 난수를 쓰지 않으므로 결정성은 그대로입니다.
 *
 * 세트 범위(§2-1): 전용 = 3일간의 행복(c7) / 공통 = 그 외 전부 + T1에서 생성한 캐릭터.
 *
 * 변주 분포(§3): 반영 후보가 80% 이상이 되도록 풀을 구성했습니다.
 *
 * 필드
 *   text            {userName}·{nickname}·{charName} 슬롯을 담은 응답문
 *   deltaAffection  이 후보가 만드는 호감도 변화
 *   memoryAdd       기억 목록에 쌓이는 항목 (메모리 슬라이스에서 반영)
 *   personaReflect  페르소나를 반영한 변주인지 — 준수율 계측이 읽는 표기
 *   contextReflect  단기 맥락을 반영한 변주인지
 *   fail            생성 실패 재현 후보. **기본 세트에는 두지 않습니다** — 서버 오류는
 *                   정상 플레이에서 저절로 나는 사건이 아니라 테스트가 일으키는 조건입니다.
 *                   사람은 T1 스위치로, 자동화는 __VN__.failNext()로 일으킵니다
 *   choices         고정 선택지와 가중치 (+2/+1/-1) — 없는 턴은 자유 입력만
 *   endTurn         경로 종점. 도달하면 엔딩 최종 판정(system-spec §4-2)
 */

/* 대사 풀 — [문장, 호감도 델타, 페르소나 반영, 맥락 반영] */

/* 전용 세트 — 3일간의 행복(c7). 사흘을 세 구간으로 나눠 100턴을 조립합니다.
 * 1~33턴 첫날 · 34~66턴 둘째 날 · 67~100턴 마지막 날. 3턴마다 고정 선택지가 붙습니다. */
const MOCK_C7_SC1 = {
  characterId: "c7", scenarioId: "sc1", label: "해수욕장 앞",
  turns: [
    { turn: 1, candidates: [
      { text: "파도 소리가 크죠, {nickname}. 그래서 여기 앉아 있었어요.", deltaAffection: 1, personaReflect: true, contextReflect: false },
      { text: "{nickname}, 모래 밟는 소리 좋아해요? 저는 이 소리 들으려고 와요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 2, candidates: [
      { text: "바다는 오래 봐도 안 질리네요. {userName}은 어때요?", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "울고 있었냐고요, {userName}? …그냥 바람이 좀 셌어요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 3, candidates: [
      { text: "여기 노을은 삼십 분쯤 뒤가 제일 좋아요. 기다려 볼래요, {nickname}?", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘 처음 봤는데 오래 앉아 있게 되네요.", deltaAffection: 1, personaReflect: false, contextReflect: true }
    ], choices: [{ label: "노을 기다려 볼게요", delta: 2 }, { label: "조금만 있다 갈게요", delta: 1 }, { label: "저는 이만 가 볼게요", delta: -1 }] },
    { turn: 4, candidates: [
      { text: "{userName}, 발 시리지 않아요? 물이 생각보다 차요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{nickname}, 이 근처에 아이스크림 파는 데가 있어요. 걸어서 오 분.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 5, candidates: [
      { text: "사실 오늘은 아무하고도 말 안 하려고 했어요. {userName} 앞에서는 왜 이럴까요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이랑 있으면 시간이 빨리 가요. 그게 좀 아깝네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 6, candidates: [
      { text: "괜찮으세요? 여기 혼자 앉아 있길래…", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}이라고 했죠. 이름을 두 번 물어봐서 미안해요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "아이스크림 좋아요", delta: 2 }, { label: "물이나 마실래요", delta: 1 }, { label: "됐어요", delta: -1 }] },
    { turn: 7, candidates: [
      { text: "파도 소리가 크죠, {nickname}. 그래서 여기 앉아 있었어요.", deltaAffection: 1, memoryAdd: "7턴에 나눈 이야기", personaReflect: true, contextReflect: false },
      { text: "{nickname}, 모래 밟는 소리 좋아해요? 저는 이 소리 들으려고 와요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 8, candidates: [
      { text: "바다는 오래 봐도 안 질리네요. {userName}은 어때요?", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "울고 있었냐고요, {userName}? …그냥 바람이 좀 셌어요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 9, candidates: [
      { text: "여기 노을은 삼십 분쯤 뒤가 제일 좋아요. 기다려 볼래요, {nickname}?", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘 처음 봤는데 오래 앉아 있게 되네요.", deltaAffection: 1, personaReflect: false, contextReflect: true }
    ], choices: [{ label: "괜찮냐고 물어봐 준 게 고마워요", delta: 2 }, { label: "그냥 지나가던 길이었어요", delta: 1 }, { label: "신경 쓰지 마세요", delta: -1 }] },
    { turn: 10, candidates: [
      { text: "{userName}, 발 시리지 않아요? 물이 생각보다 차요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{nickname}, 이 근처에 아이스크림 파는 데가 있어요. 걸어서 오 분.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 11, candidates: [
      { text: "사실 오늘은 아무하고도 말 안 하려고 했어요. {userName} 앞에서는 왜 이럴까요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이랑 있으면 시간이 빨리 가요. 그게 좀 아깝네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 12, candidates: [
      { text: "괜찮으세요? 여기 혼자 앉아 있길래…", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}이라고 했죠. 이름을 두 번 물어봐서 미안해요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "노을 기다려 볼게요", delta: 2 }, { label: "조금만 있다 갈게요", delta: 1 }, { label: "저는 이만 가 볼게요", delta: -1 }] },
    { turn: 13, candidates: [
      { text: "파도 소리가 크죠, {nickname}. 그래서 여기 앉아 있었어요.", deltaAffection: 1, personaReflect: true, contextReflect: false },
      { text: "{nickname}, 모래 밟는 소리 좋아해요? 저는 이 소리 들으려고 와요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 14, candidates: [
      { text: "바다는 오래 봐도 안 질리네요. {userName}은 어때요?", deltaAffection: 1, memoryAdd: "14턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "울고 있었냐고요, {userName}? …그냥 바람이 좀 셌어요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 15, candidates: [
      { text: "여기 노을은 삼십 분쯤 뒤가 제일 좋아요. 기다려 볼래요, {nickname}?", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘 처음 봤는데 오래 앉아 있게 되네요.", deltaAffection: 1, personaReflect: false, contextReflect: true }
    ], choices: [{ label: "아이스크림 좋아요", delta: 2 }, { label: "물이나 마실래요", delta: 1 }, { label: "됐어요", delta: -1 }] },
    { turn: 16, candidates: [
      { text: "{userName}, 발 시리지 않아요? 물이 생각보다 차요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{nickname}, 이 근처에 아이스크림 파는 데가 있어요. 걸어서 오 분.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 17, candidates: [
      { text: "사실 오늘은 아무하고도 말 안 하려고 했어요. {userName} 앞에서는 왜 이럴까요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이랑 있으면 시간이 빨리 가요. 그게 좀 아깝네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 18, candidates: [
      { text: "괜찮으세요? 여기 혼자 앉아 있길래…", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}이라고 했죠. 이름을 두 번 물어봐서 미안해요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "괜찮냐고 물어봐 준 게 고마워요", delta: 2 }, { label: "그냥 지나가던 길이었어요", delta: 1 }, { label: "신경 쓰지 마세요", delta: -1 }] },
    { turn: 19, candidates: [
      { text: "파도 소리가 크죠, {nickname}. 그래서 여기 앉아 있었어요.", deltaAffection: 1, personaReflect: true, contextReflect: false },
      { text: "{nickname}, 모래 밟는 소리 좋아해요? 저는 이 소리 들으려고 와요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 20, candidates: [
      { text: "바다는 오래 봐도 안 질리네요. {userName}은 어때요?", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "울고 있었냐고요, {userName}? …그냥 바람이 좀 셌어요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 21, candidates: [
      { text: "여기 노을은 삼십 분쯤 뒤가 제일 좋아요. 기다려 볼래요, {nickname}?", deltaAffection: 2, memoryAdd: "21턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "오늘 처음 봤는데 오래 앉아 있게 되네요.", deltaAffection: 1, personaReflect: false, contextReflect: true }
    ], choices: [{ label: "노을 기다려 볼게요", delta: 2 }, { label: "조금만 있다 갈게요", delta: 1 }, { label: "저는 이만 가 볼게요", delta: -1 }] },
    { turn: 22, candidates: [
      { text: "{userName}, 발 시리지 않아요? 물이 생각보다 차요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{nickname}, 이 근처에 아이스크림 파는 데가 있어요. 걸어서 오 분.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 23, candidates: [
      { text: "사실 오늘은 아무하고도 말 안 하려고 했어요. {userName} 앞에서는 왜 이럴까요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이랑 있으면 시간이 빨리 가요. 그게 좀 아깝네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 24, candidates: [
      { text: "괜찮으세요? 여기 혼자 앉아 있길래…", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}이라고 했죠. 이름을 두 번 물어봐서 미안해요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "아이스크림 좋아요", delta: 2 }, { label: "물이나 마실래요", delta: 1 }, { label: "됐어요", delta: -1 }] },
    { turn: 25, candidates: [
      { text: "파도 소리가 크죠, {nickname}. 그래서 여기 앉아 있었어요.", deltaAffection: 1, personaReflect: true, contextReflect: false },
      { text: "{nickname}, 모래 밟는 소리 좋아해요? 저는 이 소리 들으려고 와요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 26, candidates: [
      { text: "바다는 오래 봐도 안 질리네요. {userName}은 어때요?", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "울고 있었냐고요, {userName}? …그냥 바람이 좀 셌어요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 27, candidates: [
      { text: "여기 노을은 삼십 분쯤 뒤가 제일 좋아요. 기다려 볼래요, {nickname}?", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘 처음 봤는데 오래 앉아 있게 되네요.", deltaAffection: 1, personaReflect: false, contextReflect: true }
    ], choices: [{ label: "괜찮냐고 물어봐 준 게 고마워요", delta: 2 }, { label: "그냥 지나가던 길이었어요", delta: 1 }, { label: "신경 쓰지 마세요", delta: -1 }] },
    { turn: 28, candidates: [
      { text: "{userName}, 발 시리지 않아요? 물이 생각보다 차요.", deltaAffection: 1, memoryAdd: "28턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "{nickname}, 이 근처에 아이스크림 파는 데가 있어요. 걸어서 오 분.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 29, candidates: [
      { text: "사실 오늘은 아무하고도 말 안 하려고 했어요. {userName} 앞에서는 왜 이럴까요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이랑 있으면 시간이 빨리 가요. 그게 좀 아깝네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 30, candidates: [
      { text: "괜찮으세요? 여기 혼자 앉아 있길래…", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}이라고 했죠. 이름을 두 번 물어봐서 미안해요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "노을 기다려 볼게요", delta: 2 }, { label: "조금만 있다 갈게요", delta: 1 }, { label: "저는 이만 가 볼게요", delta: -1 }] },
    { turn: 31, candidates: [
      { text: "파도 소리가 크죠, {nickname}. 그래서 여기 앉아 있었어요.", deltaAffection: 1, personaReflect: true, contextReflect: false },
      { text: "{nickname}, 모래 밟는 소리 좋아해요? 저는 이 소리 들으려고 와요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 32, candidates: [
      { text: "바다는 오래 봐도 안 질리네요. {userName}은 어때요?", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "울고 있었냐고요, {userName}? …그냥 바람이 좀 셌어요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 33, candidates: [
      { text: "여기 노을은 삼십 분쯤 뒤가 제일 좋아요. 기다려 볼래요, {nickname}?", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘 처음 봤는데 오래 앉아 있게 되네요.", deltaAffection: 1, personaReflect: false, contextReflect: true }
    ], choices: [{ label: "아이스크림 좋아요", delta: 2 }, { label: "물이나 마실래요", delta: 1 }, { label: "됐어요", delta: -1 }] },
    { turn: 34, candidates: [
      { text: "어제보다 말이 많아졌죠, {userName}. 스스로도 놀랐어요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}은 왜 여기 왔어요? 물어본 적이 없네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 35, candidates: [
      { text: "오늘 밤은 별이 보일 것 같아요. 구름이 얇아요.", deltaAffection: 1, memoryAdd: "35턴에 나눈 이야기", personaReflect: false, contextReflect: false },
      { text: "…고마워요, {nickname}. 이유는 묻지 말아 줘요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 36, candidates: [
      { text: "어제 그 자리에 또 왔네요, {userName}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘은 파라솔을 빌렸어요, {nickname}. 그늘이 있어야 오래 앉죠.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "오늘도 보러 왔어요", delta: 2 }, { label: "지나가다 들렀어요", delta: 1 }, { label: "우연이에요", delta: -1 }] },
    { turn: 37, candidates: [
      { text: "{nickname}, 어제 아이스크림 뭐 골랐는지 기억해요? 저는 기억해요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "바다는 어제랑 같은데 {userName}과 보니 다르게 보이네요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 38, candidates: [
      { text: "병원에서는 오래 걷지 말라고 했어요. …오늘은 좀 걸었네요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "{userName}, 사진 한 장만 찍어 줄래요? 잘 나오게 말고 그냥.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 39, candidates: [
      { text: "모래성은 무너지라고 쌓는 거래요, {nickname}. 그 말이 요즘 좋아요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "이따 배 지나가는 거 볼래요? 일곱 시쯤 지나가요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "사진 찍어 줄게요", delta: 2 }, { label: "잘 못 찍는데요", delta: 1 }, { label: "사진은 좀…", delta: -1 }] },
    { turn: 40, candidates: [
      { text: "어제보다 말이 많아졌죠, {userName}. 스스로도 놀랐어요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}은 왜 여기 왔어요? 물어본 적이 없네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 41, candidates: [
      { text: "오늘 밤은 별이 보일 것 같아요. 구름이 얇아요.", deltaAffection: 1, personaReflect: false, contextReflect: false },
      { text: "…고마워요, {nickname}. 이유는 묻지 말아 줘요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 42, candidates: [
      { text: "어제 그 자리에 또 왔네요, {userName}.", deltaAffection: 2, memoryAdd: "42턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "오늘은 파라솔을 빌렸어요, {nickname}. 그늘이 있어야 오래 앉죠.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "바다가 좋아서요", delta: 2 }, { label: "쉬러 왔어요", delta: 1 }, { label: "딱히 이유는 없어요", delta: -1 }] },
    { turn: 43, candidates: [
      { text: "{nickname}, 어제 아이스크림 뭐 골랐는지 기억해요? 저는 기억해요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "바다는 어제랑 같은데 {userName}과 보니 다르게 보이네요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 44, candidates: [
      { text: "병원에서는 오래 걷지 말라고 했어요. …오늘은 좀 걸었네요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "{userName}, 사진 한 장만 찍어 줄래요? 잘 나오게 말고 그냥.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 45, candidates: [
      { text: "모래성은 무너지라고 쌓는 거래요, {nickname}. 그 말이 요즘 좋아요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "이따 배 지나가는 거 볼래요? 일곱 시쯤 지나가요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "오늘도 보러 왔어요", delta: 2 }, { label: "지나가다 들렀어요", delta: 1 }, { label: "우연이에요", delta: -1 }] },
    { turn: 46, candidates: [
      { text: "어제보다 말이 많아졌죠, {userName}. 스스로도 놀랐어요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}은 왜 여기 왔어요? 물어본 적이 없네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 47, candidates: [
      { text: "오늘 밤은 별이 보일 것 같아요. 구름이 얇아요.", deltaAffection: 1, personaReflect: false, contextReflect: false },
      { text: "…고마워요, {nickname}. 이유는 묻지 말아 줘요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 48, candidates: [
      { text: "어제 그 자리에 또 왔네요, {userName}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘은 파라솔을 빌렸어요, {nickname}. 그늘이 있어야 오래 앉죠.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "사진 찍어 줄게요", delta: 2 }, { label: "잘 못 찍는데요", delta: 1 }, { label: "사진은 좀…", delta: -1 }] },
    { turn: 49, candidates: [
      { text: "{nickname}, 어제 아이스크림 뭐 골랐는지 기억해요? 저는 기억해요.", deltaAffection: 2, memoryAdd: "49턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "바다는 어제랑 같은데 {userName}과 보니 다르게 보이네요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 50, candidates: [
      { text: "병원에서는 오래 걷지 말라고 했어요. …오늘은 좀 걸었네요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "{userName}, 사진 한 장만 찍어 줄래요? 잘 나오게 말고 그냥.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 51, candidates: [
      { text: "모래성은 무너지라고 쌓는 거래요, {nickname}. 그 말이 요즘 좋아요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "이따 배 지나가는 거 볼래요? 일곱 시쯤 지나가요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "바다가 좋아서요", delta: 2 }, { label: "쉬러 왔어요", delta: 1 }, { label: "딱히 이유는 없어요", delta: -1 }] },
    { turn: 52, candidates: [
      { text: "어제보다 말이 많아졌죠, {userName}. 스스로도 놀랐어요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}은 왜 여기 왔어요? 물어본 적이 없네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 53, candidates: [
      { text: "오늘 밤은 별이 보일 것 같아요. 구름이 얇아요.", deltaAffection: 1, personaReflect: false, contextReflect: false },
      { text: "…고마워요, {nickname}. 이유는 묻지 말아 줘요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 54, candidates: [
      { text: "어제 그 자리에 또 왔네요, {userName}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘은 파라솔을 빌렸어요, {nickname}. 그늘이 있어야 오래 앉죠.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "오늘도 보러 왔어요", delta: 2 }, { label: "지나가다 들렀어요", delta: 1 }, { label: "우연이에요", delta: -1 }] },
    { turn: 55, candidates: [
      { text: "{nickname}, 어제 아이스크림 뭐 골랐는지 기억해요? 저는 기억해요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "바다는 어제랑 같은데 {userName}과 보니 다르게 보이네요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 56, candidates: [
      { text: "병원에서는 오래 걷지 말라고 했어요. …오늘은 좀 걸었네요.", deltaAffection: 2, memoryAdd: "56턴에 나눈 이야기", personaReflect: false, contextReflect: true },
      { text: "{userName}, 사진 한 장만 찍어 줄래요? 잘 나오게 말고 그냥.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 57, candidates: [
      { text: "모래성은 무너지라고 쌓는 거래요, {nickname}. 그 말이 요즘 좋아요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "이따 배 지나가는 거 볼래요? 일곱 시쯤 지나가요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "사진 찍어 줄게요", delta: 2 }, { label: "잘 못 찍는데요", delta: 1 }, { label: "사진은 좀…", delta: -1 }] },
    { turn: 58, candidates: [
      { text: "어제보다 말이 많아졌죠, {userName}. 스스로도 놀랐어요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}은 왜 여기 왔어요? 물어본 적이 없네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 59, candidates: [
      { text: "오늘 밤은 별이 보일 것 같아요. 구름이 얇아요.", deltaAffection: 1, personaReflect: false, contextReflect: false },
      { text: "…고마워요, {nickname}. 이유는 묻지 말아 줘요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 60, candidates: [
      { text: "어제 그 자리에 또 왔네요, {userName}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘은 파라솔을 빌렸어요, {nickname}. 그늘이 있어야 오래 앉죠.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "바다가 좋아서요", delta: 2 }, { label: "쉬러 왔어요", delta: 1 }, { label: "딱히 이유는 없어요", delta: -1 }] },
    { turn: 61, candidates: [
      { text: "{nickname}, 어제 아이스크림 뭐 골랐는지 기억해요? 저는 기억해요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "바다는 어제랑 같은데 {userName}과 보니 다르게 보이네요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 62, candidates: [
      { text: "병원에서는 오래 걷지 말라고 했어요. …오늘은 좀 걸었네요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "{userName}, 사진 한 장만 찍어 줄래요? 잘 나오게 말고 그냥.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 63, candidates: [
      { text: "모래성은 무너지라고 쌓는 거래요, {nickname}. 그 말이 요즘 좋아요.", deltaAffection: 1, memoryAdd: "63턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "이따 배 지나가는 거 볼래요? 일곱 시쯤 지나가요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "오늘도 보러 왔어요", delta: 2 }, { label: "지나가다 들렀어요", delta: 1 }, { label: "우연이에요", delta: -1 }] },
    { turn: 64, candidates: [
      { text: "어제보다 말이 많아졌죠, {userName}. 스스로도 놀랐어요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}은 왜 여기 왔어요? 물어본 적이 없네요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 65, candidates: [
      { text: "오늘 밤은 별이 보일 것 같아요. 구름이 얇아요.", deltaAffection: 1, personaReflect: false, contextReflect: false },
      { text: "…고마워요, {nickname}. 이유는 묻지 말아 줘요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 66, candidates: [
      { text: "어제 그 자리에 또 왔네요, {userName}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘은 파라솔을 빌렸어요, {nickname}. 그늘이 있어야 오래 앉죠.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "사진 찍어 줄게요", delta: 2 }, { label: "잘 못 찍는데요", delta: 1 }, { label: "사진은 좀…", delta: -1 }] },
    { turn: 67, candidates: [
      { text: "{nickname}, 어제 그 배 또 지나갈까요? 같이 기다려 봐요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "짐은 어제 다 쌌어요, {userName}. 가벼워요, 생각보다.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 68, candidates: [
      { text: "이 사흘이 제일 길었으면 했는데 제일 빨리 갔어요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "{userName}, 나중에 여기 다시 오면 이 자리에 앉아 줄래요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 69, candidates: [
      { text: "울지 마요, {nickname}. 저 아직 여기 있어요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이 불러 주는 이름이 좋았어요. 그 말은 해 두고 싶었어요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "손 잡아 줄게요", delta: 2 }, { label: "…네", delta: 1 }, { label: "그건 좀 부담스러워요", delta: -1 }] },
    { turn: 70, candidates: [
      { text: "노을이 어제보다 붉네요, {userName}. 마지막이라 그런가.", deltaAffection: 1, memoryAdd: "70턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "{userName}, 손 한 번만 잡아 봐도 돼요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 71, candidates: [
      { text: "사흘 동안 웃은 게 올해 웃은 것보다 많아요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "…이제 가 볼게요. 안녕이라고는 안 할래요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 72, candidates: [
      { text: "마지막 날이라고 하면 이상하겠죠, {userName}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘은 아침부터 바다가 잔잔하네요, {nickname}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "같이 기다릴게요", delta: 2 }, { label: "잠깐이면 좋아요", delta: 1 }, { label: "오늘은 일찍 가야 해요", delta: -1 }] },
    { turn: 73, candidates: [
      { text: "{nickname}, 어제 그 배 또 지나갈까요? 같이 기다려 봐요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "짐은 어제 다 쌌어요, {userName}. 가벼워요, 생각보다.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 74, candidates: [
      { text: "이 사흘이 제일 길었으면 했는데 제일 빨리 갔어요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "{userName}, 나중에 여기 다시 오면 이 자리에 앉아 줄래요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 75, candidates: [
      { text: "울지 마요, {nickname}. 저 아직 여기 있어요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이 불러 주는 이름이 좋았어요. 그 말은 해 두고 싶었어요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "다시 와서 여기 앉을게요", delta: 2 }, { label: "올 수 있으면 올게요", delta: 1 }, { label: "약속은 못 해요", delta: -1 }] },
    { turn: 76, candidates: [
      { text: "노을이 어제보다 붉네요, {userName}. 마지막이라 그런가.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}, 손 한 번만 잡아 봐도 돼요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 77, candidates: [
      { text: "사흘 동안 웃은 게 올해 웃은 것보다 많아요.", deltaAffection: 2, memoryAdd: "77턴에 나눈 이야기", personaReflect: false, contextReflect: true },
      { text: "…이제 가 볼게요. 안녕이라고는 안 할래요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 78, candidates: [
      { text: "마지막 날이라고 하면 이상하겠죠, {userName}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘은 아침부터 바다가 잔잔하네요, {nickname}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "손 잡아 줄게요", delta: 2 }, { label: "…네", delta: 1 }, { label: "그건 좀 부담스러워요", delta: -1 }] },
    { turn: 79, candidates: [
      { text: "{nickname}, 어제 그 배 또 지나갈까요? 같이 기다려 봐요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "짐은 어제 다 쌌어요, {userName}. 가벼워요, 생각보다.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 80, candidates: [
      { text: "이 사흘이 제일 길었으면 했는데 제일 빨리 갔어요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "{userName}, 나중에 여기 다시 오면 이 자리에 앉아 줄래요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 81, candidates: [
      { text: "울지 마요, {nickname}. 저 아직 여기 있어요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이 불러 주는 이름이 좋았어요. 그 말은 해 두고 싶었어요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "같이 기다릴게요", delta: 2 }, { label: "잠깐이면 좋아요", delta: 1 }, { label: "오늘은 일찍 가야 해요", delta: -1 }] },
    { turn: 82, candidates: [
      { text: "노을이 어제보다 붉네요, {userName}. 마지막이라 그런가.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}, 손 한 번만 잡아 봐도 돼요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 83, candidates: [
      { text: "사흘 동안 웃은 게 올해 웃은 것보다 많아요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "…이제 가 볼게요. 안녕이라고는 안 할래요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 84, candidates: [
      { text: "마지막 날이라고 하면 이상하겠죠, {userName}.", deltaAffection: 2, memoryAdd: "84턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "오늘은 아침부터 바다가 잔잔하네요, {nickname}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "다시 와서 여기 앉을게요", delta: 2 }, { label: "올 수 있으면 올게요", delta: 1 }, { label: "약속은 못 해요", delta: -1 }] },
    { turn: 85, candidates: [
      { text: "{nickname}, 어제 그 배 또 지나갈까요? 같이 기다려 봐요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "짐은 어제 다 쌌어요, {userName}. 가벼워요, 생각보다.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 86, candidates: [
      { text: "이 사흘이 제일 길었으면 했는데 제일 빨리 갔어요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "{userName}, 나중에 여기 다시 오면 이 자리에 앉아 줄래요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 87, candidates: [
      { text: "울지 마요, {nickname}. 저 아직 여기 있어요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이 불러 주는 이름이 좋았어요. 그 말은 해 두고 싶었어요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "손 잡아 줄게요", delta: 2 }, { label: "…네", delta: 1 }, { label: "그건 좀 부담스러워요", delta: -1 }] },
    { turn: 88, candidates: [
      { text: "노을이 어제보다 붉네요, {userName}. 마지막이라 그런가.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}, 손 한 번만 잡아 봐도 돼요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 89, candidates: [
      { text: "사흘 동안 웃은 게 올해 웃은 것보다 많아요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "…이제 가 볼게요. 안녕이라고는 안 할래요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 90, candidates: [
      { text: "마지막 날이라고 하면 이상하겠죠, {userName}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘은 아침부터 바다가 잔잔하네요, {nickname}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "같이 기다릴게요", delta: 2 }, { label: "잠깐이면 좋아요", delta: 1 }, { label: "오늘은 일찍 가야 해요", delta: -1 }] },
    { turn: 91, candidates: [
      { text: "{nickname}, 어제 그 배 또 지나갈까요? 같이 기다려 봐요.", deltaAffection: 2, memoryAdd: "91턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "짐은 어제 다 쌌어요, {userName}. 가벼워요, 생각보다.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 92, candidates: [
      { text: "이 사흘이 제일 길었으면 했는데 제일 빨리 갔어요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "{userName}, 나중에 여기 다시 오면 이 자리에 앉아 줄래요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 93, candidates: [
      { text: "울지 마요, {nickname}. 저 아직 여기 있어요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이 불러 주는 이름이 좋았어요. 그 말은 해 두고 싶었어요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "다시 와서 여기 앉을게요", delta: 2 }, { label: "올 수 있으면 올게요", delta: 1 }, { label: "약속은 못 해요", delta: -1 }] },
    { turn: 94, candidates: [
      { text: "노을이 어제보다 붉네요, {userName}. 마지막이라 그런가.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}, 손 한 번만 잡아 봐도 돼요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 95, candidates: [
      { text: "사흘 동안 웃은 게 올해 웃은 것보다 많아요.", deltaAffection: 2, personaReflect: false, contextReflect: true },
      { text: "…이제 가 볼게요. 안녕이라고는 안 할래요, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 96, candidates: [
      { text: "마지막 날이라고 하면 이상하겠죠, {userName}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "오늘은 아침부터 바다가 잔잔하네요, {nickname}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "손 잡아 줄게요", delta: 2 }, { label: "…네", delta: 1 }, { label: "그건 좀 부담스러워요", delta: -1 }] },
    { turn: 97, candidates: [
      { text: "{nickname}, 어제 그 배 또 지나갈까요? 같이 기다려 봐요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "짐은 어제 다 쌌어요, {userName}. 가벼워요, 생각보다.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 98, candidates: [
      { text: "이 사흘이 제일 길었으면 했는데 제일 빨리 갔어요.", deltaAffection: 2, memoryAdd: "98턴에 나눈 이야기", personaReflect: false, contextReflect: true },
      { text: "{userName}, 나중에 여기 다시 오면 이 자리에 앉아 줄래요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 99, candidates: [
      { text: "울지 마요, {nickname}. 저 아직 여기 있어요.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "{nickname}이 불러 주는 이름이 좋았어요. 그 말은 해 두고 싶었어요.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "같이 기다릴게요", delta: 2 }, { label: "잠깐이면 좋아요", delta: 1 }, { label: "오늘은 일찍 가야 해요", delta: -1 }] },
    { turn: 100, candidates: [
      { text: "노을이 어제보다 붉네요, {userName}. 마지막이라 그런가.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}, 손 한 번만 잡아 봐도 돼요?", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] }
  ],
  // 엔딩 검사 시점이 10턴 이후 5턴마다라(system-spec §4-2) 경로가 짧으면 검사가 오지 않습니다.
  // 100턴이면 검사 시점을 열아홉 번 지나고 호감도 누적으로 굿 엔딩에도 자연 도달합니다
  endTurn: 100
};

/* 공통 세트 — 전용 세트가 없는 캐릭터가 씁니다. 30턴이라 맥락 창(10턴)과
 * 검사 시점(10·15·20·25·30)을 함께 지납니다. */
const MOCK_COMMON = {
  characterId: "*", scenarioId: "*", label: "공통",
  turns: [
    { turn: 1, candidates: [
      { text: "{nickname}이라고 불러도 됩니까. 그 편이 부르기 좋아서요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}이라는 이름은 알고 있었습니다. 소문이 빠른 곳이라.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 2, candidates: [
      { text: "조금 걸을까요. 서서 하는 이야기는 길어지지 않으니까.", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}은 늘 이런 식으로 대답하는군요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 3, candidates: [
      { text: "…방금 그 말, 기억해 두겠습니다 {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "여기까지 온 이유가 있을 텐데요, {nickname}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "사실 할 말이 있었어", delta: 2 }, { label: "그냥 온 거야", delta: 1 }, { label: "이유 같은 건 없어", delta: -1 }] },
    { turn: 4, candidates: [
      { text: "묻지 않겠습니다. 말하고 싶어지면 말하겠지요.", deltaAffection: 1, personaReflect: false, contextReflect: false },
      { text: "{userName}. 그 표정은 처음 봅니다.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 5, candidates: [
      { text: "바람이 찹니다, {nickname}. 안쪽으로 들어가죠.", deltaAffection: 1, personaReflect: true, contextReflect: false },
      { text: "오늘 들은 이야기는 여기 두고 가겠습니다, {userName}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 6, candidates: [
      { text: "다음에도 같은 자리에 있겠습니다, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "조심히 가세요, {userName}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "조금 더 있을게", delta: 2 }, { label: "이만 가 볼게", delta: 1 }, { label: "그만하자", delta: -1 }] },
    { turn: 7, candidates: [
      { text: "{charName}입니다. {userName}, 여기서 만날 줄은 몰랐네요.", deltaAffection: 1, memoryAdd: "7턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "왔군요, {nickname}. 오래 기다린 건 아닙니다.", deltaAffection: 1, personaReflect: true, contextReflect: false }
    ] },
    { turn: 8, candidates: [
      { text: "{nickname}이라고 불러도 됩니까. 그 편이 부르기 좋아서요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}이라는 이름은 알고 있었습니다. 소문이 빠른 곳이라.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 9, candidates: [
      { text: "조금 걸을까요. 서서 하는 이야기는 길어지지 않으니까.", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}은 늘 이런 식으로 대답하는군요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "반가워", delta: 2 }, { label: "그냥 지나가던 길이야", delta: 1 }, { label: "말 걸지 마", delta: -1 }] },
    { turn: 10, candidates: [
      { text: "…방금 그 말, 기억해 두겠습니다 {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "여기까지 온 이유가 있을 텐데요, {nickname}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 11, candidates: [
      { text: "묻지 않겠습니다. 말하고 싶어지면 말하겠지요.", deltaAffection: 1, personaReflect: false, contextReflect: false },
      { text: "{userName}. 그 표정은 처음 봅니다.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 12, candidates: [
      { text: "바람이 찹니다, {nickname}. 안쪽으로 들어가죠.", deltaAffection: 1, personaReflect: true, contextReflect: false },
      { text: "오늘 들은 이야기는 여기 두고 가겠습니다, {userName}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "사실 할 말이 있었어", delta: 2 }, { label: "그냥 온 거야", delta: 1 }, { label: "이유 같은 건 없어", delta: -1 }] },
    { turn: 13, candidates: [
      { text: "다음에도 같은 자리에 있겠습니다, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "조심히 가세요, {userName}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 14, candidates: [
      { text: "{charName}입니다. {userName}, 여기서 만날 줄은 몰랐네요.", deltaAffection: 1, memoryAdd: "14턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "왔군요, {nickname}. 오래 기다린 건 아닙니다.", deltaAffection: 1, personaReflect: true, contextReflect: false }
    ] },
    { turn: 15, candidates: [
      { text: "{nickname}이라고 불러도 됩니까. 그 편이 부르기 좋아서요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}이라는 이름은 알고 있었습니다. 소문이 빠른 곳이라.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "조금 더 있을게", delta: 2 }, { label: "이만 가 볼게", delta: 1 }, { label: "그만하자", delta: -1 }] },
    { turn: 16, candidates: [
      { text: "조금 걸을까요. 서서 하는 이야기는 길어지지 않으니까.", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}은 늘 이런 식으로 대답하는군요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 17, candidates: [
      { text: "…방금 그 말, 기억해 두겠습니다 {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "여기까지 온 이유가 있을 텐데요, {nickname}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 18, candidates: [
      { text: "묻지 않겠습니다. 말하고 싶어지면 말하겠지요.", deltaAffection: 1, personaReflect: false, contextReflect: false },
      { text: "{userName}. 그 표정은 처음 봅니다.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "반가워", delta: 2 }, { label: "그냥 지나가던 길이야", delta: 1 }, { label: "말 걸지 마", delta: -1 }] },
    { turn: 19, candidates: [
      { text: "바람이 찹니다, {nickname}. 안쪽으로 들어가죠.", deltaAffection: 1, personaReflect: true, contextReflect: false },
      { text: "오늘 들은 이야기는 여기 두고 가겠습니다, {userName}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 20, candidates: [
      { text: "다음에도 같은 자리에 있겠습니다, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "조심히 가세요, {userName}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 21, candidates: [
      { text: "{charName}입니다. {userName}, 여기서 만날 줄은 몰랐네요.", deltaAffection: 1, memoryAdd: "21턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "왔군요, {nickname}. 오래 기다린 건 아닙니다.", deltaAffection: 1, personaReflect: true, contextReflect: false }
    ], choices: [{ label: "사실 할 말이 있었어", delta: 2 }, { label: "그냥 온 거야", delta: 1 }, { label: "이유 같은 건 없어", delta: -1 }] },
    { turn: 22, candidates: [
      { text: "{nickname}이라고 불러도 됩니까. 그 편이 부르기 좋아서요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}이라는 이름은 알고 있었습니다. 소문이 빠른 곳이라.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 23, candidates: [
      { text: "조금 걸을까요. 서서 하는 이야기는 길어지지 않으니까.", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}은 늘 이런 식으로 대답하는군요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 24, candidates: [
      { text: "…방금 그 말, 기억해 두겠습니다 {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "여기까지 온 이유가 있을 텐데요, {nickname}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "조금 더 있을게", delta: 2 }, { label: "이만 가 볼게", delta: 1 }, { label: "그만하자", delta: -1 }] },
    { turn: 25, candidates: [
      { text: "묻지 않겠습니다. 말하고 싶어지면 말하겠지요.", deltaAffection: 1, personaReflect: false, contextReflect: false },
      { text: "{userName}. 그 표정은 처음 봅니다.", deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 26, candidates: [
      { text: "바람이 찹니다, {nickname}. 안쪽으로 들어가죠.", deltaAffection: 1, personaReflect: true, contextReflect: false },
      { text: "오늘 들은 이야기는 여기 두고 가겠습니다, {userName}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 27, candidates: [
      { text: "다음에도 같은 자리에 있겠습니다, {nickname}.", deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "조심히 가세요, {userName}.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "반가워", delta: 2 }, { label: "그냥 지나가던 길이야", delta: 1 }, { label: "말 걸지 마", delta: -1 }] },
    { turn: 28, candidates: [
      { text: "{charName}입니다. {userName}, 여기서 만날 줄은 몰랐네요.", deltaAffection: 1, memoryAdd: "28턴에 나눈 이야기", personaReflect: true, contextReflect: true },
      { text: "왔군요, {nickname}. 오래 기다린 건 아닙니다.", deltaAffection: 1, personaReflect: true, contextReflect: false }
    ] },
    { turn: 29, candidates: [
      { text: "{nickname}이라고 불러도 됩니까. 그 편이 부르기 좋아서요.", deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{userName}이라는 이름은 알고 있었습니다. 소문이 빠른 곳이라.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 30, candidates: [
      { text: "조금 걸을까요. 서서 하는 이야기는 길어지지 않으니까.", deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}은 늘 이런 식으로 대답하는군요.", deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [{ label: "사실 할 말이 있었어", delta: 2 }, { label: "그냥 온 거야", delta: 1 }, { label: "이유 같은 건 없어", delta: -1 }] }
  ],
  endTurn: 30
};

const MOCK_SETS = {
  "c7:sc1": MOCK_C7_SC1
};

/* 전용 세트가 없으면 공통 세트 — 시트에 새로 만든 캐릭터도 대화가 성립해야 합니다 */
function mockSetFor(charId, scenarioId) {
  return MOCK_SETS[charId + ":" + scenarioId] || MOCK_COMMON;
}

function hasDedicatedMock(charId) {
  return Object.keys(MOCK_SETS).some((k) => k.split(":")[0] === charId);
}

/* 변주 분포를 세트별로 셉니다 — 계측 TC가 전제(80%)를 코드에서 확인할 수 있게 하는 통로입니다 */
function mockVariationStats(set) {
  const cands = set.turns.reduce((a, t) => a.concat(t.candidates), [])
    .filter((c) => !c.fail);
  const persona = cands.filter((c) => c.personaReflect).length;
  const context = cands.filter((c) => c.contextReflect).length;
  return {
    total: cands.length,
    personaRate: Math.round((persona / cands.length) * 100),
    contextRate: Math.round((context / cands.length) * 100)
  };
}
