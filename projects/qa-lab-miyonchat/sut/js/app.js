/* 부트스트랩 + 라우팅
 *
 * 진입점은 홈(S2)입니다. 미로그인으로도 공개 범위를 둘러볼 수 있고, 보호 화면·보호 동작을
 * 시도할 때만 S1으로 유도합니다. 로그인하면 원래 하려던 곳으로 이어집니다 (system-spec §1-1).
 */

/* 공개 — 미로그인도 볼 수 있는 화면 */
const PUBLIC = ["s2", "s7"];
/* 보호 — 로그인해야 들어갈 수 있는 화면. URL 직접 진입도 같은 검사를 거칩니다 */
const PROTECTED = ["s3", "s4", "s5", "s6", "s8"];

/* 로그인 후 돌아갈 곳. 차단된 시도를 기억해 두었다가 이어줍니다 */
let pendingIntent = null;
/* 직전에 그린 화면 — 같은 화면을 다시 그릴 때만 스크롤을 이어 붙이는 판단에 씁니다 */
let lastScreen = null;

function go(screen) {
  if (PROTECTED.includes(screen) && !isLoggedIn()) {
    // 셸이 떠 있는 중이라 화면을 갈아 끼우지 않고 모달만 얹습니다 (system-spec §1-1)
    requireLogin("screen:" + screen, () => go(screen));
    return;
  }
  VN.screen = screen;
  render();
}

/* 보호 동작 게이트 — 통과하지 못하면 동작을 수행하지 않고 로그인 모달을 띄웁니다.
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

/* 전역 패널 — 보호 동작이므로 미로그인이면 열리지 않고 로그인으로 유도합니다 */
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
  VN.detailId = null;        // 상세는 목록 위에 열린 것이라 홈으로 오면 걷습니다
  VN.search = "";            // 검색 결과도 마찬가지로 걷고 활성 칩 화면으로 돌아옵니다
  go("s2");
  if (already) window.scrollTo(0, 0);
}

/* 홈 필터 칩 — 칩을 옮기면 앞 칩에서 걸어 둔 태그 필터는 따라오지 않습니다.
 * 카테고리마다 태그 목록이 달라 그대로 두면 결과 0건의 원인이 화면에서 읽히지 않습니다. */
function selectChip(name) {
  if (VN.homeChip !== name) {
    VN.homeChip = name;
    VN.catTag = null;
  }
  VN.search = "";            // 칩을 고르면 검색 결과에서 목록으로 돌아옵니다
  VN.detailId = null;
  render();
}

/* 키워드 검색 — 공개 범위라 미로그인도 씁니다 (system-spec §1-1).
 * 결과는 홈이 그리므로 다른 화면에서 검색하면 홈으로 옮겨 갑니다. */
function runSearch(text) {
  VN.search = (text || "").trim();
  VN.detailId = null;
  VN.notiOpen = false;
  if (VN.screen !== "s2") go("s2");
  else render();
}

function clearSearch() {
  VN.search = "";
  render();
}

/* 알림 목록 — 계정에 매인 데이터라 보호 동작으로 둡니다.
 * 미로그인이 누르면 열지 않고 로그인으로 유도합니다(T1의 알림 발송과 같은 게이트). */
function toggleNoti() {
  if (!VN.notiOpen && !requireLogin("noti", () => toggleNoti())) return;
  VN.notiOpen = !VN.notiOpen;
  render();
}

function openDetail(id) {
  VN.detailId = id;
  render();
}

function closeDetail() {
  VN.detailId = null;
  render();
}

/* 좋아요·스크랩은 보호 동작입니다 — 미로그인이면 토글하지 않고 로그인으로 유도합니다 */
function toggleCardFlag(kind, id) {
  if (!requireLogin(kind + ":" + id, () => toggleCardFlag(kind, id))) return;
  const acc = currentAccount();
  const list = kind === "like" ? acc.likes : acc.scraps;
  const at = list.indexOf(id);
  if (at >= 0) list.splice(at, 1);
  else list.push(id);
  render();
}

/* 페르소나 저장 — 이름이 비면 저장 버튼이 눌리지 않지만, 값 검증은 여기서도 한 번 더 봅니다.
 * 카드 상세에서 시작을 눌러 온 길이면 저장 직후 그 시작점으로 대화를 엽니다. */
function savePersona() {
  const acc = currentAccount();
  if (!acc) return;
  // 상한은 입력 단계에서 지켜지지만, 저장 경로에서도 잘라 두면 화면을 거치지 않은 값이
  // 들어와도 계정 스코프에 상한을 넘는 값이 남지 않습니다
  const val = (t, limit) => {
    const e = document.querySelector('[data-testid="' + t + '"]');
    const v = e ? e.value.trim() : "";
    return limit ? v.slice(0, limit) : v;
  };
  const name = val("s3-name", PERSONA_LIMITS.name);
  if (!name) return;
  acc.persona = {
    name: name,
    nickname: val("s3-nickname", PERSONA_LIMITS.nickname),
    gender: val("s3-gender"),
    desc: val("s3-desc", PERSONA_LIMITS.desc)
  };
  toast("페르소나를 저장했습니다.");
  if (VN.pendingStart) enterChat();
  else render();
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

function sendMessage(text) {
  const room = activeRoom();
  if (!room || room.ended || chatStreaming) return;
  const t = (text || "").trim().slice(0, CHAT_INPUT_MAX);
  if (!t) return;

  room.turn += 1;
  room.messages.push({ role: "user", text: t, turn: room.turn, done: true });

  const set = mockSetFor(room.charId, room.scenarioId);
  const def = set.turns[room.turn - 1];
  if (!def) {
    // 경로 종점 — 엔딩 판정은 서사 슬라이스에서 붙입니다 (system-spec §4-2)
    room.ended = true;
    render();
    return;
  }
  const cand = def.candidates[VN.seed % def.candidates.length];
  const msg = {
    role: "ai", turn: room.turn, done: false, fail: !!cand.fail,
    text: fillSlots(cand.text, room), delta: cand.deltaAffection || 0
  };
  room.messages.push(msg);
  streamMessage(room, msg);
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
      if (room.turn >= mockSetFor(room.charId, room.scenarioId).endTurn) room.ended = true;
      render();
    }
  }, STREAM_TICK_MS);
}

/* 대화 화면을 엽니다 — 시작점을 들고 왔으면 그 방으로, 아니면 마지막 방으로 */
function enterChat() {
  if (VN.pendingStart) {
    openRoom(VN.pendingStart.charId, VN.pendingStart.scenarioId);
    VN.pendingStart = null;
  }
  go("s4");
}

function leaveChat() {
  go("s2");
}

/* 대화 시작 — 시작 상황은 제작자가 정한 것이라 유저가 고르지 않습니다(system-spec §8-8).
 * 미로그인이면 시작점을 남기지 않고 모달을 띄웠다가, 로그인하면 여기서부터 다시 탑니다. */
function startConversation(charId, scenarioId) {
  const resume = () => startConversation(charId, scenarioId);
  if (!requireLogin("start:" + charId + ":" + scenarioId, resume)) return;
  VN.pendingStart = { charId: charId, scenarioId: scenarioId };
  go("s3");
}

function screenBody() {
  switch (VN.screen) {
    case "s1": return renderS1();
    case "s2": return renderS2();
    case "s3": return renderS3();
    case "s4": return renderS4();
    case "s5": return renderPlaceholder("s5", "채팅");
    case "s6": return renderPlaceholder("s6", "MY");
    case "s7": return renderStub("s7", "커뮤니티는 전시용 정적 화면입니다. 소셜 기능은 별도 앱 규모라 구현 범위에서 제외했습니다.");
    case "s8": return renderStub("s8", "캐릭터 저작은 검증 내용이 페르소나 폼과 중복되어 구현 범위에서 제외했습니다.");
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

  if (VN.session === SESSION.EXPIRED) {
    root.appendChild(renderExpiredModal());
  }

  if (sameScreen && keepPageTop) window.scrollTo(0, keepPageTop);
}

function boot() {
  const params = new URLSearchParams(location.search);
  VN.seed = Number(params.get("seed") || 1);
  VN.inject = params.get("inject");
  VN.sheet = JSON.parse(JSON.stringify(VN_DATA));

  const screen = params.get("screen");
  VN.screen = screen || "s2";                      // 진입점은 홈
  if (PROTECTED.includes(VN.screen) && !isLoggedIn()) {
    // 뒤에 깔 화면이 없는 유일한 경우라 모달이 아니라 로그인 화면으로 받습니다
    pendingIntent = { screen: VN.screen, action: "screen:" + VN.screen, run: null };
    VN.screen = "s1";
  }

  render();
  paintConsole();
}

document.addEventListener("DOMContentLoaded", boot);
