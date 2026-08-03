# -*- coding: utf-8 -*-
"""SUT 실행 GIF 생성 — README에서 「직접 만든 검증 대상」을 움직임으로 보인다

무엇을 담나
----------
  게이팅 한 갈래를 처음부터 끝까지 밟는다 — 미로그인에서 언세이프가 가려져 있고,
  로그인하면 풀리고, 대화방에서 응답이 스트리밍된다. 화면 여럿을 훑는 것보다
  **하나의 규칙이 상태에 따라 갈리는 것**을 보이는 편이 QA 산출물답다.

왜 스크립트로 만드나
------------------
  손으로 녹화하면 다시 만들 수 없다. SUT가 바뀌면 GIF는 옛 화면을 계속 보여 주는데
  아무도 모른다. 프레임을 Playwright로 찍으면 재생성이 한 줄이 된다.

의존성
------
  Pillow가 필요하다. 이것은 **문서 자산을 만드는 도구**이며 테스트 런타임이 아니므로
  automation/requirements.txt에 넣지 않는다 — 넣으면 CI가 검증과 무관한 것을 설치한다.

사용법
------
    python gen_sut_demo_gif.py --sut <sut 디렉터리> -o <출력 gif>
"""
import argparse
import functools
import http.server
import io
import os
import sys
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

W, H = 960, 620          # 캡처 크기 — README에서 줄여 보이므로 과하게 크게 잡지 않는다
SCALE = 0.75             # 파일 크기를 줄이는 가장 싼 수단
HOLD = 900               # 장면을 붙드는 시간(ms) — 읽을 틈을 준다
STEP = 260               # 동작 사이 간격(ms)


def serve(directory):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=os.path.abspath(directory))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    srv.RequestHandlerClass.log_message = lambda *a, **k: None
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % srv.server_address[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sut", required=True)
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    srv, url = serve(args.sut)
    frames, durations = [], []

    def shot(ms=STEP):
        frames.append(Image.open(io.BytesIO(page.screenshot())).convert("RGB"))
        durations.append(ms)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": W, "height": H})
            page.goto(url + "?seed=1")
            page.wait_for_function(
                "() => !!window.__VN__ && !!window.__VN__.getState().baseDay")
            page.evaluate("() => window.__VN__.reset()")

            # ① 미로그인 홈 — 언세이프가 가려져 있다
            page.wait_for_timeout(400)
            shot(HOLD)
            page.mouse.wheel(0, 420)
            page.wait_for_timeout(300)
            shot(HOLD)

            # ② 로그인 — 게이트가 풀린다
            page.evaluate("() => { VN.loginOpen = true; window.__VN__.refresh(); }")
            page.wait_for_timeout(300)
            shot()
            page.evaluate("() => { login('a'); setAdultVerified(true); "
                          "VN.loginOpen = false; window.__VN__.refresh(); }")
            page.wait_for_timeout(400)
            shot(HOLD)

            # ③ 캐릭터 페이지
            page.evaluate("() => { VN.screen = 's2'; VN.homeChip = 'reco'; "
                          "window.__VN__.refresh(); }")
            page.wait_for_timeout(200)
            card = page.locator('[data-testid^="s2-card-"]').first
            if card.count():
                card.click()
                page.wait_for_timeout(500)
                shot(HOLD)

            # ④ 대화방 — 응답이 스트리밍된다
            page.evaluate("""() => {
                const res = addProfile({ name: '서진' });
                const prof = profilesOf().find(x => x.id === (res && res.id));
                openRoom('c1', prof); VN.screen = 's4'; window.__VN__.refresh();
            }""")
            page.wait_for_timeout(400)
            shot(HOLD)
            # 입력칸에 글자가 차는 것까지 보인다 — 「직접 조작할 수 있는 대상」이 요지다
            page.fill('[data-testid="s4-input"]', "오늘 어땠어?")
            page.wait_for_timeout(200)
            shot(500)
            page.evaluate("() => sendMessage('오늘 어땠어?')")
            # 스트리밍은 응답 길이에 달렸다 — 고정 간격으로 찍으면 같은 그림이 겹쳐
            # Pillow가 합쳐 버린다. 표시가 끝나는 것을 조건으로 잡고 그 사이만 얇게 찍는다
            for _ in range(6):
                page.wait_for_timeout(130)
                shot(150)
                if page.locator('[data-testid="s4-streaming"]').count() == 0:
                    break
            page.wait_for_selector('[data-testid="s4-streaming"]', state="detached",
                                   timeout=5000)
            page.wait_for_timeout(250)
            shot(HOLD + 600)

            browser.close()
    finally:
        srv.shutdown()
        srv.server_close()

    size = (int(W * SCALE), int(H * SCALE))
    frames = [f.resize(size, Image.LANCZOS) for f in frames]
    frames[0].save(args.output, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    kb = os.path.getsize(args.output) / 1024
    print("saved %s | %d프레임 · %dx%d · %.0fKB"
          % (args.output, len(frames), size[0], size[1], kb))
    return 0


if __name__ == "__main__":
    sys.exit(main())
