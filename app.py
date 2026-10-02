"""다국어 번역기 Streamlit 앱."""

from datetime import datetime

import streamlit as st

from translator import TranslationError, get_model, translate

MAX_CHARS = 5000
MAX_HISTORY = 10

LANGUAGE_NAMES = {"en": "영어", "ja": "일본어", "ru": "러시아어"}
# 국기 이모지는 Windows에서 "US"처럼 글자로 보이므로 언어 코드로 표시한다
def language_label(code: str) -> str:
    return f"{LANGUAGE_NAMES[code]} · {code.upper()}"
TONE_NAMES = {"default": "기본", "formal": "격식체", "casual": "캐주얼"}

ERROR_MESSAGES = {
    "no_api_key": "❌ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일 또는 Secrets를 확인하세요.",
    "rate_limit": "⏳ 요청이 많습니다. 잠시 후 다시 시도해 주세요.",
    "timeout": "❌ 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.",
    "network": "❌ 네트워크 오류가 발생했습니다. 인터넷 연결을 확인해 주세요.",
    "auth": "❌ API 키가 올바르지 않습니다. .env 파일 또는 Secrets를 확인하세요.",
    "model": "❌ 모델을 사용할 수 없습니다. OPENAI_MODEL 설정을 확인하세요.",
}
DEFAULT_ERROR = "❌ 번역 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."


@st.cache_data(show_spinner=False)
def cached_translate(text: str, targets: tuple[str, ...], tone: str) -> dict:
    return translate(text, list(targets), tone)


def build_download_text(entry: dict) -> str:
    lines = [
        "[원문]",
        entry["text"],
        "",
        f"감지된 원문 언어: {entry['source_language']}",
        f"번역 톤: {TONE_NAMES[entry['tone']]}",
    ]
    for code, translated in entry["translations"].items():
        lines += ["", f"[{LANGUAGE_NAMES[code]}]", translated]
    return "\n".join(lines) + "\n"


st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="centered")

st.html(
    """
<style>
/* 번역 결과는 고정폭 글꼴 대신 본문 글꼴로 (일본어 전각 문장부호 간격 문제) */
[data-testid="stCode"] pre, [data-testid="stCode"] code {
    font-family: "Source Sans", "Source Sans Pro", sans-serif !important;
    font-size: 1rem !important;
}
/* 모바일에서 제목이 두 줄로 끊기지 않게 */
@media (max-width: 640px) {
    [data-testid="stHeading"] h1 { font-size: 2rem !important; }
}
</style>
"""
)

st.session_state.setdefault("history", [])
st.session_state.setdefault("current", None)

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    st.caption(f"사용 모델: `{get_model()}`")
    tone = st.radio(
        "번역 톤",
        options=list(TONE_NAMES),
        format_func=TONE_NAMES.get,
        horizontal=True,
    )
    st.divider()
    st.subheader("🕘 최근 번역 기록")
    if not st.session_state.history:
        st.caption("아직 번역 기록이 없습니다.")
    for entry in st.session_state.history:
        preview = entry["text"][:30] + ("…" if len(entry["text"]) > 30 else "")
        with st.expander(f"{entry['time']} · {preview}"):
            for code, translated in entry["translations"].items():
                st.markdown(f"**{language_label(code)}**")
                st.text(translated)

# 본문
st.title("🌐 다국어 번역기")
st.caption("입력한 글을 영어 · 일본어 · 러시아어로 번역합니다")

text = st.text_area(
    "번역할 텍스트",
    height=180,
    placeholder="번역할 글을 입력하세요. 원문 언어는 자동으로 감지됩니다.",
)
# max_chars를 쓰면 초과 입력이 경고 없이 통째로 거부되므로 직접 글자 수를 표시한다
over_limit = len(text) > MAX_CHARS
st.markdown(
    f"<div style='text-align:right;font-size:0.875rem;"
    f"{'color:#DC2626;font-weight:600' if over_limit else 'opacity:0.7'}'>"
    f"{len(text):,}/{MAX_CHARS:,}</div>",
    unsafe_allow_html=True,
)
targets = st.multiselect(
    "대상 언어",
    options=list(LANGUAGE_NAMES),
    default=list(LANGUAGE_NAMES),
    format_func=language_label,
)

if st.button("번역하기", type="primary", width="stretch"):
    if not text.strip():
        st.warning("⚠️ 번역할 텍스트를 입력해 주세요.")
    elif len(text) > MAX_CHARS:
        st.warning(f"⚠️ 최대 {MAX_CHARS:,}자까지 입력할 수 있습니다.")
    elif not targets:
        st.warning("⚠️ 번역할 언어를 하나 이상 선택해 주세요.")
    else:
        try:
            with st.spinner("번역 중입니다..."):
                result = cached_translate(text, tuple(targets), tone)
        except TranslationError as e:
            st.error(ERROR_MESSAGES.get(e.kind, DEFAULT_ERROR))
        except Exception:
            st.error(DEFAULT_ERROR)
        else:
            entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "text": text,
                "tone": tone,
                **result,
            }
            st.session_state.current = entry
            history = st.session_state.history
            # 직전과 같은 요청(텍스트·언어·톤)을 반복하면 기록을 중복 추가하지 않는다
            is_repeat = history and all(
                history[0][key] == entry[key] for key in ("text", "tone", "translations")
            )
            if not is_repeat:
                history.insert(0, entry)
                del history[MAX_HISTORY:]
            st.rerun()  # 사이드바 기록을 바로 갱신

# 결과 (다운로드 버튼 클릭 등으로 다시 실행돼도 유지)
current = st.session_state.current
st.subheader("번역 결과")
if not current:
    st.info("텍스트를 입력하고 **번역하기**를 누르면 이곳에 결과가 표시됩니다.", icon="💡")
else:
    with st.container(border=True):
        st.markdown(
            f"감지된 원문 언어: **{current['source_language']}** · "
            f"번역 톤: **{TONE_NAMES[current['tone']]}**"
        )
        codes = list(current["translations"])
        tabs = st.tabs([language_label(code) for code in codes])
        for tab, code in zip(tabs, codes):
            with tab:
                st.code(current["translations"][code], language=None, wrap_lines=True)
    st.download_button(
        "📥 결과 다운로드 (.txt)",
        data=build_download_text(current),
        file_name="translation.txt",
        mime="text/plain",
        width="stretch",
    )
