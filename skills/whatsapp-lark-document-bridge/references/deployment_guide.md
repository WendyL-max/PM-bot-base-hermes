# WhatsApp-Lark Bridge 部署指南

## 系統要求

### 硬件要求
- CPU: 1核心以上
- 內存: 512MB 以上
- 存儲: 1GB 以上可用空間

### 軟件要求
- 操作系統: Linux (Ubuntu 20.04+), macOS, Windows (WSL2)
- Python: 3.8 或更高版本
- 包管理器: pip 20.0+
- 數據庫: SQLite (內置) 或 PostgreSQL (可選)

### 網絡要求
- 出站訪問: Lark API (open.feishu.cn), WhatsApp API
- 入站訪問: Webhook 端口 (默認 5000)
- HTTPS: 生產環境必須使用 HTTPS

## 快速開始

### 1. 克隆代碼庫
```bash
git clone https://github.com/your-repo/whatsapp-lark-bridge.git
cd whatsapp-lark-bridge
```

### 2. 安裝依賴
```bash
# 創建虛擬環境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安裝依賴包
pip install --upgrade pip
pip install -r scripts/requirements.txt
```

### 3. 配置環境變量
```bash
# 複製環境變量模板
cp templates/.env.example .env

# 編輯 .env 文件
nano .env
```

**`.env` 文件內容示例：**
```env
# Lark API 配置
LARK_APP_ID=cli_XXXXXXXXXXXXXXXX
LARK_APP_SECRET=zXXXXXXXXXXXXXXXXXXXXXXX

# WhatsApp API 配置
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token

# 應用配置
APP_PORT=5000
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# 數據庫配置
DATABASE_URL=sqlite:///app.db

# 可選：Redis 緩存
REDIS_URL=redis://localhost:6379/0
```

### 4. 初始化數據庫
```bash
# 創建數據庫表
python scripts/init_db.py
```

### 5. 啟動服務
```bash
# 開發模式
python scripts/app.py

# 或使用部署腳本
chmod +x scripts/deploy.sh
./scripts/deploy.sh development
```

### 6. 驗證安裝
```bash
# 健康檢查
curl http://localhost:5000/health

# Lark 連接測試
curl http://localhost:5000/test/lark
```

## 生產環境部署

### 使用 Gunicorn
```bash
# 安裝 Gunicorn
pip install gunicorn

# 啟動服務
gunicorn -w 4 -b 0.0.0.0:5000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  "scripts.app:app"
```

### 使用 systemd (Linux)
創建服務文件 `/etc/systemd/system/whatsapp-lark-bridge.service`：
```ini
[Unit]
Description=WhatsApp-Lark Bridge Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/whatsapp-lark-bridge
EnvironmentFile=/opt/whatsapp-lark-bridge/.env
ExecStart=/opt/whatsapp-lark-bridge/venv/bin/gunicorn \
  -w 4 \
  -b 0.0.0.0:5000 \
  --access-logfile /opt/whatsapp-lark-bridge/logs/access.log \
  --error-logfile /opt/whatsapp-lark-bridge/logs/error.log \
  "scripts.app:app"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

啟動服務：
```bash
sudo systemctl daemon-reload
sudo systemctl enable whatsapp-lark-bridge
sudo systemctl start whatsapp-lark-bridge
sudo systemctl status whatsapp-lark-bridge
```

### 使用 Supervisor
創建配置文件 `/etc/supervisor/conf.d/whatsapp-lark-bridge.conf`：
```ini
[program:whatsapp-lark-bridge]
command=/opt/whatsapp-lark-bridge/venv/bin/gunicorn \
  -w 4 \
  -b 0.0.0.0:5000 \
  --access-logfile /opt/whatsapp-lark-bridge/logs/access.log \
  --error-logfile /opt/whatsapp-lark-bridge/logs/error.log \
  "scripts.app:app"
directory=/opt/whatsapp-lark-bridge
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
environment=PYTHONPATH="/opt/whatsapp-lark-bridge"
```

重載配置：
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start whatsapp-lark-bridge
```

## HTTPS 配置

### 使用 Nginx 反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 使用 Let's Encrypt
```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx

# 獲取證書
sudo certbot --nginx -d your-domain.com

# 自動續期測試
sudo certbot renew --dry-run
```

## 數據庫配置

### SQLite (默認)
```bash
# 默認配置，無需額外設置
DATABASE_URL=sqlite:///app.db
```

### PostgreSQL
```bash
# 安裝 PostgreSQL 驅動
pip install psycopg2-binary

# 配置環境變量
DATABASE_URL=postgresql://user:password@localhost/whatsapp_lark_bridge
```

初始化 PostgreSQL：
```sql
CREATE DATABASE whatsapp_lark_bridge;
CREATE USER whatsapp_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE whatsapp_lark_bridge TO whatsapp_user;
```

## 日誌配置

### 日誌輪轉 (logrotate)
創建 `/etc/logrotate.d/whatsapp-lark-bridge`：
```bash
/opt/whatsapp-lark-bridge/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload whatsapp-lark-bridge > /dev/null 2>&1 || true
    endscript
}
```

### 日誌級別
修改 `.env` 文件：
```env
LOG_LEVEL=DEBUG    # 最詳細
LOG_LEVEL=INFO     # 默認
LOG_LEVEL=WARNING  # 僅警告和錯誤
LOG_LEVEL=ERROR    # 僅錯誤
```

## 監控配置

### Prometheus 指標
```python
# 在 app.py 中添加
from prometheus_client import Counter, Gauge, Histogram

# 定義指標
requests_total = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_connections = Gauge('active_connections', 'Number of active connections')

# 在路由中記錄
@app.before_request
def before_request():
    requests_total.inc()
    active_connections.inc()

@app.after_request
def after_request(response):
    active_connections.dec()
    return response
```

### 健康檢查端點
```bash
# 基本健康檢查
curl http://localhost:5000/health

# Prometheus 指標
curl http://localhost:5000/metrics
```

## 備份策略

### 配置備份
```bash
#!/bin/bash
# backup-config.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/whatsapp-lark-bridge"

# 創建備份目錄
mkdir -p $BACKUP_DIR

# 備份配置
cp .env $BACKUP_DIR/.env.$DATE
cp app.db $BACKUP_DIR/app.db.$DATE

# 壓縮備份
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz \
  .env \
  app.db \
  logs/

# 保留最近7天備份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 自動備份 (cron)
```bash
# 編輯 crontab
crontab -e

# 每天凌晨2點備份
0 2 * * * /opt/whatsapp-lark-bridge/scripts/backup-config.sh
```

## 安全加固

### 防火牆配置
```bash
# 只允許必要端口
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (重定向)
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### 文件權限
```bash
# 設置正確權限
chmod 750 /opt/whatsapp-lark-bridge
chmod 640 /opt/whatsapp-lark-bridge/.env
chmod 755 /opt/whatsapp-lark-bridge/scripts/
chown -R www-data:www-data /opt/whatsapp-lark-bridge
```

### 定期更新
```bash
# 更新依賴
pip install --upgrade -r scripts/requirements.txt

# 更新系統
sudo apt update && sudo apt upgrade -y
```

## 故障排除

### 常見問題
1. **端口被占用**
   ```bash
   netstat -tulpn | grep :5000
   kill -9 <PID>
   ```

2. **權限問題**
   ```bash
   sudo chown -R www-data:www-data /opt/whatsapp-lark-bridge
   sudo chmod 640 /opt/whatsapp-lark-bridge/.env
   ```

3. **內存不足**
   ```bash
   # 檢查內存使用
   free -h
   
   # 限制 gunicorn workers
   gunicorn -w 2 ...  # 減少 worker 數量
   ```

4. **數據庫鎖定**
   ```bash
   # SQLite 數據庫鎖定
   rm -f app.db-wal app.db-shm
   ```

### 日誌檢查
```bash
# 實時查看日誌
tail -f logs/error.log

# 搜索錯誤
grep -i error logs/error.log

# 查看訪問日誌
tail -100 logs/access.log
```

### 性能監控
```bash
# 查看進程
ps aux | grep gunicorn

# 查看資源使用
top -p $(pgrep -f gunicorn)

# 查看網絡連接
ss -tulpn | grep :5000
```

## 擴展配置

### 多環境配置
創建環境特定配置文件：
```bash
# .env.development
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# .env.production
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
```

啟動時指定環境：
```bash
APP_ENV=production python scripts/app.py
```

### 負載均衡
使用多個實例：
```nginx
upstream whatsapp_lark_backend {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    location / {
        proxy_pass http://whatsapp_lark_backend;
    }
}
```

### 緩存配置
使用 Redis 緩存：
```bash
# 安裝 Redis
sudo apt install redis-server

# 配置環境變量
REDIS_URL=redis://localhost:6379/0
```

## 更新部署

### 更新流程
1. **備份當前版本**
   ```bash
   cp -r /opt/whatsapp-lark-bridge /opt/whatsapp-lark-bridge.backup
   ```

2. **拉取新代碼**
   ```bash
   cd /opt/whatsapp-lark-bridge
   git pull origin main
   ```

3. **更新依賴**
   ```bash
   source venv/bin/activate
   pip install --upgrade -r scripts/requirements.txt
   ```

4. **數據庫遷移**
   ```bash
   python scripts/migrate.py
   ```

5. **重啟服務**
   ```bash
   sudo systemctl restart whatsapp-lark-bridge
   ```

### 回滾流程
1. **停止服務**
   ```bash
   sudo systemctl stop whatsapp-lark-bridge
   ```

2. **恢復備份**
   ```bash
   rm -rf /opt/whatsapp-lark-bridge
   cp -r /opt/whatsapp-lark-bridge.backup /opt/whatsapp-lark-bridge
   ```

3. **重啟服務**
   ```bash
   sudo systemctl start whatsapp-lark-bridge
   ```
