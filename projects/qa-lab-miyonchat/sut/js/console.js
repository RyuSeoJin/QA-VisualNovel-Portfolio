/* T1 디버그 콘솔 — 트리 밖 테스트 설비(청사진 §1 T1)
 *
 * 상단 바의 [디버그] 버튼으로 열리는 모달입니다. 배경은 딤 처리해 상호작용을 막습니다.
 * 셸이 없는 화면(S1)에서는 같은 버튼이 화면 우상단에 단독으로 놓입니다.
 *
 * 사람은 이 UI로, 자동화는 __VN__.setData()로 같은 저장소에 씁니다(§3-4).
 */

let consoleOpen = false;

const DEBUG_NOTICE =
  "해당 디버그는 테스트 환경을 용이하게 세팅하기 위하여 여러 세팅값을 넣었습니다. " +
  "테스트 페이지에서 F5 등 새로고침을 하게 되면 데이터가 기본값으로 초기화되니, " +
  "데이터를 유지한 상태로 계속 페이지를 이용하려면 새로고침 행동은 " +
  "해당 디버그 화면의 [현재 화면 새로고침] 버튼으로 설정해 주세요.";

const STATE_PRESETS = [
  ["미로그인", "guest", () => { logout(); }],
  ["로그인 (성인 인증)", "adult", () => { login("a"); VN.accounts.a.adultVerified = true; VN.screen = "s2"; }],
  ["로그인 (미성년)", "minor", () => { login("b"); VN.screen = "s2"; }],
  ["세션 만료", "expired", () => {
    if (!VN.accountId) login("a");
    VN.session = SESSION.EXPIRED;
  }]
];

/* 빠른 데이터 조작 — 영역을 구현할 때마다 항목이 늘어납니다 */
const QUICK_ACTIONS = [
  ["이벤트 1건 추가 (하루·오늘)", "event-add", () => {
    const rows = VN.sheet.events.slice();
    rows.push({ user: "dbg" + rows.length, charId: "c1", day: VN.sheet.baseDay });
    window.__VN__.setData("events", rows);
  }],
  ["이벤트 전체 비우기", "event-clear", () => {
    window.__VN__.setData("events", []);
  }],
  ["알림 1건 추가", "noti-add", () => {
    const rows = VN.sheet.notifications.slice();
    rows.push({ id: "n" + (rows.length + 1), text: "디버그로 추가한 알림", day: VN.sheet.baseDay });
    window.__VN__.setData("notifications", rows);
  }]
];

function renderDebugButton() {
  return el("button", {
    class: "debug-btn", "data-testid": "g-debug", text: "디버그",
    onclick: () => { consoleOpen = true; render(); }
  });
}

function block(title, children) {
  return el("div", { class: "t1-block" }, [el("h3", { text: title })].concat(children));
}

function renderConsole() {
  if (!consoleOpen) return null;

  const notice = el("p", { class: "t1-notice", "data-testid": "t1-notice", text: DEBUG_NOTICE });

  const switcher = block("상태 스위처", STATE_PRESETS.map(([label, key, fn]) =>
    el("button", {
      "data-testid": "t1-state-" + key, text: label,
      onclick: () => { fn(); render(); }
    })
  ));

  const acc = currentAccount();
  const adultNow = el("p", {
    class: "hint", "data-testid": "t1-adult-state",
    text: !acc ? "현재: 미로그인"
      : ACCOUNTS[VN.accountId].minor ? "현재: 미성년 계정 (인증 불가)"
      : acc.adultVerified ? "현재: 성인 인증 완료" : "현재: 성인 미인증"
  });
  const adult = block("성인 인증", [
    adultNow,
    el("button", {
      "data-testid": "t1-adult-on", text: "계정 성인 인증 설정",
      onclick: () => {
        const r = setAdultVerified(true);
        if (!r.ok) alert(r.reason);
        render();
      }
    }),
    el("button", {
      "data-testid": "t1-adult-off", text: "계정 성인 인증 해제",
      onclick: () => {
        const r = setAdultVerified(false);
        if (!r.ok) alert(r.reason);
        render();
      }
    })
  ]);

  const baseDay = block("기준일 (가상 시계)", [
    el("input", { type: "text", "data-testid": "t1-baseday", value: VN.sheet.baseDay }),
    el("button", {
      "data-testid": "t1-baseday-apply", text: "적용",
      onclick: () => {
        const v = document.querySelector('[data-testid="t1-baseday"]').value.trim();
        if (v) window.__VN__.setBaseDay(v);
      }
    })
  ]);

  const quick = block("빠른 데이터 조작", QUICK_ACTIONS.map(([label, key, fn]) =>
    el("button", {
      "data-testid": "t1-quick-" + key, text: label,
      onclick: () => { fn(); }
    })
  ));

  const sheets = block("데이터 시트", SHEET_TABLES.map((table) => {
    const ta = el("textarea", {
      "data-testid": "t1-table-" + table, rows: "4",
      text: JSON.stringify(VN.sheet[table], null, 1)
    });
    return el("div", { class: "t1-table" }, [
      el("label", { text: table }),
      ta,
      el("button", {
        "data-testid": "t1-table-" + table + "-apply", text: table + " 적용",
        onclick: () => {
          try {
            window.__VN__.setData(table, JSON.parse(ta.value));
          } catch (e) {
            alert("JSON 형식 오류: " + e.message);
          }
        }
      })
    ]);
  }));

  const reset = block("초기화", [
    el("button", {
      "data-testid": "t1-reset", text: "전체 초기화 (reset)",
      onclick: () => { consoleOpen = false; window.__VN__.reset(); }
    })
  ]);

  const foot = el("div", { class: "t1-foot" }, [
    el("button", {
      class: "primary", "data-testid": "t1-refresh", text: "현재 화면 새로고침",
      onclick: () => { consoleOpen = false; render(); }   // 상태는 그대로 두고 다시 그립니다
    }),
    el("button", {
      "data-testid": "t1-close", text: "닫기",
      onclick: () => { consoleOpen = false; render(); }
    })
  ]);

  return el("div", { class: "t1-dim", "data-testid": "t1-dim" }, [
    el("aside", { class: "t1-console", "data-testid": "t1-console" }, [
      el("h2", { text: "디버그 설정" }),
      notice, switcher, adult, baseDay, quick, sheets, reset, foot
    ])
  ]);
}
