"""
LangGraph Workflow: Multi-Agent Teaching System.

This module defines the teaching workflow graph that orchestrates
the Architect, Examiner, and Tutor agents.
"""
from typing import Literal, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state.teaching_state import TeachingState
from app.agents.nodes.architect import architect_node
from app.agents.nodes.examiner import examiner_node, evaluate_answer_node
from app.agents.nodes.tutor import (
    tutor_node,
    tutor_hint_node,
    tutor_summary_node
)
from app.agents.state.level_prompts import should_adjust_level


def should_continue_quizzing(state: TeachingState) -> Literal["continue_quiz", "end_quiz"]:
    """Determine if quizzing should continue based on performance."""
    max_questions = 5
    current_attempts = state.get("quiz_attempts", 0)

    # Check if we've reached max questions
    if current_attempts >= max_questions:
        return "end_quiz"

    # Check if success rate indicates level mismatch
    success_rate = state.get("success_rate", 1.0)
    if success_rate >= 0.9 and current_attempts >= 3:
        return "end_quiz"  # Too easy
    if success_rate <= 0.2 and current_attempts >= 3:
        return "end_quiz"  # Too hard

    return "continue_quiz"


def should_adjust_level_decision(state: TeachingState) -> Literal["adjust_level", "keep_level"]:
    """Decide if student level should be adjusted."""
    success_rate = state.get("success_rate", 0.0)
    quiz_attempts = state.get("quiz_attempts", 0)

    # Get recent history (last 5 answers)
    recent_history = []
    for cq in state.get("correct_questions", []):
        recent_history.append(True)
    for wq in state.get("wrong_questions", []):
        recent_history.append(False)

    should_adjust, new_level, message = should_adjust_level(
        state["student_level"],
        success_rate,
        quiz_attempts,
        recent_history[-5:]
    )

    if should_adjust:
        state["student_level"] = new_level
        state["feedback"] = message
        return "adjust_level"

    return "keep_level"


def create_teaching_graph():
    """
    Create the LangGraph workflow for the teaching system.

    The workflow:
    1. Start -> Architect (design curriculum)
    2. Architect -> Tutor (provide initial explanation)
    3. Tutor -> Examiner (generate questions)
    4. Examiner -> [Quiz Loop]
       - Evaluate answer
       - Check if should continue
       - If correct: continue quiz
       - If wrong: provide hint
    5. End Quiz -> Summary
    6. Check level adjustment
    7. End

    Returns:
        Compiled StateGraph
    """
    # Create the graph
    workflow = StateGraph(TeachingState)

    # Add nodes
    workflow.add_node("architect", architect_node)
    workflow.add_node("tutor", tutor_node)
    workflow.add_node("examiner", examiner_node)
    workflow.add_node("evaluate_answer", lambda state: state)  # Placeholder
    workflow.add_node("tutor_hint", lambda state: state)  # Placeholder
    workflow.add_node("tutor_summary", tutor_summary_node)

    # Define the edges (workflow)
    workflow.set_entry_point("architect")

    # After architect design, go to tutor for initial explanation
    workflow.add_edge("architect", "tutor")

    # After tutor explanation, generate questions
    workflow.add_edge("tutor", "examiner")

    # After generating questions, wait for student input
    # (This is handled by the API layer, not the graph itself)

    # Conditional edges for quizzing flow
    workflow.add_conditional_edges(
        "evaluate_answer",
        should_continue_quizzing,
        {
            "continue_quiz": "examiner",
            "end_quiz": "tutor_summary"
        }
    )

    # After summary, check if level needs adjustment
    workflow.add_conditional_edges(
        "tutor_summary",
        should_adjust_level_decision,
        {
            "adjust_level": END,
            "keep_level": END
        }
    )

    # Add checkpointing for memory
    memory = MemorySaver()

    # Compile the graph
    app = workflow.compile(checkpointer=memory)

    return app


# ============ Simplified Linear Flow for Initial Implementation ============
def create_simple_teaching_flow():
    """
    Create a simplified linear teaching flow for initial implementation.

    Flow: Start -> Architect -> Tutor -> Examiner -> Generate Questions -> End
    """
    workflow = StateGraph(TeachingState)

    # Add nodes
    workflow.add_node("architect", architect_node)
    workflow.add_node("tutor", tutor_node)
    workflow.add_node("examiner", examiner_node)

    # Define linear flow
    workflow.set_entry_point("architect")
    workflow.add_edge("architect", "tutor")
    workflow.add_edge("tutor", "examiner")
    workflow.add_edge("examiner", END)

    # Compile
    app = workflow.compile()

    return app


# ============ Async Stream Handler ============
class TeachingStreamHandler:
    """
    Handles streaming responses from the teaching workflow.
    Enables SSE (Server-Sent Events) for real-time updates.
    """

    def __init__(self, graph):
        """Initialize with a teaching graph."""
        self.graph = graph

    async def stream_teaching_session(
        self,
        initial_state: TeachingState
    ):
        """
        Stream the teaching session step by step.

        Args:
            initial_state: Initial state for the teaching session

        Yields:
            Stream events with type and content
        """
        step = 0

        # Step 1: Architect - Design curriculum
        yield {
            "type": "step",
            "step": step,
            "phase": "architect",
            "message": "正在分析章节内容，设计学习路径..."
        }

        state = await architect_node(initial_state)
        yield {
            "type": "architect_complete",
            "step": step,
            "data": state.get("architect_plan")
        }
        step += 1

        # Step 2: Tutor - Provide initial explanation
        yield {
            "type": "step",
            "step": step,
            "phase": "tutor",
            "message": "正在生成知识点讲解..."
        }

        state = await tutor_node(state)
        yield {
            "type": "tutor_explanation",
            "step": step,
            "content": state.get("tutor_explanation")
        }
        step += 1

        # Step 3: Examiner - Generate questions
        yield {
            "type": "step",
            "step": step,
            "phase": "examiner",
            "message": "正在生成测试题..."
        }

        state = await examiner_node(state)
        yield {
            "type": "questions_generated",
            "step": step,
            "questions": state.get("examiner_questions")
        }

        # Final state
        yield {
            "type": "session_ready",
            "state": state
        }

    async def stream_answer_evaluation(
        self,
        state: TeachingState,
        question_id: str,
        answer: str
    ):
        """
        Stream answer evaluation and feedback.

        Args:
            state: Current teaching state
            question_id: ID of question being answered
            answer: Student's answer

        Yields:
            Stream events with evaluation results
        """
        from app.agents.nodes.examiner import evaluate_answer_node

        yield {
            "type": "evaluating",
            "message": "正在评估答案..."
        }

        # Update state with answer
        answer_data = {"question_id": question_id, "answer": answer}
        state = await evaluate_answer_node(state, answer_data)

        # Stream feedback
        yield {
            "type": "evaluation_result",
            "is_correct": state.get("correct_questions")[-1].get("question_id") == question_id
            if state.get("correct_questions") else False,
            "feedback": state.get("feedback", ""),
            "success_rate": state.get("success_rate", 0.0)
        }

        # Check if session should end
        if state.get("quiz_attempts", 0) >= 5:
            yield {
                "type": "session_ending",
                "message": "正在生成学习总结..."
            }

            state = await tutor_summary_node(state)
            yield {
                "type": "session_summary",
                "summary": state.get("tutor_explanation")
            }

        # Note: state is modified in-place and should be retrieved from the calling context
