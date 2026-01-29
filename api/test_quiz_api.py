#!/usr/bin/env python3
"""
测试答题系统的 API 端点
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    return response.status_code == 200

def test_quiz_generate(token):
    """测试生成题目"""
    print("\n=== 测试生成题目 ===")
    response = requests.post(
        f"{BASE_URL}/api/quiz/generate",
        json={
            "document_id": 1,
            "chapter_number": 1,
            "question_type": "choice",
            "difficulty": 3,
            "count": 3
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"生成了 {len(data)} 道题目")
        for i, q in enumerate(data):
            print(f"  题目 {i+1}: {q['question_text'][:50]}...")
        return data
    else:
        print(f"错误: {response.text}")
        return None

def test_quiz_get_questions(document_id, chapter_number, token):
    """测试获取题目列表"""
    print(f"\n=== 测试获取题目列表 (文档 {document_id}, 章节 {chapter_number}) ===")
    response = requests.get(
        f"{BASE_URL}/api/quiz/questions/{document_id}/{chapter_number}",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"题目总数: {data['total']}")
        return data['questions']
    else:
        print(f"错误: {response.text}")
        return []

def test_quiz_submit(question_id, user_answer, user_id, token):
    """测试提交答案"""
    print(f"\n=== 测试提交答案 ===")
    response = requests.post(
        f"{BASE_URL}/api/quiz/submit",
        json={
            "user_id": user_id,
            "question_id": question_id,
            "user_answer": user_answer
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"结果: {'正确' if data['is_correct'] else '错误'}")
        print(f"反馈: {data['feedback']}")
        return data
    else:
        print(f"错误: {response.text}")
        return None

def test_chapter_lock(document_id, token):
    """测试章节锁定状态"""
    print(f"\n=== 测试章节锁定状态 ===")
    response = requests.get(
        f"{BASE_URL}/api/documents/{document_id}/chapters",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"文档: {data['document_title']}")
        print(f"总章节数: {data['total_chapters']}")
        print("\n章节状态:")
        for chapter in data['chapters']:
            lock_status = "🔒 锁定" if chapter['is_locked'] else "🔓 解锁"
            print(f"  {chapter['status_icon']} 第 {chapter['chapter_number']} 章: {chapter['status_text']} ({lock_status})")
            if chapter['is_locked'] and chapter['lock_reason']:
                print(f"      原因: {chapter['lock_reason']}")
        return data
    else:
        print(f"错误: {response.text}")
        return None

def test_login():
    """测试登录获取 token"""
    print("\n=== 测试登录 ===")
    response = requests.post(
        f"{BASE_URL}/api/users/login",
        json={
            "email": "demo@edugenius.ai",
            "password": "demo123"
        }
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"用户: {data['username']}")
        print(f"Token: {data['access_token'][:50]}...")
        return data['access_token'], data['user_id']
    else:
        print(f"登录失败: {response.text}")
        # 如果登录失败，尝试注册
        print("\n尝试注册新用户...")
        response = requests.post(
            f"{BASE_URL}/api/users/register",
            json={
                "email": "demo@edugenius.ai",
                "username": "demo_user",
                "password": "demo123"
            }
        )
        if response.status_code == 200:
            print("注册成功，请重新登录")
        return None, None

def main():
    print("🚀 开始测试 EduGenius 答题系统\n")

    # 测试健康检查
    if not test_health():
        print("❌ 健康检查失败，请确保后端正在运行")
        return

    # 登录获取 token
    token, user_id = test_login()
    if not token:
        print("❌ 无法获取认证 token")
        return

    # 测试章节锁定
    chapters = test_chapter_lock(1, token)

    # 生成题目
    questions = test_quiz_generate(token)
    if questions:
        # 提交答案
        test_quiz_submit(questions[0]['id'], 'A', user_id, token)

    print("\n✅ 测试完成")

if __name__ == "__main__":
    main()
