/* T1 디버그 콘솔 — 트리 밖 테스트 설비(청사진 §1 T1 · §4-2)
 *
 * 상단 바의 [디버그] 버튼으로 열리는 모달입니다. 배경은 딤 처리해 상호작용을 막습니다.
 * 셸이 없는 화면(S1·S4)에서는 같은 버튼이 화면 안에 단독으로 놓입니다.
 *
 * **초안(draft) 구조** (2026-08-03) — 콘솔에서 만지는 값은 전부 초안에 쌓이고,
 * [저장]을 눌러야 실제 상태에 반영됩니다. 블록마다 [적용]이 흩어져 있으면 무엇이 이미
 * 반영됐는지 화면에서 읽히지 않기 때문입니다.
 *   [저장]              초안을 반영 — 바뀐 값이 없으면 비활성, 있으면 색이 들어옵니다.
 *                       누르면 무엇이 바뀌는지 나열한 재확인 팝업을 먼저 띄웁니다
 *   [닫기]              초안을 버리고 콘솔만 걷습니다 — 데이터·화면 그대로
 *   [현재 화면 새로고침]  **저장된 값** 기준으로 화면을 다시 그립니다
 *
 * 저장해도 화면은 따라오지 않습니다. 그래야 "데이터가 바뀌었는데 화면이 안 따라오는"
 * 결함을 테스터가 직접 확인할 수 있습니다(청사진 §3-2).
 */

let consoleOpen = false;
let rawOpen = false;
let draft = null;          // 콘솔이 열려 있는 동안의 초안
let confirmOpen = false;   // 저장 재확인 팝업

const DEBUG_NOTICE =
  "해당 디버그는 테스트 환경을 용이하게 세팅하기 위하여 여러 세팅값을 넣었습니다. " +
  "값을 바꾼 뒤 [저장]을 눌러야 반영되며, [닫기]는 바꾼 값을 버립니다. " +
  "테스트 페이지에서 F5 등 새로고침을 하면 데이터가 기본값으로 초기화되니, " +
  "데이터를 유지한 채 화면만 다시 그리려면 [현재 화면 새로고침]을 써 주세요.";

/* 게이팅 5상태 — 본인인증을 했는지, 했다면 성인인지가 갈리는 지점입니다.
 * 본인인증 미진행은 나이를 모르는 상태라 언세이프가 막히지만 인증하면 풀립니다.
 * 미성년은 인증으로 나이가 확인된 상태라 해제 수단이 없습니다(system-spec §1-1). */
const STATE_PRESETS = [
  ["미로그인", "guest"],
  ["로그인 (본인인증 미진행)", "unverified"],
  ["로그인 (성인 인증)", "adult"],
  ["로그인 (미성년)", "minor"],
  ["세션 만료", "expired"]
];

const STATE_LABEL = {
  guest: "미로그인", unverified: "로그인 (본인인증 미진행)",
  adult: "로그인 (성인 인증)", minor: "로그인 (미성년)", expired: "세션 만료"
};

/* 캐릭터 임의 생성용 풀 — 직접 입력하는 값이 아니라 자리를 채우는 용도입니다 */
const NAME_POOL = ["하윤", "서준", "도경", "시아", "라온", "해든", "윤슬", "가온", "다온", "이레"];
const LINE_POOL = [
  "같은 동아리 선배", "말수 적은 짝꿍", "계약 결혼 상대", "되돌아온 기사",
  "옆집 사는 이웃", "비 오는 날의 우산", "늦은 밤 편의점 알바", "한 번 더 만난 첫사랑"
];

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

/* ── 초안 ─────────────────────────────────────
 * 이용수는 이벤트에서 파생되는 값이라 초안에는 목표치(일·주·월)로 담고,
 * 저장할 때 조건을 만족하는 이벤트를 합성합니다(청사진 §4-2).
 */
function snapshotDraft() {
  const usage = {};
  VN.sheet.characters.forEach((c) => {
    usage[c.id] = {
      daily: usageCount(c.id, recentDays(1)),
      weekly: usageCount(c.id, recentDays(7)),
      monthly: usageCount(c.id, recentDays(30))
    };
  });
  const acc = currentAccount();
  return {
    gate: gateState(),
    // 재화는 계정 스코프지만 잔액 0·부족 경계를 만들려면 여기서 만질 수 있어야 합니다.
    // 계정이 없을 때는 담지 않습니다 — 0을 담아 두면 저장할 때 그 0이 계정에 덮어써집니다
    wallet: acc ? { free: acc.wallet.free, paid: acc.wallet.paid } : null,
    baseDay: VN.sheet.baseDay,
    characters: deepCopy(VN.sheet.characters),
    usage: usage,
    accountStats: deepCopy(VN.sheet.accountStats),
    notifications: deepCopy(VN.sheet.notifications),
    failNext: !!VN.failNext,
    showMetrics: !!VN.showMetrics
  };
}

function openConsole() {
  draft = snapshotDraft();
  rawOpen = false;
  confirmOpen = false;
  consoleOpen = true;
  paintConsole();
}

function closeConsole() {
  draft = null;              // 초안을 버립니다 — 데이터는 그대로입니다
  confirmOpen = false;
  consoleOpen = false;
  paintConsole();
}

/* 무엇이 바뀌는지 사람이 읽을 수 있는 줄로 만듭니다 — 저장 전 재확인 팝업의 내용입니다 */
function describeChanges() {
  const out = [];
  if (!draft) return out;
  if (draft.gate !== gateState()) {
    out.push("상태 — " + STATE_LABEL[gateState()] + " → " + STATE_LABEL[draft.gate]);
  }
  if (draft.baseDay !== VN.sheet.baseDay) {
    out.push("기준일 — " + VN.sheet.baseDay + " → " + draft.baseDay);
  }
  const before = VN.sheet.characters;
  const added = draft.characters.filter((c) => !before.some((b) => b.id === c.id));
  const removed = before.filter((b) => !draft.characters.some((c) => c.id === b.id));
  if (added.length) out.push("캐릭터 추가 — " + added.map((c) => c.name + "(" + c.id + ")").join(", "));
  if (removed.length) out.push("캐릭터 삭제 — " + removed.map((c) => c.name + "(" + c.id + ")").join(", "));

  const FIELDS = [["pageTitle", "페이지 제목"], ["pageSubtitle", "보조 설명"],
    ["category", "카테고리"], ["createdDay", "생성일"], ["likes", "좋아요"],
    ["reviews", "리뷰 수"], ["score", "점수"]];
  draft.characters.forEach((c) => {
    const b = before.find((x) => x.id === c.id);
    if (!b) return;
    FIELDS.forEach(([k, label]) => {
      if (String(b[k]) !== String(c[k])) {
        out.push(c.name + " " + label + " — " + b[k] + " → " + c[k]);
      }
    });
    if ((b.tags || []).join(",") !== (c.tags || []).join(",")) {
      out.push(c.name + " 태그 — " + (b.tags || []).join("·") + " → " + (c.tags || []).join("·"));
    }
    if (b.safe !== c.safe) {
      out.push(c.name + " 19세 이상 — " + (b.safe === false ? "예" : "아니오")
        + " → " + (c.safe === false ? "예" : "아니오"));
    }
    const u = draft.usage[c.id];
    if (!u) return;
    [["daily", "일간"], ["weekly", "주간"], ["monthly", "월간"]].forEach(([k, label]) => {
      const was = usageCount(c.id, recentDays(k === "daily" ? 1 : k === "weekly" ? 7 : 30));
      if (was !== u[k]) out.push(c.name + " 이용수(" + label + ") — " + was + " → " + u[k]);
    });
  });

  if (draft.notifications.length !== VN.sheet.notifications.length) {
    out.push("알림 — " + VN.sheet.notifications.length + "건 → " + draft.notifications.length + "건");
  }
  const s0 = VN.sheet.accountStats, s1 = draft.accountStats;
  if (s0.followers !== s1.followers) out.push("팔로워 — " + s0.followers + " → " + s1.followers);
  if (s0.following !== s1.following) out.push("팔로잉 — " + s0.following + " → " + s1.following);
  const acc0 = currentAccount();
  if (acc0 && draft.wallet) {
    if (acc0.wallet.free !== draft.wallet.free) {
      out.push("캔디 — " + acc0.wallet.free + " → " + draft.wallet.free);
    }
    if (acc0.wallet.paid !== draft.wallet.paid) {
      out.push("크리스탈 — " + acc0.wallet.paid + " → " + draft.wallet.paid);
    }
  }
  if (!!VN.showMetrics !== !!draft.showMetrics) {
    out.push("카드 지표 표시 — " + (VN.showMetrics ? "켜짐" : "꺼짐")
      + " → " + (draft.showMetrics ? "켜짐" : "꺼짐"));
  }
  if (!!VN.failNext !== !!draft.failNext) {
    out.push("다음 응답 생성 실패 — " + (VN.failNext ? "켜짐" : "꺼짐")
      + " → " + (draft.failNext ? "켜짐" : "꺼짐"));
  }
  return out;
}

function hasChanges() {
  return describeChanges().length > 0;
}

/* 이용수 합성 — 목표치를 만족하는 이벤트를 만들어 채웁니다(청사진 §4-2).
 * 한 캐릭터분 이벤트 배열만 돌려주고, 저장은 호출한 쪽이 한 번에 합니다. */
function synthEvents(charId, daily, weekly, monthly) {
  const days30 = recentDays(30);
  const rows = [];
  let u = 0;
  const put = (day, count) => {
    for (let i = 0; i < count; i++) rows.push({ user: charId + "-gen" + (u++), charId: charId, day: day });
  };
  put(days30[0], daily);                                    // 기준일 당일
  let rest = weekly - daily;
  for (let i = 1; i <= 6 && rest > 0; i++) {                 // 최근 7일(당일 제외)
    const n = Math.ceil(rest / (7 - i));
    put(days30[i], n);
    rest -= n;
  }
  rest = monthly - weekly;
  for (let i = 7; i <= 29 && rest > 0; i++) {                // 최근 30일(7일 제외)
    const n = Math.ceil(rest / (30 - i));
    put(days30[i], n);
    rest -= n;
  }
  return rows;
}

/* 초안을 실제 상태에 반영합니다 — 화면은 자동으로 갱신하지 않습니다 */
function commitDraft() {
  // 상태 스위처 — 세션은 시트 데이터가 아니라 계정 스코프라 여기서 전환합니다
  if (draft.gate !== gateState()) {
    if (draft.gate === "guest") logout();
    else if (draft.gate === "minor") { login("b"); VN.screen = "s2"; }
    else if (draft.gate === "expired") { if (!VN.accountId) login("a"); VN.session = SESSION.EXPIRED; }
    else { login("a"); VN.accounts.a.adultVerified = draft.gate === "adult"; VN.screen = "s2"; }
  }
  window.__VN__.setBaseDay(draft.baseDay);

  // 이용수는 이벤트로 합성합니다. 표에 없는 캐릭터의 이벤트는 건드리지 않습니다
  const keep = VN.sheet.events.filter(
    (e) => !draft.characters.some((c) => c.id === e.charId));
  const events = keep.slice();
  draft.characters.forEach((c) => {
    const u = draft.usage[c.id] || { daily: 0, weekly: 0, monthly: 0 };
    events.push.apply(events, synthEvents(c.id, u.daily, u.weekly, u.monthly));
  });
  window.__VN__.setData("characters", draft.characters);
  window.__VN__.setData("events", events);
  window.__VN__.setData("accountStats", draft.accountStats);
  window.__VN__.setData("notifications", draft.notifications);
  const acc = currentAccount();
  if (acc && draft.wallet) {
    acc.wallet.free = draft.wallet.free;
    acc.wallet.paid = draft.wallet.paid;
  }
  VN.failNext = !!draft.failNext;
  VN.showMetrics = !!draft.showMetrics;

  draft = snapshotDraft();      // 저장 뒤에는 초안과 실제가 같아집니다
  confirmOpen = false;
  paintConsole();
}

/* 콘솔만 다시 그립니다. 화면(#app)은 건드리지 않으므로, 여기서 값을 바꾸고 저장해도
 * 그 결과가 화면에 언제 나타나는지는 테스터가 [현재 화면 새로고침]으로 정합니다. */
function paintConsole() {
  const host = document.getElementById("debug");
  const prev = host.querySelector(".t1-body");
  const keep = prev ? prev.scrollTop : null;
  host.innerHTML = "";
  const node = renderConsole();
  if (node) host.appendChild(node);
  if (keep !== null) {
    const next = host.querySelector(".t1-body");
    if (next) next.scrollTop = keep;
  }
}

/* 값 하나를 고쳤을 때 — 콘솔 전체를 다시 그리면 커서가 튀므로 저장 버튼만 손봅니다 */
function touchDraft() {
  const save = document.querySelector('[data-testid="t1-save"]');
  if (!save) return;
  const on = hasChanges();
  save.disabled = !on;
  save.className = on ? "primary" : "";
}

function nextCharId() {
  let n = draft.characters.length + 1;
  while (draft.characters.some((c) => c.id === "c" + n)) n += 1;
  return "c" + n;
}

/* 캐릭터 1개 생성 — 이름·소개·카테고리·태그를 임의로 채웁니다.
 * 초안에만 쌓이고 [저장]에서 시트로 갑니다. */
function addRandomCharacter() {
  const cat = pick(VN.sheet.categories);
  const id = nextCharId();
  draft.characters.push({
    id: id,
    name: pick(NAME_POOL),
    tagline: pick(LINE_POOL),
    pageTitle: "생성된 작품 " + id,
    pageSubtitle: "데이터 시트에서 만든 작품입니다.",
    pageStory: "테스트용으로 생성한 작품이라 줄거리는 고정 문구입니다.",
    charDesc: "테스트용으로 생성한 캐릭터입니다.",
    category: cat.name,
    tags: [pick(cat.tags), pick(cat.tags)].filter((v, i, a) => a.indexOf(v) === i),
    safe: true,
    likes: Math.floor(Math.random() * 300),
    reviews: Math.floor(Math.random() * 80),
    score: Math.round((3 + Math.random() * 2) * 10) / 10,
    createdDay: draft.baseDay,
    creator: { name: "테스트 제작자", followers: 0 },
    updatedDay: draft.baseDay, version: "v1.0",
    // 카드 상세가 읽는 값 — 생성된 캐릭터도 대화가 성립해야 목록 증가를 끝까지 따라갑니다
    firstMessage: "생성된 캐릭터의 첫 메시지입니다. 데이터 시트에서 만든 캐릭터라 내용은 고정 문구입니다.",
    startSituation: { id: "sc1", label: "기본 시작점" }
  });
  draft.usage[id] = { daily: 0, weekly: 0, monthly: 0 };
  paintConsole();
}

function renderDebugButton() {
  return el("button", {
    class: "debug-btn", "data-testid": "g-debug", text: "디버그",
    onclick: () => openConsole()
  });
}

function block(title, children, badge) {
  const head = badge
    ? el("div", { class: "t1-blockhead" }, [el("h3", { text: title }), badge])
    : el("h3", { text: title });
  return el("div", { class: "t1-block" }, [head].concat(children));
}

/* 초안 기준의 계정 상태 — 계정에 매인 조작이 왜 막히는지 바로 읽히게 합니다 */
function draftAccountLabel() {
  return STATE_LABEL[draft.gate] || draft.gate;
}

function draftLoggedIn() {
  return draft.gate === "unverified" || draft.gate === "adult" || draft.gate === "minor";
}

/* 로그인 상태에 매인 조작의 게이트 — 계정이 없으면 어느 계정에 반영됐는지 알 수 없으므로
 * 막고 안내만 띄웁니다(청사진 §4-2). 상태 스위처·기준일·캐릭터 표는 계정과 무관해 열려 있습니다. */
function debugNeedsLogin() {
  if (draftLoggedIn()) return true;
  toast("로그인 상태에서 쓸 수 있는 항목입니다.");
  return false;
}

function field(label, testid, value, onchange) {
  const input = el("input", {
    type: "number", "data-testid": testid, value: String(value),
    oninput: (e) => { onchange(Number(e.target.value) || 0); touchDraft(); }
  });
  return el("label", { class: "t1-field" }, [el("span", { text: label }), input]);
}

/* ── 캐릭터 지표 표 ─────────────────────────────
 * 행=캐릭터, 열=지표. 한 건씩 보면 "누가 위인가"를 기억에 의존하게 되어
 * 랭킹 정렬·동률 체인·최소 표본 조건을 정확히 만들 수 없습니다(청사진 §4-2).
 */
const CHAR_COLS = [["좋아요", "likes"], ["리뷰 수", "reviews"], ["점수", "score"]];
const USAGE_COLS = [["일간", "daily"], ["주간", "weekly"], ["월간", "monthly"]];

function numCell(testid, value, onchange, step) {
  const i = el("input", {
    type: "number", "data-testid": testid, value: String(value),
    oninput: (e) => { onchange(Number(e.target.value) || 0); touchDraft(); }
  });
  if (step) i.setAttribute("step", step);
  return el("td", {}, [i]);
}

function renderCharBlock() {
  const chars = draft.characters;
  const children = [
    el("div", { class: "t1-row-btns" }, [
      el("button", {
        "data-testid": "t1-char-add", text: "+ 캐릭터 1개 생성",
        onclick: () => addRandomCharacter()
      }),
      el("button", {
        "data-testid": "t1-char-clear", text: "전체 비우기",
        onclick: () => { draft.characters = []; draft.usage = {}; paintConsole(); }
      })
    ])
  ];

  if (!chars.length) {
    children.push(el("p", { class: "hint", text: "캐릭터가 없습니다. 생성하면 지표를 수정할 수 있습니다." }));
    return block("캐릭터", children);
  }

  const head = el("tr", {}, ["캐릭터", "페이지 제목", "보조 설명", "mock", "카테고리", "태그", "생성일", "19세 이상"]
    .concat(CHAR_COLS.map((c) => c[0])).concat(USAGE_COLS.map((c) => c[0]))
    .map((h) => el("th", { text: h })));

  const body = chars.map((c) => {
    // 체크 = 19세 이상(언세이프). 내부 플래그는 safe라서 뜻이 뒤집힙니다
    const adult = el("input", {
      type: "checkbox", "data-testid": "t1-row-" + c.id + "-adult",
      onchange: (e) => { c.safe = !e.target.checked; touchDraft(); }
    });
    adult.checked = c.safe === false;
    const cat = el("select", {
      class: "t1-cellsel", "data-testid": "t1-row-" + c.id + "-category",
      onchange: (e) => { c.category = e.target.value; touchDraft(); }
    }, VN.sheet.categories.map((g) => el("option", { value: g.name, text: g.name })));
    cat.value = c.category;
    // 태그는 쉼표로 나눠 적습니다. 카테고리에 없는 태그도 넣을 수 있어야
    // "카테고리와 태그가 어긋난 캐릭터"라는 필터 검증 조건을 만들 수 있습니다
    const tags = el("input", {
      type: "text", class: "t1-celltag",
      "data-testid": "t1-row-" + c.id + "-tags", value: (c.tags || []).join(", "),
      oninput: (e) => {
        c.tags = e.target.value.split(",").map((s) => s.trim().replace(/^#/, "")).filter(Boolean);
        touchDraft();
      }
    });
    // 생성일은 신작 창(60일) 경계를 만드는 값이라 직접 고칠 수 있어야 합니다
    const created = el("input", {
      type: "text", class: "t1-cellday",
      "data-testid": "t1-row-" + c.id + "-created", value: c.createdDay || "",
      oninput: (e) => { c.createdDay = e.target.value.trim(); touchDraft(); }
    });
    // 어느 mock 세트로 말하는지 — 화면에서 읽히지 않으면 "이 캐릭터만 대사가 다르다"를
    // 결함으로 오인합니다 (mock-llm-spec §2-1)
    const dedicated = hasDedicatedMock(c.id);
    const u = draft.usage[c.id] || (draft.usage[c.id] = { daily: 0, weekly: 0, monthly: 0 });
    const title = el("input", {
      type: "text", class: "t1-celltitle", maxlength: String(PAGE_TITLE_MAX),
      "data-testid": "t1-row-" + c.id + "-title", value: c.pageTitle || "",
      oninput: (e) => {
        if (e.target.value.length > PAGE_TITLE_MAX) e.target.value = e.target.value.slice(0, PAGE_TITLE_MAX);
        c.pageTitle = e.target.value; touchDraft();
      }
    });
    const sub = el("input", {
      type: "text", class: "t1-cellsub", maxlength: String(PAGE_SUB_MAX),
      "data-testid": "t1-row-" + c.id + "-subtitle", value: c.pageSubtitle || "",
      oninput: (e) => {
        if (e.target.value.length > PAGE_SUB_MAX) e.target.value = e.target.value.slice(0, PAGE_SUB_MAX);
        c.pageSubtitle = e.target.value; touchDraft();
      }
    });
    return el("tr", {}, [
      el("td", { class: "t1-cname", text: c.name + " (" + c.id + ")" }),
      el("td", {}, [title]),
      el("td", {}, [sub]),
      el("td", {}, [el("span", {
        class: "t1-badge" + (dedicated ? " on" : ""),
        "data-testid": "t1-row-" + c.id + "-mock",
        text: dedicated ? "전용" : "공통"
      })]),
      el("td", {}, [cat]),
      el("td", {}, [tags]),
      el("td", {}, [created]),
      el("td", {}, [adult]),
      numCell("t1-row-" + c.id + "-likes", c.likes, (v) => { c.likes = v; }),
      numCell("t1-row-" + c.id + "-reviews", c.reviews, (v) => { c.reviews = v; }),
      numCell("t1-row-" + c.id + "-score", c.score, (v) => { c.score = v; }, "0.1"),
      numCell("t1-row-" + c.id + "-daily", u.daily, (v) => { u.daily = v; }),
      numCell("t1-row-" + c.id + "-weekly", u.weekly, (v) => { u.weekly = v; }),
      numCell("t1-row-" + c.id + "-monthly", u.monthly, (v) => { u.monthly = v; })
    ]);
  });

  children.push(el("div", { class: "t1-tablewrap" }, [
    el("table", { class: "t1-table-grid", "data-testid": "t1-char-table" }, [
      el("thead", {}, [head]), el("tbody", {}, body)
    ])
  ]));
  children.push(el("p", { class: "hint",
    text: "이용수는 이벤트를 합성해 맞춥니다 (일간 ≤ 주간 ≤ 월간) · 태그는 쉼표로 구분합니다"
      + " · 생성일을 기준일에서 " + NEW_WINDOW_DAYS + "일보다 앞으로 옮기면 신작 섹션에서 빠집니다" }));
  children.push(el("p", { class: "hint",
    text: "mock — 전용 세트는 하루(c1)뿐이고 나머지와 새로 만든 캐릭터는 공통 세트로 말합니다" }));
  children.push(el("p", { class: "hint", "data-testid": "t1-tag-guide",
    text: "쓸 수 있는 태그 — " + VN.sheet.categories
      .map((g) => g.name + "(" + g.tags.join("·") + ")").join(" / ") }));
  return block("캐릭터", children);
}

/* 저장 전 재확인 — 무엇이 바뀌는지 먼저 읽고 누르게 합니다 */
function renderConfirm() {
  const lines = describeChanges();
  return el("div", { class: "t1-confirm-dim", "data-testid": "t1-confirm" }, [
    el("div", { class: "t1-confirm-box" }, [
      el("h3", { text: "다음 내용을 반영할까요?" }),
      el("ul", { class: "t1-confirm-list", "data-testid": "t1-confirm-list" },
        lines.map((t) => el("li", { text: t }))),
      el("p", { class: "hint", text: "저장해도 화면은 그대로입니다 — [현재 화면 새로고침]으로 반영합니다." }),
      el("div", { class: "t1-confirm-btns" }, [
        el("button", { "data-testid": "t1-confirm-cancel", text: "취소",
          onclick: () => { confirmOpen = false; paintConsole(); } }),
        el("button", { class: "primary", "data-testid": "t1-confirm-ok", text: "반영",
          onclick: () => commitDraft() })
      ])
    ])
  ]);
}

function renderConsole() {
  if (!consoleOpen) return null;

  const notice = el("p", { class: "t1-notice", "data-testid": "t1-notice", text: DEBUG_NOTICE });

  const switcher = block("상태 스위처", STATE_PRESETS.map(([label, key]) =>
    el("button", {
      class: draft.gate === key ? "primary" : "",
      "data-testid": "t1-state-" + key, text: label,
      onclick: () => { draft.gate = key; paintConsole(); }
    })
  ));

  const adult = block("성인 인증", [
    el("p", { class: "hint", "data-testid": "t1-adult-state", text: "현재: " + draftAccountLabel() }),
    el("button", {
      "data-testid": "t1-adult-on", text: "계정 성인 인증 설정",
      onclick: () => {
        if (!debugNeedsLogin()) return;
        if (draft.gate === "minor") { toast("미성년 계정은 성인 인증을 할 수 없습니다."); return; }
        draft.gate = "adult"; paintConsole();
      }
    }),
    el("button", {
      "data-testid": "t1-adult-off", text: "계정 성인 인증 해제",
      onclick: () => {
        if (!debugNeedsLogin()) return;
        if (draft.gate === "minor") { toast("미성년 계정은 인증 상태를 바꿀 수 없습니다."); return; }
        draft.gate = "unverified"; paintConsole();
      }
    })
  ]);

  const baseDay = block("기준일 (가상 시계)", [
    el("p", { class: "hint", text: "집계 구간과 데일리 미션 판정의 기준이 되는 \"오늘\"입니다." }),
    el("input", {
      type: "text", "data-testid": "t1-baseday", value: draft.baseDay,
      oninput: (e) => { draft.baseDay = e.target.value.trim(); touchDraft(); }
    })
  ]);

  // 생성 실패는 mock 세트의 fail 후보로도 나지만(시드 1·5턴), 사람이 잔액 미차감을
  // 확인할 때마다 다섯 번 전송해야 하므로 1회성 스위치를 둡니다(청사진 §4-2)
  const failSwitch = block("응답 생성", [
    el("p", { class: "hint", text: "다음 전송 한 번만 생성 실패로 만듭니다. 재화 미차감 확인용입니다." }),
    el("button", {
      class: draft.failNext ? "primary" : "",
      "data-testid": "t1-fail-next",
      text: draft.failNext ? "다음 응답 생성 실패 — 켜짐" : "다음 응답 생성 실패 — 꺼짐",
      onclick: () => { draft.failNext = !draft.failNext; paintConsole(); }
    })
  ]);

  const walletBadge = el("span", {
    class: "t1-badge" + (draftLoggedIn() ? " on" : ""),
    text: draftLoggedIn() ? "계정에 반영" : "로그인 필요"
  });
  const walletKids = [
    el("p", { class: "hint",
      text: "잔액 0·부족 경계를 만드는 자리입니다. 전송 1회는 캔디 " + SEND_COST
        + "이 들고, 캔디가 모자라면 크리스탈에서 채웁니다." })
  ];
  if (draft.wallet) {
    walletKids.push(field("캔디(무료)", "t1-wallet-free", draft.wallet.free,
      (v) => { draft.wallet.free = v; }));
    walletKids.push(field("크리스탈(유료)", "t1-wallet-paid", draft.wallet.paid,
      (v) => { draft.wallet.paid = v; }));
  } else {
    // 계정이 없으면 어느 계정의 잔액인지 정할 수 없습니다 — 먼저 로그인 상태로 저장한 뒤 만집니다
    walletKids.push(el("p", { class: "hint", "data-testid": "t1-wallet-locked",
      text: "로그인 상태에서 만질 수 있습니다. 상태 스위처로 로그인하고 [저장]한 뒤 다시 열어 주세요." }));
  }
  const wallet = block("재화 (계정 스코프)", walletKids, walletBadge);

  // 카드에서 정렬 근거를 확인할 때만 켭니다 — 평소 화면은 서비스 그대로 둡니다
  const metrics = block("카드 지표 표시", [
    el("p", { class: "hint",
      text: "켜면 목록 카드에 좋아요·리뷰·이용수(랭킹에서는 정렬 기준값)가 한 줄 붙습니다." }),
    el("button", {
      class: draft.showMetrics ? "primary" : "",
      "data-testid": "t1-show-metrics",
      text: draft.showMetrics ? "카드 지표 — 켜짐" : "카드 지표 — 꺼짐",
      onclick: () => { draft.showMetrics = !draft.showMetrics; paintConsole(); }
    })
  ]);

  const noti = block("알림", [
    el("button", {
      "data-testid": "t1-noti-send", text: "+ 알림 1건 발송",
      onclick: () => {
        if (!debugNeedsLogin()) return;
        draft.notifications.push({
          id: "n" + (draft.notifications.length + 1),
          text: "테스트 알림 " + (draft.notifications.length + 1) + "건째",
          day: draft.baseDay
        });
        paintConsole();
      }
    }),
    el("button", {
      "data-testid": "t1-noti-clear", text: "알림 비우기",
      onclick: () => {
        if (!debugNeedsLogin()) return;
        draft.notifications = [];
        paintConsole();
      }
    })
  ]);

  const accountBadge = el("span", {
    class: "t1-badge" + (draftLoggedIn() ? " on" : ""),
    "data-testid": "t1-account-state", text: draftAccountLabel()
  });
  const account = block("계정 속성", [
    field("팔로워", "t1-followers", draft.accountStats.followers,
      (v) => { draft.accountStats.followers = v; }),
    field("팔로잉", "t1-following", draft.accountStats.following,
      (v) => { draft.accountStats.following = v; })
  ], accountBadge);

  // 원본 편집 — 폼으로 만들 수 없는 이상 데이터(형식 위반·극단값)용
  const rawChildren = [
    el("button", {
      class: "t1-toggle", "data-testid": "t1-raw-toggle",
      text: (rawOpen ? "▾ " : "▸ ") + "원본 편집 (JSON)",
      onclick: () => { rawOpen = !rawOpen; paintConsole(); }
    })
  ];
  if (rawOpen) {
    rawChildren.push(el("p", { class: "hint", text: "폼으로 만들 수 없는 이상 데이터를 넣을 때만 씁니다. 이것도 [저장]을 눌러야 반영됩니다." }));
    ["characters", "accountStats", "notifications"].forEach((table) => {
      const ta = el("textarea", {
        "data-testid": "t1-table-" + table, rows: "4",
        text: JSON.stringify(draft[table], null, 1)
      });
      rawChildren.push(el("div", { class: "t1-table" }, [
        el("label", { text: table }), ta,
        el("button", {
          "data-testid": "t1-table-" + table + "-apply", text: table + " 초안에 넣기",
          onclick: () => {
            try { draft[table] = JSON.parse(ta.value); paintConsole(); }
            catch (e) { alert("JSON 형식 오류: " + e.message); }
          }
        })
      ]));
    });
  }
  const raw = el("div", { class: "t1-block" }, rawChildren);

  const reset = block("초기화", [
    el("p", { class: "hint", text: "테스트 시작점을 만드는 동작이라 초안을 거치지 않고 즉시 실행됩니다." }),
    el("button", {
      "data-testid": "t1-reset", text: "전체 초기화 (reset)",
      onclick: () => { window.__VN__.reset(); draft = snapshotDraft(); paintConsole(); }
    })
  ]);

  const changed = hasChanges();
  const save = el("button", {
    class: changed ? "primary" : "", "data-testid": "t1-save", text: "저장",
    onclick: () => { confirmOpen = true; paintConsole(); }
  });
  save.disabled = !changed;

  const foot = el("div", { class: "t1-foot" }, [
    save,
    // 새로고침만 화면을 다시 그립니다 — 저장된 값 기준입니다
    el("button", {
      "data-testid": "t1-refresh", text: "현재 화면 새로고침",
      onclick: () => { render(); }
    }),
    el("button", {
      "data-testid": "t1-close", text: "닫기",
      onclick: () => closeConsole()
    })
  ]);

  // 머리와 발은 고정하고 가운데만 스크롤합니다 — 저장·새로고침·닫기는 언제나 손에 닿아야 합니다
  return el("div", { class: "t1-dim", "data-testid": "t1-dim" }, [
    el("aside", { class: "t1-console", "data-testid": "t1-console" }, [
      el("h2", { text: "디버그 설정" }),
      el("div", { class: "t1-body", "data-testid": "t1-body" }, [
        notice, switcher, adult, baseDay, wallet, failSwitch, metrics,
        renderCharBlock(), noti, account, raw, reset
      ]),
      foot
    ]),
    confirmOpen ? renderConfirm() : null
  ]);
}
