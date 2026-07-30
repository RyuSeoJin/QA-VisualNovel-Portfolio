# -*- coding: utf-8 -*-
"""
TC JSON -> 실행용 TC 시트 (조직 표준 서식)

한 행 = 한 TN = 한 스텝. 절차의 "1. / 2. / 3."을 TN 스텝으로 분해하고,
문체를 Test-Step '~한다' / Expected-Result '~된다'로 정규화한다.
서식 상세는 references/tc-sheet-format.md 참조.

사용법:
    python build_tc_template_xlsx.py input.json -o out.xlsx
    python /mnt/skills/public/xlsx/scripts/recalc.py out.xlsx   # 수식 검증 (필수)

입력 JSON 스키마
----------------
{
  "title": "Test Case Template",
  "platforms": ["Web", "And", "iOS"],       # Result 열 (조직/대상에 맞게 1~n개)
  "d1_order": ["앱 진입", "계정/인증", ...],   # 1-Depth 표시 순서 (생략 시 등장 순)
  "env": {                                    # 상단 환경 블록 기본값 (선택)
    "OS": ["", "", ""], "단말": ["", "", ""], "버전": ["", "", ""],
    "작업자 이름": ["", "", ""], "작업 시작일": ["", "", ""]
  },
  "tcs": [
    ["TC-XXX-001","1-Depth","2-Depth","3-Depth","케이스",
     "사전조건","1. 절차\\n2. 절차","기대결과 문장. 여러 문장 가능.",
     "결정적|확률적|루브릭|금칙","High|Medium|Low",
     "선행 TC ID 또는 -","대상 서비스","비고"]
  ]
}

절차는 "1. ...\\n2. ..." 로, 기대결과는 마침표+공백으로 문장 분리되어
각각 TN 스텝 행에 배치된다. 선행 TC(11번째 필드)로 실행 단계를 자동 계산해
Comment 열에 "TC ID · N단계 · 선행 X · 대상 Y"를 적는다.
"""
import argparse
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from norm import to_step, to_expected, split_steps, split_expected  # noqa: E402

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ap = argparse.ArgumentParser()
ap.add_argument("input")
ap.add_argument("-o", "--output", default="tc.xlsx")
args = ap.parse_args()

CFG = json.load(open(args.input, encoding="utf-8"))
TCS = [tuple(t) for t in CFG["tcs"]]
PLATFORMS = CFG.get("platforms", ["Web", "And", "iOS"])
TITLE = CFG.get("title", "Test Case Template")
ENV = CFG.get("env", {k: [""] * len(PLATFORMS) for k in
                      ["OS", "단말", "버전", "작업자 이름", "작업 시작일"]})
ORDER = CFG.get("d1_order") or list(dict.fromkeys(t[1] for t in TCS))

# 선행 관계 → 실행 단계
PAR = {t[0]: t[10] for t in TCS}
_LAYER = {}


def depth(tid):
    if tid in _LAYER:
        return _LAYER[tid]
    p = PAR.get(tid, "-")
    _LAYER[tid] = 1 if p in ("-", "", None) else depth(p) + 1
    return _LAYER[tid]


FONT = "Arial"
NAVY, GRAY = "1F2A44", "44546A"
HDR = PatternFill("solid", fgColor=NAVY)
SUB = PatternFill("solid", fgColor=GRAY)
ENVF = PatternFill("solid", fgColor="EDEFF4")
INPUT = PatternFill("solid", fgColor="FFF9C4")
ZEBRA = PatternFill("solid", fgColor="F7F8FA")
THIN = Side(style="thin", color="BFC5D2")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
TOP = Border(left=THIN, right=THIN, top=Side(style="medium", color="8A93A8"), bottom=THIN)

VT_NOTE = {
    "결정적": "결정적 · 1회 실행, 기대값 불일치 시 FAIL",
    "확률적": "확률적 · 20회 반복(지표성 30~50회), 명시 임계 미달 시 FAIL",
    "루브릭": "루브릭 · 5점 채점, 평가자 2인 또는 심판모델 3회, 합격선 4점",
    "금칙": "금칙 · 우회 변형 포함 20~40회, 1건이라도 발생 시 최고 심각도",
}

# ── 컬럼 레이아웃 ────────────────────────────────────────────
DEPTH_COLS = ["C", "D", "E", "F", "G", "H", "I"]
NP = len(PLATFORMS)
base = [("A", "", 3), ("B", "No", 6),
        ("C", "1-Depth", 15), ("D", "2-Depth", 14), ("E", "3-Depth", 15),
        ("F", "4-Depth", 20), ("G", "5-Depth", 11), ("H", "6-Depth", 11), ("I", "7-Depth", 11),
        ("J", "Pre-Condition", 26), ("K", "TN", 5), ("L", "Test-Step", 34),
        ("M", "Expected-Result", 46), ("N", "Priority", 9)]
c = ord("O")
TOTAL_COLS = [chr(c + i) for i in range(NP)]
c += NP
RESULT_COLS = [chr(c + i) for i in range(NP)]
c += NP
JIRA = chr(c); COMMENT = chr(c + 1); NOTE = chr(c + 2); EDIT = chr(c + 3)
LAST = EDIT
tail = [(JIRA, "JIRA No.", 11), (COMMENT, "Comment", 34), (NOTE, "Note", 30), (EDIT, "Test Case Edit", 12)]

wb = Workbook()
ws = wb.active
ws.title = "Test Case"
ws.sheet_view.showGridLines = False

# 타이틀
ws.merge_cells(f"B3:{LAST}3")
tt = ws["B3"]; tt.value = TITLE
tt.font = Font(name=FONT, size=13, bold=True, color="FFFFFF"); tt.fill = HDR
tt.alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[3].height = 26

# 헤더 4~5행
for col, label, _w in base[1:] + tail:
    ws.merge_cells(f"{col}4:{col}5")
    x = ws[f"{col}4"]; x.value = label
    x.font = Font(name=FONT, size=9.5, bold=True, color="FFFFFF"); x.fill = HDR
    x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
ws.merge_cells(f"{TOTAL_COLS[0]}4:{TOTAL_COLS[-1]}4"); ws[f"{TOTAL_COLS[0]}4"].value = "Total Result"
ws.merge_cells(f"{RESULT_COLS[0]}4:{RESULT_COLS[-1]}4"); ws[f"{RESULT_COLS[0]}4"].value = "Result"
for cc in (TOTAL_COLS[0], RESULT_COLS[0]):
    ws[f"{cc}4"].font = Font(name=FONT, size=9.5, bold=True, color="FFFFFF")
    ws[f"{cc}4"].fill = HDR
    ws[f"{cc}4"].alignment = Alignment(horizontal="center", vertical="center")
for col, lab in list(zip(TOTAL_COLS, PLATFORMS)) + list(zip(RESULT_COLS, PLATFORMS)):
    x = ws[f"{col}5"]; x.value = lab
    x.font = Font(name=FONT, size=9, bold=True, color="FFFFFF"); x.fill = SUB
    x.alignment = Alignment(horizontal="center", vertical="center")
for r in (4, 5):
    for col in [b[0] for b in base[1:]] + TOTAL_COLS + RESULT_COLS + [t[0] for t in tail]:
        ws[f"{col}{r}"].border = BOX
ws.row_dimensions[4].height = 18
ws.row_dimensions[5].height = 16

# 환경 블록 6~10행
for i, (label, vals) in enumerate(ENV.items()):
    r = 6 + i
    lc = ws[f"N{r}"]; lc.value = label
    lc.font = Font(name=FONT, size=9, bold=True); lc.fill = ENVF
    lc.alignment = Alignment(horizontal="center", vertical="center"); lc.border = BOX
    ws.merge_cells(f"{TOTAL_COLS[0]}{r}:{TOTAL_COLS[-1]}{r}")
    ws[f"{TOTAL_COLS[0]}{r}"].fill = ENVF
    for col in TOTAL_COLS:
        ws[f"{col}{r}"].border = BOX
    for col, v in zip(RESULT_COLS, list(vals) + [""] * NP):
        x = ws[f"{col}{r}"]; x.value = v
        x.font = Font(name=FONT, size=9); x.fill = INPUT
        x.alignment = Alignment(horizontal="center", vertical="center"); x.border = BOX
ws[f"{COMMENT}6"] = "※ 노란색 셀만 입력 — 환경 / Result / JIRA   ·   Comment = TC ID · 실행 단계 · 선행 TC · 대상"
ws[f"{COMMENT}6"].font = Font(name=FONT, size=8.5, italic=True, color="8A6D1B")
ws.merge_cells(f"{COMMENT}6:{EDIT}6")
ws[f"{COMMENT}8"] = "※ 1-Depth는 화면(탐색 전이면 기능 영역) 기준. 화면명 확정 시 1-Depth에 넣고 현재 계층을 한 칸씩 내림"
ws[f"{COMMENT}8"].font = Font(name=FONT, size=8.5, italic=True, color="8A6D1B")
ws.merge_cells(f"{COMMENT}8:{EDIT}10")
ws[f"{COMMENT}8"].alignment = Alignment(wrap_text=True, vertical="top")

# 데이터 행
idx = {d: [] for d in ORDER}
for t in TCS:
    idx.setdefault(t[1], []).append(t)

row = 11
zebra = False
for d1 in ORDER:
    for tid, _d1, d2, d3, case, pre, steps, exp, vt, prio, _tn, target, note in idx.get(d1, []):
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
            for col in [b[0] for b in base[1:]] + TOTAL_COLS + RESULT_COLS + [t[0] for t in tail]:
                x = ws[f"{col}{r}"]
                x.border = TOP if r == first else BOX
                x.font = Font(name=FONT, size=9)
                center = col in ("B", "K", "N") or col in TOTAL_COLS or col in RESULT_COLS
                x.alignment = Alignment(horizontal="center" if center else "left",
                                        vertical="center", wrap_text=True)
                if col in RESULT_COLS or col in (JIRA, COMMENT):
                    x.fill = INPUT if col in RESULT_COLS + [JIRA] else (ZEBRA if zebra else PatternFill())
                elif zebra:
                    x.fill = ZEBRA
            ws[f"C{r}"].font = Font(name=FONT, size=9, bold=True)
            ws[f"K{r}"].font = Font(name=FONT, size=9, bold=True, color="1F4E79")
            ws.row_dimensions[r].height = 30
        for tcol, rcol in zip(TOTAL_COLS, RESULT_COLS):
            cell = ws[f"{tcol}{first}"]
            cell.value = (f'=IF(COUNTIF({rcol}{first}:{rcol}{row-1},"Fail")>0,"Fail",'
                          f'IF(COUNTIF({rcol}{first}:{rcol}{row-1},"Blocked")>0,"Blocked",'
                          f'IF(COUNTIF({rcol}{first}:{rcol}{row-1},"Pass")>0,"Pass","")))')
            cell.font = Font(name=FONT, size=9, bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if row - 1 > first:
                ws.merge_cells(f"{tcol}{first}:{tcol}{row-1}")
        zebra = not zebra

last_row = row - 1
dv = DataValidation(type="list", formula1='"Pass,Fail,Blocked,N/A,Skip"', allow_blank=True)
ws.add_data_validation(dv)
for col in RESULT_COLS:
    dv.add(f"{col}11:{col}{last_row}")
dvp = DataValidation(type="list", formula1='"High,Medium,Low"', allow_blank=True)
ws.add_data_validation(dvp)
dvp.add(f"N11:N{last_row}")

for col, _l, w in base + tail:
    ws.column_dimensions[col].width = w
for col in TOTAL_COLS + RESULT_COLS:
    ws.column_dimensions[col].width = 7
ws.freeze_panes = "C11"
ws.auto_filter.ref = f"B5:{LAST}{last_row}"

# ── Summary ──────────────────────────────────────────────────
s2 = wb.create_sheet("Summary")
s2.sheet_view.showGridLines = False
s2["B2"] = "커버리지 요약"
s2["B2"].font = Font(name=FONT, size=14, bold=True, color=NAVY)
s2["B3"] = "Test Case 시트를 참조하는 수식으로 자동 집계. 행 추가 시 범위를 넓히세요."
s2["B3"].font = Font(name=FONT, size=9, italic=True, color="6B7280")
head = ["1-Depth", "TC 수", "테스트 스텝", "High", "Medium", "Low"] + \
       [f"{p} Pass" for p in PLATFORMS] + [f"{p} Fail" for p in PLATFORMS]
for i, h in enumerate(head):
    x = s2.cell(5, 2 + i, h)
    x.font = Font(name=FONT, size=9.5, bold=True, color="FFFFFF"); x.fill = HDR; x.border = BOX
    x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
s2.row_dimensions[5].height = 28
N = last_row
for i, d1 in enumerate(ORDER):
    r = 6 + i
    s2.cell(r, 2, d1).font = Font(name=FONT, size=9, bold=True)
    f = {3: f"=COUNTIFS('Test Case'!$C$11:$C${N},$B{r},'Test Case'!$K$11:$K${N},1)",
         4: f"=COUNTIF('Test Case'!$C$11:$C${N},$B{r})",
         5: f'=COUNTIFS(\'Test Case\'!$C$11:$C${N},$B{r},\'Test Case\'!$N$11:$N${N},"High")',
         6: f'=COUNTIFS(\'Test Case\'!$C$11:$C${N},$B{r},\'Test Case\'!$N$11:$N${N},"Medium")',
         7: f'=COUNTIFS(\'Test Case\'!$C$11:$C${N},$B{r},\'Test Case\'!$N$11:$N${N},"Low")'}
    col = 8
    for pcol in RESULT_COLS:
        f[col] = f'=COUNTIFS(\'Test Case\'!$C$11:$C${N},$B{r},\'Test Case\'!${pcol}$11:${pcol}${N},"Pass")'
        col += 1
    for pcol in RESULT_COLS:
        f[col] = f'=COUNTIFS(\'Test Case\'!$C$11:$C${N},$B{r},\'Test Case\'!${pcol}$11:${pcol}${N},"Fail")'
        col += 1
    for ci, formula in f.items():
        x = s2.cell(r, ci, formula)
        x.font = Font(name=FONT, size=9); x.alignment = Alignment(horizontal="center"); x.border = BOX
    s2.cell(r, 2).border = BOX
tot = 6 + len(ORDER)
s2.cell(tot, 2, "합계").font = Font(name=FONT, size=9.5, bold=True, color="FFFFFF")
s2.cell(tot, 2).fill = PatternFill("solid", fgColor=GRAY); s2.cell(tot, 2).border = BOX
for ci in range(3, 6 + 2 * NP + 2):
    col = get_column_letter(ci)
    x = s2.cell(tot, ci, f"=SUM({col}6:{col}{tot-1})")
    x.font = Font(name=FONT, size=9.5, bold=True, color="FFFFFF")
    x.fill = PatternFill("solid", fgColor=GRAY); x.border = BOX
    x.alignment = Alignment(horizontal="center")
s2.cell(tot + 2, 2,
        "TC 수 = TN 1행 개수(케이스 단위) · 테스트 스텝 = 전체 행 수 · "
        "Pass율은 Blocked를 분모에서 제외: Pass / (Pass+Fail)"
        ).font = Font(name=FONT, size=9, italic=True, color="6B7280")
s2.column_dimensions["B"].width = 22
for ci in range(3, 6 + 2 * NP + 2):
    s2.column_dimensions[get_column_letter(ci)].width = 10

wb.save(args.output)
print(f"saved {args.output} | TC {len(TCS)} | rows {last_row - 10} | platforms {PLATFORMS}")
