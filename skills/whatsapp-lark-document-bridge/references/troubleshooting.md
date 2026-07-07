# WhatsApp-Lark Bridge 故障排除指南

## 常見問題解決

### 1. 服務無法啟動
**症狀：** 運行 `python app.py` 時報錯
**解決方案：**
```bash
# 檢查 Python 版本
python3 --version  # 需要 Python 3.8+

# 檢查依賴安裝
pip install -r requirements.txt

# 檢查端口占用
netstat -tulpn | grep :5000
# 如果端口被占用，可以修改 .env 中的 APP_PORT

# 檢查環境變量
cat .env | grep -E "LARK_APP|WHATSAPP"
```

### 2. Lark API 連接失敗
**症狀：** `/test/lark` 端點返回錯誤
**解決方案：**
```bash
# 驗證 Lark 憑證
echo "LARK_APP_ID: $(grep LARK_APP_ID .env)"
echo "LARK_APP_SECRET: $(grep LARK_APP_SECRET .env)"

# 測試 Lark API 訪問
curl -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"YOUR_APP_ID","app_secret":"YOUR_APP_SECRET"}'

# 檢查應用權限
# 1. 登錄 Lark 開放平台
# 2. 進入應用管理
# 3. 確認已開啟以下權限：
#    - 獲取用戶信息
#    - 獲取部門信息
#    - 發送消息
#    - 讀寫文檔
```

### 3. Webhook 驗證失敗
**症狀：** WhatsApp Webhook 驗證不通過
**解決方案：**
```bash
# 檢查 Webhook 令牌
echo "WHATSAPP_WEBHOOK_VERIFY_TOKEN: $(grep WHATSAPP_WEBHOOK_VERIFY_TOKEN .env)"

# 驗證 Webhook URL
# URL 格式: https://your-domain.com/webhook/whatsapp
# 必須是 HTTPS，WhatsApp 不接受 HTTP

# 測試本地 Webhook（使用 ngrok）
ngrok http 5000
# 將生成的 HTTPS URL 配置到 WhatsApp Business API
```

### 4. 消息處理錯誤
**症狀：** 收到消息但無回應
**解決方案：**
```bash
# 檢查日誌
tail -f logs/app.log

# 常見錯誤：
# 1. 消息格式錯誤 - 檢查 WhatsApp 消息格式
# 2. Lark API 限流 - 等待後重試
# 3. 網絡問題 - 檢查防火牆和代理

# 手動測試 Webhook
curl -X POST "http://localhost:5000/webhook/whatsapp" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"from":"test","id":"1","text":{"body":"@Lark query doc_test"}}]}'
```

### 5. 性能問題
**症狀：** 響應緩慢或超時
**解決方案：**
```bash
# 檢查系統資源
top -b -n 1 | grep python

# 優化配置
# 1. 增加 gunicorn workers
#    修改 gunicorn -w 4 -> gunicorn -w 8
# 2. 啟用緩存
#    在 .env 中設置 CACHE_TYPE=redis
# 3. 使用異步任務處理
#    對於耗時操作，使用 Celery 隊列

# 監控日誌
tail -f logs/access.log
```

## 日誌分析

### 日誌位置
- 訪問日誌：`logs/access.log`
- 錯誤日誌：`logs/error.log`
- 應用日誌：`logs/app.log`

### 常見日誌模式
```log
# 正常流程
INFO - 收到 WhatsApp 消息
INFO - 檢測到 Lark 命令: @Lark query doc_project_plan
INFO - 查詢文檔: doc_project_plan
INFO - 處理結果: success

# 錯誤流程
ERROR - 解析命令失敗: 無效格式
ERROR - Lark API 錯誤: 401 Unauthorized
ERROR - Webhook 處理錯誤: 超時
```

### 日誌級別調整
```bash
# 修改 .env 中的 LOG_LEVEL
LOG_LEVEL=DEBUG    # 最詳細
LOG_LEVEL=INFO     # 默認
LOG_LEVEL=WARNING  # 僅警告和錯誤
LOG_LEVEL=ERROR    # 僅錯誤
```

## 配置檢查清單

### 部署前檢查
- [ ] Python 3.8+ 已安裝
- [ ] 依賴包已安裝 (`requirements.txt`)
- [ ] `.env` 文件已配置
- [ ] Lark 應用權限已開啟
- [ ] WhatsApp Business API 已配置
- [ ] 日誌目錄權限正確
- [ ] 防火牆端口已開放 (5000)

### 運行時檢查
- [ ] 服務正常啟動 (`http://localhost:5000/health`)
- [ ] Lark API 連接正常 (`http://localhost:5000/test/lark`)
- [ ] Webhook 可訪問 (使用 `curl` 測試)
- [ ] 日誌文件正在寫入
- [ ] 內存使用正常

### 生產環境檢查
- [ ] 使用 HTTPS (Nginx/Apache 反向代理)
- [ ] 配置 SSL 證書
- [ ] 設置系統服務 (systemd/supervisor)
- [ ] 配置監控告警
- [ ] 定期備份數據
- [ ] 設置日誌輪轉

## 緊急恢復步驟

### 1. 服務崩潰
```bash
# 查找崩潰原因
tail -100 logs/error.log

# 重啟服務
pkill -f "python app.py"
python app.py &

# 或使用 systemd
sudo systemctl restart whatsapp-lark-bridge
```

### 2. 數據庫問題
```bash
# 備份當前數據庫
cp app.db app.db.backup.$(date +%Y%m%d)

# 重新初始化
python scripts/init_db.py

# 檢查數據庫完整性
sqlite3 app.db "PRAGMA integrity_check;"
```

### 3. API 憑證失效
```bash
# 更新 Lark 憑證
sed -i "s/LARK_APP_SECRET=.*/LARK_APP_SECRET=new_secret/" .env

# 更新 WhatsApp 憑證
sed -i "s/WHATSAPP_ACCESS_TOKEN=.*/WHATSAPP_ACCESS_TOKEN=new_token/" .env

# 重啟服務
pkill -f "python app.py"
python app.py &
```

### 4. 網絡問題
```bash
# 測試網絡連接
ping open.feishu.cn
curl -I https://open.feishu.cn

# 檢查代理設置
echo $http_proxy
echo $https_proxy

# 檢查防火牆
sudo ufw status
sudo iptables -L -n
```

## 聯繫支持

### 需要提供的信息
1. **錯誤日誌**: `tail -50 logs/error.log`
2. **配置摘要**: `grep -E "LARK|WHATSAPP|APP_" .env`
3. **系統信息**: `uname -a && python3 --version`
4. **重現步驟**: 如何觸發錯誤
5. **時間戳**: 錯誤發生的具體時間

### 緊急聯繫
- **Lark API 問題**: Lark 開放平台支持
- **WhatsApp API 問題**: Meta Business 支持
- **系統問題**: 系統管理員
- **代碼問題**: 開發團隊

## 最佳實踐

### 安全性
- 定期更換 API 令牌
- 使用環境變量存儲敏感信息
- 啟用 HTTPS 和 SSL
- 限制訪問 IP
- 審計日誌記錄

### 可靠性
- 實現健康檢查端點
- 設置監控告警
- 定期備份配置
- 測試故障恢復
- 文檔更新流程

### 可維護性
- 保持代碼註釋
- 更新配置文檔
- 記錄變更日誌
- 定期依賴更新
- 性能監控指標