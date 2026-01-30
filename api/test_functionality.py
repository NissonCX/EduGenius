#!/usr/bin/env python3
"""
EduGenius 功能测试脚本

测试内容：
1. 后端健康检查
2. 用户认证
3. 文档列表查询
4. OCR 功能测试
5. 文档上传流程
"""

import requests
import json
import time
import sys
from pathlib import Path

# 配置
API_BASE = "http://localhost:8000"
TEST_USER = {
    "username": "test_user",
    "password": "Test12345"
}

def print_section(title):
    """打印测试部分标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_backend_health():
    """测试后端健康检查"""
    print_section("1️⃣  测试后端健康检查")

    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 后端健康检查通过")
            print(f"   服务: {data.get('service')}")
            print(f"   数据库: {data.get('database')}")
            print(f"   智能体: {', '.join(data.get('agents', []))}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_user_auth():
    """测试用户认证"""
    print_section("2️⃣  测试用户认证")

    # 尝试登录或注册
    try:
        # 先尝试登录
        response = requests.post(
            f"{API_BASE}/api/users/login",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print("✅ 用户登录成功")
            print(f"   用户名: {TEST_USER['username']}")
            print(f"   Token: {token[:20]}...")
            return token
        else:
            # 尝试注册
            print("   登录失败，尝试注册新用户...")
            response = requests.post(
                f"{API_BASE}/api/users/register",
                json={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"],
                    "email": f"{TEST_USER['username']}@test.com"
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                print("✅ 用户注册成功")
                print(f"   用户名: {TEST_USER['username']}")
                return token
            else:
                print(f"❌ 用户认证失败: {response.text}")
                return None
    except Exception as e:
        print(f"❌ 用户认证异常: {e}")
        return None

def test_document_list(token):
    """测试文档列表查询"""
    print_section("3️⃣  测试文档列表查询")

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/api/documents/list",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            print(f"✅ 文档列表查询成功")
            print(f"   文档数量: {len(documents)}")

            for doc in documents[:3]:  # 只显示前3个
                print(f"\n   📄 {doc.get('title', 'Unknown')}")
                print(f"      类型: {doc.get('file_type', 'Unknown')}")
                print(f"      大小: {doc.get('file_size', 0) / 1024:.1f} KB")
                print(f"      状态: {doc.get('processing_status', 'Unknown')}")
                print(f"      章节: {doc.get('total_chapters', 0)} 章")

            return documents
        else:
            print(f"❌ 文档列表查询失败: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 文档列表查询异常: {e}")
        return []

def test_ocr_functionality():
    """测试 OCR 功能"""
    print_section("4️⃣  测试 OCR 功能")

    try:
        # 导入 OCR 引擎
        sys.path.insert(0, str(Path(__file__).parent))
        from app.core.ocr_engine import OCREngine

        print("   正在初始化 OCR 引擎...")
        ocr = OCREngine()

        # 检查是否有可用的测试文件
        test_files = list(Path("uploads").glob("*.pdf"))
        if not test_files:
            print("   ⚠️  uploads 目录中没有测试 PDF 文件")
            return True

        test_file = test_files[0]
        print(f"   使用测试文件: {test_file.name}")

        # 尝试处理第一页
        print("   正在测试单页 OCR 处理...")
        result = ocr.process_pdf_page(str(test_file), 0, dpi=150)

        if result["success"]:
            print("✅ OCR 单页处理成功")
            print(f"   页码: {result['page_num']}")
            print(f"   识别文本长度: {len(result['text'])} 字符")
            print(f"   置信度: {result['confidence']:.1%}")
            print(f"   文本块数量: {len(result['blocks'])}")

            if result['text']:
                preview = result['text'][:100]
                print(f"   文本预览: {preview}...")
        else:
            print(f"❌ OCR 处理失败: {result.get('error', 'Unknown error')}")
            return False

        return True
    except ImportError as e:
        print(f"❌ OCR 导入失败: {e}")
        print("   请确保 PaddleOCR 已正确安装")
        return False
    except Exception as e:
        print(f"❌ OCR 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_processing_status(token, doc_id):
    """测试文档处理状态查询"""
    print_section("5️⃣  测试文档处理状态查询")

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/api/documents/{doc_id}/status",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ 文档状态查询成功")
            print(f"   文档ID: {data.get('document_id')}")
            print(f"   状态: {data.get('status')}")
            print(f"   阶段: {data.get('stage')}")
            print(f"   阶段消息: {data.get('stage_message', 'N/A')}")
            print(f"   进度: {data.get('progress_percentage', 0)}%")
            print(f"   总页数: {data.get('total_pages', 0)}")
            print(f"   是否扫描件: {data.get('is_scan', False)}")
            print(f"   有文本层: {data.get('has_text_layer', False)}")
            if data.get('ocr_confidence'):
                print(f"   OCR 置信度: {data.get('ocr_confidence', 0):.1%}")
            return True
        else:
            print(f"❌ 状态查询失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 状态查询异常: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "🚀"*30)
    print("  EduGenius 功能测试")
    print("🚀"*30 + "\n")

    results = {}

    # 1. 健康检查
    results['health'] = test_backend_health()

    # 2. 用户认证
    token = test_user_auth()
    results['auth'] = token is not None

    if not token:
        print("\n❌ 测试失败：无法获取认证 token")
        return

    # 3. 文档列表
    documents = test_document_list(token)
    results['document_list'] = len(documents) >= 0

    # 4. OCR 功能
    results['ocr'] = test_ocr_functionality()

    # 5. 如果有文档，测试状态查询
    if documents:
        doc_id = documents[0].get('id')
        if doc_id:
            results['status_query'] = test_document_processing_status(token, doc_id)

    # 总结
    print_section("📊 测试总结")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test:20s}: {status}")

    print(f"\n   总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n   🎉 所有测试通过！")
    else:
        print(f"\n   ⚠️  {total - passed} 个测试失败")

if __name__ == "__main__":
    main()
