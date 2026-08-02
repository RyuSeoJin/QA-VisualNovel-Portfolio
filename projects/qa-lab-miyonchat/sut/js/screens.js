/* 화면 렌더 — 첫 슬라이스는 전역 셸 + S1 로그인 + 탭 자리표시자입니다.
 * data-testid 명명은 {화면}-{요소}[-{수식어}] kebab-case (청사진 §3-1).
 */

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  for (const k in attrs || {}) {
    if (k === "text") node.textContent = attrs[k];
    else if (k === "html") node.innerHTML = attrs[k];
    else if (k === "onclick") node.addEventListener("click", attrs[k]);
    else node.setAttribute(k, attrs[k]);
  }
  (children || []).forEach((c) => c && node.appendChild(c));
  return node;
}

/* S1 로그인 — 진입점이 아니라 보호 동작 시도 시 뜨는 화면.
 * 로그인하면 원래 하려던 곳으로 이어집니다(system-spec §1-1). */
function renderS1() {
  const pick = (id) => { login(id); resumeIntent(); render(); };
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
function renderTopBar() {
  const acc = currentAccount();
  const items = [
    el("button", {
      class: "logo", "data-testid": "g-logo", text: "MiyonChat",
      onclick: () => goHome()
    }),
    el("input", {
      class: "search", "data-testid": "g-search", type: "text",
      placeholder: "캐릭터 검색"
    }),
    el("button", { class: "icon", "data-testid": "g-noti", text: "알림" }),
    renderDebugButton()          // 테스트 설비 — 로그인 여부와 무관하게 항상 노출
  ];
  if (isLoggedIn()) {
    items.push(el("button", {
      class: "icon", "data-testid": "g-wallet",
      text: "캔디 " + acc.wallet.free + " / 크리스탈 " + acc.wallet.paid
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
      onclick: () => { go("s1"); }
    }));
  }
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
            text: ACCOUNTS[id].minor ? "미성년 (언세이프 열람 불가)"
              : acc.adultVerified ? "성인 인증 완료" : "성인 미인증 (인증 시 해제 가능)"
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

function renderPanel() {
  if (VN.panel === "p4") return renderP4();
  return null;
}

function renderPlaceholder(key, label) {
  return el("section", { class: "screen todo", "data-testid": key + "-todo" }, [
    el("h2", { text: label }),
    el("p", { text: "다음 구현 단위입니다." })
  ]);
}
