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
    pendingIntent = { screen: screen };
    VN.screen = "s1";
  } else {
    VN.screen = screen;
  }
  render();
}

/* 보호 동작 게이트 — 화면 이동이 아닌 동작(좋아요·수령 등)에 씁니다.
 * 통과하지 못하면 S1으로 보내고 동작은 수행하지 않습니다. */
function requireLogin(action) {
  if (isLoggedIn()) return true;
  pendingIntent = { screen: VN.screen, action: action || null };
  VN.screen = "s1";
  render();
  return false;
}

/* 로그인 성공 후 원래 의도로 복귀 */
function resumeIntent() {
  const next = pendingIntent && pendingIntent.screen;
  pendingIntent = null;
  VN.screen = next && next !== "s1" ? next : "s2";
}

/* 전역 패널 — 보호 동작이므로 미로그인이면 열리지 않고 로그인으로 유도합니다 */
function openPanel(name) {
  if (!requireLogin("panel:" + name)) return;
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
  go("s2");
  if (already) window.scrollTo(0, 0);
}

function screenBody() {
  switch (VN.screen) {
    case "s1": return renderS1();
    case "s2": return renderPlaceholder("s2", "홈");
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

  // 셸은 S1을 뺀 모든 화면에 붙습니다 — 미로그인도 홈을 둘러볼 수 있어야 하므로
  const shell = VN.screen !== "s1";

  if (shell) root.appendChild(renderTopBar());
  root.appendChild(screenBody());
  if (shell) {
    root.appendChild(renderFooter());
    root.appendChild(renderBottomNav());
  }
  const p = renderPanel();
  if (p) root.appendChild(p);

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
  if (PROTECTED.includes(VN.screen) && !isLoggedIn()) VN.screen = "s1";

  render();
  paintConsole();
}

document.addEventListener("DOMContentLoaded", boot);
