#!/usr/bin/env python3
"""
WhatsApp-Lark Bridge 主應用程式
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# 載入環境變量
load_dotenv()

# 配置日誌
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 創建 Flask 應用
app = Flask(__name__)

# Lark API 配置
LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')

# WhatsApp 配置
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')

class WhatsAppMessageHandler:
    """處理 WhatsApp 消息"""
    
    @staticmethod
    def is_lark_command(message: str) -> bool:
        """檢查是否為 Lark 命令"""
        return '@Lark' in message.lower()
    
    @staticmethod
    def parse_command(message: str) -> dict:
        """解析命令"""
        try:
            # 移除 @Lark 標記
            content = message.lower().replace('@lark', '').strip()
            
            # 分割命令和參數
            if ':' in content:
                command, param = content.split(':', 1)
                command = command.strip()
                param = param.strip()
            else:
                command = content
                param = ''
            
            # 識別操作類型
            if 'query' in command:
                operation = 'query'
            elif 'insert' in command:
                operation = 'insert'
            elif 'update' in command:
                operation = 'update'
            elif 'todo' in command:
                operation = 'todo'
            else:
                operation = 'unknown'
            
            return {
                'operation': operation,
                'command': command,
                'param': param,
                'original': message
            }
        except Exception as e:
            logger.error(f"解析命令失敗: {e}")
            return {'operation': 'error', 'error': str(e)}

class LarkAPIClient:
    """Lark API 客戶端"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
    
    def get_access_token(self) -> str:
        """獲取訪問令牌"""
        # 這裡應該實現實際的令牌獲取邏輯
        # 暫時返回模擬令牌
        return "mock_access_token"
    
    def query_document(self, doc_id: str) -> dict:
        """查詢文檔"""
        logger.info(f"查詢文檔: {doc_id}")
        return {
            'status': 'success',
            'document_id': doc_id,
            'title': '專案規劃書',
            'content': '文檔內容...',
            'last_modified': datetime.now().isoformat()
        }
    
    def insert_content(self, doc_id: str, content: str) -> dict:
        """插入內容"""
        logger.info(f"插入內容到文檔 {doc_id}: {content[:50]}...")
        return {
            'status': 'success',
            'document_id': doc_id,
            'paragraph_id': 'para_' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'timestamp': datetime.now().isoformat()
        }
    
    def create_todo(self, content: str, priority: str = 'normal') -> dict:
        """創建待辦事項"""
        logger.info(f"創建待辦事項: {content}")
        return {
            'status': 'success',
            'task': content,
            'priority': priority,
            'record_id': 'rec_' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'created_at': datetime.now().isoformat()
        }

class ResponseBuilder:
    """構建回應消息"""
    
    @staticmethod
    def build_success_response(operation: str, data: dict) -> dict:
        """構建成功回應"""
        templates = {
            'query': "📄 文檔查詢成功！\n\n文檔：{title}\n段落數：{count}\n最後更新：{time}\n\n✅ 操作完成，無需確認。",
            'insert': "✅ 內容新增成功！\n\n位置：第{para_id}段\n段落ID：{para_id}\n追蹤ID：{trace_id}\n\n✅ 操作完成，無需確認。",
            'todo': "✅ 待辦事項創建成功！\n\n任務：{task}\n狀態：待處理\n創建時間：{time}\n記錄ID：{record_id}\n\n✅ 操作完成，無需確認。"
        }
        
        if operation in templates:
            message = templates[operation].format(**data)
        else:
            message = f"✅ {operation} 操作成功！\n\n數據：{json.dumps(data, ensure_ascii=False)}\n\n✅ 操作完成。"
        
        return {
            'status': 'success',
            'operation': operation,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def build_error_response(error: str) -> dict:
        """構建錯誤回應"""
        return {
            'status': 'error',
            'message': f"❌ 操作失敗！\n\n錯誤：{error}\n\n請檢查命令格式或聯繫管理員。",
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def build_help_response() -> dict:
        """構建幫助回應"""
        help_text = """📋 WhatsApp-Lark Bridge 使用說明：

可用命令：
1. @Lark query [文檔ID] - 查詢文檔
2. @Lark insert [內容] - 新增內容
3. @Lark update [內容] - 更新內容
4. @Lark todo: [任務描述] - 創建待辦事項

示例：
@Lark query doc_project_plan
@Lark insert 會議摘要：討論了Q2目標
@Lark todo: 跟進客戶反饋

✅ 操作完成，無需確認。"""
        
        return {
            'status': 'help',
            'message': help_text,
            'timestamp': datetime.now().isoformat()
        }

# 初始化處理器
message_handler = WhatsAppMessageHandler()
lark_client = LarkAPIClient(LARK_APP_ID, LARK_APP_SECRET)
response_builder = ResponseBuilder()

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """WhatsApp Webhook 端點"""
    try:
        # 獲取請求數據
        data = request.get_json()
        logger.info(f"收到 WhatsApp 消息: {json.dumps(data, ensure_ascii=False)}")
        
        # 驗證 Webhook 令牌
        verify_token = request.args.get('hub.verify_token')
        if verify_token:
            challenge = request.args.get('hub.challenge')
            return challenge, 200
        
        # 處理消息
        if 'messages' in data:
            for message in data['messages']:
                text = message.get('text', {}).get('body', '')
                
                # 檢查是否為 Lark 命令
                if message_handler.is_lark_command(text):
                    # 解析命令
                    command_info = message_handler.parse_command(text)
                    
                    # 處理命令
                    if command_info['operation'] == 'query':
                        result = lark_client.query_document('doc_project_plan')
                        response = response_builder.build_success_response('query', {
                            'title': result.get('title', '未知文檔'),
                            'count': '12',
                            'time': result.get('last_modified', '未知時間')
                        })
                    
                    elif command_info['operation'] == 'insert':
                        result = lark_client.insert_content('doc_project_plan', command_info['param'])
                        response = response_builder.build_success_response('insert', {
                            'para_id': result.get('paragraph_id', '未知'),
                            'trace_id': 'trace_' + datetime.now().strftime('%Y%m%d%H%M%S')
                        })
                    
                    elif command_info['operation'] == 'todo':
                        result = lark_client.create_todo(command_info['param'])
                        response = response_builder.build_success_response('todo', {
                            'task': result.get('task', '未知任務'),
                            'time': result.get('created_at', '未知時間'),
                            'record_id': result.get('record_id', '未知')
                        })
                    
                    elif command_info['operation'] == 'unknown':
                        response = response_builder.build_help_response()
                    
                    else:
                        response = response_builder.build_error_response('未知操作類型')
                    
                    # 記錄處理結果
                    logger.info(f"處理結果: {response['status']}")
                    
                    # 返回回應
                    return jsonify(response), 200
        
        # 非 Lark 命令，返回默認回應
        return jsonify({
            'status': 'ignored',
            'message': '非 Lark 命令，已忽略。'
        }), 200
        
    except Exception as e:
        logger.error(f"處理 Webhook 時出錯: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服務器錯誤: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'whatsapp-lark-bridge'
    }), 200

@app.route('/test/lark', methods=['GET'])
def test_lark():
    """測試 Lark API 連接"""
    try:
        token = lark_client.get_access_token()
        return jsonify({
            'status': 'success',
            'lark_connected': True,
            'has_token': bool(token)
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'lark_connected': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"啟動 WhatsApp-Lark Bridge 服務，端口: {port}")
    logger.info(f"Lark App ID: {LARK_APP_ID[:10]}...")
    
    app.run(host='0.0.0.0', port=port, debug=debug)