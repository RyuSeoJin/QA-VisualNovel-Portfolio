# -*- coding: utf-8 -*-
"""
structure.svg (정본) -> index.html 인라인 사본 주입

왜 필요한가
-----------
구조도는 두 곳에서 쓰인다.

  README.md   <img src="structure.svg">        파일을 그대로 참조
  index.html  <svg> … </svg>                   같은 마크업을 품음

index.html은 "네트워크 요청 0건인 자기완결 단일 파일" 규칙(CLAUDE.md 산출물 출력 방식)
때문에 파일을 참조할 수 없어서 마크업을 복사해 넣는다. 손으로 맞추면 한쪽만 고쳤을 때
두 그림이 갈라지는데, 겉으로는 아무 에러도 나지 않아 한참 모른다.

그래서 structure.svg를 정본으로 두고 index.html 쪽은 이 도구로만 갱신한다.

무엇을 하는가
-------------
index.html의 마커 사이를 structure.svg 내용으로 통째로 교체한다. 변환은 하지 않는다.
structure.svg가 index.html에 그대로 들어가도 되게 만들어져 있기 때문이다.

  * root에 class="sd"가 붙어 있어 index.html의 다크 테마 CSS가 걸린다
  * id가 sdt/sdd라서 페이지 안에서 충돌하지 않는다
  * width/height는 .sd{width:100%;height:auto}가 덮으므로 남아 있어도 무해하다

structure.svg의 root 속성이나 id를 바꾸면 이 전제가 깨진다. 바꿀 때는 index.html의
CSS(.sd 규칙)를 함께 확인할 것.

사용법
------
    python inline_structure_svg.py            주입 (index.html 갱신)
    python inline_structure_svg.py --check    동기 확인만 (다르면 exit 1)

--check는 커밋 전 확인용이다. 정본을 고치고 주입을 잊은 상태를 잡아낸다.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "structure.svg"
DST = ROOT / "index.html"

START = ("<!-- STRUCTURE-SVG:START — 정본은 structure.svg. "
         "직접 고치지 말고 inline_structure_svg.py로 주입할 것 -->")
END = "<!-- STRUCTURE-SVG:END -->"


def fail(msg):
    print(f"[inline_structure_svg] {msg}", file=sys.stderr)
    sys.exit(2)


def locate(html):
    """마커 사이 구간의 (시작, 끝) 인덱스를 돌려준다."""
    i = html.find(START)
    if i < 0:
        fail(f"{DST.name}에 START 마커가 없다. 마커를 복원할 것:\n  {START}")
    j = html.find(END, i)
    if j < 0:
        fail(f"{DST.name}에 END 마커가 없다. 마커를 복원할 것:\n  {END}")
    return i + len(START), j


def main():
    ap = argparse.ArgumentParser(description="structure.svg를 index.html에 주입한다")
    ap.add_argument("--check", action="store_true",
                    help="주입하지 않고 동기 여부만 확인한다 (다르면 exit 1)")
    args = ap.parse_args()

    for p in (SRC, DST):
        if not p.exists():
            fail(f"{p} 가 없다")

    svg = SRC.read_text(encoding="utf-8").strip()
    html = DST.read_text(encoding="utf-8")
    lo, hi = locate(html)
    current = html[lo:hi].strip()

    if args.check:
        if current == svg:
            print("[inline_structure_svg] 동기 상태 OK")
            return 0
        print("[inline_structure_svg] 어긋남 — structure.svg를 index.html에 주입할 것",
              file=sys.stderr)
        return 1

    if current == svg:
        print("[inline_structure_svg] 이미 동기 상태 — 변경 없음")
        return 0

    DST.write_text(html[:lo] + "\n" + svg + "\n" + html[hi:], encoding="utf-8")
    print(f"[inline_structure_svg] 주입 완료 — {DST.name} 갱신")
    return 0


if __name__ == "__main__":
    sys.exit(main())
