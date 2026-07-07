---
name: team-capability-manager
description: 管理團隊能力檔案，包括新增/更新/停用組員、管理技能熟練度（L1-L5）、查詢符合條件的成員。當用戶在WhatsApp消息中提及@TeamCapability或有明確的團隊能力管理需求時使用此技能。技能會解析自然語言指令，處理團隊成員資料，並返回結構化JSON結果。包含完整的驗證和錯誤處理機制。
---

# Team Capability Manager

管理團隊能力檔案的技能，用於維護團隊成員的技能、熟練度、狀態等資訊，並提供查詢功能供任務分工推薦使用。

## 何時使用此技能

當用戶需要：
- 新增、更新或停用團隊成員
- 管理成員的技能與熟練度（L1-L5等級）
- 查詢符合特定條件的成員（按技能、熟練度、狀態）
- 在WhatsApp消息中提及@TeamCapability
- 需要結構化的團隊能力管理功能
- 進行團隊人力資源盤點或技能矩陣管理

觸發關鍵詞：
- 團隊能力、團隊管理、組員管理、成員管理、團隊成員管理、人力資源管理
- team capability, team management, member management, team member management, human resource management
- 技能管理、技能庫、能力檔案、技能矩陣、能力盤點、人才庫
- skill management, skill library, capability profile, skill matrix, capability inventory, talent pool
- 新增組員、添加成員、更新成員、停用成員、禁用成員、離職成員
- add team member, add member, update member, deactivate member, disable member, remove member
- 查詢技能、找有...技能的成員、誰會...、誰懂...、誰擅長...
- query skill, find members with...skill, who can..., who knows..., who is good at...
- @TeamCapability、@團隊能力、@成員管理、@能力管理、@HR
- @TeamCapability、@teamcapability、@HR、@hr
- 團隊成員、員工技能、人力資源、人才庫、技能目錄、能力目錄
- team members, employee skills, human resources, talent pool, skill directory, capability directory
- 技能等級、熟練度、L1-L5、能力等級、專業等級
- skill level, proficiency, L1-L5, capability level, professional level
- 成員查詢、技能查詢、能力查詢、人才搜尋、人力盤點
- member query, skill query, capability query, talent search, human resource inventory
- 項目分工、任務分配、找合適人選、誰適合做
- project assignment, task allocation, find suitable candidate, who is suitable for
- 團隊結構、組織架構、部門人員、小組成員
- team structure, organizational structure, department personnel, group members
- 團隊盤點、人力盤點、技能盤點、能力盤點
- team inventory, human resource inventory, skill inventory, capability inventory
- 員工技能、人員技能、成員技能、專業技能
- employee skill, personnel skill, member skill, professional skill
- 熟練度管理、技能評估、能力評估、績效評估
- proficiency management, skill assessment, capability assessment, performance evaluation
- 人才搜尋、人員搜尋、技能搜尋、能力搜尋
- talent search, personnel search, skill search, capability search
- 團隊組織、組織管理、人員管理、員工管理
- team organization, organizational management, personnel management, employee management
- 能力目錄、技能目錄、人才目錄、資源目錄
- capability directory, skill directory, talent directory, resource directory
- 技能矩陣、能力矩陣、人才矩陣、資源矩陣
- skill matrix, capability matrix, talent matrix, resource matrix
- 項目分工、任務分配、人員配置、人力配置
- project assignment, task allocation, personnel deployment, human resource allocation
- 誰會、誰懂、誰擅長、誰有經驗、誰可以
- who can, who knows, who is good at, who has experience, who is able to
- 團隊人力、人力資源、人才資源、技能資源
- team workforce, human resources, talent resources, skill resources

觸發模式（正則表達式）：
- `(新增|添加|創建|加入|註冊|新|add|create|register|new)(組員|成員|員工|團隊成員|團隊人力|team member|member|employee|staff)`
- `(更新|修改|編輯|變更|改|調整|update|modify|edit|change|adjust)(組員|成員|技能|狀態|團隊|email|郵箱|員工編號|工號|team member|member|skill|status|team|employee id|emp id)`
- `(停用|禁用|離職|設為inactive|設為離職|設為非活躍|移除|deactivate|disable|remove|terminate|set inactive)(組員|成員|員工|team member|member|employee)`
- `(查詢|查找|搜索|找|搜|查|誰|查詢|query|search|find|who|who can|who knows)(有|會|懂|擅長|有...技能|有...經驗|適合|適合做|with|has|knows|can|good at|suitable for)`
- `(團隊|組|部門|小組|team|group|department|unit)(成員|能力|技能|盤點|管理|結構|人力|members|capability|skills|inventory|management|structure|workforce)`
- `(技能|能力|專業|skill|capability|professional)(等級|矩陣|庫|目錄|管理|盤點|評估|level|matrix|library|directory|management|inventory|assessment)`
- `@(TeamCapability|團隊能力|成員管理|能力管理|HR|人力資源|teamcapability|hr|human resources)`
- `(項目分工|任務分配|找人|合適人選|誰能做|誰負責|project assignment|task allocation|find suitable candidate|who can do|who is responsible)`
- `(團隊盤點|人力盤點|技能盤點|能力盤點|team inventory|human resource inventory|skill inventory|capability inventory)`
- `(員工|人員|成員|employee|personnel|member)(技能|能力|專業|skill|capability|professional)`
- `(熟練度|技能等級|能力等級|專業等級|proficiency|skill level|capability level|professional level)(管理|評估|評級|management|assessment|rating)`
- `(人才|人員|成員|talent|personnel|member)(搜尋|查找|搜索|找|search|find|lookup)`
- `(團隊組織|組織管理|人員管理|員工管理|team organization|organizational management|personnel management|employee management)`
- `(能力目錄|技能目錄|人才目錄|資源目錄|capability directory|skill directory|talent directory|resource directory)`
- `(技能矩陣|能力矩陣|人才矩陣|資源矩陣|skill matrix|capability matrix|talent matrix|resource matrix)`
- `(項目分工|任務分配|人員配置|人力配置|project assignment|task allocation|personnel deployment|human resource allocation)`
- `(誰會|誰懂|誰擅長|誰有經驗|誰可以|who can|who knows|who is good at|who has experience|who is able to)`
- `(團隊人力|人力資源|人才資源|技能資源|team workforce|human resources|talent resources|skill resources)`

觸發優先級：
1. 高優先級：明確包含@TeamCapability或@HR等提及
2. 中優先級：明確的操作指令（新增/更新/停用/查詢）+ 組員/成員/員工
3. 中優先級：項目分工、任務分配、找合適人選等實際應用場景
4. 低優先級：一般性查詢（誰會、誰懂、技能查詢）

## 數據結構

團隊資料儲存在 `~/.hermes/team-capability/team.json`，結構如下：

```json
{
  "members": [
    {
      "id": "unique-uuid",
      "name": "成員姓名",
      "employee_id": "員工編號",
      "email": "電子郵件",
      "team": "所屬團隊",
      "status": "active/inactive/on_leave",
      "skills": [
        {
          "name": "技能名稱",
          "level": 3,
          "level_description": "勝任（可獨立完成任務）"
        }
      ],
      "created_at": "2026-06-25T10:00:00Z",
      "updated_at": "2026-06-25T10:00:00Z"
    }
  ],
  "metadata": {
    "version": "1.0",
    "last_updated": "2026-06-25T10:00:00Z",
    "total_members": 1
  }
}
```

## 技能熟練度等級定義

- **L1 (1)**: 初學者（了解基礎概念）
- **L2 (2)**: 基礎能力（可在監督下完成任務）
- **L3 (3)**: 勝任（可獨立完成任務）
- **L4 (4)**: 專家（可指導他人）
- **L5 (5)**: 大師（可制定標準）

## 必填欄位

新增成員時必須提供：
- `name`: 成員姓名
- `employee_id`: 員工編號
- `email`: 電子郵件
- `team`: 所屬團隊

## 操作指令

技能會解析自然語言指令，支援以下操作：

### 1. 新增成員
```
指令範例：
- "新增組員：John，員工編號：EMP001，email：john@company.com，團隊：開發組"
- "新增成員：Alice，編號：EMP002，郵箱：alice@company.com，團隊：測試組，技能：Python(L3), JavaScript(L2)"
- "添加團隊成員：Bob，員工號：EMP003，電郵：bob@company.com，部門：產品組，技能：React(L4)"
- "創建新組員：Charlie，編號：EMP004，團隊：運維組，email：charlie@company.com"
- "add team member: John, employee id: EMP001, email: john@company.com, team: development"
- "create new member: Alice, emp id: EMP002, email: alice@company.com, team: testing, skills: Python(L3), JavaScript(L2)"
```

### 2. 更新成員資訊
```
指令範例：
- "更新John的技能：新增React(L4)"
- "更新EMP001的狀態為on_leave"
- "更新Alice的email為alice.new@company.com"
- "修改Bob的團隊為架構組"
- "更新Charlie的技能等級：Python(L4)"
- "update John's skills: add React(L4)"
- "modify EMP001 status to inactive"
- "edit Alice team to architecture"
```

### 3. 停用成員
```
指令範例：
- "停用John"
- "將EMP002設為inactive"
- "禁用Alice"
- "停用員工編號EMP003"
- "將Bob設為離職狀態"
- "deactivate John"
- "disable EMP002"
- "remove Alice from team"
- "set Bob status to inactive"
```

### 4. 查詢成員
```
指令範例：
- "查詢所有Python L3以上的成員"
- "找有React技能且狀態為active的成員"
- "查詢開發組所有成員"
- "找技能包含JavaScript的成員"
- "誰會Python？"
- "找有Docker經驗的工程師"
- "我需要一個React專家"
- "查詢L4以上的前端工程師"
- "找團隊為測試組且狀態為active的成員"
- "誰有AWS經驗？"
- "query all members with Python L3+"
- "find members with React skill and active status"
- "search for JavaScript developers"
- "who knows Python?"
- "who is good at AWS?"
- "find suitable candidate for frontend development"
- "list all active members in development team"
```
## 任務分析與分工建議工作流程

當用戶收到一個新的複雜任務（如客戶反饋 review、項目需求等），並需要分析及建議分工時，使用以下工作流程：

### 工作流程（4 步驟）

1. **分析任務，拆解子問題**
   - 將任務分解為多個獨立 issue
   - 對每個 issue 分析：根因可能性 + 建議行動
   - 輸出結構：`問題描述 → 根因假設 → 建議行動`

2. **讀取團隊技能 JSON**
   - 讀取 `~/.hermes/team-capability/team.json`
   - 過濾出 `status: "active"` 的成員
   - 建立技能索引：`技能名稱 → [成員列表]`（按熟練度 L1-L5 排序）

3. **匹配技能 → 建議負責人**
   - 對每個 sub-issue，推斷需要的技能領域
   - 查詢有該技能且 level ≥ L3（勝任）的活躍成員
   - 建議最匹配的成員為 Lead，次匹配的為 Support

4. **輸出分工表 + 註冊到 Lark (可選)**
   - 輸出結構化分工表（Issue / Lead / Support / 原因）
   - 如用戶同意後，使用 Lark bitable API 在表格中創建記錄
   - 記錄包含：Task（任務名稱）、Description（含分析）、Category、Priority、Status=進行中

### 示例（來自當前 session）

用戶："我收到一個任務，Q3 Customer Feedback Review，有三個問題..."

輸出：
```
| Issue | 所需技能 | Lead | Support |
|-------|---------|------|---------|
| Onboarding 改善 | UI/UX, Figma | 趙六 (L4) | — |
| Page 載入慢 | Java, Python, Docker | 王五 (Java L4) + Jack (Python L4) | Test User |
| 報表不一致 | Python, Java | Jack (Python L4) + Test User (Python L4) | — |
```

### 觸發時機
當用戶提出以下類型的請求時使用此工作流程：
- 「我收到一個任務/反饋/項目...」
- 「幫我分析這個任務...」
- 「應該點樣分工比較合理？」
- 「幫我 record task 去 Lark...」
- 提及多個問題點的複雜任務描述

## 使用步驟

1. **檢查資料檔案**：首先檢查 `~/.hermes/team-capability/team.json` 是否存在，如果不存在則創建初始結構。

2. **解析指令**：分析用戶的自然語言指令，識別操作類型和參數。支援的關鍵詞包括：
   - 新增/添加/創建/加入/註冊/新/add/create/register/new + 組員/成員/員工/團隊成員/團隊人力/team member/member/employee/staff
   - 更新/修改/編輯/變更/改/調整/update/modify/edit/change/adjust + 組員/成員/技能/狀態/團隊/email/郵箱/員工編號/工號/team member/member/skill/status/team/employee id/emp id
   - 停用/禁用/離職/設為inactive/設為離職/設為非活躍/移除/deactivate/disable/remove/terminate/set inactive + 組員/成員/員工/team member/member/employee
   - 查詢/查找/搜索/找/搜/查/誰/查詢/query/search/find/who/who can/who knows + 有/會/懂/擅長/有...技能/有...經驗/適合/適合做/with/has/knows/can/good at/suitable for
   - @TeamCapability、@團隊能力、@成員管理、@能力管理、@HR、@人力資源、@teamcapability、@hr、@human resources
   - 任務分析、分工建議、找人做、誰適合

3. **判斷場景**：根據用戶請求選擇路徑：
   - **A: 團隊成員 CRUD**（新增/更新/停用/查詢）→ 執行操作指令
   - **B: 任務分析 + 分工建議**（收到複雜任務、需要分工）→ 執行「任務分析與分工建議工作流程」

4. **執行操作**：根據指令類型執行相應操作：
   - 新增成員：驗證必填欄位，生成唯一ID，儲存資料
   - 更新成員：找到對應成員，更新指定欄位
   - 停用成員：將成員狀態設為inactive
   - 查詢成員：根據條件過濾並返回結果
   - 任務分析：執行 4 步驟工作流程

5. **驗證輸入**：確保所有必填欄位完整，技能等級在1-5範圍內。

6. **返回結果**：返回結構化JSON響應（管理操作）或結構化分工表（分析操作）。

## 錯誤處理

當操作失敗時，返回以下格式的JSON：

```json
{
  "status": "failed",
  "operation": "操作名稱",
  "error": "錯誤描述",
  "trace_id": "unique-trace-id",
  "timestamp": "2026-06-25T10:00:00Z"
}
```

成功操作返回：

```json
{
  "status": "success",
  "operation": "操作名稱",
  "data": { /* 操作結果數據 */ },
  "trace_id": "unique-trace-id",
  "timestamp": "2026-06-25T10:00:00Z"
}
```

## 使用Python腳本

技能使用 `scripts/team_manager.py` 來處理核心邏輯。當需要執行複雜操作時，調用該腳本。

主要函數：
- `add_member(member_data)`: 新增成員
- `update_member(member_id, updates)`: 更新成員
- `deactivate_member(member_id)`: 停用成員
- `query_members(filters)`: 查詢成員
- `validate_member_data(data)`: 驗證成員數據

## 注意事項

1. **數據備份**：重要操作前會自動備份現有數據
2. **唯一性檢查**：確保employee_id和email的唯一性
3. **狀態管理**：停用的成員不會出現在預設查詢結果中
4. **自然語言解析**：如果指令不明確，會詢問用戶獲取必要資訊
5. **追蹤記錄**：每個操作都會生成trace_id供後續追蹤
6. **技能觸發**：當用戶使用以下任一模式時應觸發此技能：
   - 明確提及團隊能力管理相關詞彙
   - 使用@TeamCapability或類似提及
   - 詢問團隊成員技能或能力
   - 需要新增、更新、查詢團隊成員資訊

## 示例響應

### 成功新增成員
```json
{
  "status": "success",
  "operation": "add_member",
  "data": {
    "member_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John",
    "employee_id": "EMP001",
    "email": "john@company.com",
    "team": "開發組"
  },
  "trace_id": "trace_12345",
  "timestamp": "2026-06-25T10:00:00Z"
}
```

### 查詢結果
```json
{
  "status": "success",
  "operation": "query_members",
  "data": {
    "count": 2,
    "members": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "John",
        "employee_id": "EMP001",
        "email": "john@company.com",
        "team": "開發組",
        "status": "active",
        "skills": [
          {"name": "Python", "level": 3, "level_description": "勝任"},
          {"name": "JavaScript", "level": 2, "level_description": "基礎能力"}
        ]
      }
    ]
  },
  "trace_id": "trace_12346",
  "timestamp": "2026-06-25T10:00:00Z"
}
```

### 驗證錯誤
```json
{
  "status": "failed",
  "operation": "add_member",
  "error": "validation_error: 缺少必填欄位: email",
  "trace_id": "trace_12347",
  "timestamp": "2026-06-25T10:00:00Z"
}
```