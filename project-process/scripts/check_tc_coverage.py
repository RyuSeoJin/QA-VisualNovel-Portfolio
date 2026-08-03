# -*- coding: utf-8 -*-
"""커버리지 대조 — 덮이지 않은 것을 목록으로 낸다 (rules/case-expansion.md §커버리지 보증)

무엇을 맞추는가
--------------
  ① 기획 축   기능 트리의 **구현 잎** ↔ TC의 covers
  ② 구현 축   청사진 §3-1의 **testid** ↔ TC의 covers
  ③ 상태 축   트리 잎의 **[상태:] 선언** ↔ TC의 상태(14번째 값)

  한 축만 보면 반대쪽이 통째로 샌다. 트리만 보면 푸터 링크·모달 닫기처럼 트리에 없는 화면
  요소가 빠지고, testid만 보면 집계·격리처럼 화면에 드러나지 않는 규칙이 빠진다.
  상태 축은 잎 안에서 갈린다 — [상태:]가 선언된 잎은 선언된 상태 각각에 그 잎을 covers하고
  상태 값에 그 라벨을 포함한 TC가 최소 하나씩 있어야 한다(depth-and-tn.md §상태 축).

covers는 무엇인가
----------------
  TC 한 줄의 13번째 값이며, 그 케이스가 덮는 좌표를 담은 배열이다. 두 축을 한 배열에 섞어
  담고 값의 모양으로 가른다 — `>`가 있으면 트리 경로, 없으면 testid.

      ["앱 진입/세션 > 진입 분기 > 미로그인 보호 동작 차단", "g-nav-chat", "g-login-modal"]

  한 케이스가 두 축을 동시에 덮는 것이 보통이라 필드를 나누지 않았다. 나누면 어느 쪽에 적을지를
  케이스마다 판단해야 한다.

트리 경로는 어떻게 적나
----------------------
  잎의 **전체 경로**를 ` > `로 잇는다. 잎 이름만으로는 같은 이름이 여러 가지에 있을 때 갈리지
  않는다. 꼬리만 적어도 유일하게 걸리면 통과시킨다 — 전수 경로를 외우게 하면 좌표를 안 달게 된다.

제외는 어떻게 적나
-----------------
  프로젝트의 `test-case/{프로젝트}-coverage-waiver.json`에 사유와 함께 적는다. 제외는 누락이
  아니라 판단이므로 사유가 없으면 제외로 인정하지 않는다. 형식:

      {"waivers": [{"target": "t1-save", "reason": "테스트 설비(디버그 콘솔) — 검증 대상 아님"}]}

사용법
------
    python check_tc_coverage.py <tc-input.json> --tree <feature-tree.md> \
        --blueprint <sut-blueprint.md> [--waiver <coverage-waiver.json>]

  덮이지 않은 것이 하나라도 있으면 종료 코드 1로 끝난다.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_feature_tree import parse  # noqa: E402

# 자리표시자를 포함해 잡는다 — `s2-card-{id}` · `s2-rank-period-{구간}`처럼 중괄호와 한글이
# 들어간 표기가 등재 표의 정상 형태다. 중괄호를 빼면 그 행이 통째로 안 잡혀 접두를 잃는다
TESTID_RE = re.compile(r"`([a-z][a-z0-9]*-[a-z0-9가-힣{}|\\-]+|-[a-z][a-z0-9-]*)`")


def tree_leaves(md_path):
    """구현 범위의 잎만 — 자식이 있는 노드는 묶음이라 검증 단위가 아니다."""
    with open(md_path, encoding="utf-8") as f:
        data = parse(f.read())
    nodes = data["nodes"]
    has_child = set()
    for i, n in enumerate(nodes):
        for m in nodes[i + 1:]:
            if m["depth"] <= n["depth"]:
                break
            has_child.add(id(n))
            break
    return [n for n in nodes
            if n["scope"] == "구현" and id(n) not in has_child], data["version"]


TESTID_SECTION = "### 3-1."


def blueprint_testids(md_path):
    """§3-1 등재 표의 testid — `{n}`·`{id}` 같은 자리표시자가 든 것은 접두로 맞춘다.

    **§3-1 절 안만 읽는다.** 문서 전체를 훑으면 다른 절의 백틱이 함께 잡힌다 — §3-3의
    `?inject={결함}` 행에 나열된 결함 이름(`save-leak` 등)은 URL 파라미터 **값**이지
    화면 요소가 아닌데, 그것까지 세면 등재 수(분모)가 부풀고 「검증하지 않기로 판단했다」는
    기록이 없던 판단을 만들어 낸다. 결함 주입의 검증은 자동화의 주입 매트릭스가 맡는다.
    """
    with open(md_path, encoding="utf-8") as f:
        lines, inside = [], False
        for l in f.read().splitlines():
            if l.startswith("### "):
                inside = l.startswith(TESTID_SECTION)
            elif inside and l.lstrip().startswith("| ✅"):
                lines.append(l)
    exact, prefixes = set(), set()
    for line in lines:
        bases = []
        for raw in TESTID_RE.findall(line):
            if raw.startswith("-"):
                # 축약형(`-title`)은 같은 행 앞 항목의 이름을 잇는 표기다 — 펴서 등재한다.
                # 펴지 않으면 실재하는 id가 「청사진에 없음」으로 잡혀 오타 검사가 헛돈다
                for b in bases:
                    exact.add(b + raw)
                continue
            raw = raw.replace("\\", "")          # 표의 파이프 이스케이프
            m = re.search(r"\{([^}]*)\}", raw)
            if m and "|" in m.group(1):
                # 선택지 표기(`p2-{temp|nickname}-row`)는 실제 이름 여럿을 줄인 것이라 편다.
                # 뒤의 `-row`는 그 행이 나열하는 접미 중 첫 번째이므로, 편 이름 전체를
                # 등재하면서 **어간**(`p2-temp`)을 다음 접미가 붙을 자리로 남긴다
                head, tail = raw[:m.start()], raw[m.end():]
                stems = [head + alt for alt in m.group(1).split("|")]
                exact.update(s + tail for s in stems)
                bases = stems
            elif m:
                prefixes.add(raw.split("{")[0])
                bases = []           # 자유 자리표시자는 이을 이름이 되지 못한다
            else:
                exact.add(raw)
                bases = [raw]
    return exact, prefixes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--tree", required=True)
    ap.add_argument("--blueprint", required=True)
    ap.add_argument("--waiver")
    args = ap.parse_args()

    cfg = json.load(open(args.input, encoding="utf-8"))
    tcs = cfg.get("tcs") or []

    leaves, tree_version = tree_leaves(args.tree)
    testids, id_prefixes = blueprint_testids(args.blueprint)

    waived, waived_prefix = set(), []
    if args.waiver and os.path.exists(args.waiver):
        for w in json.load(open(args.waiver, encoding="utf-8")).get("waivers", []):
            if not w.get("reason"):
                continue        # 사유 없는 제외는 인정하지 않는다
            t = w["target"]
            # 끝의 *는 접두 제외 — 디버그 콘솔처럼 묶음 전체가 검증 대상이 아닐 때 쓴다
            (waived_prefix.append(t[:-1]) if t.endswith("*") else waived.add(t))

    def is_waived(name):
        return name in waived or any(name.startswith(pre) for pre in waived_prefix)

    # ── covers·상태 수집 — 상태는 케이스가 밟는 상태 목록(쉼표 복수, 생략 시 성인 인증)
    STATE_DEFAULT = "성인 인증"
    GATE_STATES = {"미로그인", "본인인증 미진행", "성인 인증", "미성년", "세션 만료"}
    paths, ids, no_covers = [], set(), []
    tc_states = []            # (tc_id, covers 경로 목록, 상태 집합)
    bad_states = []           # 5종 밖의 상태 값 — 오타
    for t in tcs:
        cov = t[12] if len(t) >= 13 else []
        if not cov:
            no_covers.append(t[0])
        cov_paths = [c for c in cov if ">" in c]
        for c in cov:
            (paths.append(c) if ">" in c else ids.add(c))
        raw = (t[13] if len(t) >= 14 else "") or STATE_DEFAULT
        states = {s.strip() for s in str(raw).split(",") if s.strip()}
        for s in states - GATE_STATES:
            bad_states.append(f"{t[0]} — 「{s}」")
        tc_states.append((t[0], cov_paths, states))

    # ── ① 기획 축
    def covered(leaf):
        full = " > ".join(leaf["path"])
        for p in paths:
            if full == p or full.endswith(" > " + p) or p.endswith(" > " + full):
                return True
        return False

    missed_leaves = [l for l in leaves
                     if not covered(l) and not is_waived(" > ".join(l["path"]))]

    # ── ③ 상태 축 — [상태:] 선언 잎은 선언된 상태마다 최소 한 케이스
    def path_match(full, p):
        return full == p or full.endswith(" > " + p) or p.endswith(" > " + full)

    missed_states = []
    for l in leaves:
        if not l.get("states"):
            continue
        full = " > ".join(l["path"])
        for s in [x.strip() for x in l["states"].split("·") if x.strip()]:
            hit = any(s in states and any(path_match(full, p) for p in cov_paths)
                      for _, cov_paths, states in tc_states)
            if not hit and not is_waived(f"{full} × {s}"):
                missed_states.append(f"{full} × {s}")

    # ── ② 구현 축
    missed_ids = sorted(t for t in testids if t not in ids and not is_waived(t))

    # ── 좌표가 실재하는지 (오타 잡기)
    leaf_full = {" > ".join(l["path"]) for l in leaves}
    unknown_paths = sorted({p for p in paths if not any(
        f == p or f.endswith(" > " + p) or p.endswith(" > " + f) for f in leaf_full)})
    unknown_ids = sorted(i for i in ids
                         if i not in testids and not any(i.startswith(p) for p in id_prefixes))

    print(f"트리 {tree_version} · 구현 잎 {len(leaves)} · testid {len(testids)} · TC {len(tcs)}")
    print(f"덮인 잎 {len(leaves) - len(missed_leaves)}/{len(leaves)} · "
          f"덮인 testid {len(testids) - len(missed_ids)}/{len(testids)}")
    if waived or waived_prefix:
        print(f"제외 {len(waived) + len(waived_prefix)}건 (사유 있음)")

    bad = False
    for title, rows in (("좌표가 없는 TC", no_covers),
                        ("덮이지 않은 트리 잎", [" > ".join(l["path"]) for l in missed_leaves]),
                        ("잎 × 상태 — 미검증", missed_states),
                        ("덮이지 않은 testid", missed_ids),
                        ("트리에 없는 경로 (오타 의심)", unknown_paths),
                        ("청사진에 없는 testid (오타 의심)", unknown_ids),
                        ("상태 값 오타 (5종 밖)", bad_states)):
        if rows:
            bad = True
            print(f"\n[{title}] {len(rows)}건")
            for r in rows:
                print("  -", r)

    if not bad:
        print("\n덮이지 않은 것이 없습니다.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
