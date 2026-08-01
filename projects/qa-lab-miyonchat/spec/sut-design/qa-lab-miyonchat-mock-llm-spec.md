# qa-lab-miyonchat — mock LLM 사양 (mock-llm-spec)

## 0. 문서 지위

- ②SUT 레이어 사양입니다. 실제 LLM 없이 **시드로 결정되는 응답 세트**의 구조 정본이며,
  `?seed={n}` 파라미터의 의미를 정의합니다
- 호감도 임계·엔딩 판정식 등 기획 값은 `design/…-system-spec.md`가 정본입니다

## 1. 결정성 원칙

- **같은 시드 + 같은 입력 순서 = 항상 같은 응답열**입니다. 실패한 테스트는 시드와 입력을
  기록하는 것만으로 재현됩니다
- 시드 미지정 시 기본값은 `seed=1`입니다
- 무작위 함수를 쓰지 않습니다 — "변주"조차 시드가 고르는 결정적 분기입니다

## 2. 응답 세트 구조

캐릭터×시나리오마다 턴 순서대로 응답 후보를 정의하고, 시드가 후보 중 하나를 고릅니다.

```json
{
  "characterId": "c1",
  "scenarioId": "s1",
  "turns": [
    {
      "turn": 1,
      "candidates": [
        {
          "kind": "message | direction",
          "text": "…{userName}… {nickname}…",
          "deltaAffection": 1,
          "memoryAdd": "민트초코를 싫어함",
          "memoryRefs": ["mem1"],
          "personaReflect": true,
          "contextReflect": true,
          "blockedToken": false,
          "fail": false
        }
      ],
      "choices": [
        { "label": "…", "delta": 2 },
        { "label": "…", "delta": 1 },
        { "label": "…", "delta": -1 }
      ]
    }
  ],
  "endTurn": 24
}
```

| 필드 | 규칙 |
|---|---|
| `candidates` | 시드 mod 후보 수로 선택 — 후보마다 반영/미반영·델타가 다를 수 있음 |
| `text`의 `{userName}`·`{nickname}` | 페르소나 삽입 슬롯 — 준수율 검증이 붙잡는 지점 |
| `personaReflect` / `contextReflect` | 이 후보가 페르소나/단기 맥락을 반영하는 변주인지 표기 — 계측 TC가 분포를 읽는 근거 |
| `choices` | 고정 선택지와 가중치(+2/+1/−1) — 없는 턴은 자유 입력만 |
| `fail: true` | 생성 실패 재현 후보 — 실패 시 재화 미차감 TC의 트리거 |
| `blockedToken: true` | 출력 필터 검증용 — 응답에 추상 금칙 토큰 포함 |
| `endTurn` | 경로 종점 — 도달 시 엔딩 최종 판정(system-spec §4-2) 트리거 |

## 3. 변주 분포 (계측의 전제)

- 계측용 변주(페르소나·맥락 반영 여부)는 시드 후보 배치로 만들며, 설계 분포는 **반영 후보
  80% 이상**을 기본으로 합니다 — 합격선 80%와 짝입니다
- 이 분포를 우리가 작성했으므로 **계측 수치는 품질 지표가 아닙니다.** 이 문장은 리포트와
  분석 문서에 그대로 들어갑니다

## 4. 스트리밍·삭제 연동

- 응답은 문자 단위 타이핑 연출로 표시되고, 표시 완료 이벤트 후 상태 델타가 반영됩니다 —
  검증은 "표시 완료"만 봅니다(연출 시간은 검증 대상 아님)
- 삭제·재생성으로 버려진 메시지는 이후 턴의 맥락 계산(`memoryRefs`·`contextReflect`)에서
  제외됩니다 — 되돌림 공통 원칙(system-spec §5-1)의 mock 측 이행입니다
