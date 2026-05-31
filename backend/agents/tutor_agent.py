"""
agents/tutor_agent.py — AI Tutor Agent using LangGraph (Phase 5)

Architecture:
  LangGraph state machine per message exchange.
  Two nodes: assess_input → generate_response
  State carries full conversation history + student profile.

Flow per API call:
  1. assess_input  — classifies student's message (question/answer/confused/greeting)
  2. generate_response — produces teaching response adapted to classification
  3. Returns response + metadata (suggested_quiz, topic_complete)
"""

import os, json, logging
from typing import TypedDict, List, Dict, Any, Optional

from openai import OpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()
logger  = logging.getLogger(__name__)
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ─────────────────────────────────────────────────────────────────
# State definition
# ─────────────────────────────────────────────────────────────────

class TutorState(TypedDict):
    messages:         List[Dict[str, str]]   # full conversation [{role, content}]
    student_profile:  Dict[str, Any]          # weak_subjects, strong_subjects, grade_level
    subject:          str                     # current subject being tutored
    input_type:       str                     # question | answer | confused | greeting | other
    tutor_response:   str                     # the generated response
    suggested_quiz:   bool                    # True if tutor thinks student is ready for quiz
    topic_complete:   bool                    # True if topic seems mastered


# ─────────────────────────────────────────────────────────────────
# Node 1: assess_input
# ─────────────────────────────────────────────────────────────────

def assess_input(state: TutorState) -> TutorState:
    """
    Classify what the student just said.
    Cheap call — small model would work but we keep gpt-4o for consistency.
    Sets state["input_type"].
    """
    messages = state["messages"]
    if not messages:
        state["input_type"] = "greeting"
        return state

    last_student_msg = ""
    for m in reversed(messages):
        if m["role"] == "user":
            last_student_msg = m["content"]
            break

    if not last_student_msg:
        state["input_type"] = "other"
        return state

    try:
        res = _client.chat.completions.create(
            model      = "gpt-4o",
            max_tokens = 20,
            temperature= 0,
            messages   = [
                {
                    "role": "system",
                    "content": (
                        "Classify the student's message into exactly one word: "
                        "question | answer | confused | greeting | other. "
                        "Return ONLY that one word, nothing else."
                    ),
                },
                {"role": "user", "content": last_student_msg},
            ],
        )
        classification = res.choices[0].message.content.strip().lower()
        valid = {"question","answer","confused","greeting","other"}
        state["input_type"] = classification if classification in valid else "other"
    except Exception as e:
        logger.warning(f"[assess_input] classification failed: {e}")
        state["input_type"] = "other"

    return state


# ─────────────────────────────────────────────────────────────────
# Node 2: generate_response
# ─────────────────────────────────────────────────────────────────

TUTOR_SYSTEM_TEMPLATE = """
You are a warm, patient, and encouraging AI tutor helping a student with {subject}.

Student profile:
- Weak subjects: {weak_subjects}
- Strong subjects: {strong_subjects}
- Education level: {grade_level}

The student's last message was classified as: {input_type}

Your behaviour based on classification:
- "question"  → Answer clearly with a simple explanation, then ask one follow-up question to check understanding.
- "answer"    → Evaluate their answer gently. If correct: praise + introduce next concept. If wrong: correct kindly + re-explain.
- "confused"  → Re-explain the concept differently using an analogy, example, or simpler language.
- "greeting"  → Warmly introduce yourself and ask what topic in {subject} they want to work on.
- "other"     → Respond helpfully and bring focus back to {subject} learning.

Rules:
- Keep responses concise (3-6 sentences max for explanations).
- Use simple language appropriate for the detected education level.
- Always end with either a question to check understanding OR an encouragement.
- If the student has answered 3+ questions correctly in a row, add a line suggesting they take a quiz.
- Never be discouraging. Frame mistakes as learning opportunities.
- Respond in the same language the student is using (Urdu/English mix is fine).
"""


def generate_response(state: TutorState) -> TutorState:
    """
    Generate the tutor's teaching response.
    Reads full conversation history + student profile.
    """
    profile   = state.get("student_profile", {})
    subject   = state.get("subject", "General")
    input_type= state.get("input_type", "other")
    messages  = state.get("messages", [])

    system_prompt = TUTOR_SYSTEM_TEMPLATE.format(
        subject        = subject,
        weak_subjects  = profile.get("weak_subjects", []),
        strong_subjects= profile.get("strong_subjects", []),
        grade_level    = profile.get("grade_level", "school/college"),
        input_type     = input_type,
    )

    # Build messages for OpenAI — system + full conversation history
    openai_messages = [{"role": "system", "content": system_prompt}]

    # Include last 20 messages to stay within context limits
    for m in messages[-20:]:
        if m["role"] in ("user", "assistant"):
            openai_messages.append({"role": m["role"], "content": m["content"]})

    try:
        res = _client.chat.completions.create(
            model      = "gpt-4o",
            max_tokens = 400,
            temperature= 0.6,
            messages   = openai_messages,
        )
        response_text = res.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[generate_response] {e}", exc_info=True)
        response_text = "I'm having trouble connecting right now. Please try again in a moment."

    state["tutor_response"] = response_text

    # Detect quiz suggestion signal
    state["suggested_quiz"] = any(
        phrase in response_text.lower()
        for phrase in ["take a quiz", "try a quiz", "test yourself", "ready for a quiz"]
    )

    # Detect topic completion signal
    state["topic_complete"] = any(
        phrase in response_text.lower()
        for phrase in ["move on", "next topic", "well done", "mastered", "move to the next"]
    )

    return state


# ─────────────────────────────────────────────────────────────────
# Build the LangGraph
# ─────────────────────────────────────────────────────────────────

def _build_graph() -> Any:
    graph = StateGraph(TutorState)

    graph.add_node("assess_input",      assess_input)
    graph.add_node("generate_response", generate_response)

    graph.set_entry_point("assess_input")
    graph.add_edge("assess_input",      "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()


_tutor_graph = _build_graph()


# ─────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────

def run_tutor(
    messages:        List[Dict[str, str]],
    student_profile: Dict[str, Any],
    subject:         str,
) -> Dict[str, Any]:
    """
    Process one chat turn through the LangGraph tutor.

    Args:
        messages:        Full conversation history [{role, content}]
        student_profile: {weak_subjects, strong_subjects, grade_level}
        subject:         Subject being tutored

    Returns:
        {response, suggested_quiz, topic_complete} or {error: "..."}
    """
    try:
        initial_state: TutorState = {
            "messages":        messages,
            "student_profile": student_profile,
            "subject":         subject,
            "input_type":      "",
            "tutor_response":  "",
            "suggested_quiz":  False,
            "topic_complete":  False,
        }

        result = _tutor_graph.invoke(initial_state)

        return {
            "response":      result["tutor_response"],
            "suggested_quiz":result["suggested_quiz"],
            "topic_complete":result["topic_complete"],
            "input_type":    result["input_type"],
        }

    except Exception as e:
        logger.error(f"[run_tutor] {e}", exc_info=True)
        return {"error": f"Tutor agent failed: {str(e)}"}
