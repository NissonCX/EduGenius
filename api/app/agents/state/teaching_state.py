"""
LangGraph State Definition for Multi-Agent Teaching System.
Defines the shared state structure for the teaching workflow.
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class TeachingState(TypedDict):
    """
    Core state for the teaching workflow.

    Attributes:
        # Student Information
        student_level: L1-L5 cognitive level (1=Foundation, 5=Expert)
        user_id: Database user ID
        document_id: Current document being studied

        # Chapter Information
        current_chapter: Chapter number being studied
        chapter_title: Title of current chapter
        chapter_content: Content of the current chapter

        # Learning Progress
        learning_objectives: List of learning objectives for this chapter
        wrong_questions: List of incorrectly answered questions
        correct_questions: List of correctly answered questions
        quiz_attempts: Total number of quiz attempts
        success_rate: Current quiz success rate (0.0-1.0)

        # Agent Outputs
        architect_plan: Curriculum structure and learning path
        examiner_questions: Generated quiz questions
        tutor_explanation: Teaching explanation content
        feedback: Performance feedback and recommendations

        # Session State
        conversation_history: Chat history with student
        current_step: Current step in the learning flow
        needs_level_adjustment: Whether student level should be adjusted

        # Streaming
        streaming_content: Current content being streamed
    """

    # ========== Student Information ==========
    student_level: Annotated[int, "Student's cognitive level (1-5)"]
    user_id: Annotated[int, "Database user ID"]
    document_id: Annotated[int, "Current document ID"]

    # ========== Chapter Information ==========
    current_chapter: Annotated[int, "Current chapter number"]
    chapter_title: Annotated[str, "Title of current chapter"]
    chapter_content: Annotated[str, "Content of current chapter"]

    # ========== Subsection Information ==========
    subsection_id: Annotated[Optional[str], "Current subsection ID (e.g., '1.1')"]
    subsection_title: Annotated[Optional[str], "Title of current subsection"]

    # ========== Learning Progress ==========
    learning_objectives: Annotated[List[str], "Learning objectives for this chapter"]
    wrong_questions: Annotated[List[Dict[str, Any]], "Incorrectly answered questions"]
    correct_questions: Annotated[List[Dict[str, Any]], "Correctly answered questions"]
    quiz_attempts: Annotated[int, "Total quiz attempts"]
    success_rate: Annotated[float, "Quiz success rate (0.0-1.0)"]

    # ========== Agent Outputs ==========
    architect_plan: Annotated[Optional[Dict[str, Any]], "Curriculum structure from Architect"]
    examiner_questions: Annotated[List[Dict[str, Any]], "Quiz questions from Examiner"]
    tutor_explanation: Annotated[Optional[str], "Teaching explanation from Tutor"]
    feedback: Annotated[Optional[str], "Performance feedback"]

    # ========== Session State ==========
    conversation_history: Annotated[List[BaseMessage], "Chat history"]
    current_step: Annotated[str, "Current workflow step"]
    needs_level_adjustment: Annotated[bool, "Whether to adjust student level"]

    # ========== Streaming ==========
    streaming_content: Annotated[Optional[str], "Content for SSE streaming"]

    # ========== OCR Metadata ==========
    is_ocr_document: Annotated[bool, "Whether document was processed via OCR"]
    ocr_confidence: Annotated[float, "OCR confidence score (0.0-1.0)"]


class QuizQuestion(TypedDict):
    """Structure for a quiz question."""
    question_id: Annotated[str, "Unique question identifier"]
    question: Annotated[str, "Question text"]
    options: Annotated[List[str], "Multiple choice options"]
    correct_answer: Annotated[str, "Correct option (A/B/C/D)"]
    explanation: Annotated[str, "Explanation of the answer"]
    difficulty_level: Annotated[int, "Question difficulty (1-5)"]
    question_type: Annotated[str, "Question type (conceptual/application/analysis)"]


class AgentResponse(TypedDict):
    """Structure for agent responses."""
    agent_name: Annotated[str, "Name of the agent (Architect/Examiner/Tutor)"]
    content: Annotated[str, "Response content"]
    level_adapted: Annotated[bool, "Whether response was adapted to student level"]
    metadata: Annotated[Dict[str, Any], "Additional metadata"]
