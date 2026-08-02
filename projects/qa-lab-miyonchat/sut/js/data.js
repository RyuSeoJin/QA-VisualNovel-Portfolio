/* 정적 데이터 + 시트 데이터 초기값
 *
 * 정적 데이터  — 빌드 시 고정. 시나리오·첫 메시지·금칙 토큰
 * 시트 데이터  — 테스트 가변. T1 데이터 시트와 __VN__.setData()만 씁니다
 *                (청사진 §2 스코프 표)
 *
 * 가상 시계: 실시계를 쓰지 않습니다. 기준일("오늘")도 시트의 한 칸입니다
 *            (system-spec §8-1). 날짜는 YYYY-MM-DD 문자열 비교만 합니다.
 */
const VN_DATA = {
  /* 기준일 — 이 값이 SUT의 "오늘"입니다 */
  baseDay: "2026-08-02",

  /* 캐릭터 속성 — 리뷰 수·좋아요 수·태그·세이프 플래그 */
  characters: [
    { id: "c1", name: "하루", tagline: "옆자리 소꿉친구", category: "로맨스",
      tags: ["소꿉친구", "후회"], safe: true, likes: 320, reviews: 84, score: 4.6,
      createdDay: "2026-07-30" },
    { id: "c2", name: "레온", tagline: "회귀한 기사단장", category: "판타지",
      tags: ["회귀", "능력"], safe: true, likes: 512, reviews: 120, score: 4.4,
      createdDay: "2026-07-28" },
    { id: "c3", name: "미나", tagline: "야근 동료", category: "일상",
      tags: ["직장", "힐링"], safe: true, likes: 180, reviews: 41, score: 4.9,
      createdDay: "2026-08-01" },
    { id: "c4", name: "카일", tagline: "계약 연애 상대", category: "로맨스",
      tags: ["계약연애", "집착"], safe: false, likes: 640, reviews: 210, score: 4.2,
      createdDay: "2026-07-25" },
    { id: "c5", name: "세라", tagline: "이세계 동행자", category: "판타지",
      tags: ["이세계", "빙의"], safe: true, likes: 96, reviews: 12, score: 5.0,
      createdDay: "2026-08-02" },
    { id: "c6", name: "도윤", tagline: "같은 반 짝꿍", category: "일상",
      tags: ["학원물", "동거"], safe: true, likes: 74, reviews: 3, score: 5.0,
      createdDay: "2026-07-31" }
  ],

  /* 이용수 이벤트 — 유저×캐릭터×날짜. 같은 조합은 중복이어도 1로 셉니다 */
  events: [
    { user: "u1", charId: "c1", day: "2026-08-02" },
    { user: "u1", charId: "c1", day: "2026-08-02" },
    { user: "u2", charId: "c1", day: "2026-08-02" },
    { user: "u1", charId: "c2", day: "2026-08-01" },
    { user: "u2", charId: "c2", day: "2026-07-30" },
    { user: "u3", charId: "c4", day: "2026-08-02" },
    { user: "u4", charId: "c4", day: "2026-07-29" },
    { user: "u1", charId: "c3", day: "2026-07-20" }
  ],

  /* 계정 속성 — 팔로워·팔로잉. 표시만 하고 발생 로직은 없습니다 */
  accountStats: { followers: 12, following: 34 },

  /* 알림 항목 — 표시 반영만 검증합니다(발생 로직 없음) */
  notifications: [
    { id: "n1", text: "데일리 미션이 초기화되었습니다", day: "2026-08-02" },
    { id: "n2", text: "새 캐릭터가 등록되었습니다", day: "2026-08-01" }
  ],

  /* 카테고리 칩 3종·취향 태그 (system-spec §8-6) */
  categories: [
    { name: "로맨스", tags: ["집착", "소꿉친구", "계약연애", "후회"] },
    { name: "판타지", tags: ["회귀", "빙의", "이세계", "능력"] },
    { name: "일상", tags: ["힐링", "학원물", "직장", "동거"] }
  ],

  /* 금칙 코퍼스 — 실제 문자열을 저장소에 넣지 않습니다(추상 토큰) */
  blockedTokens: ["[BLOCKED_TERM_A]", "[BLOCKED_TERM_B]", "[BLOCKED_TERM_C]"]
};

/* 시트 데이터로 노출되는 테이블 — T1과 setData()가 이 키만 씁니다 */
const SHEET_TABLES = ["characters", "events", "accountStats", "notifications"];
