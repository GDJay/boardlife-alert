import json
import requests


class GistStore:
    def __init__(self, token: str, gist_id: str):
        self._api_url = f"https://api.github.com/gists/{gist_id}"
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def read(self) -> tuple[dict, dict]:
        resp = requests.get(self._api_url, headers=self._headers, timeout=10)
        resp.raise_for_status()
        files = resp.json()["files"]
        try:
            keywords = json.loads(files["keywords.json"]["content"])
            state = json.loads(files["state.json"]["content"])
        except KeyError:
            raise RuntimeError(
                "Gist is missing keywords.json or state.json. "
                "Check setup-guide.md to create the Gist correctly."
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Gist file contains invalid JSON: {e}") from e
        return keywords, state

    def write_keywords(self, keywords: dict) -> None:
        self._patch("keywords.json", keywords)

    def write_state(self, state: dict) -> None:
        self._patch("state.json", state)

    def _patch(self, filename: str, data: dict) -> None:
        payload = {
            "files": {
                filename: {
                    "content": json.dumps(data, ensure_ascii=False, indent=2)
                }
            }
        }
        resp = requests.patch(
            self._api_url, headers=self._headers, json=payload, timeout=10
        )
        resp.raise_for_status()
