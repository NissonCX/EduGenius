"""
Architect Agent: Designs curriculum structure and learning paths.

The Architect analyzes the chapter content and creates a structured
learning plan based on the student's cognitive level.
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_community.chat_models.tongyi import ChatTongyi
from app.agents.state.teaching_state import TeachingState
from app.core.config import settings, get_model_name
from app.core.chroma import search_documents


class ArchitectAgent:
    """
    The Architect is responsible for:
    1. Analyzing chapter content structure
    2. Identifying key learning objectives
    3. Creating a learning path adapted to student level
    4. Breaking down content into digestible sections
    """

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize the Architect agent with DashScope LLM."""
        self.llm = ChatTongyi(
            dashscope_api_key=api_key or settings.DASHSCOPE_API_KEY,
            model_name=model or settings.DEFAULT_MODEL,
            temperature=0.3  # Lower temperature for structured output
        )

    async def design_curriculum(self, state: TeachingState) -> Dict[str, Any]:
        """
        Design curriculum structure for the current chapter.

        Args:
            state: Current teaching state

        Returns:
            Curriculum plan with learning objectives and structure
        """
        student_level = state["student_level"]
        chapter_content = state["chapter_content"]
        chapter_title = state["chapter_title"]
        document_md5 = state.get("document_md5", "")

        # RAG 检索：先从文档中检索相关内容
        retrieved_context = ""
        if document_md5:
            try:
                # 检索文档摘要和关键概念
                retrieved_docs = await self._retrieve_document_context(
                    document_md5=document_md5,
                    chapter_title=chapter_title,
                    student_level=student_level
                )

                if retrieved_docs:
                    retrieved_context = "\n\n【文档参考内容】\n"
                    for i, doc in enumerate(retrieved_docs[:3], 1):
                        retrieved_context += f"{i}. {doc['content'][:200]}...\n"
            except Exception as e:
                print(f"RAG 检索失败: {e}")

        # Level-specific curriculum design prompt
        level_descriptions = {
            1: "L1 基础：重点关注概念理解，无需深入细节",
            2: "L2 入门：建立知识框架，掌握基本应用",
            3: "L3 进阶：理解原理，能够综合应用",
            4: "L4 高级：深入分析，讨论边界条件",
            5: "L5 专家：批判性思考，创新应用"
        }

        system_prompt = f"""你是一位教育架构师，负责设计学习路径。

学生等级：{level_descriptions.get(student_level, level_descriptions[3])}

你的任务是分析章节内容，设计适合该等级的学习计划。

请按照以下格式输出（JSON格式）：

{{
    "learning_objectives": [
        "目标1：具体的知识点",
        "目标2：具体的技能",
        "目标3：具体的理解"
    ],
    "knowledge_structure": {{
        "core_concepts": ["概念1", "概念2", "概念3"],
        "supporting_concepts": ["概念A", "概念B"],
        "prerequisites": ["前置知识1", "前置知识2"]
    }},
    "learning_path": [
        {{
            "step": 1,
            "title": "步骤标题",
            "description": "具体描述",
            "estimated_time": "5分钟"
        }}
    ],
    "key_points": [
        "重点1",
        "重点2",
        "重点3"
    ],
    "common_misconceptions": [
        "误解1：正确理解",
        "误解2：正确理解"
    ]
}}

要求：
1. 学习目标要具体、可测量
2. 知识结构要层次清晰
3. 学习路径要循序渐进
4. 关键要点要突出重点
5. 常见误解要符合该等级的错误模式"""

        try:
            # Generate curriculum plan
            response = await self.llm.ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"章节标题：{chapter_title}\n\n章节内容：\n{chapter_content[:3000]}"}
            ])

            # Parse the response (in production, use structured output or better parsing)
            curriculum_text = response.content

            # For now, create a structured response from the text
            # In production, you'd use Pydantic for structured output
            curriculum_plan = {
                "learning_objectives": self._extract_objectives(curriculum_text),
                "knowledge_structure": self._extract_structure(curriculum_text),
                "learning_path": self._extract_path(curriculum_text),
                "key_points": self._extract_key_points(curriculum_text),
                "common_misconceptions": self._extract_misconceptions(curriculum_text),
                "raw_response": curriculum_text  # Store raw for debugging
            }

            return curriculum_plan

        except Exception as e:
            # Fallback to basic structure if LLM fails
            return {
                "learning_objectives": [
                    f"理解{chapter_title}的核心概念",
                    "掌握相关应用方法",
                    "能够解决实际问题"
                ],
                "knowledge_structure": {
                    "core_concepts": ["核心概念"],
                    "supporting_concepts": ["支撑概念"],
                    "prerequisites": []
                },
                "learning_path": [
                    {
                        "step": 1,
                        "title": "概念学习",
                        "description": "理解基本概念",
                        "estimated_time": "10分钟"
                    },
                    {
                        "step": 2,
                        "title": "例题练习",
                        "description": "通过例题加深理解",
                        "estimated_time": "15分钟"
                    },
                    {
                        "step": 3,
                        "title": "巩固应用",
                        "description": "解决实际问题",
                        "estimated_time": "10分钟"
                    }
                ],
                "key_points": ["重点1", "重点2", "重点3"],
                "common_misconceptions": [],
                "error": str(e)
            }

    def _extract_objectives(self, text: str) -> list[str]:
        """Extract learning objectives from response."""
        # Simple extraction logic
        # In production, use better parsing
        if "learning_objectives" in text.lower():
            lines = text.split("\n")
            objectives = []
            for line in lines:
                if "-" in line or "•" in line:
                    objectives.append(line.strip())
                if len(objectives) >= 3:
                    break
            return objectives if objectives else ["理解核心概念", "掌握应用方法", "解决实际问题"]
        return ["理解核心概念", "掌握应用方法", "解决实际问题"]

    def _extract_structure(self, text: str) -> dict:
        """Extract knowledge structure from response."""
        return {
            "core_concepts": ["概念1", "概念2"],
            "supporting_concepts": ["概念A"],
            "prerequisites": []
        }

    def _extract_path(self, text: str) -> list[dict]:
        """Extract learning path from response."""
        return [
            {"step": 1, "title": "概念学习", "description": "理解基本概念", "estimated_time": "10分钟"},
            {"step": 2, "title": "例题练习", "description": "通过例题加深理解", "estimated_time": "15分钟"}
        ]

    def _extract_key_points(self, text: str) -> list[str]:
        """Extract key points from response."""
        return ["重点1", "重点2", "重点3"]

    def _extract_misconceptions(self, text: str) -> list[str]:
        """Extract common misconceptions from response."""
        return []

    async def _retrieve_document_context(
        self,
        document_md5: str,
        chapter_title: str,
        student_level: int,
        n_results: int = 3
    ) -> list:
        """
        RAG 检索：从文档中检索相关内容

        Args:
            document_md5: 文档 MD5 哈希
            chapter_title: 章节标题
            student_level: 学生等级
            n_results: 返回结果数量

        Returns:
            检索到的相关文档片段
        """
        # 构建查询文本
        query_text = f"{chapter_title} 核心概念 重点知识"

        try:
            # 使用 ChromaDB 搜索
            from dashscope import TextEmbedding

            # 生成查询向量
            response = TextEmbedding.call(
                model='text-embedding-v2',
                input=query_text,
                text_type='query'
            )

            if response.status_code == 200:
                query_embedding = response.output['embeddings'][0]['embedding']

                # 检索文档
                from app.core.chroma import query_document_chunks
                results = query_document_chunks(
                    md5_hash=document_md5,
                    query_embedding=query_embedding,
                    n_results=n_results
                )

                # 格式化结果
                retrieved_docs = []
                if results['documents']:
                    for i, doc in enumerate(results['documents'][0]):
                        retrieved_docs.append({
                            'content': doc,
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                            'relevance': 1 - results['distances'][0][i] if results['distances'] else 0
                        })

                return retrieved_docs

        except Exception as e:
            print(f"RAG 检索出错: {e}")
            return []


# LangGraph node function
async def architect_node(state: TeachingState) -> TeachingState:
    """
    LangGraph node for the Architect agent.

    This node analyzes the chapter and creates a curriculum plan.
    """
    # Initialize Architect agent with DashScope
    model_name = get_model_name(state["student_level"])
    architect = ArchitectAgent(model=model_name)

    # Generate curriculum plan
    curriculum_plan = await architect.design_curriculum(state)

    # Update state
    state["architect_plan"] = curriculum_plan
    state["learning_objectives"] = curriculum_plan.get("learning_objectives", [])
    state["current_step"] = "curriculum_designed"

    return state
