from __future__ import annotations
import requests


def get_updates(token: str, offset: int) -> list[dict]:
    """오프셋 이후의 새 텔레그램 메시지 조회."""
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"offset": offset, "timeout": 0, "limit": 100},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("result", [])
    except Exception:
        return []


def parse_command(text: str) -> dict | None:
    """봇 명령어 파싱. 유효하지 않으면 None 반환."""
    if not text:
        return None
    parts = text.strip().split()
    cmd = parts[0].lstrip("/").lower()

    if cmd == "list":
        return {"cmd": "list"}

    if cmd == "add":
        if len(parts) < 2:
            return None
        # Try to parse last part as price; if so, keyword is everything between
        max_price = None
        if len(parts) >= 3:
            try:
                max_price = int(parts[-1].replace(",", ""))
                keyword = " ".join(parts[1:-1])
            except ValueError:
                keyword = " ".join(parts[1:])
        else:
            keyword = parts[1]
        return {"cmd": "add", "keyword": keyword, "max_price": max_price}

    if cmd == "remove":
        if len(parts) < 2:
            return None
        return {"cmd": "remove", "keyword": parts[1]}

    return None


def process_updates(
    updates: list[dict], keywords_data: dict
) -> tuple[dict, bool, list[tuple[str, str]]]:
    """텔레그램 업데이트 처리.

    Returns:
        (updated_keywords_data, changed, [(chat_id, response_message), ...])
    """
    responses: list[tuple[str, str]] = []
    changed = False

    for update in updates:
        msg = update.get("message", {})
        text = msg.get("text", "")
        chat_id = str(msg.get("chat", {}).get("id", ""))
        if not text or not chat_id:
            continue

        parsed = parse_command(text)
        if not parsed:
            continue

        cmd = parsed["cmd"]
        alerts: list[dict] = list(keywords_data.get("alerts", []))

        if cmd == "list":
            if not alerts:
                responses.append((
                    chat_id,
                    "📋 현재 설정된 알림이 없습니다.\n\n"
                    "/add 키워드 가격 으로 추가하세요.\n"
                    "예: /add 아이패드 300000",
                ))
            else:
                lines = ["📋 현재 알림 목록:"]
                for i, alert in enumerate(alerts, 1):
                    kw = alert["keyword"]
                    mp = alert.get("max_price")
                    price_str = f"최대 {mp:,}원" if mp else "가격 무관"
                    lines.append(f"{i}. {kw} — {price_str}")
                responses.append((chat_id, "\n".join(lines)))

        elif cmd == "add":
            keyword = parsed["keyword"]
            max_price = parsed["max_price"]
            alerts = [a for a in alerts if a["keyword"] != keyword]
            new_alert: dict = {"keyword": keyword}
            if max_price is not None:
                new_alert["max_price"] = max_price
            alerts.append(new_alert)
            keywords_data = {**keywords_data, "alerts": alerts}
            changed = True
            price_str = f"최대 {max_price:,}원" if max_price else "가격 무관"
            responses.append((chat_id, f"✅ 추가됨: {keyword} ({price_str})"))

        elif cmd == "remove":
            keyword = parsed["keyword"]
            new_alerts = [a for a in alerts if a["keyword"] != keyword]
            if len(new_alerts) < len(alerts):
                keywords_data = {**keywords_data, "alerts": new_alerts}
                changed = True
                responses.append((chat_id, f"🗑️ 삭제됨: {keyword}"))
            else:
                responses.append((chat_id, f"❌ '{keyword}'을 찾을 수 없습니다."))

    return keywords_data, changed, responses
