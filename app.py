import os
import urllib.parse

import requests
import streamlit as st

st.set_page_config(
    page_title="BRACE — Bible retrieval-augmented (Catholic edition)",
    page_icon='https://brace.cdcl.ml/favicon.svg',
    initial_sidebar_state='collapsed',
    menu_items={'Get help': 'mailto:brace@cdcl.ml',
                'Report a bug': 'https://github.com/casperdcl/brace/issues/new',
                'About': "See [casperdcl/brace](https://github.com/casperdcl/brace)"})
st.title("📖 BRACE: Bible retrieval-augmented (Catholic edition)")
with st.sidebar:
    st.title("Advanced options")
    max_chapters = st.slider("Maximum number of relevant chapters for *basic chapter selection*", 1, 50, 10, 1)
    chapter_filter = st.text_input("Chapter selection (override)", help="regex, e.g. ^(Genesis [12]|Exodus 2)$")
    if not chapter_filter and st.checkbox("Use AI-based *chapter selection*"):
        chapter_filter = 'LLM'

if 'queries_processed' not in st.session_state:
    st.session_state['queries_processed'] = set()
query_url = st.query_params.get('q', "")
query_usr = st.text_area("Enter your question (try to use complete sentences):", value=query_url)
query = query_usr.strip()
submit = st.button("Submit")
if query and (
    # submit.onclick: query from text_area
    submit
    # document.onload: query from URL
    or not st.session_state.get('query_url_processed', not query_url)
    # textarea.onchange && query already processed (rely on backend cache): query from text_area
    or query in st.session_state['queries_processed']
):
    st.session_state['query_url_processed'] = True
    st.session_state['queries_processed'].add(query)
    with st.spinner("Searching for answers in the Bible..."):
        pbar = st.progress(0)
        eta = st.caption("*estimated time remaining: >5 minutes (lots of users!)*")
        res = requests.get(
            os.getenv('BRACE_BACKEND_URL', 'http://localhost:8090/api'), stream=True,
            params={'q': query, 'chapter_filter': chapter_filter, 'max_chapters': max_chapters})
        for chunk in res.iter_content(None, True):
            if "*basic chapter selection*\n" in chunk:
                pbar.progress(5)
                stream_node = None
            elif "*refined selection*\n" in chunk or "*selection override*\n" in chunk:
                eta.caption("*estimated time remaining: <1 minute*")
                pbar.progress(30)
                stream_node = None
            elif "*paraphrased question*\n" in chunk:
                pbar.progress(40)
                stream_node = None

            if "*estimated time remaining: " in chunk:
                eta.caption(chunk)
                stream_node = None
            elif "## Answer\n" in chunk:
                pbar.progress(95)
                stream_node = st.markdown(chunk)
                stream_text = chunk
            elif "## Related questions\n" in chunk:
                pbar.progress(99)
                stream_node = st.markdown(chunk)
                stream_text = chunk
            elif "*total time: " in chunk:
                st.caption(f"⏱️ {chunk}")
                stream_node = None
            elif "## About\n" in chunk:
                pbar.progress(100)
                st.caption(chunk)
                stream_node = None
            elif stream_node is not None:
                stream_text += chunk
                stream_node.markdown(stream_text)
            else:
                heading, body = chunk.partition('\n')[::2]
                with st.expander(heading, expanded=False):
                    st.markdown(body)
        eta.caption(f"Like what you see? [Link to this question](https://brace.cdcl.ml/?q={urllib.parse.quote(query)}).")
else:
    st.caption("## Example questions")
    st.caption("\n".join(f"- [{q}](https://brace.cdcl.ml/?q={urllib.parse.quote(q)})" for q in (
        "Define marriage and its purpose.",
        "What is the difference between faith and works, and can we be saved by faith alone?",
        "Are sacred tradition and sacred scripture equally important, or is scripture more important?",
        "How should criminals and evil-doers be treated, and should we punish them?",
        "Explain the Holy Trinity, and how can one God exist in three persons?",
        "Is money evil?"
    )))
