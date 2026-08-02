/* T1 디버그 콘솔 — 트리 밖 테스트 설비(청사진 §1 T1 · §4-2)
 *
 * 상단 바의 [디버그] 버튼으로 열리는 모달입니다. 배경은 딤 처리해 상호작용을 막습니다.
 * 셸이 없는 화면(S1)에서는 같은 버튼이 화면 우상단에 단독으로 놓입니다.
 *
 * 이 콘솔은 QA 도구인 동시에 열람자가 보는 화면이라, 자주 쓰는 조작은 입력 필드로 만듭니다.
 * JSON 편집은 폼으로 만들 수 없는 이상 데이터용으로 접어 둡니다.
 * 사람은 이 UI로, 자동화는 __VN__.setData()로 같은 저장소에 씁니다(§3-4).
 */

let consoleOpen = false;
let rawOpen = false;
let editCharId = null;

/* 콘솔만 다시 그립니다. 화면(#app)은 건드리지 않으므로, 여기서 상태를 바꿔도
 * 그 결과가 화면에 언제 나타나는지는 테스터가 [현재 화면 새로고침]이나 화면 이동으로 정합니다. */
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

const DEBUG_NOTICE =
  "해당 디버그는 테스트 환경을 용이하게 세팅하기 위하여 여러 세팅값을 넣었습니다. " +
  "테스트 페이지에서 F5 등 새로고침을 하게 되면 데이터가 기본값으로 초기화되니, " +
  "데이터를 유지한 상태로 계속 페이지를 이용하려면 새로고침 행동은 " +
  "해당 디버그 화면에서 가장 아래에 있는 [현재 화면 새로고침] 버튼으로 설정해 주세요.";

/* 게이팅 상태 5종 — 본인인증을 했는지, 했다면 성인인지가 갈리는 지점입니다.
 * 본인인증 미진행은 나이를 모르는 상태라 언세이프가 막히지만 인증하면 풀립니다.
 * 미성년은 인증으로 나이가 확인된 상태라 해제 수단이 없습니다(system-spec §1-1). */
const STATE_PRESETS = [
  ["미로그인", "guest", () => { logout(); }],
  ["로그인 (본인인증 미진행)", "unverified", () => {
    login("a"); VN.accounts.a.adultVerified = false; VN.screen = "s2";
  }],
  ["로그인 (성인 인증)", "adult", () => {
    login("a"); VN.accounts.a.adultVerified = true; VN.screen = "s2";
  }],
  ["로그인 (미성년)", "minor", () => { login("b"); VN.screen = "s2"; }],
  ["세션 만료", "expired", () => {
    if (!VN.accountId) login("a");
    VN.session = SESSION.EXPIRED;
  }]
];

/* 캐릭터 임의 생성용 풀 — 직접 입력하는 값이 아니라 자리를 채우는 용도입니다 */
const NAME_POOL = ["하윤", "서준", "도경", "시아", "라온", "해든", "윤슬", "가온", "다온", "이레"];
const LINE_POOL = [
  "같은 동아리 선배", "말수 적은 짝꿍", "계약 결혼 상대", "되돌아온 기사",
  "옆집 사는 이웃", "비 오는 날의 우산", "늦은 밤 편의점 알바", "한 번 더 만난 첫사랑"
];

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function nextCharId() {
  let n = VN.sheet.characters.length + 1;
  while (VN.sheet.characters.some((c) => c.id === "c" + n)) n += 1;
  return "c" + n;
}

/* 캐릭터 1개 생성 — 이름·소개·카테고리·태그를 임의로 채웁니다.
 * 생성 결과는 시트에 확정 저장되므로 이후 동작은 결정적입니다.
 * 자동화는 이 버튼을 쓰지 않고 setData()로 명시적 데이터를 넣습니다. */
function addRandomCharacter() {
  const cat = pick(VN.sheet.categories);
  const rows = VN.sheet.characters.slice();
  rows.push({
    id: nextCharId(),
    name: pick(NAME_POOL),
    tagline: pick(LINE_POOL),
    category: cat.name,
    tags: [pick(cat.tags), pick(cat.tags)].filter((v, i, a) => a.indexOf(v) === i),
    safe: true,
    likes: Math.floor(Math.random() * 300),
    reviews: Math.floor(Math.random() * 80),
    score: Math.round((3 + Math.random() * 2) * 10) / 10,
    createdDay: VN.sheet.baseDay,
    // 카드 상세가 읽는 값 — 생성된 캐릭터도 상세를 열 수 있어야 목록 증가를 끝까지 따라갑니다
    firstMessage: "생성된 캐릭터의 첫 메시지입니다. 데이터 시트에서 만든 캐릭터라 내용은 고정 문구입니다.",
    scenarios: [{ id: "sc1", label: "기본 시작점" }]
  });
  window.__VN__.setData("characters", rows);
  paintConsole();
}

/* 이용수 합성 — 이벤트 테이블에서 파생되는 값이라 직접 넣지 않고,
 * 일간·주간·월간 목표치를 만족하는 이벤트를 만들어 채웁니다(청사진 §4-2).
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

/* 로그인 상태에 매인 조작의 게이트 — 계정이 없으면 어느 계정에 반영됐는지 알 수 없으므로
 * 막고 안내만 띄웁니다(청사진 §4-2). 상태 스위처·기준일·캐릭터 표는 계정과 무관해 열려 있습니다. */
function debugNeedsLogin() {
  if (isLoggedIn()) return true;
  toast("로그인하고 이용할 수 있는 기능입니다.");
  return false;
}

function renderDebugButton() {
  return el("button", {
    class: "debug-btn", "data-testid": "g-debug", text: "디버그",
    onclick: () => { consoleOpen = true; paintConsole(); }
  });
}

function block(title, children, badge) {
  const head = badge
    ? el("div", { class: "t1-blockhead" }, [el("h3", { text: title }), badge])
    : el("h3", { text: title });
  return el("div", { class: "t1-block" }, [head].concat(children));
}

/* 지금 어떤 계정으로 보고 있는지 — 계정에 매인 조작이 왜 막히는지 바로 읽히게 합니다 */
function accountStateLabel() {
  if (!isLoggedIn()) return "미로그인";
  if (ACCOUNTS[VN.accountId].minor) return "미성년 계정";
  return currentAccount().adultVerified ? "성인 계정 · 인증 완료" : "성인 계정 · 본인인증 미진행";
}

function field(label, testid, value, type) {
  return el("label", { class: "t1-field" }, [
    el("span", { text: label }),
    el("input", { type: type || "number", "data-testid": testid, value: String(value) })
  ]);
}

function val(testid) {
  const e = document.querySelector('[data-testid="' + testid + '"]');
  return e ? Number(e.value) : 0;
}

/* ── 캐릭터 지표 표 ─────────────────────────────
 * 행=캐릭터, 열=지표. 한 건씩 보면 "누가 위인가"를 기억에 의존하게 되어
 * 랭킹 정렬·동률 체인·최소 표본 조건을 정확히 만들 수 없습니다(청사진 §4-2).
 */
const CHAR_COLS = [
  ["좋아요", "likes"], ["리뷰 수", "reviews"], ["점수", "score"],
  ["일간", "daily"], ["주간", "weekly"], ["월간", "monthly"]
];

function cell(testid, value, step) {
  const i = el("input", { type: "number", "data-testid": testid, value: String(value) });
  if (step) i.setAttribute("step", step);
  return el("td", {}, [i]);
}

function renderCharBlock() {
  const chars = VN.sheet.characters;
  const children = [
    el("div", { class: "t1-row-btns" }, [
      el("button", {
        "data-testid": "t1-char-add", text: "+ 캐릭터 1개 생성",
        onclick: () => addRandomCharacter()
      }),
      el("button", {
        "data-testid": "t1-char-clear", text: "전체 비우기",
        onclick: () => { window.__VN__.setData("characters", []); paintConsole(); }
      })
    ])
  ];

  if (!chars.length) {
    children.push(el("p", { class: "hint", text: "캐릭터가 없습니다. 생성하면 지표를 수정할 수 있습니다." }));
    return block("캐릭터", children);
  }

  const head = el("tr", {}, ["캐릭터", "카테고리", "태그", "생성일", "19세 이상"]
    .concat(CHAR_COLS.map((c) => c[0]))
    .map((h) => el("th", { text: h })));

  const body = chars.map((c) => {
    // 체크 = 19세 이상(언세이프). 내부 플래그는 safe라서 뜻이 뒤집힙니다
    const adult = el("input", {
      type: "checkbox", "data-testid": "t1-row-" + c.id + "-adult"
    });
    adult.checked = c.safe === false;
    const cat = el("select", { class: "t1-cellsel", "data-testid": "t1-row-" + c.id + "-category" },
      VN.sheet.categories.map((g) => el("option", { value: g.name, text: g.name })));
    cat.value = c.category;
    // 태그는 쉼표로 나눠 적습니다. 카테고리에 없는 태그도 넣을 수 있어야
    // "카테고리와 태그가 어긋난 캐릭터"라는 필터 검증 조건을 만들 수 있습니다
    const tags = el("input", {
      type: "text", class: "t1-celltag",
      "data-testid": "t1-row-" + c.id + "-tags", value: (c.tags || []).join(", ")
    });
    // 생성일은 신작 창(60일) 경계를 만드는 값이라 직접 고칠 수 있어야 합니다
    const created = el("input", {
      type: "text", class: "t1-cellday",
      "data-testid": "t1-row-" + c.id + "-created", value: c.createdDay || ""
    });
    return el("tr", {}, [
      el("td", { class: "t1-cname", text: c.name + " (" + c.id + ")" }),
      el("td", {}, [cat]),
      el("td", {}, [tags]),
      el("td", {}, [created]),
      el("td", {}, [adult]),
      cell("t1-row-" + c.id + "-likes", c.likes),
      cell("t1-row-" + c.id + "-reviews", c.reviews),
      cell("t1-row-" + c.id + "-score", c.score, "0.1"),
      cell("t1-row-" + c.id + "-daily", usageCount(c.id, recentDays(1))),
      cell("t1-row-" + c.id + "-weekly", usageCount(c.id, recentDays(7))),
      cell("t1-row-" + c.id + "-monthly", usageCount(c.id, recentDays(30)))
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
  children.push(el("p", { class: "hint", "data-testid": "t1-tag-guide",
    text: "쓸 수 있는 태그 — " + VN.sheet.categories
      .map((g) => g.name + "(" + g.tags.join("·") + ")").join(" / ") }));
  children.push(el("button", {
    class: "primary", "data-testid": "t1-char-apply", text: "표 전체 적용",
    onclick: () => {
      const events = VN.sheet.events.filter(
        (e) => !chars.some((c) => c.id === e.charId));      // 표에 없는 캐릭터 이벤트는 보존
      const next = [];
      for (const c of chars) {
        const d = val("t1-row-" + c.id + "-daily");
        const w = val("t1-row-" + c.id + "-weekly");
        const m = val("t1-row-" + c.id + "-monthly");
        if (w < d || m < w) {
          alert(c.name + " (" + c.id + "): 이용수는 일간 ≤ 주간 ≤ 월간이어야 합니다.");
          return;
        }
        const box = document.querySelector('[data-testid="t1-row-' + c.id + '-adult"]');
        const catSel = document.querySelector('[data-testid="t1-row-' + c.id + '-category"]');
        const tagIn = document.querySelector('[data-testid="t1-row-' + c.id + '-tags"]');
        const dayIn = document.querySelector('[data-testid="t1-row-' + c.id + '-created"]');
        const day = dayIn ? dayIn.value.trim() : "";
        if (day && !/^\d{4}-\d{2}-\d{2}$/.test(day)) {
          alert(c.name + " (" + c.id + "): 생성일은 YYYY-MM-DD 형식으로 적습니다.");
          return;
        }
        next.push(Object.assign({}, c, {
          createdDay: day || c.createdDay,
          category: catSel ? catSel.value : c.category,
          tags: tagIn
            ? tagIn.value.split(",").map((s) => s.trim().replace(/^#/, "")).filter(Boolean)
            : c.tags,
          likes: val("t1-row-" + c.id + "-likes"),
          reviews: val("t1-row-" + c.id + "-reviews"),
          score: val("t1-row-" + c.id + "-score"),
          safe: box ? !box.checked : c.safe          // 체크 = 19세 이상 = safe false
        }));
        events.push.apply(events, synthEvents(c.id, d, w, m));
      }
      VN.sheet.characters = next;                            // 두 테이블을 한 번에 반영
      window.__VN__.setData("events", events);
      paintConsole();
    }
  }));
  return block("캐릭터", children);
}

function renderConsole() {
  if (!consoleOpen) return null;

  const notice = el("p", { class: "t1-notice", "data-testid": "t1-notice", text: DEBUG_NOTICE });

  const switcher = block("상태 스위처", STATE_PRESETS.map(([label, key, fn]) =>
    el("button", {
      "data-testid": "t1-state-" + key, text: label,
      onclick: () => { fn(); paintConsole(); }
    })
  ));

  const acc = currentAccount();
  const adult = block("성인 인증", [
    el("p", {
      class: "hint", "data-testid": "t1-adult-state",
      // 세션이 만료되면 계정 정보가 남아 있어도 인증 상태를 쓸 수 없으므로 미로그인으로 읽습니다
      text: !isLoggedIn() ? "현재: 미로그인"
        : ACCOUNTS[VN.accountId].minor ? "현재: 미성년 (본인인증 완료 · 해제 수단 없음)"
        : acc.adultVerified ? "현재: 성인 인증 완료" : "현재: 본인인증 미진행"
    }),
    el("button", {
      "data-testid": "t1-adult-on", text: "계정 성인 인증 설정",
      onclick: () => {
        if (!debugNeedsLogin()) return;
        const r = setAdultVerified(true);
        if (!r.ok) toast(r.reason);
        paintConsole();
      }
    }),
    el("button", {
      "data-testid": "t1-adult-off", text: "계정 성인 인증 해제",
      onclick: () => {
        if (!debugNeedsLogin()) return;
        const r = setAdultVerified(false);
        if (!r.ok) toast(r.reason);
        paintConsole();
      }
    })
  ]);

  const baseDay = block("기준일 (가상 시계)", [
    el("p", { class: "hint", text: "집계 구간과 데일리 미션 판정의 기준이 되는 \"오늘\"입니다." }),
    el("input", { type: "text", "data-testid": "t1-baseday", value: VN.sheet.baseDay }),
    el("button", {
      "data-testid": "t1-baseday-apply", text: "적용",
      onclick: () => {
        const v = document.querySelector('[data-testid="t1-baseday"]').value.trim();
        if (v) { window.__VN__.setBaseDay(v); paintConsole(); }
      }
    })
  ]);

  const noti = block("알림", [
    el("button", {
      "data-testid": "t1-noti-send", text: "+ 알림 1건 발송",
      onclick: () => {
        if (!debugNeedsLogin()) return;
        const rows = VN.sheet.notifications.slice();
        rows.push({
          id: "n" + (rows.length + 1),
          text: "테스트 알림 " + (rows.length + 1) + "건째",
          day: VN.sheet.baseDay
        });
        window.__VN__.setData("notifications", rows);
        paintConsole();
      }
    }),
    el("button", {
      "data-testid": "t1-noti-clear", text: "알림 비우기",
      onclick: () => {
        if (!debugNeedsLogin()) return;
        window.__VN__.setData("notifications", []);
        paintConsole();
      }
    })
  ]);

  const stats = VN.sheet.accountStats;
  const accountBadge = el("span", {
    class: "t1-badge" + (isLoggedIn() ? " on" : ""),
    "data-testid": "t1-account-state", text: accountStateLabel()
  });
  const account = block("계정 속성", [
    field("팔로워", "t1-followers", stats.followers),
    field("팔로잉", "t1-following", stats.following),
    el("button", {
      "data-testid": "t1-account-apply", text: "적용",
      onclick: () => {
        if (!debugNeedsLogin()) return;
        window.__VN__.setData("accountStats", {
          followers: val("t1-followers"), following: val("t1-following")
        });
        paintConsole();
      }
    })
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
    rawChildren.push(el("p", { class: "hint", text: "폼으로 만들 수 없는 이상 데이터를 넣을 때만 씁니다." }));
    SHEET_TABLES.forEach((table) => {
      const ta = el("textarea", {
        "data-testid": "t1-table-" + table, rows: "4",
        text: JSON.stringify(VN.sheet[table], null, 1)
      });
      rawChildren.push(el("div", { class: "t1-table" }, [
        el("label", { text: table }), ta,
        el("button", {
          "data-testid": "t1-table-" + table + "-apply", text: table + " 적용",
          onclick: () => {
            try { window.__VN__.setData(table, JSON.parse(ta.value)); paintConsole(); }
            catch (e) { alert("JSON 형식 오류: " + e.message); }
          }
        })
      ]));
    });
  }
  const raw = el("div", { class: "t1-block" }, rawChildren);

  const reset = block("초기화", [
    el("button", {
      "data-testid": "t1-reset", text: "전체 초기화 (reset)",
      onclick: () => window.__VN__.reset()   // 시작점을 만드는 것이라 화면도 함께 초기화
    })
  ]);

  const foot = el("div", { class: "t1-foot" }, [
    // 새로고침만 화면을 다시 그립니다. 닫기는 콘솔만 걷어내고 화면은 그대로 둡니다 —
    // 바꾼 상태가 화면에 언제 반영되는지를 테스터가 확인해야 하기 때문입니다.
    el("button", {
      class: "primary", "data-testid": "t1-refresh", text: "현재 화면 새로고침",
      onclick: () => { consoleOpen = false; paintConsole(); render(); }
    }),
    el("button", {
      "data-testid": "t1-close", text: "닫기",
      onclick: () => { consoleOpen = false; paintConsole(); }
    })
  ]);

  // 머리와 발은 고정하고 가운데만 스크롤합니다 — 새로고침·닫기는 언제나 손에 닿아야 합니다
  return el("div", { class: "t1-dim", "data-testid": "t1-dim" }, [
    el("aside", { class: "t1-console", "data-testid": "t1-console" }, [
      el("h2", { text: "디버그 설정" }),
      el("div", { class: "t1-body", "data-testid": "t1-body" }, [
        notice, switcher, adult, baseDay,
        renderCharBlock(), noti, account, raw, reset
      ]),
      foot
    ])
  ]);
}
