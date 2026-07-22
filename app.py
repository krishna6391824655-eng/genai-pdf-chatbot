import time
import streamlit as st
from src.utils import save_uploaded_file
from src.pdf_loader import load_pdf
from src.text_splitter import split_documents
from src.vector_store import create_vector_store
from src.embedding import create_embeddings
from src.retriever import search_pdf
from src.llm import generate_answer

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="PDF Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Custom CSS (pure styling, no logic changes)
# -----------------------------
st.markdown("""
<style>

    /* ---- General App Background ---- */
    .stApp {
        background: linear-gradient(180deg, #0f1117 0%, #14161f 100%);
    }

    /* ---- Hide default Streamlit chrome (scoped, won't affect widgets) ---- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stHeader"] {visibility: hidden; height: 0;}

    /* ---- Hero header ---- */
    .hero-container {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        padding: 2.2rem 2rem;
        border-radius: 18px;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: white;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: rgba(255,255,255,0.85);
        margin-top: 0.4rem;
        font-weight: 400;
    }
    .hero-badge {
        background: rgba(255,255,255,0.18);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
        backdrop-filter: blur(6px);
        white-space: nowrap;
    }

    /* ---- Status strip ---- */
    .status-strip {
        display: flex;
        gap: 0.7rem;
        margin-bottom: 1.4rem;
        flex-wrap: wrap;
    }
    .status-chip {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 0.5rem 0.9rem;
        font-size: 0.82rem;
        color: #c9c9d1;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-green { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
    .dot-gray { background: #6b7280; }

    /* ---- Sidebar styling ---- */
    section[data-testid="stSidebar"] {
        background: #12141c;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] h2 {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f1f1f4;
    }

    /* ---- File uploader box ---- */
    div[data-testid="stFileUploader"] {
        border: 1.5px dashed rgba(139, 92, 246, 0.45);
        border-radius: 12px;
        padding: 0.6rem;
        background: rgba(139, 92, 246, 0.05);
    }

    /* ---- Success / info cards ---- */
    .pdf-info-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin-top: 0.8rem;
    }
    .pdf-info-card p {
        margin: 0.15rem 0;
        font-size: 0.88rem;
        color: #d4d4d8;
    }
    .pdf-info-card b {
        color: #a78bfa;
    }

    /* ---- Chat bubbles ---- */
    div[data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 0.4rem 0.2rem;
        margin-bottom: 0.4rem;
    }

    /* ---- Chat input box ---- */
    div[data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
    }

    /* ---- Buttons ---- */
    div[data-testid="stButton"] button {
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.12);
        font-weight: 600;
        transition: all 0.2s ease;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #a78bfa;
        color: #a78bfa;
    }

    /* ---- Metric styling ---- */
    div[data-testid="stMetric"] {
        background: rgba(139, 92, 246, 0.08);
        border-radius: 10px;
        padding: 0.5rem;
    }

    /* ---- Empty state ---- */
    .empty-state {
        text-align: center;
        padding: 3.5rem 1rem;
        color: #8b8b95;
    }
    .empty-state h3 {
        color: #d4d4d8;
        margin-bottom: 0.4rem;
    }

    /* ---- Footer caption ---- */
    .app-footer {
        text-align: center;
        color: #5f5f6b;
        font-size: 0.78rem;
        margin-top: 2rem;
    }

</style>
""", unsafe_allow_html=True)

# -----------------------------
# Session State
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "documents" not in st.session_state:
    st.session_state.documents = None

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0

if "upload_time" not in st.session_state:
    st.session_state.upload_time = None

# -----------------------------
# Hero Header
# -----------------------------
status_label = "Document Ready" if st.session_state.documents is not None else "No Document Loaded"

st.markdown(f"""
<div class="hero-container">
    <div>
        <p class="hero-title">🤖 PDF Assistant</p>
        <p class="hero-subtitle">Upload a PDF and ask questions about its content — powered by retrieval-augmented generation.</p>
    </div>
    <div class="hero-badge">⚡ {status_label}</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Status strip
# -----------------------------
doc_dot = "dot-green" if st.session_state.documents is not None else "dot-gray"
doc_text = st.session_state.pdf_name if st.session_state.pdf_name else "No file uploaded"

st.markdown(f"""
<div class="status-strip">
    <div class="status-chip"><span class="status-dot {doc_dot}"></span> {doc_text}</div>
    <div class="status-chip"><span class="status-dot {doc_dot}"></span> {st.session_state.chunk_count} chunks indexed</div>
    <div class="status-chip"><span class="status-dot dot-green"></span> {len(st.session_state.messages)} messages in session</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:

    st.header("📄 Document")

    uploaded_file = st.file_uploader(
        "Choose a PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        file_path = save_uploaded_file(uploaded_file)

        with st.spinner("Processing document..."):
            documents = load_pdf(file_path)
            chunks = split_documents(documents)
            embeddings = create_embeddings(chunks)
            index = create_vector_store(chunks, embeddings)

        st.session_state.documents = documents
        st.session_state.pdf_name = uploaded_file.name
        st.session_state.chunk_count = len(chunks)
        st.session_state.upload_time = time.strftime("%H:%M:%S")

        st.success("Document processed successfully")

        st.markdown(f"""
        <div class="pdf-info-card">
            <p><b>File:</b> {uploaded_file.name}</p>
            <p><b>Pages:</b> {len(documents)}</p>
            <p><b>Processed at:</b> {st.session_state.upload_time}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        col1.metric("Pages", len(documents))
        col2.metric("Chunks", len(chunks))

    st.divider()

    st.subheader("Session")

    if st.session_state.pdf_name:
        st.caption(f"Active document: **{st.session_state.pdf_name}**")
    else:
        st.caption("No document is currently loaded.")

    st.caption(f"Messages exchanged: **{len(st.session_state.messages)}**")

    if st.button("🗑 Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("♻ Reset Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.documents = None
        st.session_state.pdf_name = None
        st.session_state.chunk_count = 0
        st.session_state.upload_time = None
        st.rerun()

    st.divider()
    st.caption("PDF Assistant · RAG-powered · v1.0")

# -----------------------------
# Empty state (no chat yet)
# -----------------------------
if not st.session_state.messages:
    if st.session_state.documents is None:
        st.markdown("""
        <div class="empty-state">
            <h3>👋 Welcome to PDF Assistant</h3>
            <p>Upload a PDF from the sidebar to get started.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <h3>💬 Ready when you are</h3>
            <p>Type a question below about your document.</p>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------
# Show Chat History
# -----------------------------
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# Chat Input
# -----------------------------
prompt = st.chat_input("Ask something about your PDF...")

if prompt:

    # User Message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Assistant
    with st.chat_message("assistant", avatar="🤖"):

        with st.spinner("Searching document..."):

            if st.session_state.documents is None:

                response = "⚠️ Please upload a PDF first."

            else:

                context = search_pdf(prompt)

                response = generate_answer(prompt, context)

            st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )

st.markdown('<p class="app-footer">Built with Streamlit · Retrieval-Augmented Generation</p>', unsafe_allow_html=True)