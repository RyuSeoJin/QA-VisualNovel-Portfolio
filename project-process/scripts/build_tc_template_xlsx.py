# -*- coding: utf-8 -*-
"""
TC 입력 JSON -> TC 시트 xlsx (5시트 자기완결 산출물)

파이프라인에서의 위치
--------------------
  test-case/{프로젝트}-tc-input-v{X.Y}.json   (설계 원본 = 정본)
    │  이 스크립트
    ▼
  test-case/{프로젝트}-tc-v{X.Y}.xlsx          (파생 = 배포물)

생성 시트
--------
  Test Case      한 행 = 한 TN = 한 스텝. 절차의 "1. / 2."를 스텝으로 분해하고
                 문체를 Test-Step '~한다' / Expected-Result '~된다'로 정규화
  Summary        케이스 단위 자동 집계(COUNTIFS). 기준 골격 버전을 C4에 자동 기입
  이슈 관리 시트   결함 기록(JIRA 미사용, 내장 운영). 드롭다운은 '목록' 시트 참조
  목록           드롭다운 참조 목록의 정본. 숨기지 않고 맨 뒤 배치
  명세서          구조 규칙의 정본 시트

규칙 정본
--------
  구조·컬럼   project-process/rules/tc-sheet-format.md + 이 산출물의 '명세서' 시트
  서식        design-template/xlsx-design-guide.md
              (헤더 #1F2A44/#F3F3F3 · 데이터 #FFFFFF/#000000 · 표 테두리 #999999
               · 실행 채움 셀 #FFF9C4 · 맑은 고딕 · 날짜 YYYY-MM-DD)

openpyxl 함정 3종 (2026-08-02 디버깅으로 확인 — Excel '복구' 프롬프트의 원인)
--------------------------------------------------------------------------
  1) freeze_panes=None 만으로 틀 고정을 풀면 pane을 참조하는 selection이 남아
     파일이 깨진다. sheet_view.selection 도 기본값으로 초기화해야 한다
  2) DataValidation.formula1 에 '=' 접두를 붙이면 안 된다 (openpyxl이 그대로 기록)
     교차 시트 참조는 정의된 이름(defined name)을 쓰는 편이 호환에 안전하다
  3) '='로 시작하는 설명 문구는 수식으로 저장되어 파일을 깨뜨린다.
     명세서의 수식 원형은 '=' 없이 적고 본문에서 안내한다

사용법:
    python build_tc_template_xlsx.py input.json -o out.xlsx
    (생성 후 Excel로 열어 경고 없이 열리는지 확인할 것 — 함정 재발 감시)

입력 JSON 스키마
----------------
{
  "title": "Test Case Template",
  "project": "miyonchat",                    # 이슈 ID 접두 · 목록 시트 기본값
  "tree_version": "{프로젝트}-tree-vX.Y",     # Summary C4 자동 기입 (마스터는 플레이스홀더)
  "platforms": ["Web", "And", "iOS"],
  "d1_order": ["앱 진입", ...],               # 1-Depth 표시 순서 (생략 시 등장 순)
  "env": {"OS": ["", "", ""], ...},          # 상단 환경 블록 기본값
  "lists": {"레이블": [...], ...},            # 목록 시트 덮어쓰기 (선택)
  "issue_samples": [[...20개 값...]],         # 이슈 시트 예시 행 (선택)
  "tcs": [
    ["TC-XXX-001","1-Depth","2-Depth","3-Depth","케이스",
     "사전조건","1. 절차\\n2. 절차","기대결과 문장. 여러 문장 가능.",
     "결정적|확률적|루브릭|금칙","High|Medium|Low",
     "선행 TC ID 또는 -","대상 서비스","비고"]
  ]
}
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from norm import to_step, to_expected, split_steps, split_expected  # noqa: E402,F401

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.views import Selection
from openpyxl.workbook.defined_name import DefinedName

# ── 서식 토큰 (xlsx-design-guide.md) ─────────────────────────
FONT = "맑은 고딕"
NAVY, SUBH = "1F2A44", "44546A"
HEADER_TEXT = "F3F3F3"
LABEL_FILL = "EDEFF4"
INPUT_FILL = "FFF9C4"        # 실행 채움 셀 — 설계 시점에는 비어 있는 칸
NOTE_TEXT = "555555"
BORDER_RGB = "999999"

HDR = PatternFill("solid", fgColor=NAVY)
SUB = PatternFill("solid", fgColor=SUBH)
LABEL = PatternFill("solid", fgColor=LABEL_FILL)
INPUT = PatternFill("solid", fgColor=INPUT_FILL)
WHITE = PatternFill("solid", fgColor="FFFFFF")

_side = Side(style="thin", color=BORDER_RGB)
BOX = Border(left=_side, right=_side, top=_side, bottom=_side)

VT_NOTE = {
    "결정적": "결정적 · 1회 실행, 기대값 불일치 시 FAIL",
    "확률적": "확률적 · 함수 안에서 N회 반복, 명시 임계 미달 시 FAIL (계측)",
    "루브릭": "루브릭 · 자동화하지 않음. 수동 채점 후 rubric-scores.csv로 통합",
    "금칙": "금칙 · 정의된 시도 목록 전부 실행, 하나라도 통과(차단 실패) 시 FAIL",
}

DEFAULT_LISTS = {
    "프로젝트": ["{프로젝트}"],
    "이슈 상태": ["Open", "In Progress", "Resolved", "Reopen", "Closed"],
    "우선순위": ["High", "Medium", "Low"],
    "빈도": ["Always", "Often", "Sometimes", "Once"],
    "버전(영향/수정 공용)": ["{디바이스}_{QA프로젝트}_RC1"],
    "해결책": ["Fixed", "Won't Do", "Won't Fix", "Duplicate", "Incomplete",
              "Cannot Reproduce", "Done", "Declined"],
    "환경": ["PC웹", "Android", "iOS"],
    "레이블": ["{기능 트리 1-Depth 영역명}"],
    "보고자": ["{작성자}"],
    "담당자": ["{담당자}"],
    "스프린트": ["{QA 프로젝트명}"],
}
LIST_NAME_MAP = {
    "프로젝트": "list_project", "이슈 상태": "list_status", "우선순위": "list_priority",
    "빈도": "list_frequency", "버전(영향/수정 공용)": "list_version",
    "해결책": "list_resolution", "환경": "list_env", "레이블": "list_label",
    "보고자": "list_reporter", "담당자": "list_assignee", "스프린트": "list_sprint",
}
ISSUE_HEADERS = ["프로젝트 ID", "Issue No.", "이슈 상태", "요약(Summary)", "설명",
                 "우선순위", "빈도", "영향 받는 버전", "수정 버전", "해결책", "환경",
                 "레이블", "보고자", "담당자", "관측자", "첨부파일", "스프린트",
                 "이슈 등록일", "이슈 최종 수정일자", "이슈 상태 최종 변경일자"]
ISSUE_WIDTHS = [12, 13, 12, 46, 50, 9, 10, 17, 17, 16, 8, 16, 9, 10, 12, 10, 13, 12, 14, 15]
# 드롭다운을 붙일 컬럼 -> 목록 이름
ISSUE_DV = {"B": "프로젝트", "D": "이슈 상태", "G": "우선순위", "H": "빈도",
            "I": "버전(영향/수정 공용)", "J": "버전(영향/수정 공용)", "K": "해결책",
            "L": "환경", "M": "레이블", "N": "보고자", "O": "담당자", "R": "스프린트"}


def hfont(size=9, color=HEADER_TEXT):
    return Font(name=FONT, size=size, bold=True, color=color)


def dfont(size=9, bold=False, color="000000"):
    return Font(name=FONT, size=size, bold=bold, color=color)


def unfreeze(ws):
    """틀 고정 해제 — selection까지 초기화하지 않으면 파일이 깨진다(함정 1)."""
    ws.freeze_panes = None
    ws.sheet_view.selection = [Selection(activeCell="A1", sqref="A1")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default="tc.xlsx")
    args = ap.parse_args()

    CFG = json.load(open(args.input, encoding="utf-8"))
    TCS = [tuple(t) for t in CFG["tcs"]]
    PLATFORMS = CFG.get("platforms", ["Web", "And", "iOS"])
    TITLE = CFG.get("title", "Test Case Template")
    PROJECT = CFG.get("project", "{프로젝트}")
    TREE_VERSION = CFG.get("tree_version", "{프로젝트}-tree-vX.Y")
    ENV = CFG.get("env", {k: [""] * len(PLATFORMS) for k in
                          ["OS", "단말", "버전", "작업자 이름", "작업 시작일"]})
    ORDER = CFG.get("d1_order") or list(dict.fromkeys(t[1] for t in TCS))

    LISTS = dict(DEFAULT_LISTS)
    LISTS["프로젝트"] = [PROJECT]
    for k, v in (CFG.get("lists") or {}).items():
        LISTS[k] = v

    # 선행 관계 -> 실행 단계
    PAR = {t[0]: t[10] for t in TCS}
    layer = {}

    def depth(tid):
        if tid in layer:
            return layer[tid]
        p = PAR.get(tid, "-")
        layer[tid] = 1 if p in ("-", "", None) else depth(p) + 1
        return layer[tid]

    # ── 컬럼 레이아웃 ────────────────────────────────────────
    DEPTH_COLS = ["C", "D", "E", "F", "G", "H", "I"]
    NP = len(PLATFORMS)
    base = [("A", "", 3), ("B", "No", 6),
            ("C", "1-Depth", 15), ("D", "2-Depth", 14), ("E", "3-Depth", 15),
            ("F", "4-Depth", 20), ("G", "5-Depth", 11), ("H", "6-Depth", 11),
            ("I", "7-Depth", 11), ("J", "Pre-Condition", 26), ("K", "TN", 5),
            ("L", "Test-Step", 34), ("M", "Expected-Result", 46), ("N", "Priority", 9)]
    c = ord("O")
    TOTAL_COLS = [chr(c + i) for i in range(NP)]
    c += NP
    RESULT_COLS = [chr(c + i) for i in range(NP)]
    c += NP
    ISSUE_COL, COMMENT, NOTE, EDIT = chr(c), chr(c + 1), chr(c + 2), chr(c + 3)
    LAST = EDIT
    tail = [(ISSUE_COL, "Issue No.", 11), (COMMENT, "Comment", 34),
            (NOTE, "Note", 30), (EDIT, "Test Case Edit", 12)]
    ALL_COLS = [b[0] for b in base[1:]] + TOTAL_COLS + RESULT_COLS + [t[0] for t in tail]

    wb = Workbook()

    # ══ Test Case ═══════════════════════════════════════════
    ws = wb.active
    ws.title = "Test Case"
    ws.sheet_view.showGridLines = False

    ws.merge_cells(f"B3:{LAST}3")
    tt = ws["B3"]
    tt.value = TITLE
    tt.font = hfont(11)
    tt.fill = HDR
    tt.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[3].height = 22

    for col, label, _w in base[1:] + tail:
        ws.merge_cells(f"{col}4:{col}5")
        x = ws[f"{col}4"]
        x.value = label
        x.font = hfont()
        x.fill = HDR
        x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.merge_cells(f"{TOTAL_COLS[0]}4:{TOTAL_COLS[-1]}4")
    ws[f"{TOTAL_COLS[0]}4"].value = "Total Result"
    ws.merge_cells(f"{RESULT_COLS[0]}4:{RESULT_COLS[-1]}4")
    ws[f"{RESULT_COLS[0]}4"].value = "Result"
    for cc in (TOTAL_COLS[0], RESULT_COLS[0]):
        ws[f"{cc}4"].font = hfont()
        ws[f"{cc}4"].fill = HDR
        ws[f"{cc}4"].alignment = Alignment(horizontal="center", vertical="center")
    for col, lab in list(zip(TOTAL_COLS, PLATFORMS)) + list(zip(RESULT_COLS, PLATFORMS)):
        x = ws[f"{col}5"]
        x.value = lab
        x.font = hfont()
        x.fill = SUB
        x.alignment = Alignment(horizontal="center", vertical="center")
    for r in (4, 5):
        for col in ALL_COLS:
            ws[f"{col}{r}"].border = BOX
    ws.row_dimensions[4].height = 18
    ws.row_dimensions[5].height = 16

    # 환경 블록 6~10행 — 라벨(N) + 병합 여백(Total 열) + 실행 채움 셀(Result 열)
    for i, (label, vals) in enumerate(ENV.items()):
        r = 6 + i
        lc = ws[f"N{r}"]
        lc.value = label
        lc.font = dfont(bold=True)
        lc.fill = LABEL
        lc.alignment = Alignment(horizontal="center", vertical="center")
        lc.border = BOX
        ws.merge_cells(f"{TOTAL_COLS[0]}{r}:{TOTAL_COLS[-1]}{r}")
        ws[f"{TOTAL_COLS[0]}{r}"].fill = LABEL
        for col in TOTAL_COLS:
            ws[f"{col}{r}"].border = BOX
        for col, v in zip(RESULT_COLS, list(vals) + [""] * NP):
            x = ws[f"{col}{r}"]
            x.value = v
            x.font = dfont()
            x.fill = INPUT
            x.alignment = Alignment(horizontal="center", vertical="center")
            x.border = BOX

    ws.merge_cells(f"{COMMENT}6:{EDIT}6")
    ws[f"{COMMENT}6"] = ("※ 노란색 셀은 실행 단계에서 채워집니다 — 환경 정보 / Result / "
                         "Issue No.   ·   Comment = TC ID · 실행 단계 · 선행 TC · 대상")
    ws[f"{COMMENT}6"].font = Font(name=FONT, size=8, color=NOTE_TEXT)
    ws.merge_cells(f"{COMMENT}8:{EDIT}10")
    ws[f"{COMMENT}8"] = ("※ 1-Depth는 기능 영역 기준. 실제 탐색으로 화면명이 확정되면 "
                         "1-Depth에 화면명을 넣고 현재 계층을 한 칸씩 내림")
    ws[f"{COMMENT}8"].font = Font(name=FONT, size=8, color=NOTE_TEXT)
    ws[f"{COMMENT}8"].alignment = Alignment(wrap_text=True, vertical="top")

    # 데이터 행
    idx = {d: [] for d in ORDER}
    for t in TCS:
        idx.setdefault(t[1], []).append(t)

    row = 11
    for d1 in ORDER:
        for (tid, _d1, d2, d3, case, pre, steps, exp,
             vt, prio, _par, target, note) in idx.get(d1, []):
            stepl = split_steps(steps)
            expl = split_expected(exp)
            aligned = len(expl) == len(stepl)
            first = row
            for i, st in enumerate(stepl, start=1):
                is_last = i == len(stepl)
                ws[f"B{row}"] = "=ROW()-10"
                for ci, v in enumerate([d1, d2, d3, case, "", "", ""]):
                    ws[f"{DEPTH_COLS[ci]}{row}"] = v
                ws[f"J{row}"] = pre if i == 1 else ""
                ws[f"K{row}"] = i
                ws[f"L{row}"] = to_step(st)
                ws[f"M{row}"] = expl[i - 1] if aligned else (expl[0] if (is_last and expl) else "")
                ws[f"N{row}"] = prio if i == 1 else ""
                if i == 1:
                    p = PAR.get(tid, "-") or "-"
                    ws[f"{COMMENT}{row}"] = f"{tid} · {depth(tid)}단계 · 선행 {p} · 대상 {target}"
                    w = VT_NOTE.get(vt, vt)
                    if note:
                        w += " / " + note
                    ws[f"{NOTE}{row}"] = w
                row += 1
            for extra in ([] if aligned else expl[1:]):
                ws[f"K{row}"] = len(stepl)
                ws[f"M{row}"] = extra
                row += 1
            for r in range(first, row):
                for col in ALL_COLS:
                    x = ws[f"{col}{r}"]
                    x.border = BOX
                    x.font = dfont()
                    center = col in ("B", "K", "N") or col in TOTAL_COLS or col in RESULT_COLS
                    x.alignment = Alignment(horizontal="center" if center else "left",
                                            vertical="center", wrap_text=True)
                    x.fill = INPUT if col in RESULT_COLS + [ISSUE_COL] else WHITE
                ws[f"C{r}"].font = dfont(bold=True)
                ws[f"K{r}"].font = dfont(bold=True)
                ws.row_dimensions[r].height = 30
            for tcol, rcol in zip(TOTAL_COLS, RESULT_COLS):
                cell = ws[f"{tcol}{first}"]
                rng = f"{rcol}{first}:{rcol}{row - 1}"
                cell.value = (f'=IF(COUNTIF({rng},"Fail")>0,"Fail",'
                              f'IF(COUNTIF({rng},"Blocked")>0,"Blocked",'
                              f'IF(COUNTIF({rng},"NI")>0,"NI",'
                              f'IF(COUNTIF({rng},"Pass")>0,"Pass",""))))')
                cell.font = dfont(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if row - 1 > first:
                    ws.merge_cells(f"{tcol}{first}:{tcol}{row - 1}")

    last_row = row - 1
    dv = DataValidation(type="list", formula1='"Pass,Fail,NI,Blocked"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{RESULT_COLS[0]}11:{RESULT_COLS[-1]}500")
    dvp = DataValidation(type="list", formula1='"High,Medium,Low"', allow_blank=True)
    ws.add_data_validation(dvp)
    dvp.add(f"N11:N500")

    for col, _l, w in base + tail:
        ws.column_dimensions[col].width = w
    for col in TOTAL_COLS + RESULT_COLS:
        ws.column_dimensions[col].width = 7
    unfreeze(ws)   # 시트별 옵션: Test Case는 틀 고정 없음

    # ══ Summary ═════════════════════════════════════════════
    s2 = wb.create_sheet("Summary")
    s2.sheet_view.showGridLines = False
    s2["B2"] = "커버리지 요약"
    s2["B2"].font = dfont(12, bold=True)
    s2.row_dimensions[2].height = 19
    s2["B3"] = "Test Case 시트를 참조하는 수식으로 자동 집계됩니다. 행을 추가하면 아래 범위를 넓히세요."
    s2["B3"].font = Font(name=FONT, size=8, color=NOTE_TEXT)
    s2["B4"] = "기준 골격 버전"
    s2["B4"].font = dfont(bold=True)
    s2["B4"].fill = LABEL
    s2["B4"].border = BOX
    s2.merge_cells("C4:E4")
    # 자동 기입 — 사람이 옮겨 적지 않으므로 TC 세트와 골격 버전이 어긋날 수 없다
    s2["C4"] = TREE_VERSION
    s2["C4"].font = dfont()
    s2["C4"].fill = WHITE
    for cc in ("C4", "D4", "E4"):
        s2[cc].border = BOX

    s2.merge_cells("B5:B6")
    s2["B5"] = "1-Depth (영역)"
    s2.merge_cells("C5:C6")
    s2["C5"] = "TC 수"
    s2.merge_cells("D5:F5")
    s2["D5"] = "Priority"
    for i, p in enumerate(PLATFORMS):
        c0 = 7 + i * 4
        s2.merge_cells(start_row=5, start_column=c0, end_row=5, end_column=c0 + 3)
        s2.cell(5, c0, p)
    for cc in ["B5", "C5", "D5"] + [get_column_letter(7 + i * 4) + "5" for i in range(NP)]:
        s2[cc].font = hfont()
        s2[cc].fill = HDR
        s2[cc].alignment = Alignment(horizontal="center", vertical="center")
    sub6 = ["High", "Medium", "Low"] + ["Pass", "Fail", "Blocked", "Pass율"] * NP
    for i, lab in enumerate(sub6):
        x = s2.cell(6, 4 + i, lab)
        x.font = hfont()
        x.fill = SUB
        x.alignment = Alignment(horizontal="center", vertical="center")
    ncols = 3 + 3 + 4 * NP           # B..(마지막)
    for r in (5, 6):
        for ci in range(2, 2 + ncols):
            s2.cell(r, ci).border = BOX

    for i, d1 in enumerate(ORDER):
        r = 7 + i
        a = s2.cell(r, 2, d1)
        a.font = dfont(bold=True)
        a.border = BOX
        a.fill = WHITE
        tcr = "'Test Case'!"
        f = {3: f'=COUNTIFS({tcr}$C$11:$C$500,$B{r},{tcr}$K$11:$K$500,1)'}
        for j, pr in enumerate(["High", "Medium", "Low"]):
            f[4 + j] = f'=COUNTIFS({tcr}$C$11:$C$500,$B{r},{tcr}$N$11:$N$500,"{pr}")'
        for pi, tcol in enumerate(TOTAL_COLS):
            c0 = 7 + pi * 4
            for j, st in enumerate(["Pass", "Fail", "Blocked"]):
                f[c0 + j] = (f'=COUNTIFS({tcr}$C$11:$C$500,$B{r},'
                             f'{tcr}${tcol}$11:${tcol}$500,"{st}")')
            pcol, fcol = get_column_letter(c0), get_column_letter(c0 + 1)
            f[c0 + 3] = f'=IF({pcol}{r}+{fcol}{r}=0,"",{pcol}{r}/({pcol}{r}+{fcol}{r}))'
        for ci, formula in f.items():
            x = s2.cell(r, ci, formula)
            x.font = dfont()
            x.fill = WHITE
            x.alignment = Alignment(horizontal="center")
            x.border = BOX
            if (ci - 7) % 4 == 3 and ci >= 7:
                x.number_format = "0.0%"

    tot = 7 + len(ORDER)
    tc0 = s2.cell(tot, 2, "합계")
    tc0.font = hfont()
    tc0.fill = SUB
    tc0.border = BOX
    for ci in range(3, 2 + ncols):
        col = get_column_letter(ci)
        if (ci - 7) % 4 == 3 and ci >= 7:
            pcol, fcol = get_column_letter(ci - 3), get_column_letter(ci - 2)
            v = f'=IF({pcol}{tot}+{fcol}{tot}=0,"",{pcol}{tot}/({pcol}{tot}+{fcol}{tot}))'
        else:
            v = f"=SUM({col}7:{col}{tot - 1})"
        x = s2.cell(tot, ci, v)
        x.font = hfont()
        x.fill = SUB
        x.border = BOX
        x.alignment = Alignment(horizontal="center")
        if (ci - 7) % 4 == 3 and ci >= 7:
            x.number_format = "0.0%"

    s2.cell(tot + 2, 2,
            "TC 수 = 케이스 단위(TN 1행) · Pass율 = Pass ÷ (Pass + Fail) — "
            "NI·Blocked는 분모에서 제외합니다"
            ).font = Font(name=FONT, size=8, color=NOTE_TEXT)
    s2.column_dimensions["A"].width = 3
    s2.column_dimensions["B"].width = 22
    for ci in range(3, 2 + ncols):
        s2.column_dimensions[get_column_letter(ci)].width = 9
    unfreeze(s2)

    # ══ 이슈 관리 시트 ═══════════════════════════════════════
    s3 = wb.create_sheet("이슈 관리 시트")
    s3.sheet_view.showGridLines = False
    for i, h in enumerate(ISSUE_HEADERS):
        x = s3.cell(2, 2 + i, h)
        x.font = hfont(11)
        x.fill = HDR
        x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        x.border = BOX
    samples = CFG.get("issue_samples") or [[
        PROJECT, f"{PROJECT}-1", "Open",
        "{화면} 진입 > {동작} 시, {결과} 안 됨",
        "Pre-condition: {사전 조건}\nReproduce Step: {재현 스텝}\n"
        "Actual Result: {실제 결과}\nExpected Result: {기대 결과}\nQA Comment: {참고}",
        "High", "Always", "", "", "", "PC웹", "", "", "", "", "", "",
        "YYYY-MM-DD", "YYYY-MM-DD", "YYYY-MM-DD"]]
    for r, rowv in enumerate(samples, start=3):
        for i, v in enumerate(rowv):
            x = s3.cell(r, 2 + i, v)
            x.font = dfont(11)
            x.fill = WHITE
            x.alignment = Alignment(vertical="top", wrap_text=(i in (3, 4)))
            x.border = BOX
    for i, w in enumerate(ISSUE_WIDTHS):
        s3.column_dimensions[get_column_letter(2 + i)].width = w
    s3.column_dimensions["A"].width = 3
    s3.row_dimensions[2].height = 30
    s3.freeze_panes = "A3"                       # 시트별 옵션: 헤더 행 고정
    s3.auto_filter.ref = f"B2:{get_column_letter(1 + len(ISSUE_HEADERS))}{2 + len(samples)}"

    # ══ 목록 ════════════════════════════════════════════════
    s4 = wb.create_sheet("목록")
    s4.sheet_view.showGridLines = False
    for li, (name, values) in enumerate(LISTS.items()):
        col = 2 + li
        x = s4.cell(2, col, name)
        x.font = hfont(11)
        x.fill = HDR
        x.alignment = Alignment(horizontal="center", vertical="center")
        x.border = BOX
        for r, v in enumerate(values, start=3):
            y = s4.cell(r, col, v)
            y.font = dfont(11)
            y.fill = WHITE
            y.border = BOX
        s4.column_dimensions[get_column_letter(col)].width = \
            max(14, max(len(str(v)) for v in values) + 4)
        # 정의된 이름 등록 — 드롭다운은 이 이름을 참조한다(함정 2)
        ref = f"목록!${get_column_letter(col)}$3:${get_column_letter(col)}${2 + len(values)}"
        dn = LIST_NAME_MAP[name]
        wb.defined_names[dn] = DefinedName(dn, attr_text=ref)
    s4.column_dimensions["A"].width = 3
    unfreeze(s4)

    for col, list_name in ISSUE_DV.items():
        d = DataValidation(type="list", formula1=LIST_NAME_MAP[list_name],
                           allow_blank=True, showDropDown=False)
        s3.add_data_validation(d)
        d.add(f"{col}3:{col}200")

    # ══ 명세서 ═══════════════════════════════════════════════
    build_spec_sheet(wb)

    wb.save(args.output)
    print(f"saved {args.output} | TC {len(TCS)} | rows {last_row - 10} | "
          f"platforms {PLATFORMS} | tree {TREE_VERSION}")


def build_spec_sheet(wb):
    ws = wb.create_sheet("명세서")
    ws.sheet_view.showGridLines = False

    def H(*vals):
        return ("head",) + vals

    def R(*vals):
        return ("row",) + vals

    SPEC = [
        ("title", "명세서 — 시트 규칙 정본"),
        ("note", "이 시트가 구조 규칙의 정본입니다. rules/tc-sheet-format.md와 짝으로 교차 "
                 "검증하며, 불일치 발견 시 임의 판단 없이 사용자에게 기준을 확인합니다. "
                 "서식(색·테두리·폰트)의 정본은 design-template/xlsx-design-guide.md입니다."),
        ("gap",),
        ("section", "1. 시트 구성"),
        H("시트", "역할"),
        R("Test Case", "TC 작성과 실행 기록. 노란 셀은 실행 단계에서 채워집니다"),
        R("Summary", "케이스 단위 자동 집계. 기준 골격 버전(C4)은 생성 시 자동 기입됩니다"),
        R("이슈 관리 시트", "결함 기록(내장 운영, JIRA 미사용) — JIRA 이슈 등록·관리 방식을 "
                       "시트로 표현. Issue No.로 Test Case와 연결합니다"),
        R("목록", "드롭다운 참조 목록의 정본. 숨기지 않고 맨 뒤에 둡니다"),
        R("명세서", "이 시트 — 구조 규칙의 정본"),
        ("gap",),
        ("section", "2. 컬럼 정의 (Test Case)"),
        H("컬럼", "내용", "채우는 규칙"),
        R("No", "행 번호", "자동(ROW()-10). 직접 입력하지 않습니다"),
        R("1~7-Depth", "기능 계층", "스텝 행마다 반복. 의미 있는 깊이까지만 쓰고 나머지는 빈칸"),
        R("Pre-Condition", "사전조건", "TN 1행에만"),
        R("TN", "스텝 번호", "케이스마다 1부터. 새 케이스가 시작되면 1로 복귀"),
        R("Test-Step", "수행 동작", "「~한다」 체"),
        R("Expected-Result", "기대 결과",
          "「~된다」 체. 판정 가능한 문장 — 임계·합격선·시도 횟수는 문장 안에 숫자로"),
        R("Priority", "우선순위", "TN 1행에만. High/Medium/Low — 케이스의 속성입니다"),
        R("Total Result", "케이스 판정", "수식 열. 케이스 행 범위를 세로 병합하며 직접 입력하지 않습니다"),
        R("Result", "스텝 실행 결과", "드롭다운 4종(아래 상태값 정의). 실행 단계에서 채움 — 노란 셀"),
        R("Issue No.", "이슈 연결", "이슈 관리 시트의 Issue No. 실행 단계에서 채움 — 노란 셀"),
        R("Comment", "케이스 메타", "TC ID · 실행 단계 · 선행 TC · 대상 서비스"),
        R("Note", "검증 정보", "검증유형과 판정 규칙, 주의사항"),
        R("Test Case Edit", "편집 이력", "자유 기재"),
        ("gap",),
        ("section", "3. 상태값 정의"),
        H("상태", "정의", "Pass율 분모"),
        R("Pass", "성공", "포함"),
        R("Fail", "실패", "포함"),
        R("NI", "미구현이거나 스펙에 없어 실행 대상이 아님 (Not Implemented)", "제외"),
        R("Blocked", "기능은 구현됐으나 선행 TC의 Fail로 확인 불가", "제외"),
        ("note", "Pass율 = Pass ÷ (Pass + Fail). NI·Blocked를 분모에 넣지 않는 이유는 결함 "
                 "1건이 후속 Blocked 수만큼 중복 계상되는 것을 막기 위해서입니다."),
        ("gap",),
        ("section", "4. Total Result 규칙"),
        H("항목", "규칙"),
        R("우선순위", "Fail > Blocked > NI > Pass — 스텝 중 하나라도 Fail이면 케이스 Fail"),
        R("수식 원형",
          'IF(COUNTIF(범위,"Fail")>0,"Fail",IF(COUNTIF(범위,"Blocked")>0,"Blocked",'
          'IF(COUNTIF(범위,"NI")>0,"NI",IF(COUNTIF(범위,"Pass")>0,"Pass",""))))'
          ' — 셀에는 앞에 = 를 붙여 사용합니다. 아무것도 실행되지 않은 케이스는 빈칸입니다'),
        R("병합", "케이스의 스텝 행 범위를 플랫폼 열마다 세로 병합"),
        ("gap",),
        ("section", "5. TC ID 체계"),
        H("항목", "규칙"),
        R("형식", "TC-{영역코드}-{번호 3자리} — 예: TC-ENT-001"),
        R("번호", "영역 안에서만 증가합니다. 다른 영역에 케이스가 추가돼도 기존 ID가 흔들리지 않습니다"),
        R("영역코드", "기능 트리 1-Depth당 하나. 매핑표는 프로젝트 시트에서 정의합니다 (예: 앱 진입=ENT)"),
        R("기재 위치", "Comment의 첫 토큰. 자동화 케이스명·추적 매트릭스·이슈 연결이 이 ID를 참조합니다"),
        ("gap",),
        ("section", "6. 플랫폼 열 규칙"),
        H("항목", "규칙"),
        R("기본값", "마스터는 Web / And / iOS 3열"),
        R("프로젝트 조정", "TC 설계 시작 시 대상 플랫폼을 사용자에게 재확인하고, Test Case의 "
                      "Total Result·Result 하위 열과 Summary의 플랫폼 열을 함께 조정합니다"),
        ("gap",),
        ("section", "7. 입력 규칙"),
        H("항목", "규칙"),
        R("실행 채움 셀(노랑)", "설계 시점에는 비어 있고 실행 단계에서 채워지는 칸 — 환경 블록·"
                        "Result·Issue No. 채우는 주체가 사람이든 자동화든 설계자는 건드리지 않습니다"),
        R("설계 셀", "Depth·절차·기대결과는 실행 중 수정하지 않습니다"),
        R("기준 골격 버전", "Summary C4에 생성 스크립트가 자동 기입합니다 — 형식 {프로젝트}-tree-v{X.Y}. "
                      "TC 설계 입력(tc-input json)의 값을 그대로 쓰므로 사람이 옮겨 적지 않습니다"),
        ("gap",),
        ("section", "8. 컬럼 정의 (이슈 관리 시트)"),
        H("컬럼", "내용", "채우는 규칙"),
        R("프로젝트 ID", "프로젝트 식별자", "SUT명 기준. 목록 시트 참조"),
        R("Issue No.", "이슈 ID — TC 연결 키",
          "{프로젝트}-{생성 번호순} (1 > 2 > 3 > …). Test Case 시트의 Issue No.와 같은 값으로 연결됩니다"),
        R("이슈 상태", "이슈의 현재 상태",
          "Open: 열린 상태(재현됨) / In Progress: 담당자가 수정 진행 중 / Resolved: 해결됨 / "
          "Reopen: 해결된 이슈가 재현되어 다시 엶 / Closed: 재현되지 않아 닫음"),
        R("요약(Summary)", "이슈 제목",
          "재현 경로 요약 — 문단 구분은 \">\", 마지막은 무엇이 잘못됐는지 수동태로.\n"
          "ex) rules/ 폴더 이동 > A.md 실행 시, 크래시 발생됨"),
        R("설명", "재현 방법 상세",
          "Pre-condition(사전 조건) / Reproduce Step(재현 스텝) / Actual Result(실제 결과, ~됨) / "
          "Expected Result(기대 결과, ~되어야 함) / QA Comment(참고) 순서로 작성"),
        R("우선순위", "이슈 심각도",
          "High: 크래시·진입 불가 등 치명 / Medium: 진입은 되나 기능 미동작 / Low: 문구·표기 오류"),
        R("빈도", "발생 빈도",
          "Always: 항상 / Often: 종종(70% 이상) / Sometimes: 가끔(70% 미만) / Once: 1회만"),
        R("영향 받는 버전", "이슈 발생 버전",
          "{발생디바이스}_{QA프로젝트}_{실행버전후보} — RC=Release Candidate(정식 배포 직전 빌드).\n"
          "ex) PC웹_Ver1.0_RC2. 목록 시트 참조(수정 버전과 공용)"),
        R("수정 버전", "이슈가 수정된 버전", "영향 받는 버전과 같은 목록을 사용합니다"),
        R("해결책", "수정 방향",
          "Fixed: 코드 수정으로 대응 / Won't Do: 환경·기술 지원 불가로 미대응 / "
          "Won't Fix: 수정 필요하나 지금은 안 함 / Duplicate: 동일 건 존재 / "
          "Incomplete: 이슈 자체가 잘못됨 / Cannot Reproduce: 재현 불가 / "
          "Done: 기획·정책 결정으로 이슈 아님 확정 / Declined(QA Only): QA선에서 이슈로 보지 않음"),
        R("환경", "발생 디바이스", "PC웹 / Android / iOS"),
        R("레이블", "발생 영역",
          "기능 트리 1-Depth 영역명 — 목록 시트 참조. 트리 개정 시 목록만 갱신하고 기존 행 값은 "
          "소급 변경하지 않습니다"),
        R("보고자", "이슈 등록자", "목록 참조"),
        R("담당자", "이슈 수정 담당자", "목록 참조"),
        R("관측자", "함께 팔로우할 인원",
          "드롭다운 없음 — 쉼표 구분 자유 입력(멀티 선택은 xlsx 표준 기능에 없음)"),
        R("첨부파일", "재현 증적", "재현 영상·이미지의 경로 또는 링크"),
        R("스프린트", "QA 프로젝트 명칭", "어떤 목표로 QA를 진행하는지. ex) PC웹 Ver1.0. 목록 참조"),
        R("이슈 등록일", "최초 등록일", "YYYY-MM-DD. 이후 변경하지 않습니다"),
        R("이슈 최종 수정일자", "내용 최종 수정일", "YYYY-MM-DD. 요약·설명 등 내용이 바뀔 때 갱신"),
        R("이슈 상태 최종 변경일자", "상태 최종 변경일", "YYYY-MM-DD. 이슈 상태가 바뀔 때 갱신"),
        ("gap",),
        ("section", "9. 목록 시트 규칙"),
        H("항목", "규칙"),
        R("지위", "드롭다운 참조의 정본 — 전 시트의 데이터 검증이 이 시트를 참조합니다"),
        R("노출", "숨기지 않고 맨 뒤 배치 — 값 체계 자체가 전시물입니다"),
        R("갱신", "항목 추가는 행 추가로. 명칭 변경은 목록만 교체하고 기존 데이터 행은 소급 변경하지 "
                "않습니다(검증은 신규 입력에만 작동)"),
        R("레이블 동기", "기능 트리 개정 시 레이블 목록을 함께 갱신합니다(정본 수정 체크리스트 연동)"),
    ]

    r = 2
    for item in SPEC:
        kind = item[0]
        if kind == "gap":
            r += 1
            continue
        if kind == "title":
            ws.cell(r, 2, item[1]).font = dfont(13, bold=True)
        elif kind == "note":
            x = ws.cell(r, 2, item[1])
            x.font = Font(name=FONT, size=10, color=NOTE_TEXT)
        elif kind == "section":
            ws.cell(r, 2, item[1]).font = dfont(12, bold=True)
        elif kind == "head":
            for i, v in enumerate(item[1:]):
                x = ws.cell(r, 2 + i, v)
                x.font = hfont(11)
                x.fill = HDR
                x.alignment = Alignment(horizontal="center", vertical="center")
                x.border = BOX
        elif kind == "row":
            for i, v in enumerate(item[1:]):
                # '='로 시작하는 문구는 수식으로 저장되어 파일을 깨뜨린다(함정 3).
                # 명세서의 수식 원형은 '=' 없이 적고 본문에서 안내한다.
                assert not (isinstance(v, str) and v.startswith("=")), \
                    f"명세서 셀이 '='로 시작합니다: {v[:40]}"
                x = ws.cell(r, 2 + i, v)
                x.font = dfont(11)
                x.fill = WHITE
                x.alignment = Alignment(vertical="top", wrap_text=True)
                x.border = BOX
        r += 1

    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 34
    ws.column_dimensions["D"].width = 90
    unfreeze(ws)


if __name__ == "__main__":
    main()
