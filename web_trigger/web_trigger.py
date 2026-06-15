#!/usr/bin/env python3
"""
web_trigger.py — 定时网页触发与自动化流程 CLI（基于 Playwright）

- 按时间表达式（cron / 时间段）开启"触发窗口"
- 窗口内高频轮询目标元素并触发（click / js_click / dispatch）
- 触发成功后执行自定义后续流程（填表、点击、截图、Webhook 通知等）

仅用于自动化你**有权操作**的网站/账户，请遵守目标站点条款与当地法律。
"""
from __future__ import annotations

import argparse
import logging
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml
from croniter import croniter
from playwright.sync_api import TimeoutError as PWTimeout, sync_playwright

try:
    import requests
except ImportError:
    requests = None

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

log = logging.getLogger("web_trigger")


# ----------------------------- 时间与窗口解析 -----------------------------

def now_tz(tz_name: str) -> datetime:
    if ZoneInfo:
        return datetime.now(ZoneInfo(tz_name))
    return datetime.now()


def parse_range(rng: str, day: datetime):
    """解析 'HH:MM-HH:MM' 为当天的 (start, end)，跨午夜自动 +1 天。"""
    start_s, end_s = rng.split("-")
    sh, sm = map(int, start_s.split(":"))
    eh, em = map(int, end_s.split(":"))
    start = day.replace(hour=sh, minute=sm, second=0, microsecond=0)
    end = day.replace(hour=eh, minute=em, second=0, microsecond=0)
    if end <= start:
        end += timedelta(days=1)
    return start, end


def resolve_window(win: dict, now: datetime):
    """返回 (start, end, is_active)：当前所在窗口或下一个即将到来的窗口。"""
    if win.get("cron"):
        dur = timedelta(seconds=win.get("duration_seconds", 120))
        prev = croniter(win["cron"], now).get_prev(datetime)
        if prev <= now < prev + dur:
            return prev, prev + dur, True
        nxt = croniter(win["cron"], now).get_next(datetime)
        return nxt, nxt + dur, False

    if win.get("range"):
        for delta in (-1, 0, 1):  # 兼顾跨午夜
            start, end = parse_range(win["range"], now + timedelta(days=delta))
            if start <= now < end:
                return start, end, True
        cands = []
        for delta in (0, 1):
            start, end = parse_range(win["range"], now + timedelta(days=delta))
            if start > now:
                cands.append((start, end))
        start, end = min(cands, key=lambda x: x[0])
        return start, end, False

    raise ValueError(f"窗口需要 'cron' 或 'range': {win}")


def next_state(windows: list[dict], now: datetime):
    """聚合多个窗口：任一激活则返回 active（取结束最晚者），否则返回最近的下一个。"""
    active, upcoming = [], []
    for win in windows:
        s, e, is_active = resolve_window(win, now)
        (active if is_active else upcoming).append((s, e))
    if active:
        s, e = max(active, key=lambda x: x[1])
        return "active", s, e
    s, e = min(upcoming, key=lambda x: x[0])
    return "idle", s, e


# ----------------------------- 自动化核心 -----------------------------

class Automation:
    def __init__(self, cfg: dict, dry_run: bool = False):
        self.cfg = cfg
        self.dry_run = dry_run
        self.success_count = 0

    def find_and_click(self, page) -> bool:
        trig = self.cfg["trigger"]
        for sel in trig["selectors"]:
            try:
                loc = page.locator(sel).first
                if loc.count() == 0:
                    continue
                state = trig.get("wait_state", "visible")
                if state == "enabled" and not loc.is_enabled():
                    continue
                if state == "visible" and not loc.is_visible():
                    continue
                log.info("命中触发元素: %s", sel)
                if self.dry_run:
                    log.info("[dry-run] 跳过点击")
                    return True
                method = trig.get("click_method", "click")
                if method == "js_click":
                    loc.evaluate("el => el.click()")
                elif method == "dispatch":
                    loc.dispatch_event("click")
                else:
                    loc.click(timeout=2000)
                return True
            except PWTimeout:
                continue
            except Exception as exc:
                log.debug("选择器 %s 异常: %s", sel, exc)
        return False

    def check_success(self, page) -> bool:
        conds = self.cfg.get("success", {}).get("any_of", [])
        if not conds:
            return True  # 未配置则视点击为成功
        for cond in conds:
            try:
                if "url_contains" in cond and cond["url_contains"] in page.url:
                    return True
                if "selector_visible" in cond and \
                        page.locator(cond["selector_visible"]).first.is_visible():
                    return True
                if "js" in cond and page.evaluate(cond["js"]):
                    return True
            except Exception:
                pass
        return False

    def run_post_flow(self, page):
        for step in self.cfg.get("on_success", []):
            self.run_step(page, step)

    def run_step(self, page, step):
        action = step["action"]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log.info("后续步骤: %s", action)
        if self.dry_run and action != "screenshot":
            log.info("[dry-run] 跳过 %s", action)
            return
        if action == "goto":
            page.goto(step["url"])
        elif action == "click":
            page.locator(step["selector"]).first.click()
        elif action == "fill":
            page.locator(step["selector"]).first.fill(step["value"])
        elif action == "wait_for":
            page.locator(step["selector"]).first.wait_for(
                state=step.get("state", "visible"),
                timeout=step.get("timeout_ms", 15000),
            )
        elif action == "sleep":
            time.sleep(step.get("seconds", 1))
        elif action == "eval_js":
            page.evaluate(step["script"])
        elif action == "screenshot":
            path = step.get("path", "shot_{ts}.png").format(ts=ts)
            page.screenshot(path=path, full_page=step.get("full_page", False))
            log.info("已截图: %s", path)
        elif action == "notify":
            self.notify(step)
        else:
            log.warning("未知步骤: %s", action)

    def notify(self, step):
        msg = step.get("message", "触发成功")
        webhook = step.get("webhook")
        if not webhook:
            log.info("通知: %s", msg)
            return
        if requests is None:
            log.warning("未安装 requests，跳过 webhook")
            return
        try:
            payload = step.get("payload") or {
                "msg_type": "text", "content": {"text": msg}, "text": msg,
            }
            requests.post(webhook, json=payload, timeout=10)
        except Exception as exc:
            log.warning("通知失败: %s", exc)

    def _wait_page_ready(self, page):
        """导航后等待页面（SPA）渲染完成，等待触发选择器出现或超时。"""
        selectors = self.cfg["trigger"]["selectors"]
        try:
            page.wait_for_selector(selectors[0], state="attached", timeout=15000)
        except PWTimeout:
            log.debug("等待触发元素超时（15s），继续轮询")

    def run_window(self, page, end_time: datetime, tz: str) -> bool:
        s = self.cfg["schedule"]
        poll = s.get("poll_interval_ms", 500) / 1000
        jitter = s.get("jitter_ms", 200) / 1000
        max_trig = s.get("max_triggers", 1)
        reload_each = s.get("reload_each_poll", False)
        triggered = 0
        while now_tz(tz) < end_time:
            # 只在未触发过时 reload；成功后保持当前页面状态（结算页等）
            if reload_each and triggered == 0:
                try:
                    page.reload(wait_until="domcontentloaded")
                    self._wait_page_ready(page)
                except Exception:
                    pass
            # 成功后不再重复点击，只等待窗口结束或达到 max_triggers
            if triggered == 0 and self.find_and_click(page):
                time.sleep(self.cfg["trigger"].get("post_click_wait_ms", 800) / 1000)
                if self.check_success(page):
                    triggered += 1
                    self.success_count += 1
                    log.info("✅ 第 %d 次触发成功", triggered)
                    self.run_post_flow(page)
                    if triggered >= max_trig:
                        return True
                else:
                    log.info("点击成功但未达成功条件，继续重试")
            time.sleep(poll + random.uniform(0, jitter))
        return triggered > 0


# ----------------------------- 浏览器与命令 -----------------------------

def build_browser(p, cfg):
    browser = p.chromium.launch(
        headless=cfg.get("headless", True),
        slow_mo=cfg.get("slow_mo_ms", 0),
    )
    ctx_kwargs = {}
    storage = cfg.get("storage_state")
    if storage and Path(storage).exists():
        ctx_kwargs["storage_state"] = storage
    if cfg.get("user_agent"):
        ctx_kwargs["user_agent"] = cfg["user_agent"]
    context = browser.new_context(**ctx_kwargs)
    return browser, context, context.new_page()


def cmd_run(cfg, args):
    tz = cfg["schedule"].get("timezone", "Asia/Shanghai")
    auto = Automation(cfg, dry_run=args.dry_run)
    with sync_playwright() as p:
        browser, context, page = build_browser(p, cfg)
        try:
            page.goto(cfg["target_url"], wait_until="domcontentloaded")
            auto._wait_page_ready(page)
            while True:
                state, start, end = next_state(cfg["schedule"]["windows"], now_tz(tz))
                if state == "active":
                    log.info("进入触发窗口，截止 %s", end.strftime("%H:%M:%S"))
                    page.goto(cfg["target_url"], wait_until="domcontentloaded")
                    auto._wait_page_ready(page)
                    done = auto.run_window(page, end, tz)
                    if done and cfg["schedule"].get("exit_after_success", True):
                        log.info("已完成目标，退出。")
                        break
                else:
                    wait_s = max(1, min((start - now_tz(tz)).total_seconds(), 60))
                    log.info("等待下个窗口 %s（约 %.0fs 后复查）",
                             start.strftime("%m-%d %H:%M:%S"), wait_s)
                    time.sleep(wait_s)
        finally:
            if cfg.get("save_storage_state"):
                context.storage_state(path=cfg["save_storage_state"])
            browser.close()


def cmd_login(cfg, args):
    """打开浏览器手动登录，保存会话到 storage_state。"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.new_page().goto(cfg["target_url"])
        input("完成登录后按回车保存会话...")
        out = cfg.get("save_storage_state") or cfg.get("storage_state") or "auth.json"
        context.storage_state(path=out)
        print(f"已保存会话: {out}")
        browser.close()


def cmd_check(cfg):
    tz = cfg["schedule"].get("timezone", "Asia/Shanghai")
    now = now_tz(tz)
    state, start, end = next_state(cfg["schedule"]["windows"], now)
    print(f"当前时间: {now}")
    print(f"窗口状态: {state}")
    print(f"窗口区间: {start} ~ {end}")


def main():
    parser = argparse.ArgumentParser(description="定时网页触发与自动化 CLI")
    parser.add_argument("-c", "--config", required=True, help="YAML 配置文件")
    parser.add_argument("--dry-run", action="store_true", help="只检测/点击，不执行后续写操作")
    parser.add_argument("--headful", action="store_true", help="强制显示浏览器窗口")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("run", help="按计划运行（默认）")
    sub.add_parser("login", help="手动登录并保存会话")
    sub.add_parser("check", help="校验配置与时间窗口解析")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.headful:
        cfg["headless"] = False

    cmd = args.command or "run"
    if cmd == "login":
        cmd_login(cfg, args)
    elif cmd == "check":
        cmd_check(cfg)
    else:
        cmd_run(cfg, args)


if __name__ == "__main__":
    main()