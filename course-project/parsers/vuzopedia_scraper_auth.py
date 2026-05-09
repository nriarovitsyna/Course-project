import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin, urlencode, parse_qs

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Error as PwError

START_URL = "https://vuzopedia.ru/professii/338/programmy"
HEADLESS = True

SLOWDOWN_SEC = 0.2
AFTER_GOTO_WAIT_MS = 600

NAV_TIMEOUT_MS = 60000
NAV_ATTEMPTS = 6
RETRY_SLEEP_MS = 2500

BASE_DIR = Path(__file__).resolve().parent
STATE_PATH = BASE_DIR / "state.json"
OUT_CSV = BASE_DIR / "vuzopedia_export.csv"

RETRIABLE_NET_ERRORS = (
    "ERR_NETWORK_IO_SUSPENDED",
    "ERR_CONNECTION_CLOSED",
    "ERR_CONNECTION_RESET",
    "ERR_CONNECTION_REFUSED",
    "ERR_INTERNET_DISCONNECTED",
    "ERR_NAME_NOT_RESOLVED",
    "ERR_TIMED_OUT",
)


def is_retriable_nav_error(msg: str) -> bool:
    m = msg.upper()
    if "TIMEOUT" in m:
        return True
    return any(x in m for x in RETRIABLE_NET_ERRORS)


def safe_goto(page, url: str, wait_until: str = "domcontentloaded", attempts: int = NAV_ATTEMPTS) -> bool:
    """
    True  -> страница загружена
    False -> после ретраев так и не смогли (пропускаем URL, парсер живёт дальше)
    """
    last = None
    for _ in range(attempts):
        try:
            page.goto(url, wait_until=wait_until, timeout=NAV_TIMEOUT_MS)
            return True
        except PwError as e:
            last = e
            msg = str(e)
            if is_retriable_nav_error(msg):
                page.wait_for_timeout(RETRY_SLEEP_MS)
                continue
            raise

    print("SKIP url (navigation failed):", url, "|", last)
    return False


def safe_wait_selector(page, css: str, timeout_ms: int = 15000) -> bool:
    try:
        page.wait_for_selector(css, timeout=timeout_ms)
        return True
    except PwError:
        return False


def abs_url(href: Optional[str]) -> Optional[str]:
    if not href:
        return None
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return "https://vuzopedia.ru" + href
    return None


def clean_int(x: Optional[str]) -> Optional[int]:
    if not x:
        return None
    s = re.sub(r"[^\d]", "", x)
    return int(s) if s else None


def clean_text(x: Optional[str]) -> Optional[str]:
    if not x:
        return None
    x = re.sub(r"\s+", " ", x).strip()
    return x or None


def uniq_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def set_query_param(url: str, **params) -> str:
    p = urlparse(url)
    q = parse_qs(p.query)
    for k, v in params.items():
        q[k] = [str(v)]
    new_query = urlencode({k: v[0] for k, v in q.items()})
    return p._replace(query=new_query).geturl()


def pick_latest_year_value(
    kv: Dict[str, str],
    key_regex: str,
    value_transform=lambda s: s,
) -> Optional[Tuple[int, object]]:
    best_year = None
    best_val = None

    rx = re.compile(key_regex, re.IGNORECASE)
    for k, v in kv.items():
        m = rx.search(k)
        if not m:
            continue
        year = int(m.group(1))
        val = value_transform(v)
        if best_year is None or year > best_year:
            best_year = year
            best_val = val

    if best_year is None:
        return None
    return best_year, best_val


def parse_catalog_page(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("div.newBlockSpecProg")
    out = []

    for c in cards:
        a_name = c.select_one("a.spectittle[href]")
        program_name = clean_text(a_name.get_text(" ", strip=True)) if a_name else None
        program_url = abs_url(a_name.get("href")) if a_name else None

        info = c.select_one("div.osnBlockInfoSm")
        program_code = clean_text(info.get_text(" ", strip=True)) if info else None

        a_varianty = c.select_one("a.linknapWoutActive[href*='/varianty']")
        program_varianty_url = abs_url(a_varianty.get("href")) if a_varianty else None

        if program_varianty_url:
            out.append(
                {
                    "program_name": program_name,
                    "program_code": program_code,
                    "program_url": program_url,
                    "program_varianty_url": program_varianty_url,
                }
            )

    return out


def parse_catalog_pagination_urls(html: str, current_url: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    ul = soup.select_one("ul.pagination")
    if not ul:
        return []

    urls = []
    for a in ul.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        urls.append(urljoin(current_url, href))
    return uniq_keep_order(urls)


def get_next_catalog_page_url(html: str, current_url: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    ul = soup.select_one("ul.pagination")
    if not ul:
        return None

    active_li = ul.select_one("li.active")
    if not active_li:
        return None

    nxt = active_li.find_next_sibling("li")
    if not nxt:
        return None

    a = nxt.select_one("a[href]")
    if not a:
        return None

    return urljoin(current_url, a.get("href"))


def collect_all_catalog_page_urls(page, start_url: str) -> List[str]:
    """
    Ходим по страницам каталога:
    - начинаем с page=1
    - на каждой странице собираем видимые ссылки пагинации
    - переходим на следующую после active
    """
    urls: List[str] = []
    url = set_query_param(start_url, page=1)
    seen = set()

    while url and url not in seen:
        seen.add(url)

        if not safe_goto(page, url):
            break

        if not safe_wait_selector(page, "div.newBlockSpecProg", timeout_ms=15000):
            print("WARN: no catalog cards on", url)
            break

        page.wait_for_timeout(AFTER_GOTO_WAIT_MS)
        html = page.content()

        urls.append(url)
        urls.extend(parse_catalog_pagination_urls(html, url))
        url = get_next_catalog_page_url(html, url)

        time.sleep(SLOWDOWN_SEC)

    return uniq_keep_order(urls)


def parse_program_varianty_page(html: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a[href*='/vuz/'][href*='/programs/'][href*='/varianty/']"):
        u = abs_url(a.get("href"))
        if u:
            links.append(u)
    return uniq_keep_order(links)


def get_next_varianty_page_url(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")

    a = soup.select_one("ul.pagination a.page-link[rel='next'][href]")
    if a:
        return abs_url(a.get("href"))

    for a in soup.select("ul.pagination a.page-link[href]"):
        t = a.get_text(" ", strip=True)
        if "→" in t or t.strip() in (">", "»"):
            return abs_url(a.get("href"))

    return None


def collect_all_variant_links(page, first_varianty_url: str) -> List[str]:
    all_links: List[str] = []
    url = first_varianty_url
    seen = set()

    while url and url not in seen:
        seen.add(url)

        if not safe_goto(page, url):
            break

        page.wait_for_timeout(AFTER_GOTO_WAIT_MS)
        html = page.content()

        all_links.extend(parse_program_varianty_page(html))
        url = get_next_varianty_page_url(html)

        time.sleep(SLOWDOWN_SEC)

    return uniq_keep_order(all_links)


def parse_city_from_variant_page(soup: BeautifulSoup) -> Optional[str]:
    el = soup.select_one("div.choosecity#newChoose span")
    if el:
        t = clean_text(el.get_text(" ", strip=True))
        if t:
            return t

    el = soup.select_one(".underheaderq .choosecity span#newChooseq")
    if el:
        t = clean_text(el.get_text(" ", strip=True))
        if t:
            return t

    a = soup.select_one("a[href^='regioncity']")
    if a:
        t = clean_text(a.get_text(" ", strip=True))
        if t:
            return t

    return None


def parse_numbers_from_optparent(soup: BeautifulSoup):
    nums = [clean_int(x.get_text(" ", strip=True)) for x in soup.select("div.optParent p.optTitle")]
    nums = [n for n in nums if n is not None]

    budget_passing = budget_places = paid_places = tuition = None
    if len(nums) >= 4:
        budget_passing, budget_places, paid_places, tuition = nums[:4]
    return budget_passing, budget_places, paid_places, tuition


def parse_variant_title(soup: BeautifulSoup) -> Optional[str]:
    h1 = soup.select_one("h1.mainTitle")
    return clean_text(h1.get_text(" ", strip=True)) if h1 else None


def parse_tab_table(soup: BeautifulSoup, tab_id: str) -> Dict[str, str]:
    tab = soup.select_one(f"div.tab-pane#{tab_id}")
    if not tab:
        return {}

    kv: Dict[str, str] = {}
    for row in tab.select("div.specqqwe, div.specnoqqwe"):
        k_el = row.select_one("div.col-lg-4 font")
        if not k_el:
            continue
        key = clean_text(k_el.get_text(" ", strip=True))
        if not key:
            continue

        v_el = row.select_one("div.col-lg-8")
        if not v_el:
            continue

        val = clean_text(v_el.get_text(" ", strip=True))
        if val is not None:
            kv[key] = val

    return kv


def parse_paid_min_from_filial(kv_filial: Dict[str, str]) -> Optional[int]:
    for k, v in kv_filial.items():
        kl = k.lower()
        if "минимальный балл" in kl and "плат" in kl:
            m = re.search(r"(\d+)", v)
            return int(m.group(1)) if m else None
    return None


def parse_vuz_variant_detail(html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    variant_title = parse_variant_title(soup)
    city = parse_city_from_variant_page(soup)

    budget_passing_opt, budget_places_opt, paid_places_opt, tuition_opt = parse_numbers_from_optparent(soup)

    kv_fak = parse_tab_table(soup, "fak")
    kv_filial = parse_tab_table(soup, "filial")

    university_name = kv_fak.get("Вуз") or kv_filial.get("Вуз")
    faculty = kv_fak.get("Факультет") or kv_filial.get("Факультет")
    level = kv_fak.get("Квалификация") or kv_filial.get("Квалификация")
    study_format = kv_fak.get("Форма обучения") or kv_filial.get("Форма обучения")
    language = kv_fak.get("Язык обучения") or kv_filial.get("Язык обучения")
    duration = kv_fak.get("Срок обучения") or kv_filial.get("Срок обучения")
    accreditation = kv_fak.get("По учредителю") or kv_filial.get("По учредителю")

    budget_pick = pick_latest_year_value(
        kv_fak,
        r"Бюджетных мест в\s*(\d{4})",
        value_transform=lambda s: clean_int(s),
    )
    budget_places = budget_pick[1] if budget_pick else budget_places_opt

    budget_passing_score = None
    for k, v in kv_fak.items():
        if "проходной балл" in k.lower() and "бюдж" in k.lower():
            budget_passing_score = clean_int(v)
            break
    if budget_passing_score is None:
        budget_passing_score = budget_passing_opt

    paid_min_score = parse_paid_min_from_filial(kv_filial)

    paid_pick = pick_latest_year_value(
        kv_filial,
        r"Платных мест в\s*(\d{4})",
        value_transform=lambda s: clean_int(s),
    )
    paid_places = paid_pick[1] if paid_pick else paid_places_opt

    tuition_pick = pick_latest_year_value(
        kv_filial,
        r"Стоимость обучения в\s*(\d{4})",
        value_transform=lambda s: clean_int(s),
    )
    tuition = tuition_pick[1] if tuition_pick else tuition_opt

    if paid_min_score is None:
        text = soup.get_text("\n", strip=True)
        m = re.search(r"Минимальный балл на платное[^\n]{0,200}(\d+)", text, re.IGNORECASE)
        paid_min_score = int(m.group(1)) if m else None

    return {
        "variant_title": variant_title,
        "university_name": university_name,
        "city": city,
        "faculty": faculty,
        "level": level,
        "duration": duration,
        "study_format": study_format,
        "language": language,
        "accreditation": accreditation,
        "budget_places": budget_places,
        "paid_places": paid_places,
        "tuition_cost_rub_year": tuition,
        "budget_passing_score": budget_passing_score,
        "paid_min_score": paid_min_score,
    }

def main():
    if not STATE_PATH.exists():
        raise FileNotFoundError(
            f"Не найден {STATE_PATH}. Сначала сохрани авторизацию (cookies/localStorage) в state.json."
        )

    rows: List[Dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        ctx = browser.new_context(storage_state=str(STATE_PATH))
        page = ctx.new_page()

        catalog_pages = collect_all_catalog_page_urls(page, START_URL)

        for catalog_url in catalog_pages:
            if not safe_goto(page, catalog_url):
                continue

            if not safe_wait_selector(page, "div.newBlockSpecProg", timeout_ms=15000):
                print("WARN: no catalog cards on", catalog_url)
                continue

            page.wait_for_timeout(AFTER_GOTO_WAIT_MS)
            programs = parse_catalog_page(page.content())

            for pr in programs:
                pv_url = pr.get("program_varianty_url")
                if not pv_url:
                    continue

                vuz_variant_links = collect_all_variant_links(page, pv_url)

                for vlink in vuz_variant_links:
                    if not safe_goto(page, vlink):
                        continue

                    page.wait_for_timeout(AFTER_GOTO_WAIT_MS)
                    det = parse_vuz_variant_detail(page.content())

                    rows.append(
                        {
                            "id": None,
                            "program_code": pr.get("program_code"),
                            "name": pr.get("program_name"),
                            "faculty": det["faculty"],
                            "level": det["level"],
                            "university_name": det["university_name"],
                            "city": det["city"],
                            "budget_places": det["budget_places"],
                            "paid_places": det["paid_places"],
                            "tuition_cost_rub_year": det["tuition_cost_rub_year"],
                            "budget_passing_score": det["budget_passing_score"],
                            "paid_min_score": det["paid_min_score"],
                            "duration": det["duration"],
                            "study_format": det["study_format"],
                            "language": det["language"],
                            "accreditation": det["accreditation"],
                        }
                    )

                    time.sleep(SLOWDOWN_SEC)

        for i, row in enumerate(rows, start=1):
            row["id"] = i

        pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()