from __future__ import annotations
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://boardlife.co.kr"
LIST_URL = f"{BASE_URL}/board/used"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def matches(title: str, keyword: str) -> bool:
    """키워드가 제목에 포함되는지 확인. 공백 무시, 대소문자 무시."""
    return keyword.replace(" ", "").lower() in title.replace(" ", "").lower()


def parse_price(text: str) -> int | None:
    """텍스트에서 첫 번째 유효한 가격(원) 추출. 없으면 None."""
    for m in re.finditer(r"([\d,]+)원", text):
        price_str = m.group(1).replace(",", "")
        try:
            price = int(price_str)
            if 100 <= price <= 100_000_000:
                return price
        except ValueError:
            continue
    return None


def get_listings() -> list[dict]:
    """목록 페이지에서 게시글 {id, url} 목록 반환."""
    try:
        resp = requests.get(LIST_URL, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        seen: set[str] = set()
        listings = []

        for a in soup.find_all("a", href=True):
            m = re.search(r"bbs_detail\.php\?tb=board_used&bbs_num=(\d+)", a["href"])
            if m:
                bbs_id = m.group(1)
                if bbs_id not in seen:
                    seen.add(bbs_id)
                    href = a["href"]
                    url = BASE_URL + href if href.startswith("/") else href
                    listings.append({"id": bbs_id, "url": url})

        return listings
    except Exception:
        return []


def get_detail(bbs_id: str) -> dict:
    """상세 페이지에서 {title, price} 반환. 실패 시 {"title": "", "price": None}."""
    url = f"{BASE_URL}/bbs_detail.php?tb=board_used&bbs_num={bbs_id}"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
        price = parse_price(soup.get_text())
        return {"title": title, "price": price}
    except Exception:
        return {"title": "", "price": None}
