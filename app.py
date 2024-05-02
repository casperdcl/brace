import os
import random
from textwrap import dedent

import requests
import streamlit as st

st.title("BRACES: Bible retrieval-augmented (Catholic edition) study")
with st.expander("Advanced options"):
    k = st.slider("Maximum number of relevant chapters for *basic chapter selection*", 1, 50, 10, 1)
    if chapter_filter := st.text_input("Chapter selection (override)", help="regex, e.g. ^(Genesis [12]|Exodus 2)$"):
        pass
    elif st.checkbox("Use AI-based *chapter selection* (slow, ~5min)"):
        chapter_filter = 'LLM'
    else:
        chapter_filter = ''

if user_question := st.text_area(
    "Enter your query:",
    help=dedent("""\
    e.g.:
    Define marriage and the relationship between husband (man) and wife (woman).
    How to handle criminals and evil-doers?
    Explain the Holy Trinity.""")
):
    with st.spinner(random.choice((
        "Reticulating splines",
        "Searching for answers",
        "Thinking",
        "Just a moment",
        "Processing",
        "Hold tight",
        "Searching for answers",
        "One moment please",
        "Generating a response",
        "Please wait",
        "Working on it",
        "Give me a second",
        "Almost there",
        "On it",
        "Working hard",
    )) + "..."):
        res = requests.get(
            os.getenv('BRACE_BACKEND_URL', 'http://localhost:8090/api'), stream=True,
            params={'q': user_question, 'chapter_filter': chapter_filter, 'max_chapters': k})
        for chunk in res.iter_content(None, True):
            st.markdown(chunk)
