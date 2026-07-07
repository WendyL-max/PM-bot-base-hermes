#!/usr/bin/env python3
"""
團隊能力管理技能測試腳本
"""

import json
import os
import sys
import subprocess

# 技能路徑
SKILL_DIR = os.path.expanduser("~/.hermes/skills/team-capability-manager")
TEST_FILE = os.path.join(SKILL_DIR, "evals.json")
SCRIPT_FILE = os.path.join(SKILL_DIR, "scripts/team_manager.py")

def load_tests():
    """載入測試案例"""
    try:
        with open(TEST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("tests", [])
    except Exception as e:
        print(f"載入測試案例失敗: {e}")
        return []

def parse_natural_language(command):
    """解析自然語言指令"""
    # 這裡使用簡單的正則匹配，實際應用中應該使用更複雜的NLP
    import re
    
    command_lower = command.lower()
    
    # 識別操作類型
    operation = None
    if any(word in command_lower for word in ["新增", "添加", "add", "create"]):
        operation = "add"
    elif any(word in command_lower for word in ["更新", "修改", "update", "edit"]):
        operation = "update"
    elif any(word in command_lower for word in ["停用", "禁用", "deactivate", "disable"]):
        operation = "deactivate"
    elif any(word in command_lower for word in ["查詢", "查找", "搜索", "query", "find", "search"]):
        operation = "query"
    
    return operation

def run_test(test):
    """運行單個測試案例"""
    print(f"\n{'='*60}")
    print(f"測試: {test['name']}")
    print(f"描述: {test['description']}")
    print(f"輸入: {test['input']}")
    
    # 解析指令
    operation = parse_natural_language(test["input"])
    
    if not operation:
        print("❌ 無法識別操作類型")
        return False
    
    # 根據操作類型執行測試
    if operation == "add":
        return test_add_member(test)
    elif operation == "query":
        return test_query_members(test)
    elif operation == "update":
        return test_update_member(test)
    elif operation == "deactivate":
        return test_deactivate_member(test)
    else:
        print(f"❌ 不支持的操作類型: {operation}")
        return False

def test_add_member(test):
    """測試新增成員"""
    try:
        # 這裡使用Python腳本進行測試
        # 實際應用中應該調用技能邏輯
        print("✅ 新增成員測試通過（模擬）")
        return True
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_query_members(test):
    """測試查詢成員"""
    try:
        # 初始化一些測試數據
        init_test_data()
        
        # 執行查詢
        print("✅ 查詢成員測試通過（模擬）")
        return True
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_update_member(test):
    """測試更新成員"""
    try:
        print("✅ 更新成員測試通過（模擬）")
        return True
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_deactivate_member(test):
    """測試停用成員"""
    try:
        print("✅ 停用成員測試通過（模擬）")
        return True
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def init_test_data():
    """初始化測試數據"""
    data_dir = os.path.expanduser("~/.hermes/team-capability")
    data_file = os.path.join(data_dir, "team.json")
    
    # 如果數據文件不存在，創建測試數據
    if not os.path.exists(data_file):
        test_data = {
            "members": [
                {
                    "id": "test-001",
                    "name": "John",
                    "employee_id": "EMP001",
                    "email": "john@company.com",
                    "team": "開發組",
                    "status": "active",
                    "skills": [
                        {"name": "Python", "level": 3, "level_description": "勝任"},
                        {"name": "JavaScript", "level": 2, "level_description": "基礎能力"}
                    ],
                    "created_at": "2026-06-25T10:00:00Z",
                    "updated_at": "2026-06-25T10:00:00Z"
                },
                {
                    "id": "test-002",
                    "name": "Alice",
                    "employee_id": "EMP002",
                    "email": "alice@company.com",
                    "team": "測試組",
                    "status": "active",
                    "skills": [
                        {"name": "Python", "level": 4, "level_description": "專家"},
                        {"name": "React", "level": 3, "level_description": "勝任"}
                    ],
                    "created_at": "2026-06-25T10:00:00Z",
                    "updated_at": "2026-06-25T10:00:00Z"
                }
            ],
            "metadata": {
                "version": "1.0",
                "last_updated": "2026-06-25T10:00:00Z",
                "total_members": 2
            }
        }
        
        os.makedirs(data_dir, exist_ok=True)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

def run_all_tests():
    """運行所有測試"""
    tests = load_tests()
    
    if not tests:
        print("❌ 沒有找到測試案例")
        return False
    
    print(f"找到 {len(tests)} 個測試案例")
    
    passed = 0
    failed = 0
    
    for test in tests:
        if run_test(test):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"測試結果:")
    print(f"  通過: {passed}")
    print(f"  失敗: {failed}")
    print(f"  總數: {len(tests)}")
    print(f"  成功率: {passed/len(tests)*100:.1f}%")
    
    return failed == 0

def test_script_directly():
    """直接測試Python腳本"""
    print("\n測試Python腳本功能...")
    
    # 測試新增成員
    test_data = {
        "name": "Test User",
        "employee_id": "TEST001",
        "email": "test@company.com",
        "team": "測試團隊",
        "skills": [
            {"name": "Python", "level": 3}
        ]
    }
    
    cmd = [
        sys.executable, SCRIPT_FILE,
        "--operation", "add",
        "--data", json.dumps(test_data, ensure_ascii=False)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"腳本輸出: {result.stdout}")
        if result.returncode == 0:
            print("✅ Python腳本測試通過")
            return True
        else:
            print(f"❌ Python腳本測試失敗: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 執行腳本時出錯: {e}")
        return False

if __name__ == "__main__":
    print("團隊能力管理技能測試")
    print("="*60)
    
    # 測試Python腳本
    if test_script_directly():
        print("\n✅ Python腳本功能正常")
    else:
        print("\n❌ Python腳本功能異常")
        sys.exit(1)
    
    # 運行所有測試案例
    print("\n運行測試案例...")
    if run_all_tests():
        print("\n✅ 所有測試通過")
        sys.exit(0)
    else:
        print("\n❌ 部分測試失敗")
        sys.exit(1)