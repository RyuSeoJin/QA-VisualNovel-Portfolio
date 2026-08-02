/* 화면 렌더 — 첫 슬라이스는 전역 셸 + S1 로그인 + 탭 자리표시자입니다.
 * data-testid 명명은 {화면}-{요소}[-{수식어}] kebab-case (청사진 §3-1).
 */

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  for (const k in attrs || {}) {
    if (k === "text") node.textContent = attrs[k];
    else if (k === "html") node.innerHTML = attrs[k];
    else if (k === "onclick") node.addEventListener("click", attrs[k]);
    else if (k === "onchange") node.addEventListener("change", attrs[k]);
    else if (k === "onkeydown") node.addEventListener("keydown", attrs[k]);
    else if (k === "oninput") node.addEventListener("input", attrs[k]);
    else node.setAttribute(k, attrs[k]);
  }
  (children || []).forEach((c) => c && node.appendChild(c));
  return node;
}

/* 안내 토스트 — 3초 후 사라집니다.
 * #app 밖(body)에 붙여서 화면을 다시 그려도 살아남게 합니다. */
function toast(message) {
  const old = document.querySelector('[data-testid="g-toast"]');
  if (old) old.remove();
  const t = el("div", { class: "toast", "data-testid": "g-toast", text: message });
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

/* 로그인 모달 — 셸 안에서 막혔을 때 뜹니다. 뒤 화면은 그대로 남고, 로그인하면
 * 막혔던 동작을 이어서 수행합니다(system-spec §1-1). */
function renderLoginModal() {
  return el("div", { class: "login-modal", "data-testid": "g-login-modal" }, [
    el("div", { class: "login-box" }, [
      el("div", { class: "panel-head" }, [
        el("h2", { text: "로그인" }),
        el("button", {
          class: "panel-close", "data-testid": "g-login-close", text: "✕",
          onclick: () => closeLogin()
        })
      ]),
      el("p", {
        class: "lede", "data-testid": "g-login-notice",
        text: "로그인하고 이용할 수 있는 기능입니다. 로그인하면 하려던 동작을 이어서 진행합니다."
      }),
      el("button", {
        class: "account", "data-testid": "g-login-a",
        text: ACCOUNTS.a.label, onclick: () => signIn("a")
      }),
      el("button", {
        class: "account", "data-testid": "g-login-b",
        text: ACCOUNTS.b.label, onclick: () => signIn("b")
      })
    ])
  ]);
}

/* S1 로그인 — 보호 화면에 URL로 직접 들어왔을 때 뜨는 화면(뒤에 깔 화면이 없는 경우).
 * 로그인하면 원래 하려던 곳으로 이어집니다(system-spec §1-1). */
function renderS1() {
  const pick = (id) => signIn(id);
  return el("section", { class: "screen s1" }, [
    // 셸이 없는 화면이므로 디버그 버튼을 우상단에 단독 배치합니다(청사진 §1 T1)
    el("div", { class: "s1-debug" }, [renderDebugButton()]),
    el("h1", { class: "brand", text: "MiyonChat" }),
    el("p", { class: "lede", "data-testid": "s1-notice",
      text: "이 기능은 로그인이 필요합니다. 계정을 선택해 주세요." }),
    el("button", {
      class: "account", "data-testid": "s1-account-a",
      text: ACCOUNTS.a.label, onclick: () => pick("a")
    }),
    el("button", {
      class: "account", "data-testid": "s1-account-b",
      text: ACCOUNTS.b.label, onclick: () => pick("b")
    }),
    el("button", {
      class: "link", "data-testid": "s1-back-home",
      text: "로그인 없이 둘러보기", onclick: () => go("s2")
    })
  ]);
}

/* 재화 부족 안내 — 전송이 막힌 이유와 다음 행동을 함께 보여 줍니다 (system-spec §3) */
function renderNoFundModal() {
  return el("div", { class: "modal", "data-testid": "g-nofund-modal" }, [
    el("div", { class: "modal-box" }, [
      el("h3", { class: "nf-title", "data-testid": "g-nofund-title", text: "재화가 부족합니다." }),
      el("p", { "data-testid": "g-nofund-body",
        text: "재화가 부족하여 대화에 실패하였습니다. 재화를 충전하시겠습니까?" }),
      el("div", { class: "nf-btns" }, [
        el("button", { class: "primary", "data-testid": "g-nofund-charge", text: "충전",
          onclick: () => goCharge() }),
        el("button", { "data-testid": "g-nofund-close", text: "닫기",
          onclick: () => closeNoFund() })
      ])
    ])
  ]);
}

/* 만료 안내 모달 — 확인하면 미로그인 상태의 홈으로 복귀합니다 (system-spec §1-1) */
function renderExpiredModal() {
  return el("div", { class: "modal", "data-testid": "g-expired-modal" }, [
    el("div", { class: "modal-box" }, [
      el("p", { text: "세션이 만료되었습니다. 다시 로그인해 주세요." }),
      el("button", {
        "data-testid": "g-expired-ok", text: "확인",
        onclick: () => { logout(); render(); }
      })
    ])
  ]);
}

const TAB_LABELS = {
  s2: ["홈", "g-nav-home"],
  s8: ["내 작품", "g-nav-works"],
  s5: ["채팅", "g-nav-chat"],
  s7: ["커뮤니티", "g-nav-community"],
  s6: ["MY", "g-nav-my"]
};

/* 상단 바 — 잔액·미션은 로그인 전용 요소라 미로그인에는 노출하지 않고
 * 대신 로그인 버튼을 둡니다(system-spec §1-1). */
/* 알림 목록 — 데이터 시트의 항목을 표시만 합니다. 발생 로직은 없습니다(트리 제외 사유) */
function renderNotiList() {
  const rows = VN.sheet.notifications;
  return el("div", { class: "noti-pop", "data-testid": "g-noti-list" }, [
    el("div", { class: "noti-head" }, [
      el("strong", { text: "알림" }),
      el("button", {
        class: "panel-close", "data-testid": "g-noti-close", text: "✕",
        onclick: () => { VN.notiOpen = false; render(); }
      })
    ]),
    rows.length
      ? el("ul", { class: "noti-items" }, rows.map((n) =>
          el("li", { class: "noti-item", "data-testid": "g-noti-" + n.id }, [
            el("p", { class: "noti-text", text: n.text }),
            el("p", { class: "noti-day", text: n.day })
          ])))
      : el("p", {
          class: "empty", "data-testid": "g-noti-empty", text: "새 알림이 없습니다."
        })
  ]);
}

function renderTopBar() {
  const acc = currentAccount();
  // 입력 중인 값은 상태에 담지 않습니다 — 확정된 검색어(VN.search)만 결과를 만듭니다
  const search = el("input", {
    class: "search", "data-testid": "g-search", type: "text",
    placeholder: "캐릭터 검색", value: VN.search || "",
    onkeydown: (e) => { if (e.key === "Enter") runSearch(e.target.value); }
  });
  const items = [
    el("button", {
      class: "logo", "data-testid": "g-logo", text: "MiyonChat",
      onclick: () => goHome()
    }),
    search,
    el("button", {
      class: "icon", "data-testid": "g-search-submit", text: "검색",
      onclick: () => runSearch(search.value)
    }),
    el("button", {
      class: "icon", "data-testid": "g-noti", text: "알림",
      onclick: () => toggleNoti()
    }),
    renderDebugButton()          // 테스트 설비 — 로그인 여부와 무관하게 항상 노출
  ];
  if (isLoggedIn()) {
    items.push(el("button", {
      class: "icon", "data-testid": "g-wallet",
      text: "캔디 " + acc.wallet.free + " / 크리스탈 " + acc.wallet.paid,
      onclick: () => openPanel("p3")
    }));
    // 간편 프로필 — 누르면 P4가 열리고 계정 정보가 노출됩니다(청사진 §1 P4)
    items.push(el("button", {
      class: "profile", "data-testid": "g-profile",
      onclick: () => openPanel("p4")
    }, [
      el("span", { class: "avatar", text: accountDisplayName(VN.accountId).slice(0, 1) }),
      el("span", { class: "pname", text: accountDisplayName(VN.accountId) })
    ]));
  } else {
    items.push(el("button", {
      class: "icon", "data-testid": "g-login", text: "로그인",
      onclick: () => openLogin()
    }));
  }
  if (VN.notiOpen) items.push(renderNotiList());
  return el("header", { class: "topbar", "data-testid": "g-topbar" }, items);
}

function renderBottomNav() {
  const items = Object.keys(TAB_LABELS).map((key) => {
    const [label, testid] = TAB_LABELS[key];
    return el("button", {
      class: "nav-item" + (VN.screen === key ? " active" : ""),
      "data-testid": testid, text: label,
      onclick: () => (key === "s2" ? goHome() : go(key))
    });
  });
  return el("nav", { class: "bottomnav", "data-testid": "g-bottomnav" }, items);
}

function renderFooter() {
  return el("footer", { class: "footer", "data-testid": "g-footer" }, [
    el("p", { text: "이 화면은 QA 포트폴리오를 위해 만든 테스트 대상(SUT)입니다. 실제 서비스가 아닙니다." }),
    el("a", {
      "data-testid": "g-footer-tree",
      href: "https://github.com/RyuSeoJin/QA-VisualNovel-Portfolio/blob/main/projects/qa-lab-miyonchat/spec/qa-lab-miyonchat-feature-tree.md",
      target: "_blank", text: "기능 골격 트리 보기"
    }),
    // 빌드 버전 — 이슈의 「영향 받는 버전」에 그대로 적는 값입니다
    el("p", { class: "build", "data-testid": "g-build", text: "빌드 " + SUT_BUILD })
  ]);
}

/* 아직 구현하지 않은 탭 — 스텁 표기 규약(검증 범위 제외 + 사유 + 트리 링크) */
function renderStub(key, reason) {
  return el("section", { class: "screen stub", "data-testid": key + "-stub" }, [
    el("h2", { text: TAB_LABELS[key] ? TAB_LABELS[key][0] : key }),
    el("p", { class: "stub-tag", text: "검증 범위 제외" }),
    el("p", { text: reason })
  ]);
}

/* P4 간편 프로필 — 계정 정보 + 보유 재화 + 미션 진입 (청사진 §1 P4) */
function renderP4() {
  const acc = currentAccount();
  const id = VN.accountId;
  return el("div", { class: "panel-wrap", "data-testid": "p4-panel" }, [
    el("div", { class: "panel" }, [
      el("div", { class: "panel-head" }, [
        el("h2", { text: "간편 프로필" }),
        el("button", {
          class: "panel-close", "data-testid": "p4-close", text: "✕",
          onclick: () => closePanel()
        })
      ]),
      el("div", { class: "p4-id" }, [
        el("span", { class: "avatar lg", text: accountDisplayName(id).slice(0, 1) }),
        el("div", {}, [
          el("p", { class: "p4-name", "data-testid": "p4-name",
            text: accountDisplayName(id) }),
          el("p", {
            class: "p4-adult", "data-testid": "p4-adult",
            text: ACCOUNTS[id].minor ? "미성년 (언세이프 열람 불가 · 해제 수단 없음)"
              : acc.adultVerified ? "성인 인증 완료" : "본인인증 미진행 (인증하면 해제)"
          })
        ])
      ]),
      el("div", { class: "p4-wallet" }, [
        el("div", {}, [el("span", { text: "캔디(무료)" }),
          el("strong", { "data-testid": "p4-wallet-free", text: String(acc.wallet.free) })]),
        el("div", {}, [el("span", { text: "크리스탈(유료)" }),
          el("strong", { "data-testid": "p4-wallet-paid", text: String(acc.wallet.paid) })])
      ]),
      el("p", { class: "todo-note", text: "미션 수령·재화 히스토리는 재화 영역 구현 단위에서 붙습니다." }),
      el("button", {
        class: "p4-my", "data-testid": "p4-go-my", text: "MY 전체 보기",
        onclick: () => { closePanel(); go("s6"); }
      })
    ])
  ]);
}

/* ── P3 재화/충전 ─────────────────────────
 * 잔액 2종과 내역을 지갑별로 나눠 보여 줍니다. 충전은 mock이라 성공·실패 버튼이 따로 있습니다.
 */
function renderP3() {
  const acc = currentAccount();
  const rows = acc.ledger.slice().reverse();
  return el("div", { class: "panel-wrap", "data-testid": "p3-panel" }, [
    el("div", { class: "panel" }, [
      el("div", { class: "panel-head" }, [
        el("h2", { text: "재화" }),
        el("button", { class: "panel-close", "data-testid": "p3-close", text: "✕",
          onclick: () => closePanel() })
      ]),
      el("div", { class: "p4-wallet" }, [
        el("div", {}, [el("span", { text: "캔디(무료)" }),
          el("strong", { "data-testid": "p3-wallet-free", text: String(acc.wallet.free) })]),
        el("div", {}, [el("span", { text: "크리스탈(유료)" }),
          el("strong", { "data-testid": "p3-wallet-paid", text: String(acc.wallet.paid) })])
      ]),
      el("p", { class: "hint", "data-testid": "p3-help",
        text: "전송 1회에 캔디 " + SEND_COST + "이 듭니다. 캔디를 먼저 쓰고 부족분만 크리스탈에서 채웁니다. "
          + "합산이 모자라면 전송이 막힙니다." }),
      el("div", { class: "p3-charge" }, [
        el("button", { class: "primary-btn", "data-testid": "p3-charge-ok",
          text: "충전 성공 (크리스탈 +" + CHARGE_AMOUNT + ")", onclick: () => chargeMock(true) }),
        el("button", { class: "sub-btn", "data-testid": "p3-charge-fail",
          text: "충전 실패", onclick: () => chargeMock(false) })
      ]),
      el("h3", { class: "sec-title", text: "획득·소모 내역" }),
      rows.length
        ? el("ul", { class: "p3-ledger", "data-testid": "p3-ledger" }, rows.map((r) =>
            el("li", { class: "p3-row", "data-testid": "p3-row-" + r.id }, [
              el("span", { text: (r.wallet === "free" ? "캔디" : "크리스탈") + " " + r.reason }),
              el("strong", { class: r.amount < 0 ? "minus" : "plus",
                text: (r.amount > 0 ? "+" : "") + r.amount })
            ])))
        : el("p", { class: "empty", "data-testid": "p3-ledger-empty", text: "내역이 없습니다." })
    ])
  ]);
}

function renderPanel() {
  if (VN.panel === "p3") return renderP3();
  if (VN.panel === "p4") return renderP4();
  if (VN.panel === "p5") return renderP5();
  return null;
}

/* ── S2 홈 ─────────────────────────────────────────────────
 * 목록에 무엇이 몇 번째로 놓이는가가 이 화면의 기대값입니다. 선정·정렬은 state.js가 맡고
 * 여기서는 받은 순서를 그대로 그립니다 — 화면 코드에서 순서를 손보면 기대값이 두 곳으로 갈립니다.
 */

/* 캐릭터 카드 — 언세이프는 가린 채 목록에 남깁니다.
 * 존재까지 지우는 것은 게이팅이 아니라 세이프티 필터입니다(system-spec §9). */
function renderCard(c, meta, rank) {
  const locked = c.safe === false && !canViewUnsafe();
  const kids = [];
  if (rank) kids.push(el("span", { class: "card-rank", text: String(rank) }));
  kids.push(el("div", { class: "card-in" }, [
    el("p", { class: "card-name", text: c.name }),
    el("p", { class: "card-line", text: c.tagline }),
    // 기본 메타는 월간 이용수 — 동률 체인이 쓰는 값이라 순서가 왜 그런지 화면에서 읽힙니다
    el("p", { class: "card-meta", text: meta ||
      "♥ " + likeCount(c) + " · 리뷰 " + c.reviews + " · 월 이용수 " + monthUsage(c) })
  ]));
  if (locked) {
    kids.push(el("span", {
      class: "card-lock", "data-testid": "s2-card-" + c.id + "-blur", text: "19+"
    }));
  }
  return el("button", {
    class: "card" + (locked ? " locked" : ""),
    "data-testid": "s2-card-" + c.id,
    onclick: () => openCharacterPage(c.id)
  }, kids);
}

/* 섹션 하나 — 목록이 비면 그 섹션 자리에 안내 문구가 대신 놓입니다 */
function s2Section(testid, title, list, opts) {
  opts = opts || {};
  const body = list.length
    ? el("div", { class: "cards" + (opts.carousel ? " carousel" : "") },
        list.map((c, i) => renderCard(c, opts.metric ? opts.metric(c) : null,
          opts.rank ? i + 1 : 0)))
    : el("p", {
        class: "empty", "data-testid": testid + "-empty",
        text: opts.empty || "표시할 캐릭터가 없습니다."
      });
  return el("div", { class: "sec", "data-testid": testid }, [
    el("h3", { class: "sec-title", text: title }), body
  ]);
}

function renderS2Recommend() {
  const kids = [s2Section("s2-sec-carousel", "추천", carouselList(), { carousel: true })];
  // 최근 대화한 캐릭터는 대화 이력이 있을 때만 자리를 차지합니다 (system-spec §8-5)
  const recent = recentTalkedList();
  if (recent.length) kids.push(s2Section("s2-sec-recent", "최근 대화한 캐릭터", recent));
  kids.push(s2Section("s2-sec-rising", "떠오르는 신작", risingList(null)));
  kids.push(s2Section("s2-sec-hot", "지금 뜨거운", hotList()));
  return el("div", {}, kids);
}

const RANK_PERIODS = [["일간", "daily"], ["주간", "weekly"], ["월간", "monthly"]];
const RANK_SORTS = [["이용수", "usage"], ["좋아요 순", "likes"],
  ["리뷰 점수 순", "score"], ["리뷰 많은 순", "reviews"]];

/* 필터 줄 — 어느 값이 켜져 있는지가 화면에서 읽혀야 기간 전환이 눈으로 검증됩니다 */
function filterRow(prefix, options, current, onPick) {
  return el("div", { class: "filters" }, options.map(([label, key]) =>
    el("button", {
      class: "f" + (current === key ? " on" : ""),
      "data-testid": prefix + key, text: label,
      onclick: () => onPick(key)
    })));
}

function renderS2Rank() {
  const help = el("button", {
    class: "help", "data-testid": "s2-rank-help", text: "ⓘ 랭킹 규칙",
    onclick: () => { VN.rankHelp = !VN.rankHelp; render(); }
  });
  const helpBody = VN.rankHelp ? el("p", {
    class: "help-body", "data-testid": "s2-rank-help-body",
    text: "기간 필터는 이용수 기준에만 적용되고 좋아요·리뷰는 누적값입니다. "
      + "리뷰 점수 순은 리뷰 " + REVIEW_MIN_SAMPLE + "개 이상만 순위에 포함하며, "
      + "선택한 기간의 이용수가 0건인 캐릭터는 이용수 랭킹에 노출하지 않습니다. "
      + "동률은 월간 이용수 → 좋아요 수 → 캐릭터 ID 순으로 가릅니다."
  }) : null;
  return el("div", {}, [
    filterRow("s2-rank-period-", RANK_PERIODS, VN.rankPeriod,
      (k) => { VN.rankPeriod = k; render(); }),
    filterRow("s2-rank-sort-", RANK_SORTS, VN.rankSort,
      (k) => { VN.rankSort = k; render(); }),
    el("div", { class: "helpline" }, [help]), helpBody,
    s2Section("s2-rank-list", "랭킹", rankList(), {
      rank: true, metric: rankMetric,
      empty: "이 조건에 해당하는 캐릭터가 없습니다."
    })
  ]);
}

function renderS2New() {
  return s2Section("s2-new-list", "신작", newestList(),
    { metric: (c) => "생성일 " + c.createdDay });
}

/* 카테고리 칩 화면 — 인기 신작 → 취향 태그 → 전체 목록 공통 템플릿 (청사진 §1 S2) */
function renderS2Category(name) {
  const group = VN.sheet.categories.find((g) => g.name === name);
  const tags = group ? group.tags : [];
  return el("div", {}, [
    s2Section("s2-cat-new", name + " 인기 신작", risingList(name)),
    el("h3", { class: "sec-title", text: "취향 태그" }),
    el("div", { class: "filters" }, tags.map((t) =>
      el("button", {
        class: "f" + (VN.catTag === t ? " on" : ""),
        "data-testid": "s2-cat-tag-" + t, text: "#" + t,
        // 누른 태그를 다시 누르면 해제됩니다 — 필터를 풀 다른 수단이 없으면 갇힙니다
        onclick: () => { VN.catTag = VN.catTag === t ? null : t; render(); }
      }))),
    filterRow("s2-cat-sort-", [["대화순", "chat"], ["최신순", "new"]], VN.catSort,
      (k) => { VN.catSort = k; render(); }),
    s2Section("s2-cat-list", name + " 전체", categoryList(name), {
      // 대화순의 기준은 누적 이용수입니다 (system-spec §8-6)
      metric: (c) => VN.catSort === "new" ? "생성일 " + c.createdDay
        : "누적 이용수 " + usageCount(c.id, null),
      empty: "선택한 조건에 해당하는 캐릭터가 없습니다."
    })
  ]);
}

/* 검색 결과 — 상단 바에서 친 키워드의 결과는 홈이 받아 그립니다 (청사진 §1 전역 셸) */
function renderS2Search() {
  const list = searchList();
  return el("div", {}, [
    el("div", { class: "search-info" }, [
      el("p", {
        "data-testid": "s2-search-info",
        text: "\"" + VN.search + "\" 검색 결과 " + list.length + "건"
      }),
      el("button", {
        class: "f", "data-testid": "s2-search-clear", text: "검색 해제",
        onclick: () => clearSearch()
      })
    ]),
    s2Section("s2-search-list", "검색 결과", list, {
      empty: "검색 결과가 없습니다. 다른 키워드로 찾아 주세요."
    })
  ]);
}

function renderS2() {
  const names = ["추천", "랭킹", "신작"].concat(VN.sheet.categories.map((g) => g.name));
  const chips = el("div", { class: "chips", "data-testid": "s2-chips" }, names.map((n) =>
    el("button", {
      class: "chip" + (VN.homeChip === n ? " on" : ""),
      "data-testid": "s2-chip-" + n, text: n,
      onclick: () => selectChip(n)
    })));

  let body;
  if (VN.search) {
    // 검색 중에는 칩 화면 대신 결과가 자리를 차지합니다 — 칩은 그대로 두어 빠져나올 길을 남깁니다
    body = renderS2Search();
  } else if (!visibleCharacters().length) {
    body = el("p", {
      class: "empty", "data-testid": "s2-empty",
      text: "표시할 캐릭터가 없습니다."
    });
  } else if (VN.homeChip === "랭킹") body = renderS2Rank();
  else if (VN.homeChip === "신작") body = renderS2New();
  else if (VN.sheet.categories.some((g) => g.name === VN.homeChip)) {
    body = renderS2Category(VN.homeChip);
  } else body = renderS2Recommend();

  return el("section", { class: "screen s2", "data-testid": "s2-screen" }, [chips, body]);
}

/* ── S3 캐릭터 페이지 ──────────────────────
 * 카드를 누르면 열리는 화면이며 대화는 여기서만 시작합니다(system-spec §8-8).
 * 공개 범위라 미로그인도 둘러볼 수 있고, 대화 시작·좋아요만 보호 동작입니다.
 */
function statLine(label, value, testid) {
  return el("div", { class: "stat-item" }, [
    el("span", { class: "stat-num", "data-testid": testid, text: String(value) }),
    el("span", { class: "stat-lbl", text: label })
  ]);
}

/* 하단 고정 버튼 — 그 캐릭터와의 대화방 유무로 구성이 갈립니다(트리: 하단 고정 버튼 분기) */
function renderS3Footer(c) {
  const rooms = roomsOf(c.id);
  const profiles = profilesOf();
  const picked = findProfile(VN.startProfileId) || profiles[0] || null;

  const startBtn = el("button", {
    class: "primary-btn", "data-testid": "s3-start",
    text: rooms.length ? "새 대화 시작" : "대화 시작",
    onclick: () => startChat(c.id)
  });

  const pickBtn = el("button", {
    class: "sub-btn", "data-testid": "s3-pick-profile",
    text: picked ? "프로필 · " + picked.name + (picked.label ? " (" + picked.label + ")" : "")
      : "프로필 선택",
    onclick: () => openPanel("p5")
  });

  const kids = [];
  if (rooms.length) {
    kids.push(el("div", { class: "room-list", "data-testid": "s3-rooms" },
      rooms.map((r) => el("button", {
        class: "room-item", "data-testid": "s3-room-" + r.id,
        onclick: () => resumeChat(r.id)
      }, [
        el("span", { class: "room-name",
          text: (r.profile ? r.profile.name : "프로필 없음") + " · " + r.turn + "턴" }),
        el("span", { class: "room-sub", text: "대화수 " + roomMessageCount(r) })
      ]))));
  }
  if (roomLimitReached(c.id)) {
    kids.push(el("p", {
      class: "room-limit", "data-testid": "s3-room-limit",
      text: "대화방이 " + ROOM_LIMIT_PER_CHAR + "개까지 찼습니다. 새로 시작하려면 기존 대화를 지워 주세요."
    }));
    kids.push(el("div", { class: "room-del" }, rooms.map((r) => el("button", {
      class: "sub-btn", "data-testid": "s3-room-" + r.id + "-delete",
      text: (r.profile ? r.profile.name : r.id) + " 지우기",
      onclick: () => removeChat(r.id)
    }))));
  }
  kids.push(el("div", { class: "s3-actions" }, [pickBtn, startBtn]));
  return el("div", { class: "s3-foot" }, kids);
}

function renderS3() {
  const c = findCharacter(VN.pageCharId);
  if (!c) {
    return el("section", { class: "screen s3", "data-testid": "s3-screen" }, [
      el("p", { class: "empty", "data-testid": "s3-missing", text: "캐릭터를 찾을 수 없습니다." }),
      el("button", { class: "sub-btn", "data-testid": "s3-back", text: "홈으로", onclick: () => goHome() })
    ]);
  }
  const locked = c.safe === false && !canViewUnsafe();
  const kids = [
    el("div", { class: "s3-head" }, [
      el("button", { class: "chat-back", "data-testid": "s3-back", text: "‹ 뒤로", onclick: () => goHome() }),
      el("h2", { class: "screen-title", "data-testid": "s3-name", text: c.name })
    ])
  ];

  if (locked) {
    kids.push(el("p", {
      class: "lock-notice", "data-testid": "s3-locked",
      text: "19세 이상 콘텐츠입니다. " + GATE_NOTICE[gateState()]
    }));
    // 게이팅 상태에서도 현황은 보입니다 — 실측의 언세이프 프로필과 같은 처리입니다
    kids.push(el("div", { class: "stat-row", "data-testid": "s3-stats" }, [
      statLine("이용수", usageCount(c.id, null), "s3-stat-usage"),
      statLine("좋아요", likeCount(c), "s3-stat-likes"),
      statLine("팔로우", c.creator ? c.creator.followers : 0, "s3-stat-follow")
    ]));
    return el("section", { class: "screen s3", "data-testid": "s3-screen" }, kids);
  }

  kids.push(el("p", { class: "lede-sm", "data-testid": "s3-tagline", text: c.tagline }));
  kids.push(el("p", { class: "d-tags", "data-testid": "s3-tags",
    text: (c.tags || []).map((t) => "#" + t).join(" ") }));
  kids.push(el("p", { class: "s3-creator", "data-testid": "s3-creator",
    text: "제작 " + (c.creator ? c.creator.name : "-") + " · 팔로워 "
      + (c.creator ? c.creator.followers : 0) }));
  kids.push(el("div", { class: "stat-row", "data-testid": "s3-stats" }, [
    statLine("이용수", usageCount(c.id, null), "s3-stat-usage"),
    statLine("좋아요", likeCount(c), "s3-stat-likes"),
    statLine("리뷰", c.reviews, "s3-stat-reviews"),
    statLine("팔로우", c.creator ? c.creator.followers : 0, "s3-stat-follow")
  ]));
  kids.push(el("p", { class: "s3-updated", "data-testid": "s3-updated",
    text: "출시 " + c.createdDay + " · 최종 업데이트 " + (c.updatedDay || "-")
      + " (" + (c.version || "-") + ")" }));
  kids.push(el("p", { class: "d-first", "data-testid": "s3-first", text: c.firstMessage }));
  kids.push(el("p", { class: "s3-situation", "data-testid": "s3-situation",
    text: "시작 상황 — " + (c.startSituation ? c.startSituation.label : "-") }));
  kids.push(el("div", { class: "d-toggles" }, [
    el("button", {
      class: "tog" + (isLiked(c.id) ? " on" : ""), "data-testid": "s3-like",
      text: isLiked(c.id) ? "♥ 좋아요 취소" : "♡ 좋아요",
      onclick: () => toggleCardFlag("like", c.id)
    }),
    el("button", {
      class: "tog" + (isScrapped(c.id) ? " on" : ""), "data-testid": "s3-scrap",
      text: isScrapped(c.id) ? "★ 스크랩 취소" : "☆ 스크랩",
      onclick: () => toggleCardFlag("scrap", c.id)
    })
  ]));

  // 그 외 작품 — 선정식이 미확인이라 같은 카테고리에서 체인 순으로 채웁니다(TC 기대값 아님)
  const related = sortChars(visibleCharacters()
    .filter((x) => x.id !== c.id && x.category === c.category), monthUsage).slice(0, 4);
  if (related.length) {
    kids.push(s2Section("s3-related", "그 외 작품", related, { carousel: true }));
  }
  kids.push(renderS3Footer(c));
  return el("section", { class: "screen s3", "data-testid": "s3-screen" }, kids);
}

/* ── P5 대화 프로필 ───────────────────────
 * 프로필을 여러 개 만들어 두고 대화방마다 하나를 고릅니다(system-spec §2).
 */
const PROFILE_LIMITS = { name: 12, nickname: 12, desc: 1000, label: 30 };
const PROFILE_GENDERS = ["설정 안 함", "여성", "남성"];
const RANDOM_NAMES = ["서진", "하람", "유원", "연오", "도하"];
/* 호칭도 돌려 씁니다 — 프로필마다 달라야 방 사이 섞임(프로필 간 격리)이 눈에 보입니다 */
const RANDOM_NICKS = ["너", "선배", "그쪽", "이봐", "자기"];
const RANDOM_DESCS = [
  "말수는 적지만 필요한 말은 합니다.",
  "커피를 좋아하고 밤에 강합니다.",
  "농담을 잘하지만 정색도 잘합니다."
];

function profileField(key, label, opts) {
  opts = opts || {};
  const limit = PROFILE_LIMITS[key];
  const count = el("span", { class: "count", "data-testid": "p5-" + key + "-count",
    text: "0/" + limit });
  const input = el(opts.multiline ? "textarea" : "input", {
    class: "f-input", "data-testid": "p5-" + key, maxlength: String(limit),
    rows: opts.multiline ? "4" : null, type: opts.multiline ? null : "text",
    placeholder: opts.placeholder || "",
    oninput: (e) => {
      // 상한은 사람이 치는 입력과 값 주입 양쪽에서 같게 지켜야 합니다(system-spec §2)
      if (e.target.value.length > limit) e.target.value = e.target.value.slice(0, limit);
      count.textContent = e.target.value.length + "/" + limit;
      syncProfileSave();
    }
  });
  return el("div", { class: "field" }, [
    el("div", { class: "field-head" }, [
      el("label", { text: label + (opts.required ? " (필수)" : "") }), count
    ]),
    input
  ]);
}

function syncProfileSave() {
  const name = document.querySelector('[data-testid="p5-name"]');
  const save = document.querySelector('[data-testid="p5-save"]');
  if (!name || !save) return;
  save.disabled = !name.value.trim();
}

function renderP5() {
  const profiles = profilesOf();
  const kids = [
    el("div", { class: "panel-head" }, [
      el("h2", { text: "대화 프로필" }),
      el("button", { class: "panel-close", "data-testid": "p5-close", text: "✕",
        onclick: () => closePanel() })
    ]),
    el("p", { class: "lede-sm",
      text: "대화를 시작할 때 쓸 내 프로필입니다. 방마다 하나가 고정됩니다." })
  ];

  if (profiles.length) {
    kids.push(el("div", { class: "p5-list" }, profiles.map((p) => el("button", {
      class: "p5-item" + (VN.startProfileId === p.id ? " on" : ""),
      "data-testid": "p5-profile-" + p.id,
      onclick: () => pickProfile(p.id)
    }, [
      el("span", { class: "p5-pname", text: p.name + (p.nickname ? " · " + p.nickname : "") }),
      el("span", { class: "p5-plabel", text: p.label || "" })
    ]))));
  } else {
    kids.push(el("p", { class: "empty", "data-testid": "p5-empty",
      text: "등록된 프로필이 없습니다. 아래에서 추가해 주세요." }));
  }

  kids.push(el("p", { class: "hint", "data-testid": "p5-count",
    text: profiles.length + "/" + PROFILE_LIMIT + " 사용 중" }));

  if (profileLimitReached()) {
    kids.push(el("p", { class: "room-limit", "data-testid": "p5-limit",
      text: "프로필은 " + PROFILE_LIMIT + "개까지 만들 수 있습니다." }));
  } else {
    kids.push(el("h3", { class: "sec-title", text: "프로필 추가" }));
    kids.push(profileField("name", "이름", { required: true, placeholder: "대화에서 쓸 내 이름" }));
    kids.push(profileField("nickname", "호칭", { placeholder: "캐릭터가 나를 부르는 말" }));
    const gender = el("select", { class: "f-input", "data-testid": "p5-gender" },
      PROFILE_GENDERS.map((g) => el("option", { value: g, text: g })));
    kids.push(el("div", { class: "field" }, [
      el("div", { class: "field-head" }, [el("label", { text: "성별" })]), gender
    ]));
    kids.push(profileField("desc", "자유 설명", { multiline: true, placeholder: "성격·취향·관계 설정" }));
    kids.push(profileField("label", "Label", { placeholder: "연애 모드 등" }));
    const save = el("button", { class: "primary-btn", "data-testid": "p5-save", text: "추가",
      onclick: () => saveProfile() });
    save.disabled = true;
    kids.push(el("div", { class: "p5-add-row" }, [
      el("button", { class: "sub-btn", "data-testid": "p5-random", text: "랜덤 완성",
        onclick: () => fillRandomProfile() }),
      save
    ]));
  }
  return el("div", { class: "panel-wrap", "data-testid": "p5-panel" }, [
    el("div", { class: "panel" }, kids)
  ]);
}

/* ── S4 대화 ────────────────────────────────────────────────
 * 셸 밖 전체 화면입니다(청사진 §1). 셸이 없으므로 디버그 버튼을 헤더에 단독으로 둡니다.
 */
function renderChatMessage(m) {
  const who = m.role === "ai" ? "ai" : "user";
  return el("div", {
    class: "msg " + who + (m.fail ? " fail" : "") + (m.done ? "" : " typing"),
    "data-testid": "s4-msg-" + m.turn + "-" + who
  }, [
    el("div", { class: "bubble" }, [
      el("span", { class: "bubble-text", text: m.done ? m.text : "" })
    ])
  ]);
}

function renderS4() {
  const room = activeRoom();
  const c = room ? findCharacter(room.charId) : null;

  if (!room) {
    return el("section", { class: "screen chat-empty", "data-testid": "s4-noroom" }, [
      el("h2", { class: "screen-title", text: "대화" }),
      el("p", { class: "lede-sm", text: "열려 있는 대화방이 없습니다. 홈에서 캐릭터를 골라 시작해 주세요." }),
      el("button", { class: "primary-btn", "data-testid": "s4-back", text: "홈으로", onclick: () => leaveChat() })
    ]);
  }

  const set = mockSetFor(room.charId, room.scenarioId);
  const sit = c && c.startSituation;

  const input = el("textarea", {
    class: "chat-input", "data-testid": "s4-input", rows: "2",
    maxlength: String(CHAT_INPUT_MAX), placeholder: "메시지를 입력하세요",
    oninput: (e) => {
      // 상한은 사람이 치는 입력과 값 주입 양쪽에서 같게 지켜야 합니다 (system-spec §2·§5)
      if (e.target.value.length > CHAT_INPUT_MAX) {
        e.target.value = e.target.value.slice(0, CHAT_INPUT_MAX);
      }
      const n = document.querySelector('[data-testid="s4-input-count"]');
      if (n) n.textContent = e.target.value.length + "/" + CHAT_INPUT_MAX;
    },
    onkeydown: (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(e.target.value); }
    }
  });

  const send = el("button", {
    class: "primary-btn", "data-testid": "s4-send", text: "전송",
    onclick: () => sendMessage(input.value)
  });
  send.disabled = chatStreaming || room.ended;

  const foot = [
    el("div", { class: "chat-foot-head" }, [
      el("span", { class: "count", "data-testid": "s4-input-count", text: "0/" + CHAT_INPUT_MAX }),
      chatStreaming
        ? el("span", { class: "streaming", "data-testid": "s4-streaming", text: "응답 표시 중…" })
        : null
    ].filter(Boolean)),
    el("div", { class: "chat-send" }, [input, send])
  ];
  if (room.ended) {
    foot.push(el("p", {
      class: "chat-end", "data-testid": "s4-ended",
      text: "이 경로의 마지막 턴까지 왔습니다. 엔딩 판정은 다음 구현 단위에서 붙습니다."
    }));
  }

  return el("section", { class: "screen s4", "data-testid": "s4-screen" }, [
    el("header", { class: "chat-head" }, [
      el("button", { class: "chat-back", "data-testid": "s4-back", text: "‹ 뒤로", onclick: () => leaveChat() }),
      el("div", { class: "chat-title" }, [
        el("p", { class: "chat-name", "data-testid": "s4-char", text: c ? c.name : room.charId }),
        el("p", {
          class: "chat-sub", "data-testid": "s4-scenario",
          text: (sit ? sit.label : room.scenarioId)
            + " · " + (set.characterId === "*" ? "공통 세트" : "전용 세트")
            + " · 시드 " + VN.seed
        })
      ]),
      el("button", {
        class: "icon", "data-testid": "s4-wallet",
        text: "캔디 " + (currentAccount() ? currentAccount().wallet.free : 0)
          + " / 크리스탈 " + (currentAccount() ? currentAccount().wallet.paid : 0),
        onclick: () => openPanel("p3")
      }),
      renderDebugButton()      // 셸이 없는 화면이라 여기 단독으로 둡니다
    ]),
    el("div", { class: "chat-log", "data-testid": "s4-log" }, room.messages.map(renderChatMessage)),
    el("div", { class: "chat-foot" }, foot)
  ]);
}

function renderPlaceholder(key, label) {
  return el("section", { class: "screen todo", "data-testid": key + "-todo" }, [
    el("h2", { text: label }),
    el("p", { text: "다음 구현 단위입니다." })
  ]);
}
