import os
from textwrap import dedent

import requests
import streamlit as st

st.set_page_config(
    page_title="BRACES — Bible retrieval-augmented (Catholic edition) study",
    page_icon='📖',
    initial_sidebar_state='collapsed',
    menu_items={'Get help': 'mailto:braces@cdcl.ml',
                'Report a bug': 'https://github.com/casperdcl/braces/issues/new',
                'About': "See [casperdcl/braces](https://github.com/casperdcl/braces)"})
st.title("📖 BRACES: Bible retrieval-augmented (Catholic edition) study")
with st.sidebar:
    st.title("Advanced options")
    k = st.slider("Maximum number of relevant chapters for *basic chapter selection*", 1, 50, 10, 1)
    if chapter_filter := st.text_input("Chapter selection (override)", help="regex, e.g. ^(Genesis [12]|Exodus 2)$"):
        pass
    elif st.checkbox("Use AI-based *chapter selection* (slow, ~5min)"):
        chapter_filter = 'LLM'
    else:
        chapter_filter = ''

if user_question := st.text_area(
    "Enter your query (try to use complete sentences):",
    help=dedent("""\
    e.g.:
    Define marriage and the relationship between husband (man) and wife (woman).
    What is the difference between faith and works, and can we be saved by faith alone?
    How should criminals and evil-doers be handled?
    Explain the Holy Trinity.""")
):
    with st.spinner("Searching for answers in the Bible..."):
        pbar = st.progress(0)
        res = requests.get(
            os.getenv('BRACE_BACKEND_URL', 'http://localhost:8090/api'), stream=True,
            params={'q': user_question, 'chapter_filter': chapter_filter, 'max_chapters': k})
        for chunk in res.iter_content(None, True):
            if "*basic chapter selection*" in chunk:
                pbar.progress(5)
            if "*refined selection*" in chunk:
                pbar.progress(30)
            if "*paraphrased query*" in chunk:
                pbar.progress(40)
            if "## Answer" in chunk:
                pbar.progress(100)
            st.markdown(chunk)
