import os

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
    elif st.checkbox("Use AI-based *chapter selection*"):
        chapter_filter = 'LLM'
    else:
        chapter_filter = ''

query = st.text_area(
    "Enter your query (try to use complete sentences):", help="""e.g:
    Define marriage and the relationship between husband (man) and wife (woman).
    What is the difference between faith and works, and can we be saved by faith alone?
    Are sacred tradition and sacred scripture equally important, or is scripture more important?
    How should criminals and evil-doers be treated and should we punish them?
    Explain the Holy Trinity, and how can one God exist in three persons?""")
submit = st.button("Submit")
if query and submit:
    with st.spinner("Searching for answers in the Bible..."):
        pbar = st.progress(0)
        res = requests.get(
            os.getenv('BRACE_BACKEND_URL', 'http://localhost:8090/api'), stream=True,
            params={'q': query, 'chapter_filter': chapter_filter, 'max_chapters': k})
        for chunk in res.iter_content(None, True):
            if "*basic chapter selection*" in chunk:
                pbar.progress(5)
            if "*refined selection*" in chunk:
                pbar.progress(30)
            if "*paraphrased query*" in chunk:
                pbar.progress(40)
            if "## Answer" in chunk or "https://cdcl.ml" in chunk:
                pbar.progress(100)
                st.markdown(chunk)
            else:
                with st.expander(chunk.split('\n', 1)[0], expanded=False):
                    st.markdown(chunk.split('\n', 1)[1])
