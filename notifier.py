from __future__ import annotations
import requests


def send_alert(
    token: str,
    chat_id: str,
    title: str,
    price: int | None,
    keyword: str,
    max_price: int | None,
    url: str,
) -> bool:
    """매물 알림 메시지 전송. 성공 시 True."""
    price_str = f"{price:,}원" if price is not None else "가격 정보 없음"
    condition = (
        f"{keyword} (최대 {max_price:,}원)" if max_price else f"{keyword} (가격 무관)"
    )
    text = (
        f"🔔 새 매물 알림!\n\n"
        f"📌 제목: {title}\n"
        f"💰 가격: {price_str}\n"
        f"🔍 조건: {condition}\n"
        f"🔗 링크: {url}"
    )
    return _send(token, chat_id, text)


def send_message(token: str, chat_id: str, text: str) -> bool:
    """일반 텍스트 메시지 전송. 성공 시 True."""
    return _send(token, chat_id, text)


def _send(token: str, chat_id: str, text: str) -> bool:
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException:
        return False
