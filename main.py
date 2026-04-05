import os
import time

from gist_store import GistStore
from scraper import get_listings, get_detail, matches
from notifier import send_alert, send_message
from bot_handler import get_updates, process_updates


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    gist_token = os.environ["GIST_TOKEN"]
    gist_id = os.environ["GIST_ID"]

    store = GistStore(gist_token, gist_id)
    keywords_data, state = store.read()

    # 1. 텔레그램 명령어 처리
    last_update_id = state.get("last_update_id", 0)
    updates = get_updates(token, offset=last_update_id + 1)

    if updates:
        keywords_data, changed, responses = process_updates(updates, keywords_data)
        state["last_update_id"] = updates[-1]["update_id"]

        if changed:
            store.write_keywords(keywords_data)

        for resp_chat_id, message in responses:
            send_message(token, resp_chat_id, message)

    store.write_state(state)

    # 2. 크롤링 (알림 조건 없으면 스킵)
    alerts = keywords_data.get("alerts", [])
    if not alerts:
        return  # seen_ids unchanged at this point, no need to re-save

    listings = get_listings()
    seen_ids_list: list[str] = state.get("seen_ids", [])
    seen_ids_set: set[str] = set(seen_ids_list)
    new_listings = [listing for listing in listings if listing["id"] not in seen_ids_set]

    if not new_listings:
        return  # seen_ids unchanged at this point, no need to re-save

    # 3. 새 게시글 조건 대조 및 알림 발송
    for listing in new_listings:
        detail = get_detail(listing["id"])
        title = detail["title"]
        price = detail["price"]

        for alert in alerts:
            keyword = alert["keyword"]
            max_price = alert.get("max_price")

            if not matches(title, keyword):
                continue
            if max_price is not None and (price is None or price > max_price):
                continue

            send_alert(
                token=token,
                chat_id=chat_id,
                title=title or listing["url"],
                price=price,
                keyword=keyword,
                max_price=max_price,
                url=listing["url"],
            )

        time.sleep(0.5)

    # 4. seen_ids 업데이트 (최근 500개 유지)
    all_ids = seen_ids_list + [listing["id"] for listing in new_listings]
    state["seen_ids"] = all_ids[-500:]
    store.write_state(state)


if __name__ == "__main__":
    main()
