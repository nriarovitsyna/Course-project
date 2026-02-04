from playwright.sync_api import sync_playwright

STATE_PATH = "state.json"
LOGIN_URL = "https://vuzopedia.ru/"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        print("1) Войди в аккаунт в открывшемся окне")
        print("2) Открой любую страницу vuzopedia, где ты точно залогинен")
        input("3) Нажми Enter тут, чтобы сохранить state.json... ")

        ctx.storage_state(path=STATE_PATH)
        print(f"Saved: {STATE_PATH}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
