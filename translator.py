"""OpenAI를 사용한 다국어 번역 로직."""

import json
import os

import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-6-astra"
API_TIMEOUT_SECONDS = 60
MAX_PARSE_ATTEMPTS = 2  # JSON 파싱 실패 시 1회 재시도

LANGUAGES = {
    "en": "English",
    "ja": "Japanese",
    "ru": "Russian",
}

TONES = {
    "default": "",
    "formal": "Use a formal, polite register.",
    "casual": "Use a casual, friendly register.",
}

SYSTEM_PROMPT = """You are a professional translator.
Detect the source language of the user's text and translate it into the requested target languages.
Preserve the original meaning, tone, line breaks, and formatting.
Do not add explanations.
Respond ONLY in JSON:
{"source_language": "<name of the source language written in Korean, e.g. 한국어>", "translations": {"<language code>": "..."}}"""


class TranslationError(Exception):
    """번역 실패. kind로 원인을 구분한다.

    kind: no_api_key | rate_limit | timeout | network | auth | model | api | parse
    """

    def __init__(self, kind: str, detail: str = ""):
        super().__init__(detail or kind)
        self.kind = kind


def get_config(key: str, default: str | None = None) -> str | None:
    """st.secrets를 먼저 확인하고, 없으면 .env / 환경 변수에서 값을 읽는다."""
    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # secrets.toml이 없거나 Streamlit 밖에서 실행된 경우
        pass
    return os.getenv(key) or default


def get_model() -> str:
    return get_config("OPENAI_MODEL", DEFAULT_MODEL)


def _request(client: OpenAI, model: str, messages: list[dict]) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=messages,
        )
    except openai.RateLimitError as e:
        raise TranslationError("rate_limit", str(e)) from e
    except openai.APITimeoutError as e:
        raise TranslationError("timeout", str(e)) from e
    except openai.APIConnectionError as e:
        raise TranslationError("network", str(e)) from e
    except openai.AuthenticationError as e:
        raise TranslationError("auth", str(e)) from e
    except openai.NotFoundError as e:
        raise TranslationError("model", str(e)) from e
    except openai.APIError as e:
        raise TranslationError("api", str(e)) from e
    return response.choices[0].message.content or ""


def translate(text: str, targets: list[str], tone: str = "default") -> dict:
    """text를 targets 언어들로 한 번의 API 호출로 번역한다.

    반환 형식: {"source_language": "...", "translations": {"en": "...", ...}}
    """
    api_key = get_config("OPENAI_API_KEY")
    if not api_key:
        raise TranslationError("no_api_key")

    system_prompt = SYSTEM_PROMPT
    if TONES.get(tone):
        system_prompt += "\n" + TONES[tone]
    target_list = ", ".join(f"{code} ({LANGUAGES[code]})" for code in targets)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Target languages: {target_list}\n\nText:\n{text}"},
    ]

    client = OpenAI(api_key=api_key, timeout=API_TIMEOUT_SECONDS, max_retries=1)
    model = get_model()
    for attempt in range(MAX_PARSE_ATTEMPTS):
        content = _request(client, model, messages)
        try:
            result = json.loads(content)
            translations = result["translations"]
            if not isinstance(translations, dict):
                raise TypeError("translations is not an object")
            break
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            if attempt == MAX_PARSE_ATTEMPTS - 1:
                raise TranslationError("parse", str(e)) from e

    return {
        "source_language": result.get("source_language", ""),
        "translations": {code: translations.get(code, "") for code in targets},
    }
