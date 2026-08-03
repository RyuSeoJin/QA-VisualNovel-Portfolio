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
/* 스텁 — 제외 영역임을 화면에서 읽히게 둡니다.
 * 사유만 적으면 "왜 안 만들었나"가 판단으로 보이므로, **트리의 어느 항목인지**를 함께
 * 내어 제외가 기획 정본에 기록된 결정임을 드러냅니다(트리 제외 영역이 정본입니다). */
function renderStub(key, reason, node) {
  return el("section", { class: "screen stub", "data-testid": key + "-stub" }, [
    el("h2", { text: TAB_LABELS[key] ? TAB_LABELS[key][0] : key }),
    el("p", { class: "stub-tag", text: "검증 범위 제외" }),
    el("p", { "data-testid": key + "-stub-reason", text: reason }),
    el("p", { class: "hint", "data-testid": key + "-stub-node",
      text: "기능 골격 트리 · 제외 영역 「" + node + "」 — 트리가 제외 사유의 정본입니다." })
  ]);
}

/* 미션 한 줄 — 받은 뒤에는 눌리지 않는다는 것이 보여야 중복 차단이 화면에서 읽힙니다 */
function renderMissionRow(label, testid, claimed, onClaim) {
  const btn = el("button", {
    class: "sub-btn", "data-testid": testid,
    text: claimed ? "수령 완료" : "받기 (캔디 +" + MISSION_REWARD + ")",
    onclick: onClaim
  });
  btn.disabled = claimed;
  return el("div", { class: "p4-mission" }, [el("span", { text: label }), btn]);
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
      el("h3", { class: "sec-title", text: "미션" }),
      // 달성 판정 로직은 만들지 않습니다 — 사유를 화면에 적어 미구현을 결함으로 오인하지
      // 않게 합니다 (system-spec §3)
      el("p", { class: "hint", "data-testid": "p4-mission-note",
        text: "달성 판정은 만들지 않았습니다. 전 항목이 수령 가능 상태이며 검증 대상은 수령·중복 차단·잔액 반영입니다." }),
      el("div", { class: "p4-missions", "data-testid": "p4-missions" },
        [renderMissionRow("출석 체크 (데일리)", "p4-daily-claim", dailyClaimed(),
          () => claimMission("daily"))].concat(
          WELCOME_MISSIONS.map((m) => renderMissionRow(m.label + " (웰컴)",
            "p4-welcome-" + m.id + "-claim", welcomeClaimed(m.id),
            () => claimMission("welcome", m.id))))),
      renderLedger("p4"),
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
/* 내역 — P3와 P4가 같은 데이터를 봅니다. 필터는 획득/소모를 가릅니다 (system-spec §3) */
function renderLedger(prefix) {
  const rows = ledgerRows();
  const chip = (label, key) => el("button", {
    class: "f" + (VN.ledgerFilter === key ? " on" : ""),
    "data-testid": prefix + "-filter-" + key, text: label,
    onclick: () => { VN.ledgerFilter = key; render(); }
  });
  return el("div", {}, [
    el("h3", { class: "sec-title", text: "획득·소모 내역" }),
    el("div", { class: "filters" }, [chip("전체", "all"), chip("획득", "gain"), chip("소모", "spend")]),
    rows.length
      ? el("ul", { class: "p3-ledger", "data-testid": prefix + "-ledger" }, rows.map((r) =>
          el("li", { class: "p3-row", "data-testid": prefix + "-row-" + r.id }, [
            el("span", { text: (r.wallet === "free" ? "캔디" : "크리스탈") + " " + r.reason }),
            el("strong", { class: r.amount < 0 ? "minus" : "plus",
              text: (r.amount > 0 ? "+" : "") + r.amount })
          ])))
      : el("p", { class: "empty", "data-testid": prefix + "-ledger-empty", text: "내역이 없습니다." })
  ]);
}

/* ── P2 현재 상태 ─────────────────────────
 * 관계 단계·호감도·감정 온도·호칭을 보여 줍니다. 규칙성 화면이라 ⓘ에 단계표를 답니다.
 */
/* P1 세이브/로드 — 대화방 안의 시점을 슬롯에 담습니다 (system-spec §6 · save-schema).
 *
 * 슬롯은 **방의 것**입니다. 방을 옮기면 슬롯 목록도 함께 바뀌어야 하며, 그 경계가 곧
 * 슬롯 격리의 검증선입니다. 저장·로드는 무료이고 재화는 스냅샷에 담기지 않습니다.
 */
function renderP1() {
  const room = activeRoom();
  const head = el("div", { class: "panel-head" }, [
    el("h2", { text: "세이브/로드" }),
    el("button", { class: "panel-close", "data-testid": "p1-close", text: "✕",
      onclick: () => closePanel() })
  ]);

  if (!room) {
    return el("div", { class: "panel-wrap", "data-testid": "p1-panel" }, [
      el("div", { class: "panel" }, [head,
        el("p", { class: "empty", "data-testid": "p1-noroom", text: "열려 있는 대화방이 없습니다." })])
    ]);
  }

  const rows = [];
  for (let n = 1; n <= SLOT_COUNT; n++) {
    const snap = slotOf(room, n);
    const cells = [
      el("span", { class: "slot-no", text: n + "번" }),
      el("span", {
        class: "slot-info" + (snap ? "" : " empty"), "data-testid": "p1-slot-" + n + "-info",
        text: snap ? snap.summary + " · " + snap.savedAtDay : "비어 있음"
      }),
      el("button", { class: "mini", "data-testid": "p1-slot-" + n + "-save", text: "저장",
        onclick: () => saveToSlot(n) })
    ];
    // 빈 슬롯은 로드할 것이 없으므로 버튼을 비활성으로 남깁니다 — 감추면 칸의 수가 흐려집니다
    const load = el("button", { class: "mini", "data-testid": "p1-slot-" + n + "-load", text: "로드",
      onclick: () => pickLoad(n) });
    load.disabled = !snap;
    cells.push(load);

    const row = el("div", { class: "slot-row" + (VN.loadPick === n ? " picking" : ""),
      "data-testid": "p1-slot-" + n }, cells);
    rows.push(row);

    // 로드 갈래 — 이 방에 덮어쓸지, 새 방으로 갈라질지 (새 방 갈래가 곧 분기입니다)
    if (VN.loadPick === n) {
      rows.push(el("div", { class: "slot-pick", "data-testid": "p1-load-pick" }, [
        el("p", { class: "hint", "data-testid": "p1-load-pick-body",
          text: "어디에 불러올까요? 이 방에 덮어쓰면 저장 시점 이후의 대화는 남지 않고, "
            + "새 방으로 불러오면 지금 방은 그대로 남습니다(대화방 한도를 받습니다)." }),
        el("div", { class: "slot-pick-btns" }, [
          el("button", { class: "mini primary", "data-testid": "p1-load-here",
            text: "이 방에 덮어쓰기", onclick: () => loadHere(n) }),
          el("button", { class: "mini", "data-testid": "p1-load-new",
            text: "새 방으로", onclick: () => loadToNewRoom(n) }),
          el("button", { class: "mini", "data-testid": "p1-load-cancel",
            text: "취소", onclick: () => cancelLoad() })
        ])
      ]));
    }
  }

  const rooms = roomsOf(room.charId);
  const roomList = el("div", { class: "p1-rooms", "data-testid": "p1-rooms" },
    rooms.map((r) => {
      const here = r.id === room.id;
      const btn = el("button", {
        class: "slot-room" + (here ? " here" : ""), "data-testid": "p1-room-" + r.id,
        text: r.id + " · " + stageOf(r.affection).name + " " + r.affection + " · " + r.turn + "턴"
          + (here ? " (지금 방)" : ""),
        onclick: () => { if (!here) { resumeRoom(r.id); VN.loadPick = null; render(); } }
      });
      btn.disabled = here;
      return btn;
    }));

  return el("div", { class: "panel-wrap", "data-testid": "p1-panel" }, [
    el("div", { class: "panel" }, [
      head,
      el("p", { class: "hint", "data-testid": "p1-help",
        text: "슬롯은 대화방마다 " + SLOT_COUNT + "칸이며 저장·로드는 무료입니다. "
          + "재화는 계정의 것이라 로드해도 되돌아오지 않습니다." }),
      el("div", { class: "slot-list", "data-testid": "p1-slots" }, rows),
      el("p", { class: "hint", "data-testid": "p1-rooms-head",
        text: "이 캐릭터의 대화방 " + rooms.length + "/" + ROOM_LIMIT_PER_CHAR }),
      roomList
    ])
  ]);
}

function renderP2() {
  const room = activeRoom();
  if (!room) {
    return el("div", { class: "panel-wrap", "data-testid": "p2-panel" }, [
      el("div", { class: "panel" }, [
        el("div", { class: "panel-head" }, [
          el("h2", { text: "현재 상태" }),
          el("button", { class: "panel-close", "data-testid": "p2-close", text: "✕",
            onclick: () => closePanel() })
        ]),
        el("p", { class: "empty", text: "열려 있는 대화방이 없습니다." })
      ])
    ]);
  }
  const stage = stageOf(room.affection);
  // 관계 단계·호감도는 엔딩 판정의 근거라 고정 대상이 아닙니다 (system-spec §7-2)
  // 표시는 실제로 쓰이는 값(고정돼 있으면 고정값)입니다
  const rows = [
    ["관계 단계", stage.name, "p2-stage"],
    ["호감도", String(room.affection), "p2-affection"],
    ["감정 온도", stateValue(room, "temp"), "p2-temp"],
    ["호칭", stateValue(room, "nickname") || "-", "p2-nickname"]
  ];

  /* 고정 가능한 항목 — 값을 고쳐 고정하면 자동 계산보다 우선합니다.
   * 고정 중임이 화면에서 읽혀야 "왜 자동 계산을 안 따르는가"가 결함으로 오인되지 않습니다. */
  const fixable = OVERRIDABLE.map((f) => {
    const on = isOverridden(room, f.key);
    const box = el("input", {
      class: "fix-input", "data-testid": "p2-" + f.key + "-input", maxlength: "12"
    });
    box.value = stateValue(room, f.key);
    const btn = el("button", {
      class: "mini" + (on ? "" : " primary"), "data-testid": "p2-" + f.key + "-fix",
      text: on ? "고정 해제" : "고정",
      onclick: () => (on ? releaseState(f.key) : fixState(f.key, box.value))
    });
    return el("div", { class: "fix-row" + (on ? " on" : ""), "data-testid": "p2-" + f.key + "-row" }, [
      el("span", { class: "fix-label", text: f.label }),
      box, btn,
      el("span", { class: "fix-state", "data-testid": "p2-" + f.key + "-state",
        text: on ? "고정 중" : "자동 " + autoValue(room, f.key) })
    ]);
  });

  const kids = [
    el("div", { class: "panel-head" }, [
      el("h2", { text: "현재 상태" }),
      el("button", { class: "panel-close", "data-testid": "p2-close", text: "✕",
        onclick: () => closePanel() })
    ]),
    el("dl", { class: "p2-list", "data-testid": "p2-list" },
      rows.reduce((acc, [k, v, id]) => acc.concat([
        el("dt", { text: k }), el("dd", { "data-testid": id, text: v })
      ]), [])),
    el("div", { class: "fix-list", "data-testid": "p2-fixables" }, fixable),
    el("p", { class: "hint", "data-testid": "p2-fix-help",
      text: "고친 값을 고정하면 캐릭터의 자동 계산보다 우선합니다. 관계 단계·호감도는 엔딩 "
        + "판정의 근거라 고정할 수 없습니다." }),
    /* 검증 범위를 화면에도 남깁니다 — 「반말 써 줘」가 안 먹는 것을 결함으로 오인하지
     * 않도록, 값을 바꾸는 통로가 대화가 아니라 이 패널임을 여기서 알립니다 (system-spec §7-2) */
    el("p", { class: "hint scope", "data-testid": "p2-scope-note",
      text: "이 SUT는 자연어 지시를 알아듣지 않습니다 — 「반말 써 줘」처럼 대화로 부탁해도 "
        + "응답은 달라지지 않습니다. 값은 여기서 바꿉니다. 말투는 대사 세트가 두 벌 필요해 "
        + "구현 범위에서 뺐습니다(트리 제외 영역)." }),
    el("button", {
      class: "help", "data-testid": "p2-help", text: "ⓘ 단계 기준",
      onclick: () => { VN.p2Help = !VN.p2Help; render(); }
    })
  ];
  if (VN.p2Help) {
    kids.push(el("p", { class: "help-body", "data-testid": "p2-help-body",
      text: STAGES.map((x) => x.name + " " + x.from + (x.to === Infinity ? "+" : "~" + x.to)).join(" · ")
        + " · 호감도 하한은 0이며 상한은 없습니다." }));
  }

  /* 기억 목록 (system-spec §7-1)
   * 장면이 끝나면 그 장면의 기억은 요점만 남고, 고정한 항목만 원문 그대로 남습니다.
   * 어느 장면에서 온 기억인지·줄었는지가 한 줄에서 읽혀야 규칙을 화면으로 확인할 수 있습니다. */
  const ctx = contextRange(room);
  const ev = currentEvent(room);
  kids.push(el("h3", { class: "p2-sub", text: "기억" }));
  kids.push(el("p", { class: "hint", "data-testid": "p2-event",
    text: "지금 장면 — " + (ev ? ev.label + " (" + ev.from + "~" + ev.to + "턴)" : "아직 없음")
      + ". 장면이 끝나면 그 장면의 기억은 요점만 남습니다." }));
  kids.push(el("p", { class: "hint", "data-testid": "p2-context",
    text: "단기 맥락 창 " + CONTEXT_WINDOW_TURNS + "턴 — "
      + (ctx.to ? ctx.from + "~" + ctx.to + "턴" : "아직 없음")
      + ". 창 밖의 대화는 응답에 반영되지 않습니다." }));

  const mems = room.memories || [];
  kids.push(mems.length
    ? el("ul", { class: "mem-list", "data-testid": "p2-memories" }, mems.map((m) =>
        el("li", { class: "mem" + (m.pinned ? " pinned" : ""), "data-testid": "p2-memory-" + m.id }, [
          el("span", { class: "mem-text", "data-testid": "p2-memory-" + m.id + "-text",
            text: (m.pinned ? "📌 " : "") + m.text }),
          el("span", { class: "mem-turn", "data-testid": "p2-memory-" + m.id + "-turn",
            text: m.turn + "턴 · " + m.event + (m.brief ? " · 요점" : "")
              + (m.source === "user" ? " · 유저 등록" : "") }),
          el("button", { class: "mini", "data-testid": "p2-memory-" + m.id + "-pin",
            text: m.pinned ? "고정 해제" : "고정", onclick: () => pinMemory(m.id) }),
          el("button", { class: "mini", "data-testid": "p2-memory-" + m.id + "-delete",
            text: "삭제", onclick: () => removeMemory(m.id) })
        ])))
    : el("p", { class: "empty", "data-testid": "p2-memory-empty",
        text: "쌓인 기억이 없습니다. 대화를 이어가면 쌓입니다." }));

  if ((room.forgotten || []).length) {
    kids.push(el("p", { class: "hint", "data-testid": "p2-forgotten",
      text: "지운 기억 " + room.forgotten.length + "건 — 이후 응답에서 이 내용을 참조하지 않습니다" }));
  }
  return el("div", { class: "panel-wrap", "data-testid": "p2-panel" }, [
    el("div", { class: "panel" }, kids)
  ]);
}

function renderP3() {
  const acc = currentAccount();
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
      renderLedger("p3")
    ])
  ]);
}

function renderPanel() {
  if (VN.panel === "p1") return renderP1();
  if (VN.panel === "p2") return renderP2();
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
  const inner = [
    // 이미지 자리 — 그림을 넣지 않는 SUT라 이름 텍스트로 대신합니다
    el("div", { class: "card-thumb", "data-testid": "s2-card-" + c.id + "-thumb", text: c.name }),
    el("p", { class: "card-name", text: c.pageTitle || c.name }),
    el("p", { class: "card-line", text: c.pageSubtitle || c.tagline }),
    el("p", { class: "card-by", text: c.creator ? c.creator.name : "" })
  ];
  // 지표는 평소 숨기고 T1에서 켤 때만 붙입니다 — 정렬 근거를 확인할 때 씁니다
  if (VN.showMetrics) {
    inner.push(el("p", { class: "card-meta", "data-testid": "s2-card-" + c.id + "-metric",
      text: meta || "♥ " + likeCount(c) + " · 리뷰 " + c.reviews + " · 월 이용수 " + monthUsage(c) }));
  }
  kids.push(el("div", { class: "card-in" }, inner));
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
  const related = group ? group.related : [];
  return el("div", {}, [
    s2Section("s2-cat-new", name + " 인기 신작", risingList(name)),
    el("h3", { class: "sec-title", text: "함께 보는 카테고리" }),
    el("div", { class: "filters" }, related.map((t) =>
      el("button", {
        class: "f" + (VN.catFilter === t ? " on" : ""),
        "data-testid": "s2-cat-tag-" + t, text: "#" + t,
        // 누른 카테고리를 다시 누르면 해제됩니다 — 풀 수단이 없으면 필터에 갇힙니다
        onclick: () => { VN.catFilter = VN.catFilter === t ? null : t; render(); }
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

  // ① 상단 바 — 뒤로가기 + 페이지 제목
  const kids = [
    el("div", { class: "s3-head" }, [
      el("button", { class: "chat-back", "data-testid": "s3-back", text: "‹ 뒤로", onclick: () => goHome() }),
      el("h2", { class: "s3-head-title", "data-testid": "s3-page-title", text: c.pageTitle || c.name })
    ])
  ];

  // ② 캐릭터 이미지 — 그림을 넣지 않는 SUT라 이름 텍스트로 대신합니다
  kids.push(el("div", { class: "s3-hero", "data-testid": "s3-thumb", text: c.name }));

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

  // ③④⑤ 페이지 제목 · 보조 설명 · 작업자
  kids.push(el("div", { class: "s3-titleblock" }, [
    el("h1", { class: "s3-title", "data-testid": "s3-title", text: c.pageTitle || c.name }),
    el("p", { class: "s3-sub", "data-testid": "s3-page-subtitle", text: c.pageSubtitle || "" }),
    el("p", { class: "s3-creator", "data-testid": "s3-creator",
      text: "제작 " + (c.creator ? c.creator.name : "-") + " · 팔로워 "
        + (c.creator ? c.creator.followers : 0) })
  ]));

  // ⑥ 지표 — 카드에서는 숨기지만 페이지에서는 늘 보입니다 (system-spec §8-4-1)
  kids.push(el("div", { class: "stat-row", "data-testid": "s3-stats" }, [
    statLine("이용수", usageCount(c.id, null), "s3-stat-usage"),
    statLine("좋아요", likeCount(c), "s3-stat-likes"),
    statLine("리뷰", c.reviews, "s3-stat-reviews"),
    statLine("팔로우", c.creator ? c.creator.followers : 0, "s3-stat-follow")
  ]));
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

  // ⑦ 페이지 카테고리 — 대표와 나머지를 가르지 않고 전부 # 칩으로 보여 줍니다
  kids.push(el("div", { class: "s3-cats", "data-testid": "s3-categories" },
    (c.pageCategories || []).map((t) => el("span", {
      class: "cat-chip", "data-testid": "s3-cat-" + t, text: "#" + t
    }))));

  // ⑧⑨ 스토리 — 길어지면 문단을 여러 개 붙입니다
  const stories = c.pageStories || [];
  kids.push(el("div", { class: "s3-stories", "data-testid": "s3-stories" },
    stories.map((t, i) => el("p", {
      class: "s3-story", "data-testid": "s3-story-" + (i + 1), text: t
    }))));

  // 캐릭터 층 — 트리에 확정된 노드라 스토리 뒤에 둡니다
  // 캐릭터 소개 — 항목마다 구분선을 둬 한눈에 갈려 읽히게 합니다
  kids.push(el("h3", { class: "sec-title", text: "캐릭터" }));
  kids.push(el("dl", { class: "s3-charblock", "data-testid": "s3-char-block" }, [
    el("dt", { text: "이름" }),
    el("dd", { "data-testid": "s3-name", text: c.name }),
    el("dt", { text: "한 줄 설명" }),
    el("dd", { "data-testid": "s3-tagline", text: c.tagline }),
    el("dt", { text: "상세 설명" }),
    el("dd", { "data-testid": "s3-char-desc", text: c.charDesc || "" }),
    el("dt", { text: "시작 상황" }),
    el("dd", { "data-testid": "s3-situation", text: c.startSituation ? c.startSituation.label : "-" }),
    el("dt", { text: "첫 메시지" }),
    el("dd", { "data-testid": "s3-first", text: c.firstMessage })
  ]));

  // ⑩ 출시일 · 최종 업데이트(버전) — 버전은 숫자로 담고 표시할 때 v를 붙입니다 (§8-8)
  kids.push(el("p", { class: "s3-updated", "data-testid": "s3-updated",
    text: "출시 " + c.createdDay + " · 최종 업데이트 " + (c.updatedDay || "-")
      + " (" + versionLabel(c.version) + ")" }));

  // ⑪ 그 외 작품 추천 (§8-8) — 후보가 없을 때 섹션을 감추면 "안 뜬 것"과 "없는 것"이
  // 구분되지 않습니다. 기본 데이터에서 자주 나오는 화면이라 안내를 남깁니다
  const related = relatedList(c);
  if (related.length) {
    kids.push(s2Section("s3-related", "그 외 작품", related, { carousel: true }));
  } else {
    kids.push(el("p", { class: "s3-related-empty", "data-testid": "s3-related-empty",
      text: "관련 추천 작품이 없습니다" }));
  }

  // ⑫ 하단 — 대화방 목록·한도 + [프로필 선택] [대화 시작]
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
/* 메시지 액션 (system-spec §5·§5-1)
 * 최신 교환에만 편집·삭제·재생성이 붙고, 과거 턴에는 분기만 붙습니다. 과거 턴에 편집을
 * 열어 두면 "어느 시점까지 되돌렸는가"가 흐려져 재계산의 기대값을 적을 수 없습니다.
 */
function msgActions(m, room) {
  if (!room || m.turn < 1 || chatStreaming) return null;
  const key = "s4-msg-" + m.turn + "-";
  const acts = [];

  if (isLatestExchange(room, m.turn)) {
    if (m.role === "user" && VN.editTurn !== m.turn) {
      acts.push(el("button", { class: "mini", "data-testid": key + "edit", text: "편집",
        onclick: () => startEdit(m.turn) }));
      acts.push(el("button", { class: "mini", "data-testid": key + "delete", text: "삭제",
        onclick: () => askDelete(m.turn) }));
    }
    if (m.role === "ai" && m.done) {
      acts.push(el("button", { class: "mini", "data-testid": key + "regen", text: "재생성",
        onclick: () => regenerateAt(m.turn, null) }));
    }
  } else if (m.role === "user") {
    acts.push(el("button", { class: "mini", "data-testid": key + "branch",
      text: "이 지점에서 분기", onclick: () => askBranch(m.turn) }));
  }

  // 기억 등록은 모든 메시지에 붙습니다 — 되돌림과 달리 과거 턴에도 쓸 수 있어야
  // "지난 대화에서 이건 기억해 둬"가 성립합니다 (system-spec §7-1)
  acts.push(el("button", {
    class: "mini" + (m.userMemory ? " on" : ""), "data-testid": key + m.role + "-remember",
    text: m.userMemory ? "기억 해제" : "기억하기",
    onclick: () => (m.userMemory ? dropUserMemory(m.turn, m.role) : addUserMemory(m.turn, m.role))
  }));

  return acts.length ? el("div", { class: "msg-actions" }, acts) : null;
}

function renderChatMessage(m, room) {
  const who = m.role === "ai" ? "ai" : "user";
  const editing = who === "user" && VN.editTurn === m.turn;
  const body = [];

  if (editing) {
    // 편집칸도 자유 입력과 같은 상한을 받습니다 — 되돌림 경로로 상한이 새면 안 됩니다
    const box = el("textarea", {
      class: "chat-input", "data-testid": "s4-edit-input", rows: "2",
      maxlength: String(CHAT_INPUT_MAX),
      oninput: (e) => {
        if (e.target.value.length > CHAT_INPUT_MAX) {
          e.target.value = e.target.value.slice(0, CHAT_INPUT_MAX);
        }
      }
    });
    box.value = m.text;
    body.push(el("div", { class: "msg-edit" }, [
      box,
      el("div", { class: "msg-actions" }, [
        el("button", { class: "mini primary", "data-testid": "s4-edit-save", text: "저장",
          onclick: () => regenerateAt(m.turn, box.value.trim().slice(0, CHAT_INPUT_MAX)) }),
        el("button", { class: "mini", "data-testid": "s4-edit-cancel", text: "취소",
          onclick: () => cancelEdit() })
      ])
    ]));
  } else {
    body.push(el("div", { class: "bubble" }, [
      el("span", { class: "bubble-text", text: m.done ? m.text : "" })
    ]));
    // 필터가 후보를 걸러 냈으면 표기합니다 — 조용히 대체하면 필터가 돈 것이 안 보입니다
    if (m.filtered) {
      body.push(el("span", { class: "msg-note", "data-testid": "s4-msg-" + m.turn + "-filtered",
        text: "안전 필터가 후보를 걸러 냈습니다" }));
    }
    if (m.leak) {
      body.push(el("span", { class: "msg-note", "data-testid": "s4-msg-" + m.turn + "-leak",
        text: "내부 지시 요청 — 정해진 거절문만 나갑니다" }));
    }
  }

  const acts = msgActions(m, room);
  if (acts) body.push(acts);

  return el("div", {
    class: "msg " + who + (m.fail ? " fail" : "") + (m.done ? "" : " typing"),
    "data-testid": "s4-msg-" + m.turn + "-" + who
  }, body);
}

/* 세이프티 안내 모달 (system-spec §9-1)
 * 입력 차단은 사유가 갈리므로 종류별로 다른 문구를 냅니다 — 「왜 막혔는가」가 화면에서
 * 읽히지 않으면 테스터가 금칙어와 우회 시도를 구분할 수 없습니다. */
const BLOCK_TITLE = {
  blocked: "금칙어가 포함되어 있습니다.",
  jailbreak: "설정을 바꾸려는 시도로 판정되었습니다.",
  inject: "지시문 삽입으로 판정되었습니다."
};

function renderBlockedInputModal() {
  const b = VN.blockedInput;
  return el("div", { class: "modal", "data-testid": "g-blocked-modal" }, [
    el("div", { class: "modal-box" }, [
      el("h3", { class: "nf-title", "data-testid": "g-blocked-title",
        text: BLOCK_TITLE[b.kind] || "전송할 수 없습니다." }),
      el("p", { "data-testid": "g-blocked-body", text: b.reason }),
      el("p", { class: "lede-sm", "data-testid": "g-blocked-kind", text: b.kind }),
      el("p", { class: "lede-sm", "data-testid": "g-blocked-note",
        text: "재화·턴은 소비되지 않았습니다. 친 내용은 입력창에 그대로 있습니다." }),
      el("div", { class: "nf-btns" }, [
        el("button", { class: "primary", "data-testid": "g-blocked-close", text: "확인",
          onclick: () => closeBlockedInput() })
      ])
    ])
  ]);
}

/* 출력 차단 — 그 턴의 후보가 전부 금칙이라 응답을 내보내지 않은 경우 */
function renderBlockedOutputModal() {
  return el("div", { class: "modal", "data-testid": "g-outblock-modal" }, [
    el("div", { class: "modal-box" }, [
      el("h3", { class: "nf-title", "data-testid": "g-outblock-title",
        text: "응답이 차단되었습니다." }),
      el("p", { "data-testid": "g-outblock-body",
        text: "안전 필터가 이 응답을 내보내지 않았습니다. 재화·턴은 소비되지 않았습니다." }),
      el("div", { class: "nf-btns" }, [
        el("button", { class: "primary", "data-testid": "g-outblock-close", text: "확인",
          onclick: () => closeBlockedOutput() })
      ])
    ])
  ]);
}

/* 되돌릴 수 없는 동작을 한 번 묻는 모달 — 되돌림(삭제·분기)과 세이브(덮어쓰기)가
 * 같은 모달을 씁니다. 화면 위에 얹히는 전역 요소라 testid도 전역 접두사(`g-`)를 씁니다. */
const CONFIRM_TEXT = {
  delete: {
    title: "삭제하시겠습니까?",
    body: "이 교환(유저 메시지와 응답)을 삭제합니다. 호감도와 기억에서 이 턴의 기여분이 함께 "
      + "사라지며, 이미 쓴 재화는 되돌아오지 않습니다."
  },
  branch: {
    title: "분기하시겠습니까?",
    body: "이 지점까지의 대화를 복사한 새 대화방을 만듭니다. 지금 방은 그대로 남고, 두 방은 "
      + "이후 서로에게 영향을 주지 않습니다."
  },
  overwrite: {
    title: "덮어쓰시겠습니까?",
    body: "이미 저장된 슬롯입니다. 지금 시점으로 덮어쓰면 앞서 저장한 시점은 사라집니다."
  }
};

function renderConfirmModal() {
  const c = VN.confirm;
  const t = CONFIRM_TEXT[c.kind];
  const where = c.kind === "overwrite" ? c.slot + "번 슬롯" : c.turn + "턴 지점";
  return el("div", { class: "modal", "data-testid": "g-confirm" }, [
    el("div", { class: "modal-box" }, [
      el("h3", { class: "nf-title", "data-testid": "g-confirm-title", text: t.title }),
      el("p", { "data-testid": "g-confirm-body", text: t.body }),
      el("p", { class: "lede-sm", "data-testid": "g-confirm-target", text: where }),
      el("div", { class: "nf-btns" }, [
        el("button", { class: "primary", "data-testid": "g-confirm-ok", text: "확인",
          onclick: () => runConfirm() }),
        el("button", { "data-testid": "g-confirm-cancel", text: "취소",
          onclick: () => closeConfirm() })
      ])
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
  send.disabled = chatStreaming || room.ended || !!room.ending;

  // 고정 선택지 — 이번 턴에 제시된 것만 노출됩니다 (system-spec §4-1)
  const set2 = mockSetFor(room.charId, room.scenarioId);
  const nextDef = set2.turns[room.turn];
  const choices = (!room.ending && !room.ended && nextDef && nextDef.choices) ? nextDef.choices : [];

  const foot = [
    choices.length
      ? el("div", { class: "chat-choices", "data-testid": "s4-choices" },
          choices.map((ch, i) => el("button", {
            class: "choice", "data-testid": "s4-choice-" + (i + 1),
            text: ch.label, onclick: () => pickChoice(ch.label, ch.delta)
          })))
      : null,
    // 유저가 친 내용은 응답 선택에 관여하지 않습니다 — 입력창 옆에 그 사실을 둡니다
    el("p", { class: "hint scope", "data-testid": "s4-scope-note",
      text: "친 내용은 응답 선택에 관여하지 않습니다(입력 필터·길이 상한·호칭 치환만). "
        + "자연어 지시는 이 SUT의 범위 밖입니다." }),
    el("div", { class: "chat-foot-head" }, [
      el("span", { class: "count", "data-testid": "s4-input-count", text: "0/" + CHAT_INPUT_MAX }),
      chatStreaming
        ? el("span", { class: "streaming", "data-testid": "s4-streaming", text: "응답 표시 중…" })
        : null
    ].filter(Boolean)),
    el("div", { class: "chat-send" }, [input, send])
  ];
  if (room.ending) {
    foot.push(el("div", { class: "ending-card", "data-testid": "s4-ending" }, [
      el("p", { class: "ending-kind", "data-testid": "s4-ending-kind", text: room.ending + " 엔딩" }),
      el("p", { class: "ending-note",
        text: "호감도 " + room.affection + " · 단계 " + stageOf(room.affection).name }),
      el("p", { class: "ending-note", text: "엔딩에 도달해 이 방에서는 더 이상 전송할 수 없습니다." })
    ]));
  } else if (room.ended) {
    foot.push(el("p", {
      class: "chat-end", "data-testid": "s4-ended",
      text: "이 경로의 마지막 턴까지 왔습니다."
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
        class: "icon", "data-testid": "s4-save", text: "세이브",
        onclick: () => openPanel("p1")
      }),
      el("button", {
        class: "icon", "data-testid": "s4-state", text: "현재 상태",
        onclick: () => openPanel("p2")
      }),
      el("button", {
        class: "icon", "data-testid": "s4-wallet",
        text: "캔디 " + (currentAccount() ? currentAccount().wallet.free : 0)
          + " / 크리스탈 " + (currentAccount() ? currentAccount().wallet.paid : 0),
        onclick: () => openPanel("p3")
      }),
      renderDebugButton()      // 셸이 없는 화면이라 여기 단독으로 둡니다
    ]),
    el("div", { class: "chat-log", "data-testid": "s4-log" },
      room.messages.map((m) => renderChatMessage(m, room))),
    el("div", { class: "chat-foot" }, foot)
  ]);
}

/* ── S5 채팅 탭 ────────────────────────────────────────────
 * 캐릭터 페이지의 방 목록이 **그 캐릭터의 방**만 보여 주는 데 비해, 여기는 **계정의 방
 * 전부**를 봅니다. 그래서 방·분기가 여러 캐릭터에 걸쳐 있을 때 어디에 무엇이 있는지가
 * 이 화면에서만 읽힙니다.
 *
 * 대화수(유저+AI 턴 합산·첫 메시지 포함)는 이 화면과 S6 합계가 같은 값을 써야 합니다 —
 * 두 곳에서 따로 세면 「방 카드와 MY 합계가 어긋나는」 결함이 만들어집니다.
 */
function renderS5() {
  const acc = currentAccount();
  const rooms = acc ? acc.rooms : [];
  const kids = [
    el("h2", { class: "screen-title", text: "채팅" }),
    el("p", { class: "hint", "data-testid": "s5-summary",
      text: "대화방 " + rooms.length + "개 · 대화수 합계 "
        + rooms.reduce((n, r) => n + roomMessageCount(r), 0) })
  ];

  if (!rooms.length) {
    kids.push(el("p", { class: "empty", "data-testid": "s5-empty",
      text: "진행 중인 대화가 없습니다. 홈에서 캐릭터를 골라 시작해 주세요." }));
    return el("section", { class: "screen s5", "data-testid": "s5-screen" }, kids);
  }

  // 최근에 연 방이 위로 — active가 지금 방입니다
  const sorted = rooms.slice().sort((a, b) => (b.active ? 1 : 0) - (a.active ? 1 : 0));
  kids.push(el("div", { class: "room-list", "data-testid": "s5-rooms" }, sorted.map((r) => {
    const c = findCharacter(r.charId);
    const stage = stageOf(r.affection);
    return el("div", { class: "s5-room" + (r.active ? " here" : ""), "data-testid": "s5-room-" + r.id }, [
      el("button", { class: "room-item", "data-testid": "s5-room-" + r.id + "-open",
        onclick: () => resumeChat(r.id) }, [
        el("span", { class: "room-name",
          text: (c ? c.name : r.charId) + " · " + (c ? c.pageTitle : "")
            + (r.active ? " (지금 방)" : "") }),
        el("span", { class: "room-sub", "data-testid": "s5-room-" + r.id + "-info",
          text: (r.profile ? r.profile.name : "프로필 없음")
            + (r.profile && r.profile.label ? "(" + r.profile.label + ")" : "")
            + " · " + stage.name + " " + r.affection + " · " + r.turn + "턴"
            + (r.ending ? " · " + r.ending + " 엔딩" : "") }),
        el("span", { class: "room-sub", "data-testid": "s5-room-" + r.id + "-count",
          text: "대화수 " + roomMessageCount(r)
            + " · 세이브 " + Object.keys(r.slots || {}).length + "/" + SLOT_COUNT })
      ]),
      el("button", { class: "mini", "data-testid": "s5-room-" + r.id + "-delete", text: "삭제",
        onclick: () => removeChat(r.id) })
    ]);
  })));

  return el("section", { class: "screen s5", "data-testid": "s5-screen" }, kids);
}

/* ── S6 MY 탭 ──────────────────────────────────────────────
 * 여러 영역의 값이 한 화면에 모입니다 — 대화수 합계(대화 세션) · 좋아요/스크랩(탐색) ·
 * 재화(재화) · 세이프티 필터(게이팅) · 로그아웃(앱 진입/세션). 그래서 이 화면의 검증은
 * **다른 화면에서 만든 상태가 여기에 그대로 오는가**입니다.
 */
function renderS6() {
  const acc = currentAccount();
  // 정상 경로에서는 라우팅 가드가 막아 여기까지 오지 않습니다. 가드가 뚫린 상태
  // (gate-bypass 주입)에서도 화면이 깨지지 않아야 주입이 다른 영역까지 흔들지 않습니다
  if (!acc) {
    return el("section", { class: "screen s6", "data-testid": "s6-screen" }, [
      el("h2", { class: "screen-title", text: "MY" }),
      el("p", { class: "empty", "data-testid": "s6-noaccount", text: "로그인이 필요합니다." })
    ]);
  }
  const rooms = acc.rooms;
  const total = rooms.reduce((n, r) => n + roomMessageCount(r), 0);
  const stats = VN.sheet.accountStats || { followers: 0, following: 0 };

  const kids = [
    el("h2", { class: "screen-title", text: "MY" }),
    el("div", { class: "my-id" }, [
      el("span", { class: "avatar lg", text: accountDisplayName(VN.accountId).slice(0, 1) }),
      el("div", {}, [
        el("p", { class: "p4-name", "data-testid": "s6-account", text: accountDisplayName(VN.accountId) }),
        el("p", { class: "p4-adult", "data-testid": "s6-gate", text: GATE_LABEL[gateState()] })
      ])
    ]),
    el("dl", { class: "p2-list", "data-testid": "s6-stats" }, [
      el("dt", { text: "대화수 합계" }),
      el("dd", { "data-testid": "s6-total-count", text: String(total) }),
      el("dt", { text: "대화방" }),
      el("dd", { "data-testid": "s6-room-count", text: rooms.length + "개" }),
      // 팔로워·팔로잉은 시트 값의 표시만입니다 — 소셜은 제외 영역이라 동작이 없습니다
      el("dt", { text: "팔로워" }),
      el("dd", { "data-testid": "s6-followers", text: String(stats.followers) }),
      el("dt", { text: "팔로잉" }),
      el("dd", { "data-testid": "s6-following", text: String(stats.following) })
    ]),
    el("button", { class: "p4-my", "data-testid": "s6-wallet",
      text: "보유 재화 — 캔디 " + acc.wallet.free + " / 크리스탈 " + acc.wallet.paid,
      onclick: () => openPanel("p3") }),
    el("button", { class: "p4-my", "data-testid": "s6-missions",
      text: "웰컴 미션 받기", onclick: () => openPanel("p4") })
  ];

  /* 세이프티 필터 — 성인 인증 계정에만 노출됩니다. 게이팅과 층이 다릅니다:
   * 필터는 목록에서 아예 숨기고(존재도 안 보임), 게이팅은 가린 채 남깁니다 (system-spec §9) */
  if (gateState() === "adult") {
    const btn = el("button", {
      class: "p4-my" + (acc.safetyFilter ? " on" : ""), "data-testid": "s6-safety-toggle",
      text: "세이프티 필터 — " + (acc.safetyFilter ? "켜짐(언세이프 숨김)" : "꺼짐"),
      onclick: () => toggleSafetyFilter()
    });
    kids.push(btn);
  } else {
    kids.push(el("p", { class: "hint", "data-testid": "s6-safety-hidden",
      text: "세이프티 필터는 성인 인증 계정에만 노출됩니다." }));
  }

  // 활동 목록 — 좋아요·스크랩은 탐색 화면에서 만든 상태가 그대로 와야 합니다
  const actRow = (label, ids, key) => el("div", { class: "sec" }, [
    el("h3", { class: "sec-title", text: label + " " + ids.length + "건" }),
    ids.length
      ? el("div", { class: "act-list", "data-testid": "s6-activity-" + key },
          ids.map((id) => {
            const c = findCharacter(id);
            return el("button", {
              class: "act-item", "data-testid": "s6-activity-" + key + "-" + id,
              text: c ? c.pageTitle + " · " + c.name : id,
              onclick: () => { VN.pageCharId = id; go("s3"); }
            });
          }))
      : el("p", { class: "empty", "data-testid": "s6-activity-" + key + "-empty", text: "없습니다." })
  ]);
  kids.push(actRow("좋아요", acc.likes, "like"));
  kids.push(actRow("스크랩", acc.scraps, "scrap"));

  // 스텁 진입점 — 제외 영역임을 화면에서 읽히게 둡니다
  kids.push(el("div", { class: "sec" }, [
    el("h3", { class: "sec-title", text: "그 외" }),
    el("div", { class: "stub-links", "data-testid": "s6-stubs" },
      [["내 서재", "s6-stub-library"], ["공지", "s6-stub-notice"], ["FAQ", "s6-stub-faq"],
       ["문의", "s6-stub-ask"], ["설정", "s6-stub-settings"]].map(([label, id]) =>
        el("button", { class: "sub-btn", "data-testid": id, text: label,
          onclick: () => toast("검증 범위에서 제외한 영역입니다(트리 제외 영역 참조).") })))
  ]));

  kids.push(el("button", { class: "primary-btn", "data-testid": "s6-logout", text: "로그아웃",
    onclick: () => { logout(); render(); } }));

  return el("section", { class: "screen s6", "data-testid": "s6-screen" }, kids);
}

function renderPlaceholder(key, label) {
  return el("section", { class: "screen todo", "data-testid": key + "-todo" }, [
    el("h2", { text: label }),
    el("p", { text: "다음 구현 단위입니다." })
  ]);
}
