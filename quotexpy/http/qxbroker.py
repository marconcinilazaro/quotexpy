import re
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Tuple, Any
from playwright.async_api import Playwright, async_playwright

from quotexpy.utils.playwright_install import install
from quotexpy.exceptions import QuotexAuthError


async def run(email, password, playwright: Playwright) -> Tuple[Any, str]:
    browser = await playwright.firefox.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://qxbroker.com/pt/sign-in")
    await page.get_by_role("textbox", name="E-mail").click()
    await page.get_by_role("textbox", name="E-mail").fill(email)
    await page.get_by_role("textbox", name="Senha").click()
    await page.get_by_role("textbox", name="Senha").fill(password)
    await page.get_by_role("button", name="Entrar").click()
    await page.wait_for_load_state()
    creds_error = await page.query_selector(".hint -danger")
    if creds_error is not None:
        raise QuotexAuthError("email or password invalid")
    await page.wait_for_url("https://qxbroker.com/pt/trade")
    cookies = await context.cookies()
    source = await page.content()
    soup = BeautifulSoup(source, "html.parser")
    user_agent = await page.evaluate("() => navigator.userAgent;")
    script = soup.find_all("script", {"type": "text/javascript"})[1].get_text()
    match = re.sub("window.settings = ", "", script.strip().replace(";", ""))
    ssid = json.loads(match).get("token")
    output_file = Path(".session.json")
    output_file.parent.mkdir(exist_ok=True, parents=True)
    cookiejar = requests.utils.cookiejar_from_dict({c["name"]: c["value"] for c in cookies})
    cookie_string = "; ".join([f"{c.name}={c.value}" for c in cookiejar])
    output_file.write_text(
        json.dumps(
            {"cookies": cookie_string, "ssid": ssid, "user_agent": user_agent},
            indent=4,
        )
    )
    await context.close()
    await browser.close()

    return ssid, cookie_string


async def main(email, password) -> Tuple[Any, str]:
    async with async_playwright() as playwright:
        install(playwright.firefox, with_deps=True)
        return await run(email, password, playwright)


async def authorize(email, password):
    return await main(email, password)
