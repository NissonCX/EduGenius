#!/usr/bin/env python3
"""
文档上传端到端测试
"""

import requests
import time
from pathlib import Path

API_BASE = "http://localhost:8000"
TEST_USER = {
    "username": "test_user",
    "password": "Test12345"
}

def login():
    response = requests.post(
        f"{API_BASE}/api/users/login",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def upload_document(token, pdf_path):
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        data = {'title': Path(pdf_path).stem}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_BASE}/api/documents/upload",
            headers=headers,
            files=files,
            data=data
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 上传失败: {response.status_code}")
            return None

def poll_document_status(token, doc_id, max_wait=180):
    start_time = time.time()
    last_progress = 0
    print("\n   处理进度:")
    while time.time() - start_time < max_wait:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/api/documents/{doc_id}/status",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            progress = data.get('progress_percentage', 0)
            status = data.get('status')
            stage = data.get('stage')
            message = data.get('stage_message', '')
            if progress > last_progress:
                print(f"   [{progress:3d}%] {stage} - {message}")
                last_progress = progress
            if status == 'completed':
                print(f"\n   ✅ 处理完成!")
                return data
            elif status == 'failed':
                print(f"\n   ❌ 处理失败: {message}")
                return data
        time.sleep(2)
    print(f"\n   ⏰ 超时")
    return None

def main():
    print("\n" + "="*60)
    print("  文档上传端到端测试")
    print("="*60 + "\n")
    print("1️⃣  用户登录...")
    token = login()
    if not token:
        print("   ❌ 登录失败")
        return
    print(f"   ✅ 登录成功")
    
    uploads_dir = Path("uploads")
    pdf_files = list(uploads_dir.glob("*.pdf"))
    if not pdf_files:
        print("   ⚠️  没有 PDF 文件")
        return
    test_file = pdf_files[0]
    print(f"\n2️⃣  上传文档: {test_file.name}")
    
    print("\n3️⃣  开始上传...")
    upload_result = upload_document(token, str(test_file))
    if not upload_result:
        return
    doc_id = upload_result.get('document_id')
    print(f"   ✅ 上传成功，文档ID: {doc_id}")
    
    print("\n4️⃣  等待处理...")
    final_status = poll_document_status(token, doc_id)
    if final_status and final_status.get('status') == 'completed':
        print("\n5️⃣  结果:")
        print(f"   总页数: {final_status.get('total_pages', 0)}")
        print(f"   是否扫描件: {final_status.get('is_scan', False)}")
        print(f"   有文本层: {final_status.get('has_text_layer', False)}")
        if final_status.get('is_scan'):
            print(f"   OCR 置信度: {final_status.get('ocr_confidence', 0):.1%}")
    print("\n" + "="*60)
    print("  ✅ 测试完成!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
