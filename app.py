import os
import re
import uuid

import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

from graph import MAX_REVISION, build_blog_graph

st.set_page_config(
    page_title="Blog Studio",
    page_icon="✎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

AUDIENCES = [
    "General readers",
    "Developers",
    "Founders",
    "Students",
    "Marketers",
]

EXAMPLES = [
    "What is MCP, in plain language, for developers in 2026",
    "How a small team can ship a useful AI feature in a week",
    "A beginner's guide to reading an API error without panicking",
]

STEPS = [
    ("brief", "Brief"),
    ("research", "Research"),
    ("draft", "Draft"),
    ("done", "Published"),
]


def load_api_key() -> bool:
    load_dotenv()
    if os.getenv("GROQ_API_KEY"):
        return True
    try:
        key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return False
    if not key:
        return False
    os.environ["GROQ_API_KEY"] = str(key)
    return True


def init_session():
    defaults = {
        "thread_id": None,
        "stage": "brief",
        "topic": "",
        "audience": AUDIENCES[0],
        "research": "",
        "draft": "",
        "final_blog": "",
        "revision_count": 0,
        "error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def as_dict(values):
    if isinstance(values, dict):
        return values
    if hasattr(values, "model_dump"):
        return values.model_dump()
    return {}


@st.cache_resource
def get_graph():
    return build_blog_graph()


def config_for_session():
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def apply_snapshot(graph):
    snap = graph.get_state(config_for_session())
    values = as_dict(snap.values)
    st.session_state.research = values.get("research", "") or ""
    st.session_state.draft = values.get("draft", "") or ""
    st.session_state.final_blog = values.get("final_blog", "") or ""
    st.session_state.revision_count = int(values.get("revision_count", 0) or 0)
    if snap.interrupts:
        stage_name = snap.interrupts[0].value.get("stage")
        st.session_state.stage = "research" if stage_name == "researcher_review" else "draft"
    elif not snap.next:
        st.session_state.stage = "done"
    return snap


def slug_filename(topic: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return f"{(cleaned[:48] or 'blog')}.md"


def start_blog(topic: str, audience: str):
    st.session_state.error = ""
    st.session_state.thread_id = str(uuid.uuid4())
    graph = get_graph()
    graph.invoke(
        {"topic": topic, "audience": audience},
        config_for_session(),
    )
    apply_snapshot(graph)


def resume_blog(action: str, feedback: str):
    st.session_state.error = ""
    graph = get_graph()
    graph.invoke(
        Command(resume={"action": action, "feedback": feedback}),
        config_for_session(),
    )
    apply_snapshot(graph)


def reset_blog():
    st.session_state.thread_id = None
    st.session_state.stage = "brief"
    st.session_state.research = ""
    st.session_state.draft = ""
    st.session_state.final_blog = ""
    st.session_state.revision_count = 0
    st.session_state.error = ""


def inject_styles():
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,650&family=Outfit:wght@400;500;600&display=swap');
          html, body, [class*="css"] {
            font-family: "Outfit", sans-serif;
          }
          h1, h2, h3, .hero h1 {
            font-family: "Fraunces", serif !important;
            letter-spacing: -0.03em;
          }
          .hero {
            padding: 8px 0 18px 0;
          }
          .kicker {
            margin: 0 0 8px 0;
            color: #0F6E56;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.16em;
            text-transform: uppercase;
          }
          .hero h1 {
            margin: 0;
            font-size: 3.4rem;
            line-height: 0.95;
            color: #1E1A16;
          }
          .lede {
            max-width: 38rem;
            margin: 12px 0 0 0;
            color: #5C534A;
            font-size: 1.08rem;
            line-height: 1.5;
          }
          .step-row {
            display: flex;
            gap: 8px;
            margin: 8px 0 22px 0;
            flex-wrap: wrap;
          }
          .step {
            border: 1px solid #D4CBBB;
            background: transparent;
            color: #6B6258;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 0.86rem;
          }
          .step.active {
            background: #1E1A16;
            color: #F3EEE4;
            border-color: #1E1A16;
          }
          .step.complete {
            background: #E7F3EE;
            color: #0F6E56;
            border-color: #B7D8CC;
          }
          .paper {
            background: #FFFBF4;
            border: 1px solid #E4D9C6;
            border-radius: 18px;
            padding: 8px 18px 4px 18px;
          }
          div[data-testid="stTextArea"] textarea {
            background: #FFFBF4;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_steps():
    order = [name for name, _ in STEPS]
    current = order.index(st.session_state.stage)
    chips = []
    for index, (name, label) in enumerate(STEPS):
        css = "step"
        if index < current:
            css += " complete"
        elif index == current:
            css += " active"
        chips.append(f'<span class="{css}">{index + 1}  {label}</span>')
    st.markdown(f'<div class="step-row">{"".join(chips)}</div>', unsafe_allow_html=True)


def render_header():
    st.markdown(
        """
        <div class="hero">
          <p class="kicker">Personal writing desk</p>
          <h1>Blog Studio</h1>
          <p class="lede">Three agents do the work. You decide what gets published. Research, then a draft, then a clean final post.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_brief(has_key: bool):
    st.subheader("What should this post be about?")
    for example in EXAMPLES:
        if st.button(example, key=f"ex-{example}"):
            st.session_state.topic = example
            st.session_state.error = ""
            st.rerun()

    topic = st.text_area(
        "Topic",
        key="topic",
        height=110,
        placeholder="A specific question or idea. The sharper it is, the better the post.",
    )
    audience = st.selectbox("Audience", AUDIENCES, key="audience")

    if not has_key:
        st.warning("Add GROQ_API_KEY to a local .env file, or to Streamlit secrets, before generating.")

    if st.button("Start research", type="primary", disabled=not has_key):
        if not topic.strip():
            st.session_state.error = "Write a topic first."
            st.rerun()
        with st.spinner("Research agent is building the outline..."):
            try:
                start_blog(topic.strip(), audience)
            except Exception as exc:
                st.session_state.error = str(exc)
                st.session_state.stage = "brief"
        st.rerun()


def render_review(title: str, body: str, note: str, spinner: str, allow_revise: bool):
    st.subheader(title)
    st.caption(note)
    with st.container(border=True):
        st.markdown(body or "_Nothing came back._")

    feedback = st.text_area(
        "Change notes",
        key=f"feedback-{st.session_state.stage}-{st.session_state.revision_count}",
        height=90,
        placeholder="Only needed if you want a rewrite. Example: shorter intro, one concrete example, less jargon.",
    )
    approve, revise = st.columns(2)
    if approve.button("Approve", type="primary", use_container_width=True):
        with st.spinner(spinner):
            try:
                resume_blog("approve", "")
            except Exception as exc:
                st.session_state.error = str(exc)
        st.rerun()
    if revise.button("Send back", use_container_width=True, disabled=not allow_revise):
        if not feedback.strip():
            st.session_state.error = "Write what should change, then send it back."
            st.rerun()
        with st.spinner("Applying your notes..."):
            try:
                resume_blog("revise", feedback.strip())
            except Exception as exc:
                st.session_state.error = str(exc)
        st.rerun()


def render_done():
    st.subheader("Ready to publish")
    st.caption(f"{st.session_state.topic} · {st.session_state.audience}")
    with st.container(border=True):
        st.markdown(st.session_state.final_blog or "_The editor returned an empty post._")
    st.download_button(
        "Download markdown",
        data=st.session_state.final_blog,
        file_name=slug_filename(st.session_state.topic),
        mime="text/markdown",
        type="primary",
    )
    with st.expander("Earlier steps"):
        st.markdown("**Research**")
        st.markdown(st.session_state.research or "_No research saved._")
        st.markdown("**Draft**")
        st.markdown(st.session_state.draft or "_No draft saved._")


def main():
    init_session()
    inject_styles()
    has_key = load_api_key()
    render_header()
    render_steps()

    if st.session_state.stage != "brief":
        _, top_right = st.columns([4, 1])
        with top_right:
            if st.button("New post"):
                reset_blog()
                st.rerun()

    if st.session_state.error:
        st.error(st.session_state.error)

    stage = st.session_state.stage
    if stage == "brief":
        render_brief(has_key)
    elif stage == "research":
        render_review(
            "Research outline",
            st.session_state.research,
            "Approve it to start the draft, or send notes back to the researcher.",
            "Writer is drafting the post...",
            allow_revise=True,
        )
    elif stage == "draft":
        used = st.session_state.revision_count
        render_review(
            "Draft",
            st.session_state.draft,
            f"Approve it for a final edit, or send it back. Revisions used: {used} of {MAX_REVISION}.",
            "Editor is polishing the post...",
            allow_revise=used < MAX_REVISION,
        )
    else:
        render_done()


main()
