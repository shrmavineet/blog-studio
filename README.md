# Blog Studio

A small writing desk for blog posts. A research agent outlines the topic, a writer drafts it, and an editor polishes the final piece. You approve the research and the draft before anything moves forward.

## Run it on your computer

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Put your Groq key in `.env`:

```
GROQ_API_KEY=your_groq_key_here
```

Get a free key from [console.groq.com](https://console.groq.com).

## Put it online so anyone can open it

1. Push this folder to a GitHub repository. Do not commit `.env` or `blog_agent.ipynb`.
2. Open [share.streamlit.io](https://share.streamlit.io) and create an app from that repo.
3. Set the main file to `app.py` and Python to 3.11.
4. In the app settings, add this secret:

```toml
GROQ_API_KEY = "your_groq_key_here"
```

Streamlit Cloud gives you a public link. Anyone with the link can generate a post. The key stays in secrets, not in the repository.
