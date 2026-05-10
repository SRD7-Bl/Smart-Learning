import json
import time
import re
from playwright.sync_api import Playwright, sync_playwright

TARGET_HINT = "MyDayCalendarStudentList"  # 先用这个当线索

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # 记录：我们真正抓到的“请求 URL”
    found = {
        "url": None,
        "method": None,
        "page": None,
        "candidates": set(),  # 记录一些可疑的 URL，方便你定位
    }

    # 1) 全局拦截所有 request：比 page.on("response") 更稳
    def route_handler(route):
        req = route.request
        url = req.url

        # 只要 URL 里带 MyDay / Schedule 这些词，我们就记下来（帮助你找对真正的接口）
        if ("MyDay" in url) or ("Schedule" in url) or ("Calendar" in url):
            found["candidates"].add(url)

        # 命中我们想要的接口线索
        if found["url"] is None and TARGET_HINT in url:
            found["url"] = url
            found["method"] = req.method
            print("🎯 FOUND request:", req.method, url, flush=True)

        route.continue_()

    context.route("**/*", route_handler)

    # 2) 找到最终“真正的 schedule 页面 page”，并保存下来
    def on_new_page(p):
        print("🆕 new page:", p.url, flush=True)
    context.on("page", on_new_page)

    page = context.new_page()

    # --- 登录流程（你原来的 codegen 可以保留，但注意：不要手动 goto authorize URL） ---
    page.goto("https://ridleycollege.myschoolapp.com/app?svcid=edu#login")

    page.get_by_role("textbox", name="Username or Email").fill("liang_yang@ridleycollege.com")
    page.get_by_role("button", name="Next").click()

    # 等微软登录页出现（可能同页跳转）
    page.wait_for_load_state("domcontentloaded")
    page.get_by_role("textbox", name=re.compile(r"Enter the password", re.I)).fill("Leo20091117")
    page.get_by_role("button", name=re.compile(r"Sign in", re.I)).click()

    # 可能出现 Stay signed in?
    try:
        page.get_by_role("button", name=re.compile(r"^No$|^Yes$", re.I)).click(timeout=2000)
    except Exception:
        pass

    # 3) 等回到 myschoolapp（或者至少等到任何一个 page 在 myschoolapp 域名上）
    deadline = time.time() + 60
    schedule_page = None
    while time.time() < deadline:
        for p in context.pages:
            if "myschoolapp.com/app" in p.url:
                schedule_page = p
        if schedule_page:
            break
        time.sleep(0.2)

    if not schedule_page:
        raise RuntimeError("没找到回到 myschoolapp 的页面（可能还卡在 SSO / MFA）")

    print("✅ schedule page:", schedule_page.url, flush=True)

    # 4) 触发一次“刷新/切换日期”让它一定发请求（你说你切日期会发，那就做一次点击）
    #    这里我给你两种方式：你任选一种

    # 方式A：你手动点一下（最可靠调试）：给你 15 秒手动操作切到有课那天
    print("👉 请在 15 秒内手动切到一个有课的日期/周，让页面发出 schedule 请求", flush=True)
    time.sleep(15)

    # 方式B（如果你已经知道哪个按钮能触发）：用代码点
    # schedule_page.get_by_role("button", name="Next week").click()

    # 5) 等 route 捕获到真实 URL
    deadline = time.time() + 30
    while time.time() < deadline and found["url"] is None:
        time.sleep(0.2)

    if found["url"] is None:
        print("❌ 没捕获到包含 MyDayCalendarStudentList 的请求", flush=True)
        # 打印一些候选 URL（只打印前 30 个，避免刷屏）
        cands = list(found["candidates"])[:30]
        print("候选请求 URL（前30个）:", flush=True)
        for u in cands:
            print("  -", u, flush=True)
        raise RuntimeError("请从候选 URL 里找到真正的 schedule 接口关键词，然后更新 TARGET_HINT。")

    # 6) 拿到了 URL 后：不用等 response，直接在页面里 fetch（自动带 cookie/session）
    url = found["url"]
    print("== fetching json via page.evaluate(fetch) ==", flush=True)

    data = schedule_page.evaluate(
        """async (u) => {
            const r = await fetch(u, { credentials: 'include' });
            const text = await r.text();
            // 有些接口可能返回空字符串/非json，做个保护
            try { return JSON.parse(text); } catch(e) { return {__raw:text}; }
        }""",
        url
    )

    with open("schedule_raw.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if isinstance(data, list):
        print(f"✅ saved schedule_raw.json (list len={len(data)})", flush=True)
    else:
        print("✅ saved schedule_raw.json (non-list)", flush=True)

    context.close()
    browser.close()

with sync_playwright() as p:
    run(p)

