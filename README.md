# TutorMe AI 🎓

An AI-powered tutoring platform providing personalized, 24/7 educational support using large language models and adaptive learning algorithms to support students with independent study.

**Live demo:** [tutorme-ai.streamlit.app](https://tutorme-ai.streamlit.app)

---

## Overview

TutorMe AI is a Streamlit web app built on Google's Gemini API. It acts as "Shruti," a friendly AI tutor who can explain concepts, give real-life examples, generate and grade interactive quizzes, answer open questions, and hold a follow-up conversation with memory.

## Features

- **Explain Concept** — a beginner-friendly explanation of any topic, with an analogy and a check-in question
- **Real-Life Example** — a concrete, step-by-step real-world example of the topic
- **Generate Quiz** — a 5-question multiple-choice quiz, generated on the fly, auto-graded in the app, with an explanation for every answer
- **Ask Anything** — open-ended Q&A with the Shruti persona
- **Chat with Shruti** — a multi-turn conversation that remembers earlier messages in the session

## Tech Stack

| Component | Choice |
|---|---|
| UI / app framework | [Streamlit](https://streamlit.io) |
| LLM | Google Gemini (`gemini-2.5-flash`) via the [`google-genai`](https://pypi.org/project/google-genai/) SDK |
| Hosting | Streamlit Community Cloud |
| Language | Python 3 |

## Getting Started

### Prerequisites

- Python 3.10+
- A free [Gemini API key](https://aistudio.google.com/apikey) from Google AI Studio

### Installation

```bash
git clone https://github.com/ishrutiagarwal/tutorme-ai.git
cd tutorme-ai
pip install -r requirements.txt
```

### Configuration

Create a `.streamlit/secrets.toml` file in the project root:

```toml
GEMINI_API_KEY = "your-api-key-here"
```

> Never commit this file or your API key to version control.

### Run locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Deployment

This app is deployed on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push the repo to GitHub.
2. Create a new app on Streamlit Cloud pointing to `app.py` on the `main` branch.
3. Add `GEMINI_API_KEY` under the app's **Secrets** settings (same format as `secrets.toml` above).
4. Deploy. Any future push to `main` triggers a redeploy.

## Project Structure

```
tutorme-ai/
├── app.py              # Main Streamlit app
├── requirements.txt    # Python dependencies
└── README.md
```

## Known Limitations

- Single shared API key — heavy concurrent use may hit Gemini's free-tier rate limits.
- No persistent storage yet — chat history and quiz results reset when the session ends.
- Gemini may occasionally produce incorrect information; answers in **Explain Concept**, **Ask Anything**, and **Chat with Shruti** are not fact-checked against a source document.

## Roadmap

- [ ] RAG support — upload your own notes/PDF so answers are grounded in your material, with citations
- [ ] Answer evaluator — submit a written answer and get rubric-based feedback
- [ ] Adaptive difficulty and per-topic mastery tracking
- [ ] Spaced-repetition flashcards
- [ ] Progress dashboard
- [ ] Persistent storage (database-backed) for progress across sessions

## Acknowledgements

Built using the [Gemini API](https://ai.google.dev/) and [Streamlit](https://streamlit.io).

## License

Add a license of your choice (e.g., MIT) here.
