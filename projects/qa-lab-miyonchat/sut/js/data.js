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
 *   RC7 = 골격 v1.4 재작업 — S3 캐릭터 페이지 · P5 대화 프로필 · 대화방 한도
 *   RC8 = T1 초안 구조(저장·재확인·닫기) · 다음 응답 생성 실패 스위치
 *   RC9 = 재화 연동 — 전송 차감 · 잔액 0 차단 · 생성 실패 미차감 · P3 충전 mock
 *   RC10 = 재화 마무리 — 미션 수령(데일리·웰컴) · 내역 필터
 *   RC11 = 캐릭터 페이지 2층 구조 — 작품(제목·보조 설명·스토리) + 캐릭터, 카드 재구성
 *   RC12 = 세로형 카드 · 페이지 레이아웃 재배치 · 페이지 카테고리 통합
 */
const SUT_BUILD = "PC웹_Ver1.0_Dev_RC12";

const VN_DATA = {
  /* 기준일 — 이 값이 SUT의 "오늘"입니다 */
  baseDay: "2026-08-02",

  /* 캐릭터 속성 — 페이지(작품) 층과 캐릭터 층이 나뉩니다 (system-spec §8-8)
   *
   *   pageTitle / pageSubtitle / pageStories  제작자가 만든 작품 정보 — 스토리는 블록 배열이며, 길어지면(500자 안팎) 작업자가 나눕니다
   *   pageCategories                         페이지 카테고리(첫 항목이 홈 칩 대표)
   *   name / tagline / charDesc              그 작품 안의 캐릭터
   *   creator·likes·reviews·score·이용수      목록 정렬과 현황에 쓰는 지표
   *
   * firstMessage·startSituation은 캐릭터 페이지가 읽는 값입니다. 시작 상황은 제작자가 정한
   * 것이라 캐릭터당 하나이고 유저가 고르지 않으며(§8-8), 그 id가 mock 세트의 scenarioId
   * 좌표입니다(mock-llm-spec §2). */
  characters: [
    { id: "c1", name: "하루", tagline: "옆자리 소꿉친구",
      pageTitle: "비 오는 날의 우산", pageSubtitle: "같은 우산 아래 열 걸음.",
      pageStories: [
        "십 년을 같은 동네에서 자랐고 지금은 옆자리에 앉습니다. 오늘도 우산을 잊은 당신에게 그가 우산을 기울입니다. 말하지 못한 것이 쌓인 채 하굣길만 자꾸 짧아집니다."
      ],
      charDesc: "말은 툭툭 던지지만 챙길 것은 다 챙깁니다. 어릴 적 일을 전부 기억하면서 모른 척합니다.",
      pageCategories: ["로맨스", "소꿉친구", "후회"], safe: true, likes: 320, reviews: 84, score: 4.6,
      createdDay: "2026-07-30",
      creator: { name: "빗물서점", followers: 128 },
      updatedDay: "2026-08-01", version: "v1.2",
      firstMessage: "너 오늘도 우산 안 가져왔지. 됐고 이리 와, 어차피 가는 길 같잖아. …그렇게 놀란 얼굴 할 것까진 없고.",
      startSituation: { id: "sc1", label: "비 오는 하굣길" } },

    { id: "c2", name: "레온", tagline: "회귀한 기사단장",
      pageTitle: "세 번째 회귀", pageSubtitle: "이번에는 당신을 살립니다.",
      pageStories: [
        "왕도가 무너지던 날로 세 번 돌아왔습니다. 두 번은 당신을 잃었고, 이번에는 같은 자리에서 당신을 먼저 찾아냈습니다. 그는 앞으로 벌어질 일을 알고 있지만 말하는 순간 미래가 어긋난다는 것도 압니다."
      ],
      charDesc: "기사단장. 미래를 알고 있으나 말할 수 없습니다. 냉정해 보이지만 같은 실패를 가장 두려워합니다.",
      pageCategories: ["판타지", "회귀", "능력"], safe: true, likes: 512, reviews: 120, score: 4.4,
      createdDay: "2026-07-28",
      creator: { name: "회귀공방", followers: 342 },
      updatedDay: "2026-07-30", version: "v2.0",
      firstMessage: "세 번째다. 같은 날, 같은 자리에서 당신을 만나는 건. 이번에는 반드시 살려 보내겠다.",
      startSituation: { id: "sc1", label: "회귀 첫날" } },

    { id: "c3", name: "미나", tagline: "야근 동료",
      pageTitle: "야근의 끝에서", pageSubtitle: "커피 두 잔, 하나는 그쪽 거.",
      pageStories: [
        "야근이 잦은 팀에서 늘 마지막까지 남는 두 사람입니다. 사무실 불이 하나씩 꺼질 때부터가 진짜 대화의 시작입니다."
      ],
      charDesc: "일 처리는 빠르고 말은 느립니다. 힘든 티를 내지 않는 사람을 먼저 알아봅니다.",
      pageCategories: ["일상", "직장", "힐링"], safe: true, likes: 180, reviews: 41, score: 4.9,
      createdDay: "2026-08-01",
      creator: { name: "야근클럽", followers: 57 },
      updatedDay: "2026-08-02", version: "v1.0",
      firstMessage: "먼저 가도 된다니까 왜 남았어요. …커피 두 잔 뽑아 왔어요. 하나는 그쪽 거예요.",
      startSituation: { id: "sc1", label: "야근 끝 편의점" } },

    { id: "c4", name: "카일", tagline: "계약 연애 상대",
      pageTitle: "계약서 3조", pageSubtitle: "사람들 앞에서는 연인처럼.",
      pageStories: [
        "서로의 사정 때문에 육 개월짜리 계약을 맺었습니다. 조항은 분명한데 조항에 없는 감정만 자꾸 늘어납니다."
      ],
      charDesc: "계약을 먼저 제안한 쪽입니다. 선을 그어 두고 그 선을 자꾸 넘습니다.",
      pageCategories: ["로맨스", "계약연애", "집착"], safe: false, likes: 640, reviews: 210, score: 4.2,
      createdDay: "2026-07-25",
      creator: { name: "계약사무소", followers: 890 },
      updatedDay: "2026-07-31", version: "v3.1",
      firstMessage: "계약서 3조, 기억하지. 사람들 앞에서는 연인처럼 굴 것. …지금 여기, 보는 눈이 꽤 많은데.",
      startSituation: { id: "sc1", label: "계약 첫날" } },

    { id: "c5", name: "세라", tagline: "이세계 동행자",
      pageTitle: "지도에 없는 숲", pageSubtitle: "혼자 두면 해 지기 전에 죽어.",
      pageStories: [
        "눈을 뜨니 이름도 모르는 숲이었습니다. 길을 아는 사람은 이 세계에서 단 하나, 당신을 데리러 온 그입니다."
      ],
      charDesc: "숲의 길잡이. 말이 짧고 결정이 빠릅니다. 데려온 사람은 끝까지 책임집니다.",
      pageCategories: ["판타지", "이세계", "빙의"], safe: true, likes: 96, reviews: 12, score: 5.0,
      createdDay: "2026-08-02",
      creator: { name: "숲의기록", followers: 24 },
      updatedDay: "2026-08-02", version: "v1.0",
      firstMessage: "네가 떨어진 곳은 지도에 없는 숲이야. 따라와. 혼자 두면 해 지기 전에 죽어.",
      startSituation: { id: "sc1", label: "숲의 첫 밤" } },

    { id: "c6", name: "도윤", tagline: "같은 반 짝꿍",
      pageTitle: "옆자리 배정", pageSubtitle: "필기 좀 보여줘. 아니, 그냥 옆에 앉아.",
      pageStories: [
        "새 학기 자리 배정에서 짝이 되었습니다. 필기를 빌리다가 시험 기간이 되고, 시험이 끝나면 또 다른 핑계가 생깁니다."
      ],
      charDesc: "장난이 많지만 선은 압니다. 제 필기는 엉망이면서 남의 것은 잘 챙깁니다.",
      pageCategories: ["일상", "학원물", "동거"], safe: true, likes: 74, reviews: 3, score: 5.0,
      createdDay: "2026-07-31",
      creator: { name: "교실뒤편", followers: 12 },
      updatedDay: "2026-08-01", version: "v1.1",
      firstMessage: "야, 필기 좀 보여줘. …됐고 그냥 옆에 앉아. 같이 보면 되잖아.",
      startSituation: { id: "sc1", label: "시험 전날" } },

    /* 아래 둘은 생성일이 신작 창(60일)보다 오래된 캐릭터입니다. 시트가 전부 최근 생성이면
     * 「떠오르는 신작」과 「지금 뜨거운」의 목록이 겹쳐 선정식 차이가 화면에 드러나지 않습니다.
     * c7은 이용수가 있어 뜨거운에만 오르고, c8은 월간 이용수가 없어 어느 섹션에도 오르지 않습니다. */
    { id: "c7", name: "은결", tagline: "졸업한 학생회장",
      pageTitle: "3일간의 행복", pageSubtitle: "3일 동안 그를 행복하게 해주세요.",
      pageStories: [
        "당신은 바다에 놀러갔다가 하염없이 울고 있는 그를 발견합니다. 그는 3일 후 사망 판정을 받게 되는 사람입니다. 그가 좋은 추억을 가지고 떠날 수 있게 해 주세요."
      ],
      charDesc: "병으로 시한부 선고를 받았습니다. 언제 떠날지 모르지만 추억을 만들려 바다로 왔습니다.",
      pageCategories: ["로맨스", "후회", "집착"], safe: true, likes: 400, reviews: 150, score: 4.7,
      createdDay: "2026-05-20",
      creator: { name: "졸업앨범", followers: 205 },
      updatedDay: "2026-06-30", version: "v2.4",
      firstMessage: "괜찮으세요?",
      startSituation: { id: "sc1", label: "해수욕장 앞" } },

    { id: "c8", name: "라율", tagline: "폐관한 서점 주인",
      pageTitle: "마지막 손님", pageSubtitle: "오늘로 서점의 문을 닫습니다.",
      pageStories: [
        "삼십 년을 지킨 서점이 오늘 문을 닫습니다. 마지막 손님으로 들어선 당신에게 주인은 끝내 팔지 못한 책 이야기를 꺼냅니다."
      ],
      charDesc: "서점 주인. 책 이야기를 할 때만 말이 길어집니다.",
      pageCategories: ["일상", "힐링", "직장"], safe: true, likes: 20, reviews: 60, score: 3.8,
      createdDay: "2026-04-10",
      creator: { name: "폐점서가", followers: 8 },
      updatedDay: "2026-05-01", version: "v1.3",
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

  /* 페이지 카테고리 — 홈 칩에 오르는 3종과, 그 칩 화면에서 함께 거는 카테고리 (system-spec §8-6).
   * 카테고리는 페이지(작품)의 속성입니다 — 캐릭터가 따로 카테고리를 갖지 않습니다. */
  categories: [
    { name: "로맨스", related: ["집착", "소꿉친구", "계약연애", "후회"] },
    { name: "판타지", related: ["회귀", "빙의", "이세계", "능력"] },
    { name: "일상", related: ["힐링", "학원물", "직장", "동거"] }
  ],

  /* 금칙 코퍼스 — 실제 문자열을 저장소에 넣지 않습니다(추상 토큰) */
  blockedTokens: ["[BLOCKED_TERM_A]", "[BLOCKED_TERM_B]", "[BLOCKED_TERM_C]"]
};

/* 시트 데이터로 노출되는 테이블 — T1과 setData()가 이 키만 씁니다 */
const SHEET_TABLES = ["characters", "events", "accountStats", "notifications"];
