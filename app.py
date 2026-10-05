"""
TutorMe AI — Streamlit tutoring app powered by Gemini.

Fixes applied in this version:
1. safe_generate() wraps every Gemini call with error handling + one retry.
2. Generate Quiz returns structured JSON, is rendered as an interactive form,
   is auto-graded, and shows per-question feedback.
3. Chat with Shruti keeps conversation memory across turns using
   model.start_chat() + st.session_state.
4. Explain Concept, Real-Life Example, and Ask Anything all route through
   safe_generate() and consistently use the Shruti persona.
5. Prompt formatting/spacing issues corrected.
"""

import json

import streamlit as st
from google import genai

# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------

st.set_page_config(page_title="TutorMe AI", page_icon="🎓")

MODEL_NAME = "gemini-2.5-flash"

try:
    # Store the client in session_state so the SAME client instance is reused
    # across Streamlit reruns. Recreating it every rerun causes the old
    # client's connection to close, breaking any chat session built on it
    # ("Cannot send a request, as the client has been closed.").
    if "genai_client" not in st.session_state:
        st.session_state.genai_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    client = st.session_state.genai_client
except Exception as e:
    st.error(
        "Could not configure the AI model. Check that GEMINI_API_KEY is set "
        f"in your Streamlit secrets. Details: {e}"
    )
    st.stop()

PERSONA = (
    "You are TutorMe, a warm, friendly, encouraging and patient AI tutor who explains things simply, "
    "uses relatable analogies, and checks in with the students to keep them engaged."
)

# ----------------------------------------------------------------------
# Core helper: wraps every Gemini call with error handling
# ----------------------------------------------------------------------


def safe_generate(prompt, as_json=False, retries=1):
    """
    Calls Gemini with the given prompt.
    - Retries once on a bad/malformed response.
    - Returns None (and shows a friendly st.error) if it still fails.
    - If as_json=True, strips markdown code fences and parses the JSON.
    """
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            text = (response.text or "").strip()

            if not text:
                raise ValueError("Empty response from the model.")

            if as_json:
                cleaned = text.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned)

            return text

        except json.JSONDecodeError:
            if attempt == retries:
                st.error("The AI returned an unexpected format. Please try again.")
                return None
        except Exception as e:
            if attempt == retries:
                st.error(f"Something went wrong talking to the AI: {e}")
                return None
    return None


# ----------------------------------------------------------------------
# Activity: Explain Concept
# ----------------------------------------------------------------------


def explain_concept(topic):
    prompt = f"""{PERSONA}

Explain the topic "{topic}" to a beginner in about 150-200 words.
Requirements: Use exactly one simple analogy, keep the language clear and
jargon-free, and end with one short check-in question to make sure the
student followed along."""
    return safe_generate(prompt)


# ----------------------------------------------------------------------
# Activity: Real-Life Example
# ----------------------------------------------------------------------


def real_life_example(topic):
    prompt = f"""{PERSONA}

Give ONE clear, everyday real-life example that illustrates the topic
"{topic}". Walk through the example step by step so a beginner can connect
it back to the underlying concept."""
    return safe_generate(prompt)


# ----------------------------------------------------------------------
# Activity: Generate Quiz (interactive + scored)
# ----------------------------------------------------------------------


def generate_quiz(topic):
    prompt = f"""{PERSONA}

Create a 5-question multiple-choice quiz on the topic "{topic}" for a
high-school level learner. Requirements: Order the questions from easy to
hard, give exactly 4 options (A-D) per question, and provide a short
explanation for why the correct answer is correct. If the student gives wrong answer, 
give him the correct answer explaining why the given answer is wrong and the correct 
answer is correct.

Return ONLY valid JSON, with no extra commentary and no markdown fences,
in exactly this format:
{{
  "questions": [
    {{
      "question": "string",
      "options": {{"A": "string", "B": "string", "C": "string", "D": "string"}},
      "correct_answer": "A",
      "explanation": "string"
    }}
  ]
}}"""
    return safe_generate(prompt, as_json=True)


def render_quiz(topic):
    # (Re)generate the quiz only when the topic changes or none exists yet
    if "quiz_data" not in st.session_state or st.session_state.get("quiz_topic") != topic:
        with st.spinner("Generating your quiz..."):
            data = generate_quiz(topic)
        if not data or "questions" not in data:
            st.warning("Couldn't generate a quiz right now. Please try again.")
            return

        st.session_state.quiz_data = data["questions"]
        st.session_state.quiz_topic = topic
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False

    questions = st.session_state.quiz_data

    with st.form("quiz_form"):
        for i, q in enumerate(questions):
            st.write(f"**Q{i + 1}. {q['question']}**")
            options = [f"{key}: {val}" for key, val in q["options"].items()]
            choice = st.radio(
                f"Select an answer for Q{i + 1}",
                options,
                key=f"quiz_choice_{i}",
                index=None,
                label_visibility="collapsed",
            )
            st.session_state.quiz_answers[i] = choice.split(":")[0] if choice else None
        submitted = st.form_submit_button("Submit Quiz")

    if submitted:
        st.session_state.quiz_submitted = True

    if st.session_state.get("quiz_submitted"):
        score = 0
        st.divider()
        st.subheader("Results")
        for i, q in enumerate(questions):
            user_ans = st.session_state.quiz_answers.get(i)
            correct = q["correct_answer"]
            is_correct = user_ans == correct
            score += int(is_correct)
            icon = "✅" if is_correct else "❌"
            st.write(f"{icon} **Q{i + 1}:** Your answer: {user_ans or 'None'} | Correct answer: {correct}")
            st.caption(q["explanation"])
        st.success(f"Score: {score} / {len(questions)}")

        if st.button("Try a new quiz on this topic"):
            del st.session_state.quiz_data
            st.rerun()


# ----------------------------------------------------------------------
# Activity: Ask Anything (now uses the TutorMe persona)
# ----------------------------------------------------------------------


def ask_anything(question):
    prompt = f"""{PERSONA}

A student has asked you the following question. Answer clearly, at a level
a beginner can follow, and offer to explain further if it would help.

Student's question: {question}"""
    return safe_generate(prompt)


# ----------------------------------------------------------------------
# Activity: Chat with TutorMe AI (has memory across turns)
# ----------------------------------------------------------------------


def init_chat():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = client.chats.create(model=MODEL_NAME)


def render_chat():
    init_chat()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask TutorMe a follow-up question...")
    if not user_input:
        return

    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    prompt = f"""{PERSONA} You are having an ongoing conversation with a
student — answer in a way that builds naturally on what has already been
discussed.

Student: {user_input}"""

    try:
        response = st.session_state.chat_session.send_message(prompt)
        reply = response.text
    except Exception as e:
        reply = f"Sorry, I ran into an error: {e}"

    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.write(reply)


# ----------------------------------------------------------------------
# Main UI
# ----------------------------------------------------------------------

st.title("TutorMe AI 🎓")
st.caption("Your 24/7 AI-powered study buddy")

activity = st.selectbox(
    "Choose an activity",
    ["Explain Concept", "Real-Life Example", "Generate Quiz", "Ask Anything", "Chat with TutorMe"],
)

if activity == "Chat with TutorMe":
    render_chat()

else:
    topic = st.text_input("Enter a topic" if activity != "Ask Anything" else "Enter your question")
    generate_clicked = st.button("Generate")

    if generate_clicked and not topic:
        st.warning("Please enter a topic first.")

    elif generate_clicked or (activity == "Generate Quiz" and "quiz_data" in st.session_state):
        if activity == "Explain Concept" and topic:
            with st.spinner("Thinking..."):
                result = explain_concept(topic)
            if result:
                st.write(result)

        elif activity == "Real-Life Example" and topic:
            with st.spinner("Thinking..."):
                result = real_life_example(topic)
            if result:
                st.write(result)

        elif activity == "Generate Quiz" and topic:
            render_quiz(topic)

        elif activity == "Ask Anything" and topic:
            with st.spinner("Thinking..."):
                result = ask_anything(topic)
            if result:
                st.write(result)
