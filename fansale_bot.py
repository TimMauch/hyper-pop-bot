import asyncio
import logging
import os
from playwright.async_api import async_playwright
from telegram import Bot

# === CONFIG FROM ENVIRONMENT ===
FANSALE_URL = os.environ["FANSALE_URL"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

# === TELEGRAM BOT ===
bot = Bot(token=BOT_TOKEN)

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

async def check_tickets(playwright):
    browser = await playwright.chromium.launch(
        headless=HEADLESS,
        args=["--disable-http2", "--disable-features=NetworkService"]
    )
    context = await browser.new_context()
    page = await context.new_page()

    try:
        logging.info("Loading FanSALE page...")
        await page.goto(FANSALE_URL, timeout=30000)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(2000)

        # Accept cookie banner if present
        try:
            await page.wait_for_selector("button:has-text('Accept')", timeout=5000)
            accept_button = await page.query_selector("button:has-text('Accept')")
            if accept_button:
                await accept_button.click()
                logging.info("Cookie banner accepted.")
                await page.wait_for_timeout(1000)
        except Exception as e:
            logging.warning(f"Cookie banner could not be removed: {e}")

        # Check if ticket container exists
        container = await page.query_selector(".js-EventEntryList")
        if container:
            logging.info("🎫 Tickets available!")
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"🎫 Tickets available on FanSALE!\n{FANSALE_URL}"
            )
        else:
            logging.info("No tickets currently available.")

    except Exception as e:
        logging.error(f"Error loading or processing page: {e}")
    finally:
        await browser.close()

async def main_loop():
    async with async_playwright() as playwright:
        while True:
            await check_tickets(playwright)
            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main_loop())
