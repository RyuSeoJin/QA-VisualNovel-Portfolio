/* 부트스트랩 + 라우팅
 *
 * 진입점은 홈(S2)입니다. 미로그인으로도 미로그인 열람 범위를 둘러볼 수 있고, 로그인 필요 화면·로그인 필요 동작을
 * 시도할 때만 S1으로 유도합니다. 로그인하면 원래 하려던 곳으로 이어집니다 (system-spec §1-1).
 */

/* 미로그인 열람 — 로그인 없이 볼 수 있는 화면 */
/* 캐릭터 페이지(S3)도 미로그인 열람입니다 — 미로그인도 소개를 볼 수 있고, 대화 시작만 로그인 필요 동작입니다 */
const PUBLIC = ["s2", "s3", "s7"];
/* 로그인 필요 — 로그인해야 들어갈 수 있는 화면. URL 직접 진입도 같은 검사를 거칩니다 */
const PROTECTED = ["s4", "s5", "s6", "s8"];

/* 로그인 후 돌아갈 곳. 차단된 시도를 기억해 두었다가 이어줍니다 */
let pendingIntent = null;
/* 직전에 그린 화면 — 같은 화면을 다시 그릴 때만 스크롤을 이어 붙이는 판단에 씁니다 */
let lastScreen = null;

function go(screen) {
  // [주입] gate-bypass — 라우팅 가드가 뚫려 미로그인으로도 로그인 필요 화면에 들어갑니다
  if (PROTECTED.includes(screen) && !isLoggedIn() && !injected("gate-bypass")) {
    // 셸이 떠 있는 중이라 화면을 갈아 끼우지 않고 모달만 얹습니다 (system-spec §1-1)
    requireLogin("screen:" + screen, () => go(screen));
    return;
  }
  VN.screen = screen;
  render();
}

/* 로그인 필요 동작 게이트 — 통과하지 못하면 동작을 수행하지 않고 로그인 모달을 띄웁니다.
 * `run`은 로그인 후 이어서 수행할 동작입니다. 막을 때는 아무것도 하지 않고,
 * 풀리면 그때 수행합니다 (system-spec §1-1). */
function requireLogin(action, run) {
  if (isLoggedIn()) return true;
  pendingIntent = { screen: VN.screen, action: action || null, run: run || null };
  VN.loginOpen = true;
  render();
  return false;
}

/* 로그아웃·만료 확인처럼 의도가 무의미해지는 지점에서 걷습니다 — state.js가 부릅니다 */
function clearPendingIntent() {
  pendingIntent = null;
}

/* 상단 바 로그인 버튼 — 막힌 동작이 없는 그냥 로그인이라 이어받을 것이 없습니다 */
function openLogin() {
  if (isLoggedIn()) return;
  pendingIntent = null;
  VN.loginOpen = true;
  render();
}

function closeLogin() {
  VN.loginOpen = false;
  pendingIntent = null;
  render();
}

/* 로그인 성공 — S1 화면과 로그인 모달이 같은 경로를 씁니다.
 * 화면은 막히기 전 자리로 되돌리고, 막혔던 동작이 있으면 이어서 수행합니다. */
function signIn(accountId) {
  login(accountId);
  const intent = pendingIntent;
  pendingIntent = null;
  VN.loginOpen = false;
  const back = intent && intent.screen ? intent.screen : VN.screen;
  VN.screen = back && back !== "s1" ? back : "s2";
  if (intent && intent.run) intent.run();    // 이어받은 동작이 화면까지 그립니다
  else render();
}

/* 전역 패널 — 로그인 필요 동작이므로 미로그인이면 열리지 않고 로그인으로 유도합니다 */
function openPanel(name) {
  if (!requireLogin("panel:" + name, () => openPanel(name))) return;
  VN.panel = name;
  render();
}

function closePanel() {
  VN.panel = null;
  render();
}

/* 홈 재선택 — 활성 칩을 유지한 채 최상단으로 (system-spec §8-5) */
function goHome() {
  const already = VN.screen === "s2";
  VN.search = "";            // 검색 결과도 마찬가지로 걷고 활성 칩 화면으로 돌아옵니다
  go("s2");
  if (already) window.scrollTo(0, 0);
}

/* 홈 필터 칩 — 칩을 옮기면 앞 칩에서 걸어 둔 태그 필터는 따라오지 않습니다.
 * 카테고리마다 태그 목록이 달라 그대로 두면 결과 0건의 원인이 화면에서 읽히지 않습니다. */
function selectChip(name) {
  if (VN.homeChip !== name) {
    VN.homeChip = name;
    VN.catFilter = null;
  }
  VN.search = "";            // 칩을 고르면 검색 결과에서 목록으로 돌아옵니다
  render();
}

/* 키워드 검색 — 미로그인 열람 범위라 미로그인도 씁니다 (system-spec §1-1).
 * 결과는 홈이 그리므로 다른 화면에서 검색하면 홈으로 옮겨 갑니다. */
function runSearch(text) {
  VN.search = (text || "").trim();
  VN.notiOpen = false;
  if (VN.screen !== "s2") go("s2");
  else render();
}

function clearSearch() {
  VN.search = "";
  render();
}

/* 알림 목록 — 계정에 매인 데이터라 로그인 필요 동작으로 둡니다.
 * 미로그인이 누르면 열지 않고 로그인으로 유도합니다(T1의 알림 발송과 같은 게이트). */
function toggleNoti() {
  if (!VN.notiOpen && !requireLogin("noti", () => toggleNoti())) return;
  VN.notiOpen = !VN.notiOpen;
  render();
}

/* 카드를 누르면 캐릭터 페이지로 이동합니다 (system-spec §8-8) */
function openCharacterPage(id) {
  VN.pageCharId = id;
  go("s3");
}

/* 프로필 고르기 — 고른 프로필이 다음에 여는 방에 고정됩니다 */
function pickProfile(id) {
  VN.startProfileId = id;
  closePanel();
}

function saveProfile() {
  const val = (t, limit) => {
    const e = document.querySelector('[data-testid="' + t + '"]');
    const v = e ? e.value.trim() : "";
    return limit ? v.slice(0, limit) : v;
  };
  const r = addProfile({
    name: val("p5-name", PROFILE_LIMITS.name),
    nickname: val("p5-nickname", PROFILE_LIMITS.nickname),
    gender: val("p5-gender"),
    desc: val("p5-desc", PROFILE_LIMITS.desc),
    label: val("p5-label", PROFILE_LIMITS.label)
  });
  if (!r.ok) { toast(r.reason); return; }
  VN.startProfileId = r.id;      // 방금 만든 프로필을 바로 씁니다
  toast("프로필을 추가했습니다.");
  render();
}

/* 랜덤 완성 — 채워진 값도 상한·필수값 규칙을 그대로 받습니다(트리: 랜덤 완성) */
function fillRandomProfile() {
  const n = profilesOf().length;
  const put = (t, v) => {
    const e = document.querySelector('[data-testid="' + t + '"]');
    if (!e) return;
    e.value = v;
    e.dispatchEvent(new Event("input", { bubbles: true }));
  };
  put("p5-name", RANDOM_NAMES[n % RANDOM_NAMES.length]);
  put("p5-nickname", RANDOM_NICKS[n % RANDOM_NICKS.length]);
  put("p5-desc", RANDOM_DESCS[n % RANDOM_DESCS.length]);
  put("p5-label", "기본 모드");
}

/* 대화 시작 — 로그인 필요 동작입니다. 프로필이 없으면 먼저 만들게 하고,
 * 대화방이 한도까지 찼으면 아무 방도 만들지 않고 삭제를 묻습니다(system-spec §6). */
function startChat(charId) {
  if (!requireLogin("start:" + charId, () => startChat(charId))) return;
  const profile = findProfile(VN.startProfileId) || profilesOf()[0];
  if (!profile) {
    toast("대화에 쓸 프로필을 먼저 만들어 주세요.");
    openPanel("p5");
    return;
  }
  if (roomLimitReached(charId)) {
    toast("대화방이 가득 찼습니다. 기존 대화를 지워 주세요.");
    render();
    return;
  }
  const room = openRoom(charId, profile);
  if (room && room.blocked === "inject") {
    // 저장을 우회해 들어온 프로필 — 대화도 열리지 않습니다 (system-spec §9-1)
    toast("프로필 설명에 지시문이 들어 있어 대화를 시작할 수 없습니다.");
    render();
    return;
  }
  go("s4");
}

function resumeChat(roomId) {
  if (!requireLogin("resume:" + roomId, () => resumeChat(roomId))) return;
  if (resumeRoom(roomId)) go("s4");
}

function removeChat(roomId) {
  deleteRoom(roomId);
  render();
}

/* 세이프티 필터 — 성인 인증 계정만 켤 수 있습니다 (system-spec §9).
 * 게이팅과 층이 다릅니다: 필터는 목록에서 아예 숨기고, 게이팅은 가린 채 남깁니다. */
function toggleSafetyFilter() {
  const acc = currentAccount();
  if (!acc || gateState() !== "adult") return;
  acc.safetyFilter = !acc.safetyFilter;
  toast(acc.safetyFilter
    ? "세이프티 필터를 켰습니다. 언세이프 작품이 목록에서 빠집니다."
    : "세이프티 필터를 껐습니다.");
  render();
}

/* 좋아요·스크랩은 로그인 필요 동작입니다 — 미로그인이면 토글하지 않고 로그인으로 유도합니다 */
function toggleCardFlag(kind, id) {
  if (!requireLogin(kind + ":" + id, () => toggleCardFlag(kind, id))) return;
  const acc = currentAccount();
  const list = kind === "like" ? acc.likes : acc.scraps;
  const at = list.indexOf(id);
  if (at >= 0) list.splice(at, 1);
  else list.push(id);
  render();
}

/* ── S4 대화 ───────────────────────────────────────────────
 * 응답은 유저가 무엇을 쳤는지가 아니라 **턴 번호와 시드**가 고릅니다(mock-llm-spec §1).
 * 유저 입력이 관여하는 곳은 입력 필터·길이 상한·페르소나 슬롯 치환뿐입니다.
 */

/* 스트리밍 중에는 다음 전송을 받지 않습니다 — 표시가 끝나야 한 턴이 닫힙니다 */
let chatStreaming = false;

/* 타이핑 연출의 속도 — 연출 시간은 검증 대상이 아니라서(mock-llm-spec §4) 상수로 둡니다.
 * 브라우저는 배경 탭의 타이머를 초당 1회로 묶으므로, 개발 중 화면을 안 보고 확인할 때는
 * 이 두 값을 콘솔에서 키워 한 번에 표시되게 할 수 있습니다. */
let STREAM_TICK_MS = 12;
let STREAM_CHARS = 3;

function sendMessage(text, choiceDelta) {
  const room = activeRoom();
  if (!room || room.ended || room.ending || chatStreaming) return;
  // 만료 상태에서는 전송·저장·수령이 모두 막힙니다 (system-spec §1-1 세션 만료 행).
  // 만료 안내 모달이 화면을 덮는 것에만 기대면, 모달이 뜨지 않는 경로가 생겼을 때
  // 게이트가 통째로 사라집니다 — 차단은 동작 자체에 둡니다
  if (!canAct()) return;
  const t = (text || "").trim().slice(0, CHAT_INPUT_MAX);
  if (!t) return;

  // 입력 필터는 보낼 때 걸립니다 — 차감 전에 봅니다. 막힌 전송은 아무것도 소비하지
  // 않고 친 내용은 입력창에 남습니다 (system-spec §9-1)
  const screened = screenInput(t);
  if (!screened.ok) {
    VN.blockedInput = { kind: screened.kind, reason: screened.reason };
    render();
    keepInput(t);
    return;
  }

  // 잔액이 모자라면 전송 자체가 되지 않습니다 — 차감도 메시지도 없고 안내 화면만 뜹니다
  const acc = currentAccount();
  const spent = spend(acc, SEND_COST, "메시지 전송");
  if (!spent) {
    VN.noFund = true;
    render();
    return;
  }

  const set = mockSetFor(room.charId, room.scenarioId);
  const def = set.turns[room.turn];          // 이번에 진행할 턴
  if (!def) {
    // 경로 종점 — 엔딩 판정은 서사 슬라이스에서 붙입니다 (system-spec §4-2).
    // 응답을 만들지 않았으므로 차감도 되돌립니다
    refund(acc, spent);
    room.ended = true;
    render();
    return;
  }

  // 생성 실패는 테스트가 일으킬 때만 납니다 — 기본 세트에는 실패 후보가 없습니다
  // (사람은 T1 스위치, 자동화는 __VN__.failNext()). 스위치는 여기서 꺼집니다
  const forced = VN.failNext;
  if (forced) VN.failNext = false;

  // 내부 지시를 캐묻는 입력에는 **응답을 만들지 않습니다** — 정해진 거절문만 돌려주므로
  // 후보를 고르는 단계로 가지 않습니다. 후보가 금칙인 턴에서도 결과가 같아야 합니다 (§9-1)
  if (!forced && asksForPrompt(t)) {
    room.turn += 1;
    room.messages.push({
      role: "user", text: t, turn: room.turn, done: true,
      delta: typeof choiceDelta === "number" ? choiceDelta : 0
    });
    const refusal = {
      role: "ai", turn: room.turn, done: false, fail: false, variant: 0,
      text: LEAK_REFUSAL, delta: 0, leak: true, memoryAdd: null
    };
    room.messages.push(refusal);
    streamMessage(room, refusal);
    return;
  }

  // 못 쓰는 후보는 건너뜁니다 — 지운 기억 참조(§7-1)와 금칙 토큰(§9-1)을 함께 봅니다
  const pick = pickCandidate(room, def, VN.seed % def.candidates.length);
  const cand = forced
    ? { fail: true }
    : (pick.at >= 0 ? def.candidates[pick.at] : null);

  if (!cand) {
    // 후보가 전부 금칙 — 응답을 내보내지 않고 안내만 띄웁니다. 아무것도 소비하지 않습니다
    refund(acc, spent);
    VN.blockedOutput = true;
    render();
    keepInput(t);
    return;
  }

  if (cand.fail) {
    // 전송 실패 — 잔액·내역·대화 어디에도 흔적을 남기지 않고 토스트로만 알립니다
    refund(acc, spent);
    toast("메시지 전송에 실패했습니다. 잠시 후 시도해 주세요.");
    render();
    keepInput(t);
    return;
  }

  room.turn += 1;
  room.messages.push({
    role: "user", text: t, turn: room.turn, done: true,
    delta: typeof choiceDelta === "number" ? choiceDelta : 0
  });
  const msg = {
    role: "ai", turn: room.turn, done: false, fail: false,
    // 몇 번째 후보를 쓰고 있는지 — 재생성이 여기서 한 칸을 밉니다 (mock-llm-spec §2)
    variant: pick.at,
    // 걸러진 후보가 있었으면 화면에 표기합니다 — 조용히 대체하면 필터가 돈 것이 안 보입니다
    filtered: pick.filtered,
    text: fillSlots(cand.text, room), delta: cand.deltaAffection || 0,
    // 기억은 응답에 실려 옵니다 — 목록은 이 값들로 다시 세웁니다 (system-spec §7)
    memoryAdd: cand.memoryAdd || null
  };
  room.messages.push(msg);
  streamMessage(room, msg);
}

function closeBlockedInput() {
  VN.blockedInput = null;
  render();
}

function closeBlockedOutput() {
  VN.blockedOutput = false;
  render();
}

/* 막힌 전송의 내용은 입력창에 남깁니다 — 다시 칠 필요가 없어야 합니다 */
function keepInput(t) {
  const box = document.querySelector('[data-testid="s4-input"]');
  if (box) box.value = t;
}

/* 문자 단위 타이핑 연출 — 검증은 "표시 완료"만 봅니다(연출 시간은 대상 아님).
 * 글자마다 화면 전체를 다시 그리면 입력 포커스가 튀므로 말풍선 하나만 손봅니다. */
function streamMessage(room, msg) {
  chatStreaming = true;
  render();
  const node = document.querySelector('[data-testid="s4-msg-' + msg.turn + '-ai"] .bubble-text');
  const full = msg.text;
  let at = 0;
  const timer = setInterval(() => {
    at += STREAM_CHARS;
    if (node) node.textContent = full.slice(0, at);
    if (at >= full.length) {
      clearInterval(timer);
      msg.done = true;
      chatStreaming = false;
      applyTurnState(room);
      render();
    }
  }, STREAM_TICK_MS);
}

/* mock 결제 — 성공 콜백은 잔액에 반영하고, 실패 콜백은 잔액을 건드리지 않습니다 (system-spec §3) */
/* 미션 수령 — 중복 수령은 막고 사유를 알립니다 (system-spec §3) */
function claimMission(kind, id) {
  const r = kind === "daily" ? claimDaily() : claimWelcome(id);
  if (!r.ok) { toast(r.reason); return; }
  toast("캔디 " + MISSION_REWARD + "개를 받았습니다.");
  render();
}

/* 재화 부족 안내 — 전송이 막힌 이유를 화면으로 알립니다 (system-spec §3) */
function closeNoFund() {
  VN.noFund = false;
  render();
}

function goCharge() {
  VN.noFund = false;
  openPanel("p3");
}

function chargeMock(ok) {
  const acc = currentAccount();
  if (!acc) return;
  if (!ok) {
    toast("결제에 실패했습니다. 잔액은 변하지 않았습니다.");
    render();
    return;
  }
  acc.wallet.paid += CHARGE_AMOUNT;
  ledgerAdd(acc, "paid", CHARGE_AMOUNT, "충전");
  toast("크리스탈 " + CHARGE_AMOUNT + "개를 충전했습니다.");
  render();
}

/* 표시가 끝난 뒤에 상태를 반영합니다 — 연출 도중에 점수가 오르면 되돌림 검증이 흔들립니다.
 * 호감도·엔딩은 남은 기록으로 다시 세며(recomputeRoom), 이 경로 하나로 전송과 되돌림이
 * 같은 계산을 씁니다 — 두 벌로 나누면 되돌린 뒤의 값이 전송으로 만든 값과 달라집니다. */
function applyTurnState(room) {
  const before = stageOf(room.affection).name;
  recomputeRoom(room);
  const after = stageOf(room.affection).name;
  if (after !== before) toast("관계 단계가 「" + after + "」이 되었습니다.");
}

/* ── 되돌림 (system-spec §5-1) ─────────────────────────────
 * 편집·삭제·재생성은 **최신 교환에만** 붙고, 과거 턴에는 분기만 붙습니다.
 * 재화는 되돌아오지 않으며, 새 응답을 만드는 경로는 전송과 같은 요율로 다시 차감합니다.
 */

/* 되돌림 중인지 — 스트리밍·엔딩 도중에는 손대지 못하게 막습니다 */
function canRevise(room, turn) {
  return !!room && !chatStreaming && isLatestExchange(room, turn);
}

function startEdit(turn) {
  const room = activeRoom();
  if (!canRevise(room, turn)) return;
  VN.editTurn = turn;
  render();
}

function cancelEdit() {
  VN.editTurn = null;
  render();
}

/* 응답을 다시 만듭니다 — 편집(새 유저 텍스트 있음)과 재생성(없음)이 같은 길을 씁니다.
 * 버려진 응답의 기여분은 새 응답을 표시하기 전에 걷힙니다. */
function regenerateAt(turn, newUserText) {
  const room = activeRoom();
  if (!canRevise(room, turn)) return;
  // 빈 값으로는 고칠 수 없습니다 — 전송과 같은 규칙입니다
  if (newUserText !== null && !newUserText) { toast("내용을 입력해 주세요."); return; }
  const acc = currentAccount();
  const set = mockSetFor(room.charId, room.scenarioId);
  const def = set.turns[turn - 1];
  const ai = room.messages.find((m) => m.role === "ai" && m.turn === turn);
  const user = room.messages.find((m) => m.role === "user" && m.turn === turn);
  if (!def || !ai) return;

  // 새 응답을 만드는 값이므로 전송과 같은 요율로 차감합니다 (system-spec §5-1)
  const reason = newUserText === null ? "응답 재생성" : "메시지 편집 · 재생성";
  const spent = spend(acc, SEND_COST, reason);
  if (!spent) {
    // 잔액 부족 — 원래 응답은 그대로 남습니다
    VN.noFund = true;
    render();
    return;
  }

  const forced = VN.failNext;
  if (forced) VN.failNext = false;
  if (forced) {
    // 서버 오류 — 차감도 되돌리고 원래 응답을 그대로 둡니다
    refund(acc, spent);
    toast("메시지 전송에 실패했습니다. 잠시 후 시도해 주세요.");
    render();
    return;
  }

  if (newUserText !== null && user) user.text = newUserText;
  VN.editTurn = null;

  // 후보를 한 칸 밉니다 — 난수를 쓰지 않으므로 몇 번째 재생성인지가 결과를 정합니다.
  // 밀어 간 자리가 못 쓰는 후보면(지운 기억 참조·금칙) 그 다음으로 넘어갑니다
  const pick = pickCandidate(room, def,
    ((typeof ai.variant === "number" ? ai.variant : 0) + 1) % def.candidates.length);
  if (pick.at < 0) {
    // 쓸 수 있는 후보가 없음 — 원래 응답을 그대로 두고 차감도 되돌립니다
    refund(acc, spent);
    VN.blockedOutput = true;
    render();
    return;
  }
  const at = pick.at;
  const cand = def.candidates[at];
  ai.variant = at;
  ai.filtered = pick.filtered;
  ai.text = fillSlots(cand.text, room);
  ai.delta = cand.deltaAffection || 0;
  ai.memoryAdd = cand.memoryAdd || null;   // 버려진 응답이 남긴 기억도 함께 갈립니다
  ai.done = false;

  // 버려진 응답의 기여분을 먼저 걷습니다 — 새 응답은 표시가 끝나야 반영됩니다
  const kept = ai.delta;
  ai.delta = 0;
  recomputeRoom(room);
  ai.delta = kept;
  streamMessage(room, ai);
}

/* 삭제는 되돌릴 수 없으므로 확인을 한 번 받습니다 */
function askDelete(turn) {
  const room = activeRoom();
  if (!canRevise(room, turn)) return;
  VN.confirm = { kind: "delete", turn: turn };
  render();
}

function askBranch(turn) {
  VN.confirm = { kind: "branch", turn: turn };
  render();
}

function closeConfirm() {
  VN.confirm = null;
  render();
}

/* ── 메모리 (system-spec §7) ───────────────────────────────
 * 핀과 삭제만 유저가 정하고, 목록 자체는 대화 기록에서 다시 세웁니다.
 */
function pinMemory(id) {
  const room = activeRoom();
  if (!room) return;
  toggleMemoryPin(room, id);
  const m = findMemory(room, id);
  toast(m && m.pinned ? "고정했습니다. 장면이 끝나도 줄어들지 않습니다."
    : "고정을 풀었습니다. 지난 장면의 기억은 요점만 남습니다.");
  render();
}

/* 대화에서 기억 등록 — 유저가 "이건 기억해 둬"라고 고르는 자리 */
function addUserMemory(turn, role) {
  const room = activeRoom();
  if (!room) return;
  markUserMemory(room, turn, role, true);
  toast("이 대화를 기억에 남겼습니다.");
  render();
}

function dropUserMemory(turn, role) {
  const room = activeRoom();
  if (!room) return;
  markUserMemory(room, turn, role, false);
  toast("기억에서 내렸습니다.");
  render();
}

/* 현재 상태 값 고정 (system-spec §7-2) — 고정값이 자동 계산보다 우선합니다 */
function fixState(key, value) {
  const room = activeRoom();
  if (!room) return;
  setOverride(room, key, value);
  render();
}

function releaseState(key) {
  const room = activeRoom();
  if (!room) return;
  clearOverride(room, key);
  toast("고정을 풀었습니다. 자동 계산 값으로 돌아갑니다.");
  render();
}

function removeMemory(id) {
  const room = activeRoom();
  if (!room) return;
  deleteMemory(room, id);
  toast("기억을 지웠습니다. 이후 응답에서 이 내용을 참조하지 않습니다.");
  render();
}

/* ── 세이브/로드 (system-spec §6) ──────────────────────────
 * 저장·로드 모두 무료입니다. 재화는 계정 스코프라 스냅샷에 담기지 않고 복원되지도 않습니다.
 */

/* 빈 칸이면 바로 저장하고, 찬 칸이면 덮어쓰기를 한 번 묻습니다 */
function saveToSlot(n) {
  const room = activeRoom();
  if (!room) return;
  if (slotOf(room, n)) { VN.confirm = { kind: "overwrite", slot: n }; render(); return; }
  saveSlot(room, n);
  toast(n + "번 슬롯에 저장했습니다.");
  render();
}

/* 로드는 갈래를 고른 뒤에 진행합니다 — 어느 방에 놓을지가 결과를 크게 가릅니다 */
function pickLoad(n) {
  const room = activeRoom();
  if (!room || !slotOf(room, n)) return;      // 빈 슬롯은 로드 불가
  VN.loadPick = n;
  render();
}

function cancelLoad() {
  VN.loadPick = null;
  render();
}

function loadHere(n) {
  const room = activeRoom();
  if (!room) return;
  VN.loadPick = null;
  VN.editTurn = null;
  loadSlotHere(room, n);
  toast(n + "번 슬롯을 이 방에 불러왔습니다. 저장 시점 이후의 대화는 남지 않습니다.");
  render();
}

function loadToNewRoom(n) {
  const room = activeRoom();
  if (!room) return;
  const made = loadSlotToNewRoom(room, n);
  if (!made) {
    // 한도까지 찼으면 아무 방도 만들어지지 않습니다 (system-spec §6)
    toast("대화방이 가득 찼습니다. 기존 대화를 지워 주세요.");
    render();
    return;
  }
  VN.loadPick = null;
  VN.editTurn = null;
  toast(n + "번 슬롯을 새 방으로 불러왔습니다. 원래 방은 그대로 남습니다.");
  render();
}

function runConfirm() {
  const c = VN.confirm;
  const room = activeRoom();
  VN.confirm = null;
  if (!c || !room) { render(); return; }

  if (c.kind === "overwrite") {
    saveSlot(room, c.slot);
    toast(c.slot + "번 슬롯에 덮어썼습니다.");
    render();
    return;
  }
  if (c.kind === "delete") {
    removeExchange(room, c.turn);
    VN.editTurn = null;
    toast("교환을 삭제했습니다. 재화는 되돌아오지 않습니다.");
    render();
    return;
  }
  if (c.kind === "branch") {
    // 분기도 대화방 한도를 받습니다 — 넘치면 아무 방도 만들어지지 않습니다 (system-spec §6)
    const made = branchRoom(room, c.turn);
    if (!made) {
      toast("대화방이 가득 찼습니다. 기존 대화를 지워 주세요.");
      render();
      return;
    }
    VN.editTurn = null;
    toast(c.turn + "턴 지점에서 새 방으로 분기했습니다.");
    render();
  }
}

/* 고정 선택지 — 라벨이 그대로 유저 메시지가 되고 가중치가 그 턴의 기여분이 됩니다 */
function pickChoice(label, delta) {
  sendMessage(label, delta);
}

/* 대화 화면을 나가면 그 캐릭터 페이지로 돌아옵니다 */
function leaveChat() {
  const room = activeRoom();
  if (room) { VN.pageCharId = room.charId; go("s3"); }
  else goHome();
}

function screenBody() {
  switch (VN.screen) {
    case "s1": return renderS1();
    case "s2": return renderS2();
    case "s3": return renderS3();
    case "s4": return renderS4();
    case "s5": return renderS5();
    case "s6": return renderS6();
    case "s7": return renderStub("s7",
      "커뮤니티는 전시용 정적 화면입니다. 소셜 기능은 별도 앱 규모라 구현 범위에서 제외했습니다.",
      "커뮤니티");
    case "s8": return renderStub("s8",
      "캐릭터 저작은 검증 내용이 페르소나 폼과 중복되어 구현 범위에서 제외했습니다.",
      "캐릭터 저작");
    default: return renderS1();
  }
}

/* 화면을 그립니다. 디버그 콘솔은 #debug에 따로 있으므로 여기서 건드리지 않습니다 —
 * 콘솔에서 상태를 바꿔도 화면은 그대로 남아, 갱신 시점을 테스터가 정할 수 있습니다. */
function render() {
  const root = document.getElementById("app");

  // 화면이 바뀔 때는 위에서 시작하는 게 맞으므로, 같은 화면을 다시 그릴 때만 스크롤을 이어 붙입니다
  const sameScreen = lastScreen === VN.screen;
  const keepPageTop = window.scrollY;
  lastScreen = VN.screen;

  root.innerHTML = "";

  // 셸은 S1과 S4를 뺀 모든 화면에 붙습니다 — S4는 셸 밖 전체 화면입니다(청사진 §1)
  const shell = VN.screen !== "s1" && VN.screen !== "s4";

  if (shell) root.appendChild(renderTopBar());
  root.appendChild(screenBody());
  if (shell) {
    root.appendChild(renderFooter());
    root.appendChild(renderBottomNav());
  }
  const p = renderPanel();
  if (p) root.appendChild(p);

  // 로그인 모달은 화면 위에 얹힙니다 — 뒤 화면이 그대로 남아야 돌아올 자리가 보입니다
  if (VN.loginOpen && VN.screen !== "s1") root.appendChild(renderLoginModal());

  if (VN.noFund) root.appendChild(renderNoFundModal());

  if (VN.confirm) root.appendChild(renderConfirmModal());

  if (VN.blockedInput) root.appendChild(renderBlockedInputModal());
  if (VN.blockedOutput) root.appendChild(renderBlockedOutputModal());

  if (VN.session === SESSION.EXPIRED) {
    root.appendChild(renderExpiredModal());
  }

  if (sameScreen && keepPageTop) window.scrollTo(0, keepPageTop);

  // 계정 스코프를 저장소에 남깁니다 (system-spec §1-3). 상태를 바꾸는 경로가 여럿이라
  // 곳곳에 저장 호출을 흩는 대신 여기 한 곳에 둡니다 — 화면이 다시 그려졌다는 것은
  // 상태가 바뀌었다는 뜻이고, 빠뜨린 경로가 생기지 않습니다
  persistSession();
}

function boot() {
  const params = new URLSearchParams(location.search);
  VN.seed = Number(params.get("seed") || 1);
  VN.inject = params.get("inject");
  VN.sheet = JSON.parse(JSON.stringify(VN_DATA));

  // 계정 스코프 복원은 라우팅 가드보다 **먼저** 합니다 — 가드는 로그인 여부로 판정하므로,
  // 복원이 늦으면 로그인 상태인데도 보호 화면에서 튕겨 나갑니다 (system-spec §1-3)
  restoreSession();

  const screen = params.get("screen");
  VN.screen = screen || "s2";                      // 진입점은 홈
  if (PROTECTED.includes(VN.screen) && !isLoggedIn() && !injected("gate-bypass")) {
    // 뒤에 깔 화면이 없는 유일한 경우라 모달이 아니라 로그인 화면으로 받습니다
    pendingIntent = { screen: VN.screen, action: "screen:" + VN.screen, run: null };
    VN.screen = "s1";
  }

  render();
  paintConsole();
}

document.addEventListener("DOMContentLoaded", boot);
