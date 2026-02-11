"""
Tutor Agent: Provides adaptive teaching explanations.

The Tutor offers explanations and guidance tailored to the student's
cognitive level, learning style, and current understanding.
"""
from typing import Dict, Any, List
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.state.teaching_state import TeachingState
from app.agents.state.level_prompts import get_tutor_prompt, get_level_description
from app.core.config import settings, get_model_name
from app.core.chroma import query_document_chunks


class TutorAgent:
    """
    The Tutor is responsible for:
    1. Providing explanations adapted to student level
    2. Answering questions in an appropriate style
    3. Offering hints and guidance
    4. Adjusting explanations based on student responses
    """

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize the Tutor agent with DashScope LLM."""
        self.llm = ChatTongyi(
            dashscope_api_key=api_key or settings.DASHSCOPE_API_KEY,
            model_name=model or settings.DEFAULT_MODEL,
            temperature=0.7  # Higher for more varied, natural responses
        )

    async def explain_concept(
        self,
        state: TeachingState,
        topic: str = None,
        context: str = None
    ) -> str:
        """
        Generate an explanation for a concept or topic.

        Args:
            state: Current teaching state
            topic: Specific topic to explain (optional)
            context: Additional context or question (optional)

        Returns:
            Formatted explanation text with document source references
        """
        student_level = state["student_level"]
        chapter_content = state["chapter_content"]
        chapter_title = state["chapter_title"]
        learning_objectives = state.get("learning_objectives", [])
        wrong_questions = state.get("wrong_questions", [])
        document_md5 = state.get("document_md5", "")

        # RAG 检索：查找相关文档内容作为来源
        document_sources = ""
        if document_md5:
            try:
                from dashscope import TextEmbedding

                # 生成查询向量
                query_text = topic or f"{chapter_title} {context or '核心概念'}"
                response = TextEmbedding.call(
                    model='text-embedding-v2',
                    input=query_text,
                    text_type='query'
                )

                if response.status_code == 200:
                    query_embedding = response.output['embeddings'][0]['embedding']

                    # 检索相关文档片段
                    results = query_document_chunks(
                        md5_hash=document_md5,
                        query_embedding=query_embedding,
                        n_results=2
                    )

                    if results['documents'] and results['documents'][0]:
                        document_sources = "\n\n【教材原文参考】\n"
                        for i, doc in enumerate(results['documents'][0][:2], 1):
                            # 获取页码信息
                            page_num = results['metadatas'][0][i].get('page', '?')
                            content = doc[:150] + "..." if len(doc) > 150 else doc
                            document_sources += f"📖 第{page_num}页：{content}\n"
            except Exception as e:
                print(f"检索文档来源失败: {e}")

        # Get level-specific tutor prompt
        tutor_prompt = get_tutor_prompt(student_level)
        level_info = get_level_description(student_level)

        # Build context from conversation and mistakes
        conversation_context = ""
        if state.get("conversation_history"):
            recent_messages = state["conversation_history"][-3:]
            conversation_context = "\n\n【最近对话】\n"
            for msg in recent_messages:
                if isinstance(msg, HumanMessage):
                    conversation_context += f"学生：{msg.content}\n"
                elif isinstance(msg, AIMessage):
                    conversation_context += f"老师：{msg.content}\n"

        # Address weak points
        review_points = ""
        if wrong_questions:
            review_points = "\n\n【需要重点关注的知识点】\n"
            for wq in wrong_questions[-2:]:
                review_points += f"- {wq.get('question', '')}\n"

        system_prompt = f"""{tutor_prompt}

当前信息：
- 学生等级：{level_info['name']}（{level_info['characteristics']}）
- 教学风格：{level_info['teaching_style']}

注意事项：
1. 严格按照学生等级的语言风格和讲解方式
2. 避免使用超出等级理解范围的专业术语
3. 多用适合等级的例子和类比
4. 对于低等级（L1-L2），要更耐心、鼓励式
5. 对于高等级（L4-L5），要更思辨、启发式
6. 控制输出长度，确保信息密度适中"""

        # Determine what to explain
        if topic:
            user_prompt = f"请详细讲解：{topic}\n"
        elif context:
            user_prompt = f"学生问题：{context}\n"
        else:
            user_prompt = f"请为本章节提供核心知识点的讲解。\n"

        user_prompt += f"""
章节：{chapter_title}

学习目标：
{chr(10).join(f'- {obj}' for obj in learning_objectives) if learning_objectives else '- 理解核心概念'}

相关内容：
{chapter_content[:3000]}{review_points}{conversation_context}

请提供适合该等级的讲解。"""

        try:
            response = await self.llm.ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])

            return response.content

        except Exception as e:
            # Fallback explanation
            return f"""【核心知识点讲解】

{topic or chapter_title}

很抱歉，AI 讲解服务暂时不可用。请稍后再试。

您可以：
1. 阅读章节内容进行自学
2. 尝试完成练习题
3. 向助教提问

错误信息：{str(e)}"""

    async def answer_question(
        self,
        state: TeachingState,
        question: str
    ) -> str:
        """
        Answer a student's question with level-adapted response.

        Args:
            state: Current teaching state
            question: Student's question

        Returns:
            Formatted answer
        """
        student_level = state["student_level"]
        chapter_content = state["chapter_content"]

        # Get context about what student is struggling with
        wrong_topics = [
            wq.get("question", "")[:50]
            for wq in state.get("wrong_questions", [])
        ]

        system_prompt = get_tutor_prompt(student_level)

        # 构建上下文信息，包含小节信息
        context_info = f"当前章节背景（用于回答）：\n{chapter_content[:2000]}"

        # 如果有小节信息，添加到上下文中
        subsection_id = state.get("subsection_id")
        subsection_title = state.get("subsection_title")
        if subsection_id and subsection_title:
            context_info = f"""当前学习内容：
- 章节：{state.get('chapter_title', '')}
- 小节：{subsection_id} {subsection_title}

上下文背景：
{chapter_content[:2000]}"""

        user_prompt = f"""学生提问：{question}

{context_info}

学生薄弱点：
{chr(10).join(f'- {t}' for t in wrong_topics) if wrong_topics else '暂无明显薄弱点'}

请提供适合该等级的解答。"""

        try:
            response = await self.llm.ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])

            return response.content

        except Exception as e:
            return f"抱歉，我暂时无法回答这个问题。请稍后再试。\n\n错误：{str(e)}"

    async def provide_hint(
        self,
        state: TeachingState,
        question: Dict[str, Any],
        attempt_number: int = 1
    ) -> str:
        """
        Provide a progressive hint for a question.

        Args:
            state: Current teaching state
            question: The question the student is struggling with
            attempt_number: Which attempt this is (1st, 2nd, 3rd)

        Returns:
            Hint text
        """
        student_level = state["student_level"]
        question_text = question.get("question", "")
        correct_answer = question.get("correct_answer", "")
        explanation = question.get("explanation", "")

        # Progressive hints based on attempt
        hint_templates = {
            1: {
                1: "💡 g提示：仔细阅读题目，关键信息就在题干中。",
                2: "💡 提示2：回忆一下本章节的核心概念。",
                3: "💡 提示3：这道题考查的是基础知识点，再想想？"
            },
            2: {
                1: "💡 提示：先理清题目在问什么，再思考相关知识。",
                2: "💡 提示2：可以用排除法，先排除明显错误的选项。",
                3: "💡 提示3：回到教材，找到相关的定义或例子。"
            },
            3: {
                1: "💡 提示：分析题目涉及的核心概念是什么。",
                2: "💡 提示2：考虑一下这个概念的应用场景。",
                3: "💡 提示3：对比各个选项，找出最符合定义的答案。"
            }
        }

        # For higher levels, give less direct hints
        if student_level >= 4:
            return {
                1: "💡 提示：思考这个问题的本质是什么。",
                2: "💡 提示2：考虑边界条件。",
                3: "💡 提示3：从原理出发分析。"
            }.get(attempt_number, "💡 再深入思考一下。")

        hint = hint_templates.get(student_level, hint_templates[3])
        return hint.get(attempt_number, "💡 继续努力，你离答案很近了。")

    async def generate_summary(
        self,
        state: TeachingState
    ) -> str:
        """
        Generate a learning summary based on session performance.

        Args:
            state: Current teaching state with performance data

        Returns:
            Formatted summary with recommendations
        """
        student_level = state["student_level"]
        success_rate = state.get("success_rate", 0.0)
        correct_count = len(state.get("correct_questions", []))
        wrong_count = len(state.get("wrong_questions", []))

        # Build performance summary
        performance_summary = f"""
学习情况总结

✅ 正确：{correct_count} 题
❌ 错误：{wrong_count} 题
📊 正确率：{success_rate * 100:.1f}%
"""

        if success_rate >= 0.8:
            feedback = "太棒了！你对本章节的掌握非常好。继续保持，可以尝试更难的挑战。"
        elif success_rate >= 0.6:
            feedback = "不错的表现！大部分概念都已经理解。建议重点复习一下错题涉及的知识点。"
        else:
            feedback = "建议重新阅读章节内容，巩固基础概念。不要着急，打好基础很重要。"

        # Add review recommendations
        review_section = ""
        if wrong_count > 0:
            review_section = "\n\n【建议复习的知识点】\n"
            for i, wq in enumerate(state["wrong_questions"][:3], 1):
                review_section += f"{i}. {wq.get('question', '')[:50]}...\n"

        return performance_summary + feedback + review_section


# LangGraph node function
async def tutor_node(state: TeachingState) -> TeachingState:
    """
    LangGraph node for the Tutor agent.

    This node provides explanations based on student level.
    """
    # Initialize Tutor agent with DashScope
    model_name = get_model_name(state["student_level"])
    tutor = TutorAgent(model=model_name)

    # Get the last user message if available
    user_question = None
    if state.get("conversation_history"):
        last_msg = state["conversation_history"][-1]
        if isinstance(last_msg, HumanMessage):
            user_question = last_msg.content

    # Generate explanation
    if user_question:
        explanation = await tutor.answer_question(state, user_question)
    else:
        explanation = await tutor.explain_concept(state)

    # Update state
    state["tutor_explanation"] = explanation
    state["streaming_content"] = explanation
    state["current_step"] = "explanation_provided"

    # Add to conversation history
    state["conversation_history"].append(AIMessage(content=explanation))

    return state


async def tutor_hint_node(state: TeachingState, question_id: str, attempt: int) -> TeachingState:
    """
    LangGraph node for providing hints.

    Args:
        state: Current teaching state
        question_id: ID of question needing hint
        attempt: Attempt number (1, 2, 3)

    Returns:
        Updated state with hint
    """
    tutor = TutorAgent()

    # Find the question
    question = next(
        (q for q in state.get("examiner_questions", [])
         if q.get("question_id") == question_id),
        None
    )

    if not question:
        return state

    # Generate hint
    hint = await tutor.provide_hint(state, question, attempt)

    state["streaming_content"] = hint
    state["conversation_history"].append(AIMessage(content=hint))

    return state


async def tutor_summary_node(state: TeachingState) -> TeachingState:
    """
    LangGraph node for generating session summary.

    Args:
        state: Current teaching state with performance data

    Returns:
        Updated state with summary
    """
    tutor = TutorAgent()
    summary = await tutor.generate_summary(state)

    state["tutor_explanation"] = summary
    state["streaming_content"] = summary
    state["feedback"] = summary
    state["current_step"] = "session_complete"

    return state
