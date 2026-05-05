import os
import urllib.parse
from textwrap import dedent

import requests
import streamlit as st

CNAME = 'brace.cdcl.ml'
BRACE_BACKEND_URL = os.getenv('BRACE_BACKEND_URL', 'http://localhost:8090')
st.set_page_config(
    page_title="BRACE — Bible retrieval-augmented (Catholic edition)",
    page_icon='https://img.cdcl.ml/brace.svg',
    initial_sidebar_state='collapsed',
    menu_items={'Get help': 'mailto:brace@cdcl.ml',
                'Report a bug': 'https://github.com/casperdcl/brace/issues/new',
                'About': "See [casperdcl/brace](https://github.com/casperdcl/brace)"})
st.title("📖 BRACE: Bible retrieval-augmented (Catholic edition)")
with st.sidebar:
    st.title("Advanced options")
    max_chapters_url = st.query_params.get('n', "10")
    max_chapters = st.slider("Maximum number of relevant chapters for *basic chapter selection*", 1, 50, int(max_chapters_url), 1)
    chapter_filter_url = st.query_params.get('ch', "")
    chapter_filter_usr = st.text_input("Chapter selection (override)", value=chapter_filter_url, help="regex, e.g. ^(Genesis [12]|Exodus 2)$")
    chapter_filter = chapter_filter_usr.strip()
    if not chapter_filter and st.checkbox("Use AI-based *chapter selection*"):
        chapter_filter = 'LLM'
    ccc_url = bool(st.query_params.get('ccc', ""))
    ccc = st.checkbox(f"Include *Catechism ([CCC](https://www.vatican.va/archive/ccc/index.htm?utm_source={CNAME}))*", ccc_url)

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
    if submit:
        st.markdown(f"""<script>plausible('pageview', {{u: 'https://{CNAME}/{query}'}})</script>""", unsafe_allow_html=True)
    st.session_state['query_url_processed'] = True
    st.session_state['queries_processed'].add(query)
    with st.spinner("Searching for answers in the Bible..."):
        pbar = st.progress(0)
        eta = st.caption("*estimated time remaining: >5 minutes (lots of users!)*")
        share = st.empty()
        res = requests.get(f'{BRACE_BACKEND_URL}/api', stream=True, params={'q': query, 'chapter_filter': chapter_filter, 'max_chapters': max_chapters, 'ccc': ccc})
        total_chapters = 0
        stream_node = None
        for chunk in res.iter_content(None, True):
            if "*basic chapter selection*\n" in chunk:
                pbar.progress(5)
                stream_node = None
            elif "*refined selection*\n" in chunk or "*selection override*\n" in chunk:
                eta.caption("*estimated time remaining: <1 minute*")
                pbar.progress(30)
                total_chapters = chunk.count("\n- [")
                stream_node = None
            elif "*paraphrased question*\n" in chunk:
                pbar.progress(40)
                stream_node = None

            if "*estimated time remaining: " in chunk:
                eta.caption(chunk)
                stream_node = None
            elif "## Answer\n" in chunk or "## Related questions\n" in chunk:
                stream_node = st.markdown(chunk)
                stream_body = chunk
                link = f"https://{CNAME}/?q={urllib.parse.quote_plus(query)}"
                if max_chapters != 10:
                    link += f"&n={max_chapters}"
                if chapter_filter:
                    link += f"&ch={urllib.parse.quote_plus(chapter_filter)}"
                if ccc:
                    link += f"&ccc=1"
                share.caption(f"Like what you see? [Link to this question]({link}).")
            elif "*total time: " in chunk:
                pbar.progress(100)
                st.caption(f"⏱️ {chunk}")
                stream_node = None
            elif stream_node is None:
                heading, body = chunk.partition('\n')[::2]
                with st.expander(heading, expanded=False):
                    st.markdown(body)
            else:
                stream_body += chunk
                seen_chapters = stream_body.count("\n**")
                pbar.progress(.4 + .5 * (seen_chapters / max((total_chapters, seen_chapters, 1))))
                stream_node.markdown(stream_body)
        eta.empty()
else:
    st.caption("## Example questions")
    st.caption("\n".join(f"- [{q}](https://{CNAME}/?q={urllib.parse.quote_plus(q)})" for q in (
        "Define marriage and its purpose.",
        "What is the difference between faith and works, and can we be saved by faith alone?",
        "Are sacred tradition and sacred scripture equally important, or is scripture more important?",
        "How should criminals and evil-doers be treated, and should we punish them?",
        "Explain the Holy Trinity, and how can one God exist in three persons?",
        "Is money evil?"
    )))
    st.caption(dedent("""\
    ## Coming soon/under development

    Things which non-AI websearch is better at, e.g.:

    - Meta(data) questions (How many books are in the Catholic Bible, and when were they written?)
    - Citation lookup (What does Matthew 5:30 say?)
    - Reverse citation lookup (Where does it say  <insert quote>?)
    - What is the difference between Catholic and <insert denomination> beliefs?
    """))

st.caption(f"""
----

### About

By default, this AI tool provides insights & answers solely based on the Biblical text. The tool itself can be viewed as a bespoke commentary generator.

### Tips

:ledger: Some questions might be answerable by selecting the *Include Catechism ([CCC](https://www.vatican.va/archive/ccc/index.htm?utm_source={CNAME}))* checkbox in the sidebar.
This might work on topics which the Bible doesn't cover, e.g.:

- What is the Church (tradition rather than scripture) stance on <insert topic>?
- Is <insert modern invention> sinful?

Whilst the CCC and numerous Bible commentaries aim to aid understanding, they are not as meticulously worded as the Bible itself, and are thus significantly easier for AI to misinterpret.
The Bible is the most studied and translated book in existence. Despite this, it is oft misinterpreted and misunderstood.

:black_nib: To improve answers, try rewording and adding more details to your query. For example, instead of *"tradition vs scripture"*, ask *"Are sacred tradition and sacred scripture equally important, or is scripture more important?"*

:bug: Found a bug or have a feature request? [Open an issue](https://github.com/casperdcl/brace/issues) or email `brace@cdcl.ml`.

### Privacy, security & licensing

- I tweak & host the permissively-licensed AI model(s) behind this site (in my own time, on my own hardware, at my expense)
  + No personal info (queries, answers, IP addresses, etc.) are sent to any third-party, no cookie banner is needed
  + Answers are generated based on the Bible so should be in the public domain
  + If you want, you can support my work [here](https://cdcl.ml/sponsor)
- :warning: The underlying AI can misinterpret text (*machina imperfecta sub divina* rather than *deus ex machina*), so please verify all Bible references/citations
  + An AI Bible *study* tool is not an authoritative Bible *substitute*

### Further reading

- [Bible (RSVCE)](https://www.biblegateway.com/passage/?search=Genesis%201&version=RSVCE&utm_source={CNAME})
- [Corrective Retrieval-Augmented Generation](https://arxiv.org/pdf/2401.15884.pdf?utm_source={CNAME})
- [To Christians Developing LLM Applications: A Warning, and Some Suggestions](https://aiandfaith.org/to-christians-developing-llm-applications-a-warning-and-some-suggestions?utm_source={CNAME})

### Other tools

- [OpenBible Labs AI-Assisted Bible Study](https://www.openbible.info/labs/ai-bible-study?utm_source={CNAME}) — chapter summary & question generator
- [Viz.Bible](https://viz.bible?utm_source={CNAME}) — data visualisations, infographics, and illustrated diagrams
- [Biblos](https://github.com/dssjon/biblos) — similar to [BRACE](https://{CNAME}) but using [instructor-large](https://huggingface.co/hkunlp/instructor-large) & [Claude Sonnet](https://www.anthropic.com/claude/sonnet) 3.5 for plain RAG on [ESV](https://www.biblegateway.com/passage/?search=Genesis%201&version=ESV&utm_source={CNAME}) & [commentaries](https://github.com/HistoricalChristianFaith/Commentaries-Database)
- [ChristGPT](https://github.com/ortegaalfredo/ChristGPT) — LLaMA-13B [Alpaca-LoRA](https://github.com/tloen/alpaca-lora) fine-tuned on [KJV](https://www.biblegateway.com/passage/?search=Genesis%201&version=KJV&utm_source={CNAME})
""")

st.image(requests.get(f'{BRACE_BACKEND_URL}/status').text)
