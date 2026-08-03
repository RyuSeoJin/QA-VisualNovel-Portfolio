/* 상태 모델 + SUT 테스트 인터페이스(window.__VN__)
 *
 * 스코프는 다섯입니다 — 정적 / 시트 / 계정 / 방 / 슬롯 (청사진 §2).
 * 스코프 경계가 곧 격리 검증의 경계이므로, 경계를 넘는 참조를 만들지 않습니다.
 *
 * 모든 상태는 메모리에만 있습니다. 브라우저 새로고침(F5)이면 초기화되며,
 * 상태 재현은 T1 테스트 콘솔과 이 파일의 API가 담당합니다(save-schema §1).
 */

/* 계정 정의 — 미성년 여부만 계정의 고정 속성입니다.
 * 성인 인증은 켜고 끌 수 있는 상태이므로 계정 스코프(adultVerified)에 둡니다.
 * 계정 B는 미성년이라 인증 자체가 불가능합니다 (system-spec §1-1). */
const ACCOUNTS = {
  a: { id: "a", label: "계정 A (성인)", minor: false },
  b: { id: "b", label: "계정 B (미성년)", minor: true }
};

const SESSION = { GUEST: "guest", ACTIVE: "active", EXPIRED: "expired" };

function deepCopy(v) {
  return JSON.parse(JSON.stringify(v));
}

/* 계정 스코프 초기값 — 계정 간 격리의 단위 */
function newAccountState(id) {
  return {
    adultVerified: id === "a",                // 미성년(b)은 언제나 false
    wallet: { free: 150, paid: 0 },          // 캔디 / 크리스탈 (system-spec §3)
    ledger: [],                               // 획득·소모 내역
    missions: { daily: {}, welcome: {} },     // 수령 기록 (기준일별 / 항목별)
    // 대화 프로필 — 여러 개를 만들어 두고 방마다 하나를 골라 씁니다 (system-spec §2)
    profiles: [],                             // [{ id, name, nickname, gender, desc, label }]
    likes: [], scraps: [],
    rooms: [],                                // 방 목록 (방 스코프는 각 방 안에)
    safetyFilter: false                       // MY 콜아웃 토글 (성인 계정만 노출)
  };
}

const VN = {
  session: SESSION.GUEST,
  accountId: null,
  accounts: { a: newAccountState("a"), b: newAccountState("b") },
  sheet: null,          // 시트 데이터 — boot에서 VN_DATA 사본으로 채웁니다
  screen: "s1",
  panel: null,          // 전역 패널 — P3 재화 / P4 간편 프로필
  homeChip: "추천",     // 홈 필터 칩 — 홈 재선택 시 유지 (system-spec §8-5)
  /* 홈 화면 안의 필터 상태 — 칩을 옮겨도 유지되어야 "돌아왔을 때 그대로인가"를 볼 수 있습니다 */
  rankPeriod: "daily",  // 랭킹 기간 — daily / weekly / monthly
  rankSort: "usage",    // 랭킹 기준 — usage(기본) / likes / score / reviews
  rankHelp: false,      // 랭킹 ⓘ 도움말 펼침
  catFilter: null,      // 카테고리 화면에서 함께 건 페이지 카테고리 — null이면 필터 없음
  catSort: "chat",      // 카테고리 전체 목록 정렬 — chat(대화순) / new(최신순)
  pageCharId: null,     // 열려 있는 캐릭터 페이지의 캐릭터 id
  startProfileId: null, // 다음에 여는 방에 고정될 대화 프로필
  search: "",           // 확정된 검색어 — 결과는 홈에 표시합니다 (청사진 §1 전역 셸)
  notiOpen: false,      // 상단 바 알림 목록 펼침
  loginOpen: false,     // 로그인 모달 — 셸 안에서 막혔을 때만 (system-spec §1-1)
  pendingStart: null,   // 시나리오 선택 시작의 시작점 — S4 슬라이스가 읽습니다
  failNext: false,      // T1의 1회성 스위치 — 다음 전송 한 번을 생성 실패로 (청사진 §4-2)
  noFund: false,        // 재화 부족 안내 화면 (system-spec §3)
  ledgerFilter: "all",  // 재화 내역 필터 — all / gain / spend
  showMetrics: false,   // 카드 지표 표시 — T1에서 켜는 검증용 표시 (청사진 §4-2)
  /* 그 외 작품 추천의 두 값 — 확정값은 아래 상수이고 여기 담긴 것은 T1에서 옮긴 현재 값입니다 */
  relatedLikeMin: 10,   // 좋아요 임계 (system-spec §8-8)
  relatedMax: 5,        // 노출 상한 (system-spec §8-8)
  p2Help: false,        // P2 단계표 ⓘ 펼침
  editTurn: null,       // 편집 중인 턴 — 되돌림 (system-spec §5-1)
  confirm: null,        // 확인 모달 { kind, turn, slot }
  loadPick: null,       // 로드 갈래를 고르는 중인 슬롯 번호 (system-spec §6)
  blockedInput: null,   // 입력 차단 안내 { kind, reason } (system-spec §9-1)
  blockedOutput: false, // 출력 차단 안내 — 후보가 전부 금칙인 경우
  seed: 1,
  inject: null
};

/* 계정 표시명 — 화면에서 어느 계정으로 로그인했는지 확인할 수 있어야
 * 계정 전환 격리를 사람이 검증할 수 있습니다 */
function accountDisplayName(id) {
  return id === "a" ? "성인 계정" : id === "b" ? "미성년 계정" : "";
}

function currentAccount() {
  return VN.accountId ? VN.accounts[VN.accountId] : null;
}

function isLoggedIn() {
  return VN.session === SESSION.ACTIVE && VN.accountId !== null;
}

/* 로그인 필요 동작 차단 — 만료 상태에서는 전송·저장·수령이 모두 막힙니다 */
function canAct() {
  return isLoggedIn();
}

/* 언세이프 열람 가능 여부 — 미로그인·미인증·미성년은 모두 불가.
 * 다만 해제 가능성이 다릅니다(미성년만 수단 없음). */
function isAdultVerified() {
  const acc = currentAccount();
  return !!(acc && acc.adultVerified);
}

/* 성인 인증 설정·해제 — 미성년 계정에는 적용되지 않습니다 */
function setAdultVerified(on) {
  const acc = currentAccount();
  if (!acc) return { ok: false, reason: "미로그인 상태입니다." };
  if (ACCOUNTS[VN.accountId].minor && on) {
    return { ok: false, reason: "미성년 계정은 성인 인증을 할 수 없습니다." };
  }
  acc.adultVerified = on;
  return { ok: true };
}

function login(accountId) {
  VN.accountId = accountId;
  VN.session = SESSION.ACTIVE;
}

/* 화면의 보기 상태를 처음으로 되돌립니다 — 로그아웃·초기화가 함께 씁니다.
 * 검색어와 알림 펼침도 앞 계정의 흔적이므로 여기서 걷습니다. */
function resetViewState() {
  VN.search = "";
  VN.notiOpen = false;
  VN.loginOpen = false;
  clearPendingIntent();      // 앞 계정에서 막혔던 의도를 다음 계정이 이어받으면 안 됩니다
  VN.homeChip = "추천";
  VN.rankPeriod = "daily";
  VN.rankSort = "usage";
  VN.rankHelp = false;
  VN.catFilter = null;
  VN.catSort = "chat";
  VN.pageCharId = null;
  VN.startProfileId = null;
  VN.pendingStart = null;
  VN.editTurn = null;
  VN.confirm = null;
  VN.loadPick = null;
  VN.blockedInput = null;
  VN.blockedOutput = false;
}

function logout() {
  // 앞 계정의 데이터가 화면·저장소 어디에도 남지 않아야 합니다
  VN.accountId = null;
  VN.session = SESSION.GUEST;
  VN.screen = "s2";          // 미로그인 상태의 홈으로 복귀
  VN.panel = null;
  resetViewState();
}

/* 이용수 집계 — 유저×캐릭터×날짜 중복 제거 (system-spec §8-2) */
function usageCount(charId, days) {
  const seen = new Set();
  for (const e of VN.sheet.events) {
    if (e.charId !== charId) continue;
    if (e.day > VN.sheet.baseDay) continue;          // 미래 이벤트 제외
    if (days !== null && !days.includes(e.day)) continue;
    seen.add(e.user + "|" + e.charId + "|" + e.day);
  }
  return seen.size;
}

/* 기준일에서 n일 전까지의 날짜 목록 — 실시계 없이 문자열로 계산 */
function recentDays(n) {
  const [y, m, d] = VN.sheet.baseDay.split("-").map(Number);
  const out = [];
  for (let i = 0; i < n; i++) {
    const dt = new Date(Date.UTC(y, m - 1, d - i));
    out.push(dt.toISOString().slice(0, 10));
  }
  return out;
}

/* ── 홈 목록의 모수·정렬·게이팅 ─────────────────────────────
 * 목록에 무엇이 몇 번째로 놓이는가가 탐색 영역의 기대값이라, 선정과 정렬을 화면 코드에
 * 두지 않고 여기 모읍니다. 화면은 여기서 받은 순서를 그대로 그립니다.
 */

/* 게이팅 상태 5종 (system-spec §1-1) — 세션이 만료되면 계정이 남아 있어도 미로그인으로 읽습니다 */
function gateState() {
  if (!isLoggedIn()) return "guest";
  if (ACCOUNTS[VN.accountId].minor) return "minor";
  return currentAccount().adultVerified ? "adult" : "unverified";
}

function canViewUnsafe() {
  // [주입] gate-bypass — 게이팅 계층이 뚫려 미인증·미성년에게도 언세이프가 열립니다
  if (injected("gate-bypass")) return true;
  return gateState() === "adult";
}

/* 게이팅 상태의 화면 표기 — MY에서 지금 어느 상태인지 읽히지 않으면 언세이프가 왜
 * 가려졌는지 판단할 수 없습니다. T1의 STATE_LABEL은 디버그 프리셋 이름이라 따로 둡니다 */
const GATE_LABEL = {
  guest: "미로그인",
  unverified: "본인인증 미진행",
  adult: "성인 인증 완료",
  minor: "미성년"
};

/* 막힌 이유는 상태마다 다릅니다 — 미로그인·미인증은 풀 수단이 있고 미성년은 없습니다 */
const GATE_NOTICE = {
  guest: "로그인하고 본인인증을 하면 볼 수 있습니다.",
  unverified: "본인인증을 하면 볼 수 있습니다.",
  minor: "미성년 계정은 열람할 수 없습니다. 해제 수단이 없습니다."
};

/* 정렬에 쓰는 좋아요 수 = 시트 기본값 + 계정의 토글 반영 (system-spec §8-7) */
function likeCount(c) {
  const acc = currentAccount();
  return c.likes + (acc && acc.likes.indexOf(c.id) >= 0 ? 1 : 0);
}

function isLiked(id) {
  const acc = currentAccount();
  return !!(acc && acc.likes.indexOf(id) >= 0);
}

function isScrapped(id) {
  const acc = currentAccount();
  return !!(acc && acc.scraps.indexOf(id) >= 0);
}

/* 날짜를 비교 가능한 수로 — 실시계를 쓰지 않으므로 문자열에서 바로 뽑습니다 */
function dayNum(day) {
  return Number(String(day || "").replace(/-/g, "")) || 0;
}

/* 홈에 노출되는 모수 — 세이프티 필터가 켜져 있으면 언세이프를 목록에서 아예 뺍니다.
 * 게이팅과는 층이 다릅니다: 필터는 숨기고(존재도 안 보임), 게이팅은 가린 채 남깁니다 */
function visibleCharacters() {
  const acc = currentAccount();
  const hide = !!(acc && acc.safetyFilter);
  return VN.sheet.characters.filter((c) => !(hide && c.safe === false));
}

function weekUsage(c) {
  return usageCount(c.id, recentDays(7));
}

function monthUsage(c) {
  return usageCount(c.id, recentDays(30));
}

/* 동률 체인 — 선택 기준 → 이용수 → 좋아요 수 → 캐릭터 ID (system-spec §8-4).
 * 두 번째 고리의 이용수는 월간(최근 30일)입니다. 창이 닫혀 있어 오래된 이벤트가 순서에
 * 영원히 남지 않습니다 — 누적값을 쓰면 옛 인기가 계속 순위를 붙잡습니다. */
function sortChars(list, keyFn) {
  return list.slice().sort((a, b) =>
    keyFn(b) - keyFn(a) ||
    monthUsage(b) - monthUsage(a) ||
    likeCount(b) - likeCount(a) ||
    (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}

/* 신작 = 생성일이 기준일 포함 최근 60일 안 (system-spec §8-5) */
const NEW_WINDOW_DAYS = 60;

function isRising(c) {
  return recentDays(NEW_WINDOW_DAYS).indexOf(c.createdDay) >= 0;
}

const RANK_PERIOD_DAYS = { daily: 1, weekly: 7, monthly: 30 };

/* 리뷰 점수 순의 최소 표본 (system-spec §8-3) */
const REVIEW_MIN_SAMPLE = 50;

/* 랭킹 목록 — 기간은 이용수 기준에만 걸리고, 좋아요·리뷰는 누적값입니다 (system-spec §8-3) */
const RANK_PERIOD_LABEL = { daily: "일간", weekly: "주간", monthly: "월간" };

function rankList() {
  const period = recentDays(RANK_PERIOD_DAYS[VN.rankPeriod] || 1);
  const base = visibleCharacters();
  if (VN.rankSort === "likes") return sortChars(base, likeCount);
  if (VN.rankSort === "reviews") return sortChars(base, (c) => c.reviews);
  if (VN.rankSort === "score") {
    // 리뷰 표본이 적은 캐릭터의 만점은 순위의 뜻을 지우므로 최소 표본 미만은 제외합니다
    return sortChars(base.filter((c) => c.reviews >= REVIEW_MIN_SAMPLE), (c) => c.score);
  }
  // 이용수 기준 — 집계 0건은 노출하지 않습니다 (system-spec §8-2)
  const counted = base.filter((c) => usageCount(c.id, period) > 0);
  return sortChars(counted, (c) => usageCount(c.id, period));
}

/* 랭킹 카드에 함께 보이는 값 — 무엇으로 줄을 세웠는지 화면에서 읽혀야 합니다 */
function rankMetric(c) {
  const period = recentDays(RANK_PERIOD_DAYS[VN.rankPeriod] || 1);
  if (VN.rankSort === "likes") return "좋아요 " + likeCount(c);
  if (VN.rankSort === "reviews") return "리뷰 " + c.reviews + "개";
  if (VN.rankSort === "score") return "평점 " + c.score.toFixed(1) + " (리뷰 " + c.reviews + ")";
  return RANK_PERIOD_LABEL[VN.rankPeriod] + " 이용수 " + usageCount(c.id, period);
}

/* 추천 탭의 섹션들 (system-spec §8-5) */
const CAROUSEL_MAX = 7;
const SECTION_TOP = 5;

/* 선택 기준이 따로 없는 목록이라 체인의 첫 고리인 월간 이용수가 1차 키가 됩니다 */
function carouselList() {
  return sortChars(visibleCharacters(), monthUsage).slice(0, CAROUSEL_MAX);
}

/* 떠오르는 신작 — 두 창이 서로 다른 일을 합니다.
 * 월간은 모수를 거르고(이용자가 아예 없는 캐릭터 제외), 주간은 순서를 만듭니다. */
function risingList(category) {
  const base = visibleCharacters().filter((c) =>
    isRising(c) && monthUsage(c) > 0 && (!category || hasCategory(c, category)));
  return sortChars(base, weekUsage).slice(0, SECTION_TOP);
}

/* 지금 뜨거운 — 주간 이용수가 0이면 섹션의 뜻과 어긋나므로 모수에서 뺍니다 */
function hotList() {
  return sortChars(visibleCharacters().filter((c) => weekUsage(c) > 0), weekUsage)
    .slice(0, SECTION_TOP);
}

/* 최근 대화한 캐릭터 — 대화 이력이 없으면 섹션 자체를 노출하지 않습니다 */
function recentTalkedList() {
  const acc = currentAccount();
  if (!acc) return [];
  const ids = acc.rooms.map((r) => r.charId);
  return visibleCharacters().filter((c) => ids.indexOf(c.id) >= 0);
}

/* 신작 탭 — 생성일 최신순 */
function newestList() {
  return sortChars(visibleCharacters(), (c) => dayNum(c.createdDay));
}

/* 카테고리 전체 목록 — 두 페이지 카테고리의 AND 필터 (system-spec §8-6) */
function hasCategory(c, name) {
  return (c.pageCategories || []).indexOf(name) >= 0;
}

function categoryList(category) {
  let base = visibleCharacters().filter((c) => hasCategory(c, category));
  if (VN.catFilter) base = base.filter((c) => hasCategory(c, VN.catFilter));
  if (VN.catSort === "new") return sortChars(base, (c) => dayNum(c.createdDay));
  return sortChars(base, (c) => usageCount(c.id, null));   // 대화순 = 누적 이용수
}

/* 그 외 작품 추천의 확정값 (system-spec §8-8).
 *
 * 두 값은 T1에서 옮길 수 있습니다. 기본 데이터는 캐릭터가 여덟이라 카테고리를 공유하는 후보가
 * 상한에 닿지 않고 좋아요도 전부 임계를 넘어, 값을 옮기지 않으면 어느 경계도 만들 수 없기
 * 때문입니다. 옮긴 값은 경계를 만드는 수단이고 TC 기대값은 언제나 이 확정값입니다. */
const RELATED_LIKE_MIN = 10;
const RELATED_MAX = 5;

/* 작품 버전 표기 (system-spec §8-8) — 저장은 숫자와 점만 담고, 표시할 때 `v`를 붙입니다.
 * 입력에서 그 밖의 문자를 걷어내므로 테스터가 `v`를 직접 적어도 접두가 겹치지 않습니다. */
function versionInput(s) {
  return String(s == null ? "" : s).replace(/[^0-9.]/g, "");
}

function versionLabel(v) {
  const n = versionInput(v);
  return n ? "v" + n : "-";
}

/* 그 외 작품 추천 — 캐릭터 페이지 하단의 연관 작품 (system-spec §8-8).
 *
 * 페이지 카테고리를 하나라도 공유하고 좋아요가 임계 이상인 작품을, 좋아요를 선택 기준으로 삼은
 * 동률 체인(§8-4) 순으로 상한까지 내놓습니다. 자기 자신은 빼고, 가시성 필터를 먼저 태우므로
 * 필터로 숨겨진 작품은 후보에 들지 않습니다.
 *
 * 임계·정렬 모두 `likeCount`를 씁니다 — 화면에 보이는 좋아요 수(시트 값 + 내가 누른 것)와
 * 판정 근거가 갈라지면 "10인데 왜 빠졌나"를 설명할 수 없습니다. */
function relatedList(c) {
  const cats = c.pageCategories || [];
  const base = visibleCharacters().filter((x) =>
    x.id !== c.id
    && likeCount(x) >= VN.relatedLikeMin
    && (x.pageCategories || []).some((n) => cats.indexOf(n) >= 0));
  return sortChars(base, likeCount).slice(0, VN.relatedMax);
}

/* ── 방 스코프 ───────────────────────────────────────────
 * 방·분기 간 격리의 단위입니다(청사진 §2). 대화 이력·호감도·기억이 방 안에만 있고,
 * 방 밖에서 이 값을 참조하지 않아야 격리 검증이 성립합니다.
 */

/* 캐릭터 페이지 글자수 상한 (system-spec §8-8) — 제작자가 넣는 값이라 T1 입력에서 지킵니다 */
const PAGE_TITLE_MAX = 20;
const PAGE_SUB_MAX = 30;

/* 자유 입력 상한 (system-spec §5) */
const CHAT_INPUT_MAX = 500;

/* ── 재화 (system-spec §3) ─────────────────────────────────
 * 무료 재화 캔디 / 유료 재화 크리스탈. 캔디를 먼저 쓰고 부족분만 크리스탈에서 채웁니다.
 */
const SEND_COST = 10;          // 전송 1회 요율
const CHARGE_AMOUNT = 100;     // mock 충전 1회 (크리스탈)

function walletTotal(acc) {
  return acc.wallet.free + acc.wallet.paid;
}

function ledgerAdd(acc, wallet, amount, reason) {
  const row = { id: "L" + (acc.ledger.length + 1), wallet: wallet, amount: amount,
    reason: reason, day: VN.sheet.baseDay };
  acc.ledger.push(row);
  return row;
}

/* 소모 — 합산이 모자라면 아무것도 깎지 않고 null을 돌려줍니다(전송 차단의 근거).
 * 혼합 차감은 지갑별로 두 줄이 남습니다(system-spec §3). */
function spend(acc, cost, reason) {
  if (walletTotal(acc) < cost) return null;
  const free = Math.min(acc.wallet.free, cost);
  const paid = cost - free;
  acc.wallet.free -= free;
  acc.wallet.paid -= paid;
  const rows = [];
  if (free) rows.push(ledgerAdd(acc, "free", -free, reason));
  if (paid) rows.push(ledgerAdd(acc, "paid", -paid, reason));
  return { free: free, paid: paid, rows: rows };
}

/* ── 서사 (system-spec §4) ────────────────────────────────
 * 호감도는 0에서 시작하고 하한은 0입니다. 단계는 호감도에서 파생하며 따로 저장하지
 * 않습니다 — 두 곳에 저장하면 어긋나기 시작합니다(save-schema §2).
 */
const STAGES = [
  { name: "경계", from: 0, to: 19, temp: "서먹함" },
  { name: "호기심", from: 20, to: 59, temp: "미지근함" },
  { name: "애착", from: 60, to: 119, temp: "따뜻함" },
  { name: "운명", from: 120, to: Infinity, temp: "뜨거움" }
];

function stageOf(affection) {
  return STAGES.find((s) => affection >= s.from && affection <= s.to) || STAGES[0];
}

const ENDING_CHECK_FROM = 10;   // 10턴 이후 5턴마다
const ENDING_CHECK_EVERY = 5;
const ENDING_GOOD = 120;        // 운명 도달
const ENDING_BAD_AFFECTION = 20;

/* 검사 시점 판정 — 10·15·20…턴에서만 보며 **호감도만** 봅니다.
 * 참여율(선택지 응답 비율)은 폐지했습니다 — 원 출처는 실시간 채팅 참여였는데 이 SUT에는
 * 실시계가 없고, 자유 입력으로도 호감도가 오르는 구조라 "호감도가 높은데 배드"가 되어
 * 기대값을 설명할 수 없었습니다(2026-08-03 확정). */
function endingAtCheckpoint(room) {
  if (room.turn < ENDING_CHECK_FROM) return null;
  if ((room.turn - ENDING_CHECK_FROM) % ENDING_CHECK_EVERY !== 0) return null;
  if (room.affection >= ENDING_GOOD) return "굿";
  return null;
}

/* 경로 종점 최종 판정 */
function endingAtPathEnd(room) {
  if (room.affection >= ENDING_GOOD) return "굿";
  if (room.affection < ENDING_BAD_AFFECTION) return "배드";
  return "노멀";
}

/* ── 미션 (system-spec §3) ─────────────────────────────────
 * 달성 판정 로직은 만들지 않습니다 — 전 항목이 수령 가능 상태로 노출되며, 검증 대상은
 * 수령·중복 차단·잔액 반영입니다. 미구현 사유는 화면에 적습니다.
 */
const MISSION_REWARD = 50;      // 데일리·웰컴 모두 캔디 50

const WELCOME_MISSIONS = [
  { id: "join", label: "가입 환영" },
  { id: "firstchat", label: "첫 대화" },
  { id: "persona", label: "페르소나 등록" }
];

function dailyClaimed() {
  const acc = currentAccount();
  // 기준일별로 기록합니다 — 기준일을 옮기면 다시 받을 수 있고, 그 자체가 검증 대상입니다
  return !!(acc && acc.missions.daily[VN.sheet.baseDay]);
}

function welcomeClaimed(id) {
  const acc = currentAccount();
  return !!(acc && acc.missions.welcome[id]);
}

function claimDaily() {
  const acc = currentAccount();
  if (!acc) return { ok: false, reason: "미로그인 상태입니다." };
  if (dailyClaimed()) return { ok: false, reason: "오늘은 이미 받았습니다." };
  acc.missions.daily[VN.sheet.baseDay] = true;
  acc.wallet.free += MISSION_REWARD;
  ledgerAdd(acc, "free", MISSION_REWARD, "데일리 미션 · 출석 체크");
  return { ok: true };
}

function claimWelcome(id) {
  const acc = currentAccount();
  if (!acc) return { ok: false, reason: "미로그인 상태입니다." };
  if (welcomeClaimed(id)) return { ok: false, reason: "이미 받은 미션입니다." };
  const m = WELCOME_MISSIONS.find((x) => x.id === id);
  if (!m) return { ok: false, reason: "없는 미션입니다." };
  acc.missions.welcome[id] = true;
  acc.wallet.free += MISSION_REWARD;
  ledgerAdd(acc, "free", MISSION_REWARD, "웰컴 미션 · " + m.label);
  return { ok: true };
}

/* 내역 필터 — 획득/소모를 갈라 봅니다 (system-spec §3) */
function ledgerRows() {
  const acc = currentAccount();
  if (!acc) return [];
  const rows = acc.ledger.slice().reverse();
  if (VN.ledgerFilter === "gain") return rows.filter((r) => r.amount > 0);
  if (VN.ledgerFilter === "spend") return rows.filter((r) => r.amount < 0);
  return rows;
}

/* 차감 취소 — 실패한 전송은 재화를 소모하지 않으므로 내역에도 남기지 않습니다.
 * 잔액만 되돌리고 기록을 남기면 "소모했다"로 읽혀 명세와 어긋납니다. */
function refund(acc, spent) {
  if (!spent) return;
  acc.wallet.free += spent.free;
  acc.wallet.paid += spent.paid;
  acc.ledger = acc.ledger.filter((r) => spent.rows.indexOf(r) < 0);
}

/* 캐릭터당 대화방 한도 (system-spec §6) — 넘기면 새 방·분기가 막힙니다 */
const ROOM_LIMIT_PER_CHAR = 4;

function roomsOf(charId) {
  const acc = currentAccount();
  return acc ? acc.rooms.filter((r) => r.charId === charId) : [];
}

function roomLimitReached(charId) {
  return roomsOf(charId).length >= ROOM_LIMIT_PER_CHAR;
}

function newRoom(charId, scenarioId, firstMessage, profile) {
  const acc = currentAccount();
  const prefix = charId + "-" + scenarioId + "-";
  // 실시계·난수를 쓰지 않으므로 방 id도 결정적으로 만듭니다.
  // 개수로 번호를 매기면 중간 방을 지운 뒤 id가 겹치므로, 쓰인 적 있는 가장 큰 번호 다음을
  // 씁니다 — 지운 방의 id를 재사용하지 않아야 잔존 검증에서 방이 헷갈리지 않습니다
  const used = acc.rooms
    .filter((r) => r.id.indexOf(prefix) === 0)
    .map((r) => Number(r.id.slice(prefix.length)) || 0);
  return {
    id: prefix + (used.length ? Math.max.apply(null, used) + 1 : 1),
    charId: charId,
    scenarioId: scenarioId,
    // 프로필은 방에 고정됩니다 — 목록에서 지워도 이 방은 저장된 값으로 답합니다(save-schema)
    profile: profile ? deepCopy(profile) : null,
    turn: 0,                 // 진행한 유저 턴 수
    // 첫 메시지는 대화수에 포함됩니다 (system-spec §5)
    messages: firstMessage
      ? [{ role: "ai", text: firstMessage, turn: 0, done: true }] : [],
    affection: 0,
    // 재계산의 기준점 — T1으로 호감도를 세우면 여기가 옮겨집니다.
    // 되돌림은 남은 기록으로 다시 세는데, 기록 없이 세운 값(T1)은 다시 셀 근거가 없으므로
    // 기준점으로 남기고 그 뒤 턴만 더합니다 (청사진 §4-2)
    affectionBase: 0,
    affectionBaseTurn: 0,
    // 기억 목록은 대화 기록에서 다시 세웁니다(rebuildMemories) — 아래 둘이 유저가 손댄 부분
    memories: [],
    pins: {},                // 고정한 기억의 id — 장면이 끝나도 요점화되지 않습니다
    forgotten: [],           // 지운 기억의 id — 이후 응답이 참조하지 않습니다
    // 현재 상태 값 고정 — 유저가 고친 값이 자동 계산보다 우선합니다 (system-spec §7-2)
    overrides: {},           // { temp, nickname }
    // 시점 슬롯 — 방마다 독립입니다(분기 방도 자기 4칸을 새로 받습니다, system-spec §6)
    slots: {},
    ending: null,                            // 도달한 엔딩 — 있으면 입력이 막힙니다
    ended: false,
    active: true
  };
}

function activeRoom() {
  const acc = currentAccount();
  return acc ? acc.rooms.find((r) => r.active) || null : null;
}

/* 새 대화방을 엽니다 — 고른 프로필이 그 방에 고정됩니다.
 * 한도까지 찼으면 아무것도 만들지 않고 null을 돌려줍니다(호출한 쪽이 삭제를 묻습니다). */
function openRoom(charId, profile) {
  const acc = currentAccount();
  if (!acc) return null;
  if (roomLimitReached(charId)) return null;
  // 2차 방어 — 저장을 우회해 들어온 값도 대화 경로에서 다시 막습니다 (system-spec §9-1).
  // 폼으로 들어오든 값 주입으로 들어오든 같은 결과여야 합니다
  if (profileHasInjection(profile)) return { blocked: "inject" };
  const c = findCharacter(charId);
  const sit = (c && c.startSituation) || { id: "sc1" };
  const room = newRoom(charId, sit.id, c ? c.firstMessage : "", profile);
  acc.rooms.forEach((r) => { r.active = false; });
  acc.rooms.push(room);
  room.active = true;
  return room;
}

/* 이전 대화방으로 돌아갑니다 */
function resumeRoom(roomId) {
  const acc = currentAccount();
  if (!acc) return null;
  const room = acc.rooms.find((r) => r.id === roomId);
  if (!room) return null;
  acc.rooms.forEach((r) => { r.active = false; });
  room.active = true;
  return room;
}

function deleteRoom(roomId) {
  const acc = currentAccount();
  if (!acc) return;
  acc.rooms = acc.rooms.filter((r) => r.id !== roomId);
}

/* ── 되돌림 (system-spec §5-1) ─────────────────────────────
 * "화면에서 사라진 메시지는 점수와 기억에서도 사라진다"를 지키는 자리입니다.
 *
 * 되돌린 뒤의 상태는 **남은 기록만으로 처음부터 다시 셉니다.** 지운 만큼 빼는 방식으로
 * 만들면 하한 0에 걸렸던 턴에서 어긋납니다 — 예를 들어 호감도 0에서 −1을 받은 턴은 실제로
 * 0에 머물렀으므로, 그 턴을 지우면서 +1을 되돌려 주면 없던 점수가 생깁니다.
 */

function messagesOfTurn(room, turn) {
  return room.messages.filter((m) => m.turn === turn);
}

function lastTurnOf(room) {
  return room.messages.reduce((max, m) => Math.max(max, m.turn), 0);
}

/* 최신 교환에만 편집·삭제·재생성이 붙습니다 — 과거 턴은 분기가 담당합니다 (system-spec §5) */
function isLatestExchange(room, turn) {
  return turn > 0 && turn === room.turn;
}

/* 남은 기록으로 호감도·엔딩·턴수를 다시 셉니다.
 * 한 턴의 기여분은 유저 선택지 가중치 + 응답 델타이고 턴마다 하한 0을 받습니다(§4-1). */
function recomputeRoom(room) {
  const set = mockSetFor(room.charId, room.scenarioId);
  const byTurn = {};
  room.messages.forEach((m) => {
    if (m.turn > 0) byTurn[m.turn] = (byTurn[m.turn] || 0) + (m.delta || 0);
  });
  const baseTurn = room.affectionBaseTurn || 0;
  const turns = Object.keys(byTurn).map(Number).sort((a, b) => a - b)
    .filter((t) => t > baseTurn);          // 기준점 이전은 기록이 아니라 세팅값입니다

  let aff = room.affectionBase || 0, ending = null, ended = false;
  for (const t of turns) {
    aff = Math.max(0, aff + byTurn[t]);
    const probe = { turn: t, affection: aff };
    // 검사 시점에 굿이 뜨면 그 방은 거기서 멈춥니다 — 이후 턴이 있을 수 없습니다
    const hit = endingAtCheckpoint(probe);
    if (hit) { ending = hit; break; }
    if (t >= set.endTurn) { ended = true; ending = endingAtPathEnd(probe); break; }
  }
  room.affection = aff;
  room.ending = ending;
  room.ended = ended;
  room.turn = lastTurnOf(room);
  // 기억도 같은 기록에서 다시 세웁니다 — 지운 턴의 기억이 남지 않는 것이 여기서 보장됩니다
  rebuildMemories(room);
}

/* 교환 통째로 삭제 — 유저 메시지와 그에 딸린 응답을 한 쌍으로 지웁니다 */
function removeExchange(room, turn) {
  room.messages = room.messages.filter((m) => m.turn !== turn);
  recomputeRoom(room);
}

/* 대화 기록으로 새 방을 세웁니다 — 분기와 「새 방으로 로드」가 같은 길을 씁니다.
 * 두 동작 모두 "이 기록에서 시작하는 방을 하나 더 만든다"라서, 새 방을 만드는 규칙(한도·
 * 활성 전환·슬롯은 새로)이 한 곳에만 있어야 갈라지지 않습니다.
 * 한도까지 찼으면 아무것도 만들지 않고 null을 돌려줍니다(호출한 쪽이 삭제를 묻습니다). */
function cloneRoomFrom(src, data) {
  const acc = currentAccount();
  if (!acc) return null;
  if (roomLimitReached(src.charId)) return null;
  const copy = newRoom(src.charId, src.scenarioId, "", data.profile);
  copy.messages = deepCopy(data.messages || []);
  // 고정·삭제·상태 값 고정은 유저가 정한 값이라 함께 따라갑니다.
  // 기억 목록 자체는 기록에서 다시 세웁니다
  copy.pins = deepCopy(data.pins || {});
  copy.forgotten = deepCopy(data.forgotten || []);
  copy.overrides = deepCopy(data.overrides || {});
  copy.affectionBase = data.affectionBase || 0;
  copy.affectionBaseTurn = data.affectionBaseTurn || 0;
  recomputeRoom(copy);                     // 상태는 여기서도 다시 셉니다 (system-spec §5-1)
  acc.rooms.forEach((r) => { r.active = false; });
  acc.rooms.push(copy);
  copy.active = true;
  return copy;
}

/* 분기 — 그 지점까지를 복사한 새 방을 만들고 원본은 그대로 둡니다 */
function branchRoom(room, turn) {
  return cloneRoomFrom(room, {
    profile: room.profile,
    messages: room.messages.filter((m) => m.turn <= turn),
    pins: room.pins, forgotten: room.forgotten, overrides: room.overrides,
    affectionBase: room.affectionBase || 0,
    affectionBaseTurn: Math.min(room.affectionBaseTurn || 0, turn)
  });
}

/* ── 결함 주입 (fault-injection) ───────────────────────────
 *
 * `?inject={키}`로 켜는 **일부러 만든 고장**입니다. 목적은 "내 테스트가 이 결함을 실제로
 * 잡는다"는 탐지력 증명이며, 매트릭스에서 **대각선만 FAIL**이 되어야 읽힙니다.
 *
 * 그래서 주입 지점을 **한 곳씩만** 잡습니다 — 넓게 걸면 다른 영역의 TC까지 깨져 표가
 * 증거로서의 값어치를 잃습니다. 화면에는 주입 상태를 표시하지 않습니다(탐지는 테스트의 몫).
 */
function injected(key) {
  return VN.inject === key;
}

/* ── 세이프티 (system-spec §9-1) ───────────────────────────
 *
 * 판정은 **추상 토큰으로만** 합니다. 자연어 패턴은 어디까지가 위반인지 경계가 흔들려
 * 기대값을 적을 수 없고, 실제 탈옥 문자열을 저장소에 넣지 않는다는 방침과도 맞습니다.
 *
 * 이 영역이 보는 것은 **게이팅 계층**이지 모델의 안전성이 아닙니다 — 실제 LLM이 없으므로
 * 모델 내성은 검증 범위 밖이며, 이 문장은 산출물에 그대로 들어갑니다.
 */

/* 우회 방어 — 대조 전에 공백·특수문자를 지웁니다.
 * 토큰을 쪼개 넣는 것(`[BLOCKED_ TERM_A]`·`[B-L-O-C-K-E-D_TERM_A]`)이 우회 시도의 형태이고,
 * 그것을 같은 것으로 보는 것이 이 노드입니다. */
function normalizeForFilter(text) {
  return String(text || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
}

function hitToken(text, tokens) {
  const flat = normalizeForFilter(text);
  return (tokens || []).find((t) => flat.indexOf(normalizeForFilter(t)) >= 0) || null;
}

/* 입력 판정 — 종류마다 막는 자리와 안내가 다릅니다 */
function screenInput(text) {
  const sheet = VN.sheet || {};
  const blocked = hitToken(text, sheet.blockedTokens);
  if (blocked) {
    return { ok: false, kind: "blocked", token: blocked,
      reason: "금칙어가 포함되어 전송할 수 없습니다." };
  }
  const jail = hitToken(text, sheet.jailbreakTokens);
  if (jail) {
    return { ok: false, kind: "jailbreak", token: jail,
      reason: "설정을 바꾸려는 시도로 판정되어 전송할 수 없습니다." };
  }
  const inject = hitToken(text, sheet.injectTokens);
  if (inject) {
    return { ok: false, kind: "inject", token: inject,
      reason: "지시문 삽입으로 판정되어 전송할 수 없습니다." };
  }
  return { ok: true };
}

/* 프롬프트 누출 — 응답을 만들지 않고 정해진 거절문만 돌려줍니다.
 * 내부 지시·mock 세트의 내용이 응답에 섞이면 실패입니다. */
const LEAK_REFUSAL = "그건 알려 드릴 수 없어요.";

function asksForPrompt(text) {
  return !!hitToken(text, (VN.sheet || {}).leakTokens);
}

/* 프로필 설명란 주입 — 저장에서 막고, 값 주입으로 들어온 경우를 위해 대화 경로에서
 * 한 번 더 봅니다. 어느 경로로 들어와도 같은 결과여야 합니다(§2와 같은 원칙). */
function profileHasInjection(p) {
  if (!p) return null;
  return hitToken([p.name, p.nickname, p.desc, p.label].join(" "),
    ((VN.sheet || {}).injectTokens || []).concat((VN.sheet || {}).jailbreakTokens || []));
}

/* 출력 판정 — 금칙 토큰이 든 후보는 화면에 내보내지 않습니다 */
function candidateBlocked(cand) {
  if (!cand) return false;
  if (cand.blockedToken) return true;
  return !!hitToken(cand.text, (VN.sheet || {}).blockedTokens);
}

/* ── 메모리/컨텍스트 (system-spec §7) ──────────────────────
 *
 * **기억 목록은 저장하지 않고 대화 기록에서 다시 세웁니다.** 호감도와 같은 이유입니다 —
 * 목록을 따로 들고 있으면 되돌림 때 무엇을 빼야 하는지 다시 계산해야 하고, 그 계산이
 * 어긋나면 지운 턴의 기억이 남습니다. 유저가 손댄 부분(핀·삭제)만 방에 남깁니다.
 */
const CONTEXT_WINDOW_TURNS = 10;

/* 단기 맥락 창 — 최근 10턴. 창 밖은 응답에 반영되지 않아야 하므로 경계가 화면과
 * getState에서 읽혀야 합니다(창이 몇 턴인지 눈으로 못 보면 경계를 검증할 수 없습니다) */
function contextRange(room) {
  if (!room || room.turn < 1) return { from: 0, to: 0 };
  return { from: Math.max(1, room.turn - CONTEXT_WINDOW_TURNS + 1), to: room.turn };
}

function inContext(room, turn) {
  const r = contextRange(room);
  return turn >= r.from && turn <= r.to;
}

/* 이벤트 — 대화는 장면 단위로 끊깁니다(mock 세트의 `events`).
 * 한 장면이 끝나면 그 장면에서 알게 된 것들이 간략형으로 정리됩니다 — 캐릭터가 지난 일을
 * 요점만 기억하는 자리이고, 이 SUT에서 **기억이 저절로 바뀌는 유일한 사건**입니다. */
function eventsOf(room) {
  return mockSetFor(room.charId, room.scenarioId).events || [];
}

function eventOfTurn(room, turn) {
  return eventsOf(room).find((e) => turn >= e.from && turn <= e.to) || null;
}

function currentEvent(room) {
  return eventOfTurn(room, Math.max(1, room.turn));
}

/* 그 기억이 속한 장면이 이미 끝났는가 — 끝났으면 간략형으로 남습니다 */
function eventEnded(room, turn) {
  const e = eventOfTurn(room, turn);
  return !!e && room.turn > e.to;
}

/* 남은 응답들의 memoryAdd를 턴 순서대로 훑어 목록을 세웁니다.
 * - 지운 항목은 받지 않습니다
 * - 장면이 끝난 기억은 간략형(brief)으로 바뀝니다
 * - **핀이 꽂힌 항목은 간략화되지 않습니다** — 유저가 세부까지 남기라고 정한 것이라
 *   캐릭터의 자동 정리가 그 위를 덮지 못합니다 (system-spec §7-1) */
function rebuildMemories(room) {
  const forgotten = room.forgotten || [];
  const pins = room.pins || {};
  const seen = {};
  const out = [];
  room.messages.forEach((m) => {
    // 유저가 등록한 기억 — 그 메시지에 표시가 붙어 있습니다. 유저가 고른 문장이라
    // 줄일 근거(요약본)가 없으므로 간략화하지 않습니다 (system-spec §7-1)
    if (m.userMemory) {
      const uid = "u" + m.turn + "-" + m.role;
      if (forgotten.indexOf(uid) < 0 && !seen[uid]) {
        seen[uid] = true;
        const uev = eventOfTurn(room, m.turn);
        out.push({
          id: uid, turn: m.turn, text: m.text,
          brief: false, pinned: !!pins[uid], source: "user",
          event: uev ? uev.label : ""
        });
      }
    }
    const add = m.memoryAdd;
    if (!add || !add.id) return;
    if (forgotten.indexOf(add.id) >= 0 || seen[add.id]) return;
    seen[add.id] = true;
    const pinned = !!pins[add.id];
    const brief = !pinned && eventEnded(room, m.turn);
    const ev = eventOfTurn(room, m.turn);
    out.push({
      id: add.id, turn: m.turn,
      text: brief ? (add.brief || add.text) : add.text,
      brief: brief, pinned: pinned, source: "auto",
      event: ev ? ev.label : ""
    });
  });
  room.memories = out;
}

/* 대화에서 기억 등록 — 그 메시지에 표시를 답니다.
 * 목록에 직접 넣지 않는 이유는 자동 축적과 같습니다 — 기록에서 파생되어야 되돌림·분기·
 * 로드가 저절로 따라옵니다(메시지가 사라지면 기억도 사라집니다). */
function markUserMemory(room, turn, role, on) {
  const m = room.messages.find((x) => x.turn === turn && x.role === role);
  if (!m) return null;
  m.userMemory = on !== false;
  if (!m.userMemory) {
    const uid = "u" + turn + "-" + role;
    if (room.pins) delete room.pins[uid];
    room.forgotten = (room.forgotten || []).filter((id) => id !== uid);
  }
  rebuildMemories(room);
  return m;
}

/* ── 현재 상태 값 고정 (system-spec §7-2) ──────────────────
 * 캐릭터가 계속 다시 계산하는 값을 유저가 붙잡아 두는 자리입니다. 관계 단계·호감도는
 * 엔딩 판정의 근거라 대상에서 뺐습니다 — 고정하면 판정과 표시가 어긋납니다.
 */
const OVERRIDABLE = [
  { key: "temp", label: "감정 온도" },
  { key: "nickname", label: "호칭" }
];

function autoValue(room, key) {
  if (key === "temp") return stageOf(room.affection).temp;
  return (room.profile && room.profile.nickname) || "";
}

/* 표시·응답에 실제로 쓰이는 값 — 고정돼 있으면 고정값이 이깁니다 */
function stateValue(room, key) {
  const ov = (room.overrides || {})[key];
  return typeof ov === "string" ? ov : autoValue(room, key);
}

function isOverridden(room, key) {
  return typeof (room.overrides || {})[key] === "string";
}

function setOverride(room, key, value) {
  room.overrides = room.overrides || {};
  room.overrides[key] = String(value == null ? "" : value).slice(0, 12);
}

function clearOverride(room, key) {
  if (room.overrides) delete room.overrides[key];
}

function findMemory(room, id) {
  return (room.memories || []).find((m) => m.id === id) || null;
}

/* 핀 토글 — 켜면 그 항목은 장면이 끝나도 줄어들지 않습니다 */
function toggleMemoryPin(room, id) {
  if (!findMemory(room, id)) return;
  room.pins = room.pins || {};
  if (room.pins[id]) delete room.pins[id];
  else room.pins[id] = true;
  rebuildMemories(room);
}

/* 삭제 — 목록에서 빼고, 이후 그 기억을 참조하는 응답도 나오지 않습니다 */
function deleteMemory(room, id) {
  if (!findMemory(room, id)) return;
  room.forgotten = room.forgotten || [];
  if (room.forgotten.indexOf(id) < 0) room.forgotten.push(id);
  if (room.pins) delete room.pins[id];
  rebuildMemories(room);
}

/* 그 후보가 참조하는 기억이 아직 남아 있는가.
 * 삭제·되돌림·분기로 사라진 기억을 참조하는 응답이 나오면 실패이므로(트리: 삭제 기억
 * 재등장 차단), 그런 후보는 쓰지 않고 다음 후보로 넘깁니다. 난수를 쓰지 않으므로
 * 어느 후보로 넘어가는지도 정해져 있습니다. */
function candidateRefsAlive(room, cand) {
  // [주입] ghost-memory — 판정이 늘 「살아 있다」로 답해 지운 기억을 언급하는 응답이
  // 그대로 나갑니다. 목록에서는 사라졌는데 대화에는 다시 나오는 것이 증상입니다
  if (injected("ghost-memory")) return true;
  const refs = (cand && cand.memoryRefs) || [];
  return refs.every((id) => !!findMemory(room, id));
}

/* 시드가 고른 자리에서 시작해 쓸 수 있는 첫 후보를 찾습니다.
 * 못 쓰는 이유는 둘이고 같은 자리에서 함께 봅니다 — 지운 기억을 참조하거나(§7-1),
 * 금칙 토큰이 들었거나(§9-1). 전부 못 쓰면 -1을 돌려주고 호출한 쪽이 응답을 차단합니다. */
function pickCandidate(room, def, at) {
  const n = def.candidates.length;
  let filtered = false;
  for (let i = 0; i < n; i++) {
    const idx = (at + i) % n;
    const cand = def.candidates[idx];
    if (candidateBlocked(cand)) { filtered = true; continue; }
    if (!candidateRefsAlive(room, cand)) { filtered = true; continue; }
    return { at: idx, filtered: filtered };
  }
  return { at: -1, filtered: true };
}

/* ── 세이브/로드 (system-spec §6 · save-schema) ─────────────
 * 시점 슬롯은 방 스코프 상태의 **깊은 복사 스냅샷**입니다. 얕게 복사해 참조를 공유하면
 * 저장 뒤 대화를 이어갈 때 스냅샷까지 함께 변합니다 — 결함 주입의 save-leak이 이것입니다.
 */
const SLOT_COUNT = 4;

function slotOf(room, n) {
  return (room && room.slots && room.slots[n]) || null;
}

function usedSlotCount(room) {
  return room ? Object.keys(room.slots || {}).length : 0;
}

/* 슬롯 목록에 보이는 한 줄 — 무엇을 되돌리는지 열지 않고 읽혀야 합니다 */
function slotSummary(room) {
  const c = findCharacter(room.charId);
  const where = (c && c.startSituation && c.startSituation.label) || room.scenarioId;
  return stageOf(room.affection).name + " · " + room.turn + "턴 · " + where;
}

function saveSlot(room, n) {
  if (!room) return null;
  room.slots = room.slots || {};
  // [주입] save-leak — 깊은 복사 대신 참조를 공유합니다. 저장한 뒤 대화를 이어가면
  // 스냅샷의 메시지·기억까지 함께 변합니다(저장 전후 오염)
  const copy = injected("save-leak") ? (v) => v : deepCopy;
  room.slots[n] = {
    slot: n,
    savedAtDay: VN.sheet.baseDay,          // 가상 시계의 오늘 — 실시각을 쓰지 않습니다
    summary: slotSummary(room),
    room: {
      messages: copy(room.messages),
      affection: room.affection,
      // 재계산의 기준점도 함께 담습니다 — 로드는 이 값으로 복원됩니다(§5-1)
      affectionBase: room.affectionBase || 0,
      affectionBaseTurn: room.affectionBaseTurn || 0,
      temperature: stateValue(room, "temp"),
      nickname: stateValue(room, "nickname"),
      profile: copy(room.profile),
      memories: copy(room.memories || []),            // 표시 확인용 사본
      // 복원의 근거는 유저가 정한 값들입니다 — 목록 자체는 기록에서 다시 세웁니다
      pins: copy(room.pins || {}),
      forgotten: copy(room.forgotten || []),
      overrides: copy(room.overrides || {}),
      seedPath: { seed: VN.seed, turn: room.turn }
    }
  };
  return room.slots[n];
}

/* 슬롯 스냅샷을 방 스코프로 되돌립니다 — 호감도를 그대로 얹지 않고 기준점에 실어
 * 재계산을 통과시킵니다. 얹어 두면 다음 되돌림 때 재계산이 기록만 보고 그 값을 지웁니다. */
function applySnapshot(room, snap) {
  room.messages = deepCopy(snap.room.messages);
  room.pins = deepCopy(snap.room.pins || {});
  room.forgotten = deepCopy(snap.room.forgotten || []);
  room.overrides = deepCopy(snap.room.overrides || {});
  room.profile = deepCopy(snap.room.profile);
  room.affectionBase = snap.room.affectionBase || 0;
  room.affectionBaseTurn = snap.room.affectionBaseTurn || 0;
  recomputeRoom(room);
}

/* 로드 갈래 ① 이 방에 덮어쓰기 — 저장 시점 이후의 대화·상태 변화가 남지 않습니다.
 * 슬롯 목록은 방의 것이므로 로드로 지워지지 않습니다. */
function loadSlotHere(room, n) {
  const snap = slotOf(room, n);
  if (!snap) return null;
  applySnapshot(room, snap);
  return room;
}

/* 로드 갈래 ② 새 방으로 — 이 갈래가 곧 분기입니다. 대화방 한도를 받습니다 */
function loadSlotToNewRoom(room, n) {
  const snap = slotOf(room, n);
  if (!snap) return null;
  return cloneRoomFrom(room, {
    profile: snap.room.profile,
    messages: snap.room.messages,
    // 유저가 정한 값도 스냅샷의 일부입니다 — 빼면 지운 기억이 새 방에서 되살아납니다
    pins: snap.room.pins,
    forgotten: snap.room.forgotten,
    overrides: snap.room.overrides,
    affectionBase: snap.room.affectionBase || 0,
    affectionBaseTurn: snap.room.affectionBaseTurn || 0
  });
}

/* ── 대화 프로필 (system-spec §2) ───────────────────────── */
const PROFILE_LIMIT = 5;

function profilesOf() {
  const acc = currentAccount();
  return acc ? acc.profiles : [];
}

function profileLimitReached() {
  return profilesOf().length >= PROFILE_LIMIT;
}

function addProfile(p) {
  const acc = currentAccount();
  if (!acc) return { ok: false, reason: "미로그인 상태입니다." };
  if (profileLimitReached()) {
    return { ok: false, reason: "프로필은 " + PROFILE_LIMIT + "개까지 만들 수 있습니다." };
  }
  if (!p.name) return { ok: false, reason: "이름은 필수입니다." };
  // 설명란 프롬프트 주입 차단 — 저장에서 막습니다 (system-spec §9-1)
  const inject = profileHasInjection(p);
  if (inject) {
    return { ok: false, kind: "inject", token: inject,
      reason: "설명에 지시문이 들어 있어 저장할 수 없습니다." };
  }
  const id = "p" + (acc.profiles.length + 1);
  acc.profiles.push({
    id: id, name: p.name, nickname: p.nickname || "",
    gender: p.gender || "", desc: p.desc || "", label: p.label || ""
  });
  return { ok: true, id: id };
}

function findProfile(id) {
  return profilesOf().find((p) => p.id === id) || null;
}

/* 대화수 — 유저+AI 메시지 합산, 첫 메시지 포함 (system-spec §5) */
function roomMessageCount(room) {
  return room ? room.messages.length : 0;
}

/* 응답문의 페르소나 슬롯을 채웁니다 — 준수율 계측이 붙잡는 지점입니다 */
function fillSlots(text, room) {
  // 방에 고정된 프로필로 채웁니다 — 계정의 프로필 목록이 바뀌어도 이 방은 그대로입니다.
  // 호칭은 유저가 고정해 두었으면 그 값이 이깁니다 (system-spec §7-2)
  const p = room.profile || {};
  const c = findCharacter(room.charId);
  const nick = stateValue(room, "nickname") || p.name || "당신";
  // [주입] persona-drift — 치환을 무시하고 기본 호칭으로 답합니다 (fault-injection §2)
  if (injected("persona-drift")) {
    return String(text)
      .replace(/\{userName\}/g, "당신")
      .replace(/\{nickname\}/g, "당신")
      .replace(/\{charName\}/g, c ? c.name : "");
  }
  return String(text)
    .replace(/\{userName\}/g, p.name || "당신")
    .replace(/\{nickname\}/g, nick)
    .replace(/\{charName\}/g, c ? c.name : "");
}

/* 키워드 검색 — **페이지 제목과 페이지 카테고리**의 부분일치 (system-spec §8-7).
 * 제작자 검색은 소셜 제외 영역이라 넣지 않습니다.
 * 선택 기준이 따로 없는 목록이라 순서는 체인의 첫 고리인 월간 이용수가 잡습니다(§8-4). */
function searchList() {
  const key = (VN.search || "").trim().toLowerCase();
  if (!key) return [];
  const hit = (c) => {
    const title = (c.pageTitle || "").toLowerCase();
    if (title.indexOf(key) >= 0) return true;
    return (c.pageCategories || []).some((t) => t.toLowerCase().indexOf(key) >= 0);
  };
  return sortChars(visibleCharacters().filter(hit), monthUsage);
}

function findCharacter(id) {
  return VN.sheet.characters.find((c) => c.id === id) || null;
}

/* ── SUT 테스트 인터페이스 ─────────────────────────────────
 * 요소 셀렉터(data-testid) · 상태 조회/제어 · 실행 조건 파라미터 · 데이터 주입
 * 네 갈래 중 뒤의 셋이 여기 있습니다 (청사진 §3).
 */
window.__VN__ = {
  /* 현재 계정·방 스코프 상태 전체를 읽기 전용 사본으로 반환 */
  getState() {
    return deepCopy({
      session: VN.session,
      accountId: VN.accountId,
      screen: VN.screen,
      homeChip: VN.homeChip,
      rankPeriod: VN.rankPeriod,
      rankSort: VN.rankSort,
      catFilter: VN.catFilter,
      catSort: VN.catSort,
      search: VN.search,
      notiOpen: VN.notiOpen,
      loginOpen: VN.loginOpen,
      failNext: VN.failNext,
      noFund: VN.noFund,
      showMetrics: VN.showMetrics,
      editTurn: VN.editTurn,
      confirm: VN.confirm,
      loadPick: VN.loadPick,
      blockedInput: VN.blockedInput,
      blockedOutput: VN.blockedOutput,
      // 막혀서 미뤄 둔 동작 — 로그인 후 이어서 수행됩니다
      pendingAction: pendingIntent ? pendingIntent.action : null,
      pageCharId: VN.pageCharId,
      startProfileId: VN.startProfileId,
      profileCount: profilesOf().length,
      pendingStart: VN.pendingStart,
      seed: VN.seed,
      inject: VN.inject,
      account: currentAccount(),
      // 방 스코프 요약 — 격리 검증은 화면에 나타나지 않으므로 이 통로가 유일한 수단입니다
      room: (() => {
        const r = activeRoom();
        return r ? {
          id: r.id, charId: r.charId, scenarioId: r.scenarioId, turn: r.turn,
          messageCount: roomMessageCount(r), affection: r.affection,
          stage: stageOf(r.affection).name, ending: r.ending,
          ended: r.ended, streaming: !!chatStreaming,
          // 슬롯은 방의 것입니다 — 어느 칸이 찼는지가 격리 검증의 첫 대조점입니다
          savedSlots: Object.keys(r.slots || {}).map(Number).sort(),
          // 기억과 단기 맥락 창 — 창 경계는 화면만으로 대조하기 어려워 여기서도 냅니다
          memories: r.memories || [],
          forgotten: r.forgotten || [],
          // 고정한 상태 값 — 표시가 자동 계산을 따르지 않는 이유가 여기 있습니다
          overrides: r.overrides || {},
          temp: stateValue(r, "temp"),
          nickname: stateValue(r, "nickname"),
          context: contextRange(r)
        } : null;
      })(),
      baseDay: VN.sheet ? VN.sheet.baseDay : null
    });
  },

  /* 슬롯 스냅샷 — 방 스코프가 붙는 다음 슬라이스에서 채웁니다 */
  getSave(slot) {
    const acc = currentAccount();
    if (!acc) return null;
    const room = acc.rooms.find((r) => r.active);
    if (!room || !room.slots) return null;
    return deepCopy(room.slots[slot] || null);
  },

  /* 현재 상태로 화면을 다시 그립니다.
   *
   * 아래 상태 변경 API는 **화면을 자동으로 갱신하지 않습니다.** 데이터가 바뀌었는데 화면이
   * 따라오지 않는 결함이 있을 수 있으므로, 갱신 시점을 도구가 대신 정해 버리면 그 결함을
   * 검증할 수 없습니다. 상태를 바꾼 뒤 무엇을 볼지는 테스트가 정합니다 —
   * 이 함수로 다시 그리거나, 화면을 이동해 확인합니다. */
  refresh() {
    render();
  },

  /* 전체 상태를 초기값으로 — 매 테스트 전 conftest에서 호출합니다.
   * 시작점을 만드는 것이므로 화면도 함께 초기화합니다. */
  reset() {
    VN.session = SESSION.GUEST;
    VN.accountId = null;
    VN.accounts = { a: newAccountState("a"), b: newAccountState("b") };
    VN.sheet = deepCopy(VN_DATA);
    VN.screen = "s2";
    VN.panel = null;
    resetViewState();
    VN.failNext = false;
    VN.noFund = false;
    VN.ledgerFilter = "all";
    VN.showMetrics = false;
    VN.inject = null;
    consoleOpen = false;
    render();
    paintConsole();
  },

  /* 다음 전송 한 번을 생성 실패로 — 서버 오류는 테스트가 일으키는 조건입니다.
   * 사람은 T1 스위치로 같은 값을 켭니다. 화면은 자동 갱신하지 않습니다 */
  failNext(on) {
    VN.failNext = on !== false;
  },

  /* 세션 만료 — 시간 조건을 명시적 트리거로 대체합니다. 화면은 자동 갱신하지 않습니다 */
  expireSession() {
    if (VN.accountId) VN.session = SESSION.EXPIRED;
  },

  /* 데이터 주입 — T1 데이터 시트와 같은 저장소에 씁니다. 화면은 자동 갱신하지 않습니다 */
  setData(table, rows) {
    if (!SHEET_TABLES.includes(table)) {
      throw new Error("알 수 없는 테이블: " + table);
    }
    VN.sheet[table] = deepCopy(rows);
  },

  /* 기준일 변경 — 가상 시계의 "오늘"을 옮깁니다. 화면은 자동 갱신하지 않습니다 */
  setBaseDay(day) {
    VN.sheet.baseDay = day;
  }
};
