"""실행: python -m streamlit run web/stream_lit2.py"""

import json
import os
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

MODEL = "gpt-6-luna"
MAX_CHARS = 4000

PERSONAS = {
    "친절한 도우미": (
        "당신은 친절한 AI 어시스턴트입니다. "
        "쉽고 명확한 한국어로 답하세요. "
        "확인되지 않은 사실을 지어내지 말고 불확실한 부분을 밝혀 주세요."
    ),
    "꼼꼼한 전문가": (
        "당신은 꼼꼼한 업무 도우미입니다. "
        "핵심을 먼저 설명하고 필요한 근거와 절차를 정리하세요. "
        "정보가 부족하면 필요한 내용을 질문하세요. "
        "실제로 확인하지 않은 출처나 규정을 만들지 마세요."
    ),
    "친근한 친구": (
        "당신은 친근한 대화 상대입니다. "
        "편안한 반말로 대화하되 과장하거나 사실을 지어내지 마세요."
    ),
}

SUGGESTIONS = [
    (
        "💡 개념 이해",
        "어려운 개념을 쉽게 풀어보기",
        "LLM, RAG, MCP의 차이를 초보자도 이해하도록 예시와 함께 설명해 줘.",
    ),
    (
        "✍️ 글 다듬기",
        "업무 문장을 자연스럽게",
        "업무 이메일을 다듬고 싶어. 먼저 필요한 내용을 질문해 줘.",
    ),
    (
        "🧭 아이디어 정리",
        "생각을 실행 계획으로",
        "나만의 챗봇을 만들고 싶어. 주제를 정할 수 있도록 질문을 하나씩 해 줘.",
    ),
]

st.set_page_config(
    page_title="Chat Studio",
    page_icon="✦",
    layout="centered",
)

dark_mode = st.session_state.get("dark_mode", False)
theme = {
    "app_bg": "#11131a" if dark_mode else "#f7f8fc",
    "sidebar_bg": "#191c25" if dark_mode else "#eef0f8",
    "surface": "#202430" if dark_mode else "#ffffff",
    "surface_hover": "#2a2f3d" if dark_mode else "#f4f1ff",
    "text": "#f1f3f8" if dark_mode else "#172033",
    "muted": "#b4bdcd" if dark_mode else "#58657b",
    "border": "#3a4050" if dark_mode else "#d6dbea",
    "accent": "#b2a5ff" if dark_mode else "#6754d9",
    "color_scheme": "dark" if dark_mode else "light",
}

st.markdown(
    f"""
    <style>
    :root {{
        --app-bg: {theme['app_bg']};
        --sidebar-bg: {theme['sidebar_bg']};
        --surface: {theme['surface']};
        --surface-hover: {theme['surface_hover']};
        --app-text: {theme['text']};
        --muted-text: {theme['muted']};
        --app-border: {theme['border']};
        --app-accent: {theme['accent']};
        color-scheme: {theme['color_scheme']};
    }}

    .stApp {{
        --text-color: var(--app-text);
        --background-color: var(--app-bg);
        --secondary-background-color: var(--sidebar-bg);
        --primary-color: var(--app-accent);
        background: var(--app-bg) !important;
        color: var(--app-text) !important;
        color-scheme: {theme['color_scheme']};
    }}
    [data-testid="stAppViewContainer"],
    section.main {{
        background: var(--app-bg) !important;
    }}
    .block-container {{
        max-width: 880px;
        padding-top: 2.8rem;
        padding-bottom: 2rem;
    }}
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div {{
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--app-border);
    }}
    .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2,
    .stApp h3, .stApp h4, .stApp span, .stApp [data-testid="stMarkdownContainer"] {{
        color: var(--app-text) !important;
    }}
    [data-testid="stSidebar"] * {{
        color: var(--app-text) !important;
    }}
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stCaptionContainer"] p,
    .stApp small {{
        color: var(--muted-text) !important;
    }}
    [data-testid="stHeader"] {{
        background: transparent;
    }}
    [data-testid="stChatMessage"] {{
        background: var(--surface) !important;
        color: var(--app-text) !important;
        border: 1px solid var(--app-border);
        border-radius: 18px;
        margin-bottom: 14px;
        padding: 18px;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {{
        color: var(--app-text) !important;
        line-height: 1.8;
    }}
    [data-testid="stBottom"] > div {{
        background: var(--app-bg) !important;
    }}
    [data-testid="stChatInput"] textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background: var(--surface) !important;
        color: var(--app-text) !important;
        border-color: var(--app-border) !important;
    }}
    .stApp input::placeholder,
    .stApp textarea::placeholder {{
        color: var(--muted-text) !important;
        opacity: 1;
    }}
    [data-testid="stExpander"] {{
        background: var(--surface) !important;
        border-color: var(--app-border) !important;
    }}
    .stButton > button,
    .stDownloadButton > button {{
        background: var(--surface) !important;
        color: var(--app-text) !important;
        border-radius: 11px;
        border: 1px solid var(--app-border);
        transition: border-color .15s, background .15s;
    }}
    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        border-color: var(--app-accent) !important;
        color: var(--app-accent) !important;
        background: var(--surface-hover) !important;
    }}
    .brand {{
        color: var(--app-accent) !important;
        font-size: .8rem;
        font-weight: 700;
        letter-spacing: .18em;
        margin-bottom: 12px;
    }}
    .hero {{
        color: var(--app-text) !important;
        font-size: clamp(1.8rem, 5vw, 2.5rem);
        font-weight: 750;
        letter-spacing: -.06em;
        line-height: 1.25;
        margin-bottom: 12px;
    }}
    .subtitle {{
        color: var(--muted-text) !important;
        font-size: 1rem;
        line-height: 1.7;
        margin-bottom: 28px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# 세션별 대화 상태
DEFAULTS = {
    "messages": [],
    "pending_question": None,
    "last_error": None,
    "input_tokens": 0,
    "output_tokens": 0,
    "usage_calls": 0,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, list) else value


def clear_chat():
    """대화만 초기화하고 사이드바 설정은 유지."""
    for key, value in DEFAULTS.items():
        st.session_state[key] = value.copy() if isinstance(value, list) else value


def export_chat():
    lines = ["Chat Studio 대화 기록", ""]
    for message in st.session_state.messages:
        name = "나" if message["role"] == "user" else "AI"
        lines.extend([f"[{name}]", message["content"], ""])
    return "\n".join(lines)


def extract_text(content):
    """문자열 또는 텍스트 블록 목록을 출력용 문자열로 변환."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        )

    return ""


with st.sidebar:
    st.markdown("## ✦ Chat Studio")
    st.caption("생각을 정리하는 나만의 대화 공간")
    st.toggle("다크 모드", key="dark_mode")
    st.divider()

    if st.button("＋ 새로운 대화", use_container_width=True):
        clear_chat()
        st.rerun()

    st.markdown("#### 대화 설정")
    persona = st.selectbox(
        "대화 스타일",
        list(PERSONAS),
        key="persona",
    )

    with st.expander("답변 세부 설정"):
        temperature = st.slider(
            "표현의 다양성",
            0.0,
            2.0,
            0.8,
            0.1,
            key="temperature_v2",
            help="0에 가까우면 답변이 더 일관되고, 높을수록 표현이 다양해질 수 있습니다. GPT-6 Luna의 temperature 범위는 0~2입니다.",
        )
        st.caption(f"현재 temperature: {temperature:.1f}")
        st.caption(f"사용 모델: {MODEL}")

    st.caption("설정 변경은 다음 답변부터 적용됩니다.")
    st.divider()

    st.markdown("#### 이번 대화")
    st.metric("완료한 질문", len(st.session_state.messages) // 2)

    if st.session_state.usage_calls:
        total = (
            st.session_state.input_tokens
            + st.session_state.output_tokens
        )
        st.caption(
            f"보고된 사용량: {total:,} 토큰\n\n"
            f"입력 {st.session_state.input_tokens:,} · "
            f"출력 {st.session_state.output_tokens:,}"
        )
        st.caption(
            "사용량 정보가 반환된 호출만 집계합니다. "
            "실패한 호출에도 비용이 발생할 수 있습니다."
        )

    if st.session_state.messages:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        st.download_button(
            "↓ 대화 내려받기",
            data=export_chat(),
            file_name=f"chat_{stamp}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        with st.expander("개발용 데이터"):
            st.download_button(
                "JSON 다운로드",
                data=json.dumps(
                    st.session_state.messages,
                    ensure_ascii=False,
                    indent=2,
                ),
                file_name=f"chat_{stamp}.json",
                mime="application/json",
                use_container_width=True,
            )

    st.divider()
    st.caption(
        "대화는 현재 브라우저 세션에 보관됩니다. "
        "필요한 내용은 파일로 내려받으세요."
    )

st.markdown('<div class="brand">CHAT STUDIO</div>', unsafe_allow_html=True)

has_key = bool(os.getenv("OPENAI_API_KEY", "").strip())

if not has_key:
    st.warning(
        "API 키가 설정되지 않았습니다. "
        ".env에 OPENAI_API_KEY를 설정한 뒤 앱을 다시 실행해 주세요."
    )

selected_question = None
has_pending = st.session_state.pending_question is not None

if not st.session_state.messages and not has_pending:
    st.markdown(
        '<div class="hero">오늘은 무엇을 함께 해볼까요?</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">'
        '궁금한 개념부터 업무 문장, 새로운 아이디어까지.<br>'
        '질문을 입력하거나 아래 주제로 시작해 보세요.'
        '</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(3)

    for column, (title, description, question) in zip(columns, SUGGESTIONS):
        with column:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.caption(description)

                if st.button(
                    "시작하기 →",
                    key=title,
                    use_container_width=True,
                    disabled=not has_key,
                ):
                    selected_question = question
else:
    st.markdown("### 함께 나누는 이야기")
    st.caption(f"{persona} · 앞선 대화를 참고해 답변합니다.")

# 저장된 대화 표시
for message in st.session_state.messages:
    avatar = "🧑" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 실패한 요청은 대화 기록과 별도로 보관
if has_pending:
    with st.chat_message("user", avatar="🧑"):
        st.markdown(st.session_state.pending_question)

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

        retry_column, cancel_column = st.columns(2)

        with retry_column:
            if st.button(
                "다시 시도",
                use_container_width=True,
                disabled=not has_key,
            ):
                st.session_state.last_error = None
                st.rerun()

        with cancel_column:
            if st.button("질문 취소", use_container_width=True):
                st.session_state.pending_question = None
                st.session_state.last_error = None
                st.rerun()

typed_question = st.chat_input(
    "메시지를 입력하세요…",
    max_chars=MAX_CHARS,
    disabled=not has_key or has_pending,
)

question = typed_question or selected_question

if question and question.strip():
    st.session_state.pending_question = question.strip()
    st.session_state.last_error = None
    st.rerun()

# pending_question이 있고 오류가 없으면 한 번 실행
if (
    st.session_state.pending_question
    and not st.session_state.last_error
    and has_key
):
    question = st.session_state.pending_question

    messages = [SystemMessage(content=PERSONAS[persona])]

    for message in st.session_state.messages:
        message_type = (
            HumanMessage if message["role"] == "user" else AIMessage
        )
        messages.append(message_type(content=message["content"]))

    messages.append(HumanMessage(content=question))

    try:
        llm = ChatOpenAI(
            model=MODEL,
            reasoning_effort="none",
            temperature=temperature,
            stream_usage=True,
            timeout=60,
            max_retries=1,
        )

        result = {"text": "", "usage": None}

        def generate():
            combined = None

            for chunk in llm.stream(messages):
                combined = chunk if combined is None else combined + chunk

                text = extract_text(chunk.content)
                if text:
                    result["text"] += text
                    yield text

            if combined is not None:
                result["usage"] = combined.usage_metadata

        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("답변을 준비하고 있어요…"):
                st.write_stream(generate())

        answer = result["text"].strip()

        if not answer:
            raise ValueError("Empty response")

    except Exception as error:
        st.session_state.last_error = (
        f"{type(error).__name__}: {error}"
    )
        st.rerun()

    # 답변 완료 후에만 대화에 반영
    st.session_state.messages.extend([
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ])

    usage = result["usage"]
    if usage:
        st.session_state.input_tokens += usage.get("input_tokens", 0) or 0
        st.session_state.output_tokens += usage.get("output_tokens", 0) or 0
        st.session_state.usage_calls += 1

    st.session_state.pending_question = None
    st.session_state.last_error = None
    st.rerun()
