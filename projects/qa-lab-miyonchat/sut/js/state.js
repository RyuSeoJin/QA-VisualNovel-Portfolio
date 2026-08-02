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
    persona: null,                            // { name, nickname, gender, desc }
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

/* 보호 동작 차단 — 만료 상태에서는 전송·저장·수령이 모두 막힙니다 */
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

function logout() {
  // 앞 계정의 데이터가 화면·저장소 어디에도 남지 않아야 합니다
  VN.accountId = null;
  VN.session = SESSION.GUEST;
  VN.screen = "s2";          // 미로그인 상태의 홈으로 복귀
  VN.panel = null;
  VN.homeChip = "추천";
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
      seed: VN.seed,
      inject: VN.inject,
      account: currentAccount(),
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

  /* 전체 상태를 초기값으로 — 매 테스트 전 conftest에서 호출합니다 */
  reset() {
    VN.session = SESSION.GUEST;
    VN.accountId = null;
    VN.accounts = { a: newAccountState("a"), b: newAccountState("b") };
    VN.sheet = deepCopy(VN_DATA);
    VN.screen = "s2";
    VN.panel = null;
    VN.homeChip = "추천";
    VN.inject = null;
    render();
  },

  /* 세션 만료 — 시간 조건을 명시적 트리거로 대체합니다 */
  expireSession() {
    if (VN.accountId) VN.session = SESSION.EXPIRED;
    render();
  },

  /* 데이터 주입 — T1 데이터 시트와 같은 저장소에 씁니다 */
  setData(table, rows) {
    if (!SHEET_TABLES.includes(table)) {
      throw new Error("알 수 없는 테이블: " + table);
    }
    VN.sheet[table] = deepCopy(rows);
    render();
  },

  /* 기준일 변경 — 가상 시계의 "오늘"을 옮깁니다 */
  setBaseDay(day) {
    VN.sheet.baseDay = day;
    render();
  }
};
