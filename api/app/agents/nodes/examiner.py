"""
Examiner Agent: Generates adaptive quiz questions.

The Examiner creates questions tailored to the student's cognitive level,
assesses understanding, and tracks performance.
"""
from typing import Dict, Any, List
from langchain_community.chat_models.tongyi import ChatTongyi
from app.agents.state.teaching_state import TeachingState, QuizQuestion
from app.agents.state.level_prompts import get_examiner_prompt, get_level_description
from app.core.config import settings, get_model_name


class ExaminerAgent:
    """
    The Examiner is responsible for:
    1. Generating quiz questions adapted to student level
    2. Creating questions that test appropriate depth
    3. Evaluating student answers
    4. Recommending level adjustments based on performance
    """

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize the Examiner agent with DashScope LLM."""
        self.llm = ChatTongyi(
            dashscope_api_key=api_key or settings.DASHSCOPE_API_KEY,
            model_name=model or settings.DEFAULT_MODEL,
            temperature=0.4  # Slightly higher for varied questions
        )

    async def generate_questions(
        self,
        state: TeachingState,
        num_questions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions based on student level and chapter content.

        Args:
            state: Current teaching state
            num_questions: Number of questions to generate

        Returns:
            List of quiz questions
        """
        student_level = state["student_level"]
        chapter_content = state["chapter_content"]
        chapter_title = state["chapter_title"]
        learning_objectives = state.get("learning_objectives", [])
        wrong_questions = state.get("wrong_questions", [])

        # Get level-specific prompt
        level_prompt = get_examiner_prompt(student_level)
        level_info = get_level_description(student_level)

        # Build context from wrong questions (if any)
        review_context = ""
        if wrong_questions:
            review_context = f"\n\n【需要重点复习的知识点】\n"
            for wq in wrong_questions[-3:]:  # Last 3 wrong questions
                review_context += f"- {wq.get('question', '')}\n"

        system_prompt = f"""你是一位经验丰富的出题专家，擅长根据学生等级设计检测题。

学生等级：{level_info['name']} - {level_info['characteristics']}
出题风格：{level_info['question_style']}

{level_prompt}

请严格按照以下 JSON 格式输出 {num_questions} 道题目：

[
  {{
    "question_id": "q1",
    "question": "题目内容",
    "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
    "correct_answer": "A",
    "explanation": "详细解析（根据学生等级调整解释深度）",
    "difficulty_level": {student_level},
    "question_type": "conceptual"
  }}
]

要求：
1. 题目必须基于提供的章节内容
2. 难度要匹配学生等级
3. 选项要有一定的迷惑性（但等级越低越明显）
4. 解释要帮助学生理解，而不仅是给答案
5. 题目要检测学习目标中的关键点"""

        user_prompt = f"""章节：{chapter_title}

学习目标：
{chr(10).join(f'- {obj}' for obj in learning_objectives) if learning_objectives else '- 理解核心概念'}

章节内容：
{chapter_content[:4000]}{review_context}

请生成 {num_questions} 道检测题。"""

        try:
            from app.core.logging_config import get_logger
            logger = get_logger(__name__)

            logger.info(f"开始调用 LLM 生成 {num_questions} 道题目...")
            response = await self.llm.ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            logger.info(f"LLM 响应成功，内容长度: {len(response.content) if response.content else 0}")
            logger.info(f"=== LLM 完整响应开始 ===")
            logger.info(response.content)
            logger.info(f"=== LLM 完整响应结束 ===")

            # Parse questions from response
            questions = self._parse_questions(response.content)
            logger.info(f"解析出 {len(questions)} 道题目")

            if not questions:
                logger.warning(f"未能从 LLM 响应中解析出题目，使用 fallback")
                return self._generate_fallback_questions(num_questions, error="解析失败")

            return questions

        except Exception as e:
            from app.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"LLM 生成题目异常: {type(e).__name__}: {str(e)}", exc_info=True)
            # Fallback to simpler questions
            return self._generate_fallback_questions(num_questions, error=str(e))

    async def evaluate_answer(
        self,
        question: Dict[str, Any],
        student_answer: str,
        state: TeachingState
    ) -> Dict[str, Any]:
        """
        Evaluate student's answer and provide feedback.

        Args:
            question: The question being answered
            student_answer: Student's answer
            state: Current teaching state

        Returns:
            Evaluation result with correctness and feedback
        """
        correct_answer = question.get("correct_answer", "")
        explanation = question.get("explanation", "")

        # Simple correctness check (can be enhanced with LLM)
        is_correct = student_answer.strip().upper() == correct_answer.strip().upper()

        # Generate feedback based on level
        student_level = state["student_level"]
        if is_correct:
            if student_level <= 2:
                feedback = f"✅ 正确！{explanation}"
            elif student_level == 3:
                feedback = f"✅ 回答正确。{explanation}\n\n思考：你能举一反三吗？"
            else:
                feedback = f"✅ 正确。{explanation}\n\n深入思考：这个结论在边界情况下还成立吗？"
        else:
            if student_level <= 2:
                feedback = f"❌ 不太对。正确答案是 {correct_answer}。\n\n{explanation}"
            elif student_level == 3:
                feedback = f"❌ 不正确。正确答案是 {correct_answer}。\n\n{explanation}\n\n提示：回顾一下核心概念。"
            else:
                feedback = f"❌ 回答有误。正确答案是 {correct_answer}。\n\n{explanation}\n\n反思：你的思路在哪里出现了偏差？"

        return {
            "is_correct": is_correct,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "feedback": feedback,
            "question_id": question.get("question_id"),
            "needs_review": not is_correct
        }

    def _parse_questions(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse questions from LLM response."""
        import json

        from app.core.logging_config import get_logger
        logger = get_logger(__name__)

        logger.info(f"开始解析 LLM 响应，原始内容长度: {len(response_text)}")

        # 方法1：直接尝试解析整个响应
        try:
            questions = json.loads(response_text.strip())
            if isinstance(questions, list) and len(questions) > 0:
                logger.info(f"直接解析成功，获得 {len(questions)} 道题目")
                return questions
        except json.JSONDecodeError:
            logger.debug("直接解析失败，尝试提取 JSON 片段")

        # 方法2：智能查找 JSON 数组（处理嵌套的 []）
        def extract_json_array(text: str) -> str:
            """智能提取完整的 JSON 数组，处理嵌套情况"""
            start_idx = text.find('[')
            if start_idx == -1:
                return None

            bracket_count = 0
            in_string = False
            escape_next = False

            for i in range(start_idx, len(text)):
                char = text[i]

                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            # 找到完整的数组
                            return text[start_idx:i+1]

            return None

        try:
            json_str = extract_json_array(response_text)
            if json_str:
                logger.info(f"找到 JSON 片段，长度: {len(json_str)}")
                questions = json.loads(json_str)
                logger.info(f"JSON 解析成功，获得 {len(questions)} 道题目")
                return questions
            else:
                logger.warning("未在响应中找到完整的 JSON 数组")
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.debug(f"尝试解析的 JSON: {json_str[:500] if json_str else 'N/A'}...")
        except Exception as e:
            logger.error(f"解析异常: {type(e).__name__}: {e}")

        logger.warning("未能解析出任何题目，将使用 fallback")
        return []

    def _generate_fallback_questions(
        self,
        num_questions: int,
        error: str = None
    ) -> List[Dict[str, Any]]:
        """Generate fallback questions when LLM fails."""
        questions = []
        for i in range(num_questions):
            questions.append({
                "question_id": f"q_fallback_{i+1}",
                "question": f"这是第 {i+1} 道测试题（LLM 服务暂不可用，使用备用题目）",
                "options": [
                    "A. 选项A - 基础理解",
                    "B. 选项B - 待确认",
                    "C. 选项C - 待确认",
                    "D. 选项D - 待确认"
                ],
                "correct_answer": "A",
                "explanation": "这是备用解析。当 LLM 服务恢复后将提供智能出题。",
                "difficulty_level": 1,
                "question_type": "fallback"
            })
        return questions


# LangGraph node function
async def examiner_node(state: TeachingState) -> TeachingState:
    """
    LangGraph node for the Examiner agent.

    This node generates quiz questions based on student level.
    """
    # Initialize Examiner agent with DashScope
    model_name = get_model_name(state["student_level"])
    examiner = ExaminerAgent(model=model_name)

    # Generate questions
    questions = await examiner.generate_questions(state, num_questions=3)

    # Update state
    state["examiner_questions"] = questions
    state["current_step"] = "questions_generated"

    return state


async def evaluate_answer_node(state: TeachingState, answer_data: Dict[str, Any]) -> TeachingState:
    """
    LangGraph node for evaluating student answers.

    Args:
        state: Current teaching state
        answer_data: Contains question_id and student_answer

    Returns:
        Updated state with evaluation results
    """
    examiner = ExaminerAgent()

    # Find the question
    question_id = answer_data.get("question_id")
    question = next(
        (q for q in state["examiner_questions"] if q["question_id"] == question_id),
        None
    )

    if not question:
        return state

    # Evaluate answer
    evaluation = await examiner.evaluate_answer(
        question,
        answer_data.get("answer", ""),
        state
    )

    # Update progress tracking
    if evaluation["is_correct"]:
        state["correct_questions"].append({
            "question_id": question_id,
            "question": question["question"],
            "answer": answer_data.get("answer", "")
        })
    else:
        state["wrong_questions"].append({
            "question_id": question_id,
            "question": question["question"],
            "answer": answer_data.get("answer", ""),
            "correct_answer": evaluation["correct_answer"]
        })

    # Update statistics
    state["quiz_attempts"] += 1
    total = state["quiz_attempts"]
    correct = len(state["correct_questions"])
    state["success_rate"] = correct / total if total > 0 else 0.0

    # Store feedback for streaming
    state["feedback"] = evaluation["feedback"]
    state["streaming_content"] = evaluation["feedback"]

    return state
