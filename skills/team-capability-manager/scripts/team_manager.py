#!/usr/bin/env python3
"""
Team Capability Manager - 團隊能力管理核心腳本
處理團隊成員的新增、更新、查詢等操作
"""

import json
import os
import uuid
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import sys

# 配置文件路徑
DATA_DIR = os.path.expanduser("~/.hermes/team-capability")
DATA_FILE = os.path.join(DATA_DIR, "team.json")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

# 技能等級描述
LEVEL_DESCRIPTIONS = {
    1: "初學者（了解基礎概念）",
    2: "基礎能力（可在監督下完成任務）",
    3: "勝任（可獨立完成任務）",
    4: "專家（可指導他人）",
    5: "大師（可制定標準）"
}

class TeamManager:
    def __init__(self):
        """初始化團隊管理器"""
        self.ensure_data_dir()
        self.data = self.load_data()
    
    def ensure_data_dir(self):
        """確保數據目錄存在"""
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
    
    def load_data(self) -> Dict[str, Any]:
        """載入團隊數據"""
        if not os.path.exists(DATA_FILE):
            # 創建初始數據結構
            initial_data = {
                "members": [],
                "metadata": {
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "total_members":164
                }
            }
            self.save_data(initial_data)
            return initial_data
        
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"錯誤載入數據: {e}", file=sys.stderr)
            # 返回空數據結構
            return {
                "members": [],
                "metadata": {
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "total_members": 0
                }
            }
    
    def save_data(self, data: Dict[str, Any]):
        """儲存團隊數據"""
        # 創建備份
        self.create_backup()
        
        # 更新元數據
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        data["metadata"]["total_members"] = len(data["members"])
        
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.data = data
            return True
        except Exception as e:
            print(f"錯誤儲存數據: {e}", file=sys.stderr)
            return False
    
    def create_backup(self):
        """創建數據備份"""
        if os.path.exists(DATA_FILE):
            backup_file = os.path.join(
                BACKUP_DIR,
                f"team_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            except Exception as e:
                print(f"備份失敗: {e}", file=sys.stderr)
    
    def generate_trace_id(self) -> str:
        """生成追蹤ID"""
        return f"trace_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def validate_member_data(self, data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, str]:
        """
        驗證成員數據
        
        Args:
            data: 成員數據
            is_update: 是否為更新操作（某些欄位在更新時可不提供）
        
        Returns:
            (是否有效, 錯誤訊息)
        """
        # 必填欄位檢查
        required_fields = ["name", "employee_id", "email", "team"]
        
        if not is_update:
            # 新增操作：所有必填欄位都需要
            for field in required_fields:
                if field not in data or not str(data[field]).strip():
                    return False, f"validation_error: 缺少必填欄位: {field}"
        
        else:
            # 更新操作：至少提供一個可更新欄位
            updatable_fields = required_fields + ["status", "skills"]
            has_updates = any(field in data for field in updatable_fields)
            if not has_updates:
                return False, "validation_error: 未提供任何可更新欄位"
        
        # 電子郵件格式檢查
        if "email" in data and data["email"]:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data["email"]):
                return False, "validation_error: 電子郵件格式不正確"
        
        # 技能等級檢查
        if "skills" in data and data["skills"]:
            for skill in data["skills"]:
                if "name" not in skill or not skill["name"].strip():
                    return False, "validation_error: 技能名稱不能為空"
                if "level" in skill:
                    level = skill["level"]
                    if not isinstance(level, int) or level < 1 or level > 5:
                        return False, f"validation_error: 技能等級必須是1-5的整數，收到: {level}"
        
        # 狀態檢查
        if "status" in data and data["status"]:
            valid_statuses = ["active", "inactive", "on_leave"]
            if data["status"] not in valid_statuses:
                return False, f"validation_error: 狀態必須是 {', '.join(valid_statuses)}"
        
        return True, ""
    
    def find_member(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        根據識別符查找成員
        
        Args:
            identifier: 可以是name, employee_id, 或email
        
        Returns:
            成員資料或None
        """
        for member in self.data["members"]:
            if (member["name"] == identifier or 
                member["employee_id"] == identifier or 
                member["email"] == identifier):
                return member
        return None
    
    def find_member_by_id(self, member_id: str) -> Optional[Dict[str, Any]]:
        """根據成員ID查找成員"""
        for member in self.data["members"]:
            if member["id"] == member_id:
                return member
        return None
    
    def add_member(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        新增成員
        
        Args:
            member_data: 成員數據
        
        Returns:
            操作結果
        """
        trace_id = self.generate_trace_id()
        
        try:
            # 驗證數據
            is_valid, error_msg = self.validate_member_data(member_data, is_update=False)
            if not is_valid:
                return {
                    "status": "failed",
                    "operation": "add_member",
                    "error": error_msg,
                    "trace_id": trace_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 檢查唯一性
            for field in ["employee_id", "email"]:
                if field in member_data:
                    existing = self.find_member(member_data[field])
                    if existing:
                        return {
                            "status": "failed",
                            "operation": "add_member",
                            "error": f"validation_error: {field} '{member_data[field]}' 已存在",
                            "trace_id": trace_id,
                            "timestamp": datetime.now().isoformat()
                        }
            
            # 創建新成員
            new_member = {
                "id": str(uuid.uuid4()),
                "name": member_data["name"],
                "employee_id": member_data["employee_id"],
                "email": member_data["email"],
                "team": member_data["team"],
                "status": member_data.get("status", "active"),
                "skills": self._process_skills(member_data.get("skills", [])),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 添加到數據
            self.data["members"].append(new_member)
            
            # 儲存數據
            if self.save_data(self.data):
                return {
                    "status": "success",
                    "operation": "add_member",
                    "data": {
                        "member_id": new_member["id"],
                        "name": new_member["name"],
                        "employee_id": new_member["employee_id"],
                        "email": new_member["email"],
                        "team": new_member["team"],
                        "status": new_member["status"]
                    },
                    "trace_id": trace_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "operation": "add_member",
                    "error": "儲存數據時發生錯誤",
                    "trace_id": trace_id,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "operation": "add_member",
                "error": f"系統錯誤: {str(e)}",
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def update_member(self, identifier: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新成員
        
        Args:
            identifier: 成員識別符（name, employee_id, 或email）
            updates: 更新數據
        
        Returns:
            操作結果
        """
        trace_id = self.generate_trace_id()
        
        try:
            # 查找成員
            member = self.find_member(identifier)
            if not member:
                return {
                    "status": "failed",
                    "operation": "update_member",
                    "error": f"找不到成員: {identifier}",
                    "trace_id": trace_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 驗證更新數據
            is_valid, error_msg = self.validate_member_data(updates, is_update=True)
            if not is_valid:
                return {
                    "status": "failed",
                    "operation": "update_member",
                    "error": error_msg,
                    "trace_id": trace_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 檢查唯一性（除了當前成員）
            for field in ["employee_id", "email"]:
                if field in updates:
                    existing = self.find_member(updates[field])
                    if existing and existing["id"] != member["id"]:
                        return {
                            "status": "failed",
                            "operation": "update_member",
                            "error": f"validation_error: {field} '{updates[field]}' 已被其他成員使用",
                            "trace_id": trace_id,
                            "timestamp": datetime.now().isoformat()
                        }
            
            # 應用更新
            for key, value in updates.items():
                if key == "skills":
                    member["skills"] = self._process_skills(value)
                elif key in ["name", "employee_id", "email", "team", "status"]:
                    member[key] = value
            
            member["updated_at"] = datetime.now().isoformat()
            
            # 儲存數據
            if self.save_data(self.data):
                return {
                    "status": "success",
                    "operation": "update_member",
                    "data": {
                        "member_id": member["id"],
                        "updated_fields": list(updates.keys())
                    },
                    "trace_id": trace_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "operation": "update_member",
                    "error": "儲存數據時發生錯誤",
                    "trace_id": trace_id,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "operation": "update_member",
                "error": f"系統錯誤: {str(e)}",
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def deactivate_member(self, identifier: str) -> Dict[str, Any]:
        """
        停用成員
        
        Args:
            identifier: 成員識別符
        
        Returns:
            操作結果
        """
        return self.update_member(identifier, {"status": "inactive"})
    
    def query_members(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        查詢成員
        
        Args:
            filters: 過濾條件
        
        Returns:
            查詢結果
        """
        trace_id = self.generate_trace_id()
        
        try:
            members = self.data["members"]
            
            # 應用過濾條件
            filtered_members = []
            for member in members:
                include = True
                
                # 技能過濾
                if "skill_name" in filters:
                    skill_name = filters["skill_name"].lower()
                    has_skill = any(
                        skill["name"].lower() == skill_name 
                        for skill in member.get("skills", [])
                    )
                    if not has_skill:
                        include = False
                
                # 技能等級過濾
                if "min_skill_level" in filters and "skill_name" in filters:
                    min_level = filters["min_skill_level"]
                    skill_name = filters["skill_name"].lower()
                    member_skill_level = None
                    
                    for skill in member.get("skills", []):
                        if skill["name"].lower() == skill_name:
                            member_skill_level = skill["level"]
                            break
                    
                    if member_skill_level is None or member_skill_level < min_level:
                        include = False
                
                # 狀態過濾
                if "status" in filters:
                    if member["status"] != filters["status"]:
                        include = False
                elif filters.get("exclude_inactive", False):
                    # 預設排除停用成員
                    if member["status"] == "inactive":
                        include = False
                
                # 團隊過濾
                if "team" in filters:
                    if member["team"] != filters["team"]:
                        include = False
                
                # 關鍵字搜尋
                if "search" in filters:
                    search_term = filters["search"].lower()
                    searchable_fields = [
                        member["name"].lower(),
                        member["employee_id"].lower(),
                        member["email"].lower(),
                        member["team"].lower()
                    ]
                    # 搜尋技能
                    for skill in member.get("skills", []):
                        searchable_fields.append(skill["name"].lower())
                    
                    if not any(search_term in field for field in searchable_fields):
                        include = False
                
                if include:
                    filtered_members.append(member)
            
            return {
                "status": "success",
                "operation": "query_members",
                "data": {
                    "count": len(filtered_members),
                    "filters": filters,
                    "members": filtered_members
                },
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "operation": "query_members",
                "error": f"系統錯誤: {str(e)}",
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_skills(self, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """處理技能數據，添加等級描述"""
        processed = []
        for skill in skills:
            processed_skill = skill.copy()
            level = skill.get("level", 1)
            processed_skill["level_description"] = LEVEL_DESCRIPTIONS.get(level, "未知等級")
            processed.append(processed_skill)
        return processed
    
    def get_all_members(self) -> Dict[str, Any]:
        """獲取所有成員（用於測試）"""
        return {
            "status": "success",
            "operation": "get_all_members",
            "data": {
                "count": len(self.data["members"]),
                "members": self.data["members"]
            },
            "trace_id": self.generate_trace_id(),
            "timestamp": datetime.now().isoformat()
        }

def parse_natural_language(command: str) -> Dict[str, Any]:
    """
    解析自然語言指令
    
    Args:
        command: 自然語言指令
    
    Returns:
        解析後的指令結構
    """
    command_lower = command.lower()
    
    # 識別操作類型
    operation = None
    
    # 新增操作關鍵詞
    add_keywords = ["新增", "添加", "add", "create", "創建", "加入", "註冊", "新組員", "新成員", "新員工", "new member", "register", "new employee", "new team member"]
    if any(word in command_lower for word in add_keywords):
        operation = "add_member"
    else:
        # 更新操作關鍵詞
        update_keywords = ["更新", "修改", "update", "edit", "變更", "編輯", "改", "調整", "modify", "change", "adjust"]
        if any(word in command_lower for word in update_keywords):
            operation = "update_member"
        else:
            # 停用操作關鍵詞
            deactivate_keywords = ["停用", "禁用", "deactivate", "disable", "離職", "設為inactive", "設為離職", "設為非活躍", "remove", "terminate", "set inactive"]
            if any(word in command_lower for word in deactivate_keywords):
                operation = "deactivate_member"
            else:
                # 查詢操作關鍵詞
                query_keywords = ["查詢", "查找", "搜索", "query", "find", "search", "找", "誰", "誰會", "誰有", "誰懂", "誰擅長", "who", "who can", "who knows", "who has", "who is good at", "who is able to"]
                if any(word in command_lower for word in query_keywords):
                    operation = "query_members"
    
    # 如果沒有明確操作類型，嘗試根據上下文推斷
    if not operation:
        # 檢查是否包含技能查詢
        if any(word in command_lower for word in ["技能", "會", "懂", "擅長", "經驗"]):
            operation = "query_members"
        # 檢查是否包含成員資訊
        elif any(word in command_lower for word in ["組員", "成員", "員工", "團隊"]):
            # 如果有冒號或等號，可能是更新
            if "：" in command or ":" in command or "為" in command:
                operation = "update_member"
            else:
                operation = "query_members"
    
    # 提取參數
    params = {}
    
    # 提取姓名（多種模式）
    name_patterns = [
        r'[：:]\s*([^，,\s]+)',  # 標準格式
        r'新增\s*([^，,]+)',      # "新增張三"
        r'添加\s*([^，,]+)',      # "添加李四"
        r'創建\s*([^，,]+)',      # "創建王五"
        r'組員\s*([^，,]+)',      # "組員趙六"
        r'成員\s*([^，,]+)',      # "成員錢七"
        r'員工\s*([^，,]+)',      # "員工孫八"
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, command)
        if name_match:
            params["name"] = name_match.group(1).strip()
            break
    
    # 提取員工編號
    id_patterns = [
        r'員工編號[：:]\s*([^，,\s]+)',
        r'編號[：:]\s*([^，,\s]+)',
        r'員工號[：:]\s*([^，,\s]+)',
        r'工號[：:]\s*([^，,\s]+)',
        r'emp[：:]\s*([^，,\s]+)',
        r'employee_id[：:]\s*([^，,\s]+)',
        r'employee id[：:]\s*([^，,\s]+)',
        r'emp id[：:]\s*([^，,\s]+)',
        r'employee[：:]\s*([^，,\s]+)',
    ]
    
    for pattern in id_patterns:
        id_match = re.search(pattern, command, re.IGNORECASE)
        if id_match:
            params["employee_id"] = id_match.group(1).strip()
            break
    
    # 提取電子郵件
    email_patterns = [
        r'email[：:]\s*([^，,\s@]+@[^，,\s@]+\.[^，,\s@]+)',
        r'郵箱[：:]\s*([^，,\s@]+@[^，,\s@]+\.[^，,\s@]+)',
        r'電子郵件[：:]\s*([^，,\s@]+@[^，,\s@]+\.[^，,\s@]+)',
        r'電郵[：:]\s*([^，,\s@]+@[^，,\s@]+\.[^，,\s@]+)',
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # 通用郵箱格式
        r'mail[：:]\s*([^，,\s@]+@[^，,\s@]+\.[^，,\s@]+)',
    ]
    
    for pattern in email_patterns:
        email_match = re.search(pattern, command, re.IGNORECASE)
        if email_match:
            params["email"] = email_match.group(1).strip()
            break
    
    # 提取團隊
    team_patterns = [
        r'團隊[：:]\s*([^，,\s]+)',
        r'team[：:]\s*([^，,\s]+)',
        r'部門[：:]\s*([^，,\s]+)',
        r'組別[：:]\s*([^，,\s]+)',
        r'小組[：:]\s*([^，,\s]+)',
        r'部門為\s*([^，,\s]+)',
        r'團隊為\s*([^，,\s]+)',
        r'group[：:]\s*([^，,\s]+)',
        r'department[：:]\s*([^，,\s]+)',
    ]
    
    for pattern in team_patterns:
        team_match = re.search(pattern, command)
        if team_match:
            params["team"] = team_match.group(1).strip()
            break
    
    # 提取技能
    skills_patterns = [
        r'技能[：:]\s*([^，,]+)',
        r'技能為\s*([^，,]+)',
        r'會\s*([^，,]+)',
        r'懂\s*([^，,]+)',
        r'擅長\s*([^，,]+)',
        r'有\s*([^，,]+)\s*經驗',
        r'有\s*([^，,]+)\s*技能',
        r'skills[：:]\s*([^，,]+)',
        r'skill[：:]\s*([^，,]+)',
        r'can do\s*([^，,]+)',
        r'knows\s*([^，,]+)',
        r'good at\s*([^，,]+)',
    ]
    
    for pattern in skills_patterns:
        skills_match = re.search(pattern, command)
        if skills_match:
            skills_str = skills_match.group(1)
            skills = []
            
            # 多種技能格式解析
            # 1. Python(L3), JavaScript(L2)
            skill_pattern1 = r'([^(]+)\(L?(\\d)\)'
            # 2. Python L3, JavaScript L2
            skill_pattern2 = r'([^L\\d]+)\\s*L?(\\d)'
            # 3. Python(3), JavaScript(2)
            skill_pattern3 = r'([^(]+)\\((\\d)\\)'
            
            for match in re.finditer(skill_pattern1, skills_str):
                skill_name = match.group(1).strip()
                skill_level = int(match.group(2))
                skills.append({"name": skill_name, "level": skill_level})
            
            for match in re.finditer(skill_pattern2, skills_str):
                skill_name = match.group(1).strip()
                skill_level = int(match.group(2))
                skills.append({"name": skill_name, "level": skill_level})
            
            for match in re.finditer(skill_pattern3, skills_str):
                skill_name = match.group(1).strip()
                skill_level = int(match.group(2))
                skills.append({"name": skill_name, "level": skill_level})
            
            # 如果沒有等級，預設為L3
            if not skills and skills_str.strip():
                # 嘗試用逗號或空格分割技能
                skill_names = re.split(r'[，,\\s]+', skills_str)
                for skill_name in skill_names:
                    if skill_name.strip():
                        skills.append({"name": skill_name.strip(), "level": 3})
            
            if skills:
                params["skills"] = skills
            break
    
    # 提取狀態
    status_patterns = [
        r'狀態為\s*([^，,\s]+)',
        r'狀態[：:]\s*([^，,\s]+)',
        r'設為\s*([^，,\s]+)',
        r'status[：:]\s*([^，,\s]+)',
        r'set to\s*([^，,\s]+)',
    ]
    
    for pattern in status_patterns:
        status_match = re.search(pattern, command, re.IGNORECASE)
        if status_match:
            status = status_match.group(1).strip().lower()
            # 狀態映射
            status_map = {
                "active": "active",
                "活躍": "active",
                "啟用": "active",
                "在職": "active",
                "inactive": "inactive",
                "非活躍": "inactive",
                "停用": "inactive",
                "禁用": "inactive",
                "離職": "inactive",
                "on_leave": "on_leave",
                "休假": "on_leave",
                "請假": "on_leave",
            }
            params["status"] = status_map.get(status, status)
            break
    
    # 查詢特定條件
    if operation == "query_members":
        filters = {}
        
        # 技能查詢
        if "技能" in command_lower or "會" in command_lower or "懂" in command_lower:
            # 提取技能名稱
            skill_query_patterns = [
                r'有\s*([^，,\\s]+)\\s*技能',
                r'會\s*([^，,\\s]+)',
                r'懂\s*([^，,\\s]+)',
                r'擅長\s*([^，,\\s]+)',
                r'([^，,\\s]+)\\s*技能',
            ]
            
            for pattern in skill_query_patterns:
                skill_match = re.search(pattern, command)
                if skill_match:
                    skill_name = skill_match.group(1).strip()
                    filters["skill_name"] = skill_name
                    break
        
        # 技能等級查詢
        if any(word in command_lower for word in ["l1", "l2", "l3", "l4", "l5", "等級", "級別", "level", "level 1", "level 2", "level 3", "level 4", "level 5"]):
            for pattern in level_patterns:
                level_match = re.search(pattern, command, re.IGNORECASE)
                if level_match:
                    level = int(level_match.group(1))
                    filters["min_skill_level"] = level
                    break
        # 團隊查詢
        if "團隊" in command_lower or "部門" in command_lower or "組" in command_lower:
            for pattern in team_patterns:
                team_match = re.search(pattern, command)
                if team_match:
                    filters["team"] = team_match.group(1).strip()
                    break
        
        # 狀態查詢
        if "狀態" in command_lower:
            for pattern in status_patterns:
                status_match = re.search(pattern, command, re.IGNORECASE)
                if status_match:
                    status = status_match.group(1).strip().lower()
                    status_map = {
                        "active": "active",
                        "活躍": "active",
                        "啟用": "active",
                        "在職": "active",
                        "inactive": "inactive",
                        "非活躍": "inactive",
                        "停用": "inactive",
                        "禁用": "inactive",
                        "離職": "inactive",
                        "on_leave": "on_leave",
                        "休假": "on_leave",
                        "請假": "on_leave",
                    }
                    filters["status"] = status_map.get(status, status)
                    break
        
        # 關鍵字搜尋
        if "找" in command_lower or "搜索" in command_lower or "查" in command_lower:
            # 提取搜尋關鍵字
            search_patterns = [
                r'找\s*([^，,\\s]+)',
                r'搜索\s*([^，,\\s]+)',
                r'查\s*([^，,\\s]+)',
                r'查詢\s*([^，,\\s]+)',
            ]
            
            for pattern in search_patterns:
                search_match = re.search(pattern, command)
                if search_match:
                    filters["search"] = search_match.group(1).strip()
                    break
        
        if filters:
            params["filters"] = filters
    
    return {
        "operation": operation,
        "params": params
    }

def main():
    """命令行入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(description="團隊能力管理器")
    parser.add_argument("--operation", choices=["add", "update", "deactivate", "query", "list"], 
                       help="操作類型")
    parser.add_argument("--identifier", help="成員識別符（姓名、員工編號或郵箱）")
    parser.add_argument("--data", help="JSON格式的成員數據")
    parser.add_argument("--filters", help="JSON格式的查詢過濾條件")
    
    args = parser.parse_args()
    
    manager = TeamManager()
    
    if args.operation == "add" and args.data:
        data = json.loads(args.data)
        result = manager.add_member(data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.operation == "update" and args.identifier and args.data:
        data = json.loads(args.data)
        result = manager.update_member(args.identifier, data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.operation == "deactivate" and args.identifier:
        result = manager.deactivate_member(args.identifier)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.operation == "query" and args.filters:
        filters = json.loads(args.filters)
        result = manager.query_members(filters)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.operation == "list":
        result = manager.get_all_members()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print("錯誤: 無效的參數組合", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()