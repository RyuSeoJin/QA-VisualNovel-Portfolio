/* 정적 데이터 + 시트 데이터 초기값
 *
 * 정적 데이터  — 빌드 시 고정. 시나리오·첫 메시지·금칙 토큰
 * 시트 데이터  — 테스트 가변. T1 데이터 시트와 __VN__.setData()만 씁니다
 *                (청사진 §2 스코프 표)
 *
 * 가상 시계: 실시계를 쓰지 않습니다. 기준일("오늘")도 시트의 한 칸입니다
 *            (system-spec §8-1). 날짜는 YYYY-MM-DD 문자열 비교만 합니다.
 */
/* 빌드 버전 — {테스트환경}_{개발목표버전}_{스프린트}_{확인버전}
 *
 * 확인버전(RC)은 검증 대상 빌드가 바뀔 때마다 올립니다 — 화면 슬라이스가 끝났을 때든
 * 결함 수정이 반영됐을 때든. 이슈의 「영향 받는 버전」이 이 값을 가리키므로, 테스터가
 * 어느 빌드에서 재현했는지 화면(푸터)에서 바로 확인할 수 있어야 합니다.
 *   RC1 = 첫 슬라이스 개발 빌드 (miyonchat-1 재현)
 *   RC2 = miyonchat-1 수정 반영 — 전역 셸 · S1 · 라우팅 가드 · P4 · T1 디버그 콘솔
 *   RC3 = S2 홈 — 필터 칩 · 추천/랭킹/신작/카테고리 · 캐릭터 카드·상세 · 언세이프 게이팅
 *   RC4 = 상단 바 — 키워드 검색(결과는 홈에 표시) · 알림 목록
 *         + 로그인 유도를 모달로 전환하고 막힌 동작을 로그인 후 이어서 수행
 *   RC5 = S3 페르소나 폼 — 글자수 경계 · 필수값 검증 · 저장 후 시작점 인계
 *   RC6 = S4 대화 뼈대 — mock 응답(시드 결정) · 스트리밍 표시 · 방 스코프
 */
const SUT_BUILD = "PC웹_Ver1.0_Dev_RC6";

const VN_DATA = {
  /* 기준일 — 이 값이 SUT의 "오늘"입니다 */
  baseDay: "2026-08-02",

  /* 캐릭터 속성 — 리뷰 수·좋아요 수·태그·세이프 플래그
   *
   * firstMessage·startSituation은 캐릭터 페이지가 읽는 값입니다. 시작 상황은 제작자가 정한
   * 것이라 캐릭터당 하나이고 유저가 고르지 않으며(system-spec §8-8), 그 id가 mock 세트의
   * scenarioId 좌표입니다(mock-llm-spec §2). */
  characters: [
    { id: "c1", name: "하루", tagline: "옆자리 소꿉친구", category: "로맨스",
      tags: ["소꿉친구", "후회"], safe: true, likes: 320, reviews: 84, score: 4.6,
      createdDay: "2026-07-30",
      firstMessage: "너 오늘도 우산 안 가져왔지. 됐고 이리 와, 어차피 가는 길 같잖아. …그렇게 놀란 얼굴 할 것까진 없고.",
      startSituation: { id: "sc1", label: "비 오는 하굣길" } },
    { id: "c2", name: "레온", tagline: "회귀한 기사단장", category: "판타지",
      tags: ["회귀", "능력"], safe: true, likes: 512, reviews: 120, score: 4.4,
      createdDay: "2026-07-28",
      firstMessage: "세 번째다. 같은 날, 같은 자리에서 당신을 만나는 건. 이번에는 반드시 살려 보내겠다.",
      startSituation: { id: "sc1", label: "회귀 첫날" } },
    { id: "c3", name: "미나", tagline: "야근 동료", category: "일상",
      tags: ["직장", "힐링"], safe: true, likes: 180, reviews: 41, score: 4.9,
      createdDay: "2026-08-01",
      firstMessage: "먼저 가도 된다니까 왜 남았어요. …커피 두 잔 뽑아 왔어요. 하나는 그쪽 거예요.",
      startSituation: { id: "sc1", label: "야근 끝 편의점" } },
    { id: "c4", name: "카일", tagline: "계약 연애 상대", category: "로맨스",
      tags: ["계약연애", "집착"], safe: false, likes: 640, reviews: 210, score: 4.2,
      createdDay: "2026-07-25",
      firstMessage: "계약서 3조, 기억하지. 사람들 앞에서는 연인처럼 굴 것. …지금 여기, 보는 눈이 꽤 많은데.",
      startSituation: { id: "sc1", label: "계약 첫날" } },
    { id: "c5", name: "세라", tagline: "이세계 동행자", category: "판타지",
      tags: ["이세계", "빙의"], safe: true, likes: 96, reviews: 12, score: 5.0,
      createdDay: "2026-08-02",
      firstMessage: "네가 떨어진 곳은 지도에 없는 숲이야. 따라와. 혼자 두면 해 지기 전에 죽어.",
      startSituation: { id: "sc1", label: "숲의 첫 밤" } },
    { id: "c6", name: "도윤", tagline: "같은 반 짝꿍", category: "일상",
      tags: ["학원물", "동거"], safe: true, likes: 74, reviews: 3, score: 5.0,
      createdDay: "2026-07-31",
      firstMessage: "야, 필기 좀 보여줘. …됐고 그냥 옆에 앉아. 같이 보면 되잖아.",
      startSituation: { id: "sc1", label: "시험 전날" } },
    /* 아래 둘은 생성일이 신작 창(60일)보다 오래된 캐릭터입니다. 시트가 전부 최근 생성이면
     * 「떠오르는 신작」과 「지금 뜨거운」의 목록이 겹쳐 선정식 차이가 화면에 드러나지 않습니다.
     * c7은 이용수가 있어 뜨거운에만 오르고, c8은 월간 이용수가 없어 어느 섹션에도 오르지 않습니다. */
    { id: "c7", name: "은결", tagline: "졸업한 학생회장", category: "로맨스",
      tags: ["후회", "집착"], safe: true, likes: 400, reviews: 150, score: 4.7,
      createdDay: "2026-05-20",
      firstMessage: "졸업식 이후로 처음이네. 그때 못 한 말이 있어서, 계속 여기 서 있었어.",
      startSituation: { id: "sc1", label: "졸업식 그날" } },
    { id: "c8", name: "라율", tagline: "폐관한 서점 주인", category: "일상",
      tags: ["힐링", "직장"], safe: true, likes: 20, reviews: 60, score: 3.8,
      createdDay: "2026-04-10",
      firstMessage: "오늘로 문을 닫습니다. …마지막 손님이 당신이라 다행이네요.",
      startSituation: { id: "sc1", label: "폐점 전날" } }
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
    { user: "u1", charId: "c3", day: "2026-07-20" },
    { user: "u5", charId: "c7", day: "2026-08-02" },
    { user: "u6", charId: "c7", day: "2026-08-02" },
    { user: "u5", charId: "c7", day: "2026-08-01" }
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
