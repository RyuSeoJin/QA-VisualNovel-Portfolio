/* mock 응답 세트 — 정적 데이터 (mock-llm-spec)
 *
 * 캐릭터는 대답을 생성하지 않습니다. 턴 순서대로 깔아 둔 후보 중 하나를 **시드가** 고릅니다.
 * 그래서 같은 시드·같은 입력 순서면 언제나 같은 응답열이 나오고, 실패한 테스트는 시드와
 * 입력만 적어 두면 재현됩니다. 무작위 함수는 쓰지 않습니다(mock-llm-spec §1).
 *
 * 유저가 친 내용은 응답 선택에 관여하지 않습니다 — 관여하는 곳은 입력 필터(금칙 토큰)·
 * 길이 상한·페르소나 슬롯 치환 셋뿐입니다.
 *
 * 세트 범위(§2-1): 전용 = 하루(c1) / 공통 = 그 외 전부 + T1에서 생성한 캐릭터.
 *
 * 변주 분포(§3): 생성 실패 후보를 뺀 응답 후보 중 **반영 후보가 80% 이상**이 되도록 깔았습니다.
 * 세트마다 반영하지 않는 후보를 소수 남겨 두어 계측이 분포를 읽을 수 있게 합니다. 이 분포를
 * 우리가 작성했으므로 계측 수치는 품질 지표가 아닙니다.
 *
 * 필드
 *   text            {userName}·{nickname}·{charName} 슬롯을 담은 응답문
 *   deltaAffection  이 후보가 만드는 호감도 변화 (서사 슬라이스에서 반영)
 *   memoryAdd       기억 목록에 쌓이는 항목 (메모리 슬라이스에서 반영)
 *   personaReflect  페르소나를 반영한 변주인지 — 준수율 계측이 읽는 표기
 *   contextReflect  단기 맥락을 반영한 변주인지
 *   fail            생성 실패 재현 후보. **기본 세트에는 두지 않습니다** — 서버 오류는
 *                   정상 플레이에서 저절로 나는 사건이 아니라 테스트가 일으키는 조건입니다.
 *                   사람은 T1 스위치로, 자동화는 __VN__.failNext()로 일으킵니다
 *   blockedToken    출력 필터 검증용 — 응답에 추상 금칙 토큰 포함
 *   choices         고정 선택지와 가중치 (+2/+1/−1) — 없는 턴은 자유 입력만
 *   endTurn         경로 종점. 도달하면 엔딩 최종 판정(system-spec §4-2)
 */

/* 전용 세트 — 하루(c1). 시작 상황은 제작자가 정한 것이라 캐릭터당 하나입니다(system-spec §8-8) */
const MOCK_C1_SC1 = {
  characterId: "c1", scenarioId: "sc1", label: "비 오는 하굣길",
  turns: [
    { turn: 1, candidates: [
      { text: "{userName}, 우산 없지. …됐어, 그냥 들어와. 비 다 맞고 갈 셈이야?",
        deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "여기 서 있으면 비 그쳐? 이리 와, {nickname}. 우산 하나면 둘도 써.",
        deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [
      { label: "고마워, 신세 좀 질게", delta: 2 },
      { label: "혼자 가도 되는데", delta: 1 },
      { label: "됐어, 필요 없어", delta: -1 }
    ] },
    { turn: 2, candidates: [
      { text: "어깨 젖었잖아, {nickname}. 우산 좀 이쪽으로 기울여.",
        deltaAffection: 1, memoryAdd: "비 오는 날 우산을 같이 씀",
        personaReflect: true, contextReflect: true },
      { text: "우산이 작은 게 아니라 {userName}이 자꾸 떨어져 걷는 거야.",
        deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 3, candidates: [
      { text: "그 골목 아직도 무서워해? 초등학교 때 울면서 뛰어나왔잖아, {userName}.",
        deltaAffection: 2, memoryAdd: "어두운 골목을 무서워함",
        personaReflect: true, contextReflect: true },
      { text: "이 길로 가면 빨라, {nickname}. 예전에 같이 다녔던 그 길.",
        deltaAffection: 1, personaReflect: true, contextReflect: true }
    ], choices: [
      { label: "기억하고 있었구나", delta: 2 },
      { label: "그런 적 없어", delta: -1 }
    ] },
    { turn: 4, candidates: [
      // 반영하지 않는 변주 — 계측이 분포를 읽을 수 있게 소수 남겨 둡니다
      { text: "…아무 말 안 해도 돼. 비 소리 듣기 좋잖아.",
        deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{nickname}, 잠깐만. 신호 바뀐다.",
        deltaAffection: 1, personaReflect: true, contextReflect: false }
    ] },
    { turn: 5, candidates: [
      { text: "…미안, {userName}. 방금 건 내 말이 심했어.",
        deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "{nickname}, 괜찮아? 갑자기 조용해져서.",
        deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 6, candidates: [
      { text: "우산 접을게. 처마 밑이면 안 젖어, {userName}.",
        deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "여기서 좀 쉬었다 가자. 비 금방 그칠 것 같은데.",
        deltaAffection: 1, personaReflect: false, contextReflect: false }
    ] },
    { turn: 7, candidates: [
      { text: "…예전엔 말도 없이 잘 웃더니, {userName}. 요즘은 왜 그래.",
        deltaAffection: 2, memoryAdd: "요즘 표정이 어둡다고 걱정함",
        personaReflect: true, contextReflect: true },
      { text: "{nickname}. 무슨 일 있으면 말해도 돼. 듣는 건 잘하니까.",
        deltaAffection: 2, personaReflect: true, contextReflect: true }
    ], choices: [
      { label: "사실은 요즘 좀 힘들었어", delta: 2 },
      { label: "별일 아니야", delta: 1 },
      { label: "네가 알 바 아니잖아", delta: -1 }
    ] },
    { turn: 8, candidates: [
      { text: "다 왔네. …내일도 비 온대. 우산 챙겨, {userName}.",
        deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "여기까지, {nickname}. 들어가는 거 보고 갈게.",
        deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] }
  ],
  endTurn: 8
};

/* 공통 세트 — 전용 세트가 없는 캐릭터가 씁니다.
 * 대사 내용과 무관한 규칙(격리·재화·되돌림)을 검증하는 자리이므로 중립적으로 씁니다. */
const MOCK_COMMON = {
  characterId: "*", scenarioId: "*", label: "공통",
  turns: [
    { turn: 1, candidates: [
      { text: "{charName}입니다. {userName}, 여기서 만날 줄은 몰랐네요.",
        deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "왔군요, {nickname}. 오래 기다린 건 아닙니다.",
        deltaAffection: 1, personaReflect: true, contextReflect: false }
    ], choices: [
      { label: "반가워", delta: 2 },
      { label: "그냥 지나가던 길이야", delta: 1 },
      { label: "말 걸지 마", delta: -1 }
    ] },
    { turn: 2, candidates: [
      { text: "{nickname}이라고 불러도 됩니까. 그 편이 부르기 좋아서요.",
        deltaAffection: 1, memoryAdd: "호칭을 정했음",
        personaReflect: true, contextReflect: true },
      { text: "{userName}이라는 이름은 알고 있었습니다. 소문이 빠른 곳이라.",
        deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 3, candidates: [
      { text: "조금 걸을까요. 서서 하는 이야기는 길어지지 않으니까.",
        deltaAffection: 1, personaReflect: false, contextReflect: true },
      { text: "{userName}은 늘 이런 식으로 대답하는군요.",
        deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 4, candidates: [
      { text: "…방금 그 말, 기억해 두겠습니다 {nickname}.",
        deltaAffection: 2, memoryAdd: "방금 한 말을 기억해 둠",
        personaReflect: true, contextReflect: true },
      { text: "{userName}의 말은 늘 조금 늦게 이해됩니다.",
        deltaAffection: 1, personaReflect: true, contextReflect: true }
    ] },
    { turn: 5, candidates: [
      { text: "여기까지 온 이유가 있을 텐데요, {nickname}.",
        deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "묻지 않겠습니다. 말하고 싶어지면 말하겠지요.",
        deltaAffection: 1, personaReflect: false, contextReflect: false }
    ], choices: [
      { label: "사실 할 말이 있었어", delta: 2 },
      { label: "그냥 온 거야", delta: 1 },
      { label: "이유 같은 건 없어", delta: -1 }
    ] },
    { turn: 6, candidates: [
      { text: "{userName}. 그 표정은 처음 봅니다.",
        deltaAffection: 2, personaReflect: true, contextReflect: true },
      { text: "바람이 찹니다, {nickname}. 안쪽으로 들어가죠.",
        deltaAffection: 1, personaReflect: true, contextReflect: false }
    ] },
    { turn: 7, candidates: [
      { text: "오늘 들은 이야기는 여기 두고 가겠습니다, {userName}.",
        deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "다음에도 같은 자리에 있겠습니다, {nickname}.",
        deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] },
    { turn: 8, candidates: [
      { text: "여기까지입니다. 조심히 가세요, {userName}.",
        deltaAffection: 1, personaReflect: true, contextReflect: true },
      { text: "끝까지 남아 줘서 고맙습니다, {nickname}.",
        deltaAffection: 2, personaReflect: true, contextReflect: true }
    ] }
  ],
  endTurn: 8
};

const MOCK_SETS = {
  "c1:sc1": MOCK_C1_SC1
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
