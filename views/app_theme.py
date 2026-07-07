import streamlit as st


TEMA_INTERNO_PREMIUM_CSS = """
<style>
    :root {
        --fp-bg: #f5f7fb;
        --fp-surface: #ffffff;
        --fp-surface-soft: #f8fafc;
        --fp-ink: #0f172a;
        --fp-muted: #64748b;
        --fp-border: #dbe4ef;
        --fp-accent: #059669;
        --fp-accent-strong: #047857;
        --fp-navy: #0b1f33;
        --fp-gold: #b8892f;
        --fp-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        --fp-radius: 10px;
    }

    .stApp {
        background:
            radial-gradient(circle at 18% 0%, rgba(5, 150, 105, 0.08), transparent 30%),
            linear-gradient(180deg, #ffffff 0%, var(--fp-bg) 42%, #eef3f8 100%);
        color: var(--fp-ink);
    }

    [data-testid="stAppViewContainer"] > .main .block-container {
        max-width: 1180px;
        padding-top: 3.2rem;
        padding-bottom: 4rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #071827 0%, #10243a 55%, #0b1f33 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    [data-testid="stSidebar"] * {
        color: rgba(255, 255, 255, 0.9);
    }

    [data-testid="stSidebar"] section {
        padding-top: 1.35rem;
    }

    .fp-sidebar-brand {
        padding: 0.4rem 0.1rem 1.25rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.12);
        margin-bottom: 1.05rem;
    }

    .fp-brand-row {
        display: flex;
        align-items: center;
        gap: 0.72rem;
        margin-bottom: 0.8rem;
    }

    .fp-brand-mark {
        width: 2.45rem;
        height: 2.45rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 0.85rem;
        background: linear-gradient(145deg, #00a86b 0%, #087f5b 100%);
        box-shadow: 0 14px 28px rgba(5, 150, 105, 0.28);
        font-weight: 900;
        color: #ffffff;
    }

    .fp-brand-name {
        font-size: 1.02rem;
        line-height: 1.1;
        font-weight: 800;
        letter-spacing: 0;
    }

    .fp-brand-subtitle {
        color: rgba(255, 255, 255, 0.62);
        font-size: 0.78rem;
        line-height: 1.35;
        margin-top: 0.15rem;
    }

    .fp-user-card {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 0.85rem;
        padding: 0.85rem;
    }

    .fp-user-label {
        color: rgba(255, 255, 255, 0.58);
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.25rem;
    }

    .fp-user-email {
        color: #ffffff;
        font-size: 0.82rem;
        font-weight: 700;
        word-break: break-word;
        line-height: 1.35;
    }

    .fp-plan-pill {
        display: inline-flex;
        align-items: center;
        margin-top: 0.72rem;
        padding: 0.32rem 0.58rem;
        border-radius: 999px;
        background: rgba(184, 137, 47, 0.18);
        border: 1px solid rgba(184, 137, 47, 0.34);
        color: #f7d083;
        font-size: 0.74rem;
        font-weight: 800;
    }

    [data-testid="stSidebar"] [role="radiogroup"] {
        display: grid;
        gap: 0.28rem;
    }

    [data-testid="stSidebar"] label[data-baseweb="radio"] {
        min-height: 2.3rem;
        padding: 0.24rem 0.48rem;
        border-radius: 0.72rem;
        transition: background 160ms ease, transform 160ms ease;
    }

    [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateX(2px);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .stCaptionContainer {
        color: rgba(255, 255, 255, 0.68);
    }

    h1, h2, h3 {
        color: var(--fp-ink);
        letter-spacing: 0;
    }

    h1 {
        font-size: 2.45rem;
        font-weight: 850;
        line-height: 1.05;
        margin-bottom: 0.35rem;
    }

    h2 {
        font-weight: 820;
    }

    h3 {
        font-weight: 760;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid var(--fp-border);
        border-radius: var(--fp-radius);
        padding: 1rem 1.05rem;
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
    }

    div[data-testid="stMetric"] label {
        color: var(--fp-muted);
        font-weight: 750;
    }

    div[data-testid="stMetricValue"] {
        color: var(--fp-ink);
        font-weight: 850;
    }

    .stButton > button,
    .stLinkButton > a,
    [data-testid="stFormSubmitButton"] button {
        border-radius: 0.72rem;
        border: 1px solid #c8d5e3;
        min-height: 2.75rem;
        font-weight: 800;
        box-shadow: none;
        transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
    }

    .stButton > button:hover,
    .stLinkButton > a:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px);
        border-color: var(--fp-accent);
        box-shadow: 0 12px 24px rgba(5, 150, 105, 0.14);
    }

    .stButton > button[kind="primary"],
    [data-testid="stFormSubmitButton"] button[kind="primary"] {
        background: linear-gradient(135deg, var(--fp-accent) 0%, var(--fp-accent-strong) 100%);
        border-color: var(--fp-accent-strong);
    }

    .stAlert {
        border-radius: var(--fp-radius);
        border: 1px solid rgba(15, 23, 42, 0.08);
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stTable"] {
        border-radius: var(--fp-radius);
        overflow: hidden;
        border: 1px solid var(--fp-border);
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
    }

    hr {
        border-color: rgba(100, 116, 139, 0.18);
        margin: 1.6rem 0;
    }

    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stDateInput input {
        border-radius: 0.72rem;
        border-color: #cbd7e6;
        background: #ffffff;
    }

    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stDateInput input:focus {
        border-color: var(--fp-accent);
        box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.12);
    }

    @media (max-width: 900px) {
        [data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 2rem;
        }

        h1 {
            font-size: 2rem;
        }
    }
</style>
"""


def aplicar_tema_interno():
    st.markdown(TEMA_INTERNO_PREMIUM_CSS, unsafe_allow_html=True)
