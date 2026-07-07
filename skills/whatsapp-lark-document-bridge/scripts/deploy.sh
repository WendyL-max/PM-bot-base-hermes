#!/bin/bash
# whatsapp-lark-bridge.sh - WhatsApp-Lark Bridge 部署和管理腳本

set -e  # 遇到錯誤時退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
APP_NAME="whatsapp-lark-bridge"
APP_DIR="/opt/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="$APP_DIR/logs"
BACKUP_DIR="/backup/$APP_NAME"
CONFIG_FILE="$APP_DIR/.env"
PID_FILE="$APP_DIR/$APP_NAME.pid"
PORT=5000

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 檢查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "命令 $1 不存在，請先安裝"
        exit 1
    fi
}

# 檢查目錄權限
check_permissions() {
    if [ ! -w "$APP_DIR" ]; then
        log_error "目錄 $APP_DIR 不可寫，請檢查權限"
        exit 1
    fi
}

# 創建目錄結構
create_directories() {
    log_info "創建目錄結構..."
    
    mkdir -p "$APP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$APP_DIR/scripts"
    mkdir -p "$APP_DIR/templates"
    
    log_success "目錄創建完成"
}

# 安裝依賴
install_dependencies() {
    log_info "檢查系統依賴..."
    
    check_command python3
    check_command pip3
    check_command git
    
    # 更新系統包
    log_info "更新系統包..."
    apt-get update && apt-get upgrade -y
    
    # 安裝系統依賴
    log_info "安裝系統依賴..."
    apt-get install -y \
        python3-venv \
        python3-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        sqlite3 \
        nginx \
        supervisor \
        redis-server
    
    log_success "系統依賴安裝完成"
}

# 配置 Python 環境
setup_python_env() {
    log_info "設置 Python 環境..."
    
    # 創建虛擬環境
    python3 -m venv "$VENV_DIR"
    
    # 激活虛擬環境
    source "$VENV_DIR/bin/activate"
    
    # 升級 pip
    pip install --upgrade pip
    
    # 安裝 Python 依賴
    if [ -f "$APP_DIR/scripts/requirements.txt" ]; then
        pip install -r "$APP_DIR/scripts/requirements.txt"
    else
        log_warning "requirements.txt 不存在，跳過 Python 依賴安裝"
    fi
    
    log_success "Python 環境設置完成"
}

# 配置環境變量
setup_environment() {
    log_info "配置環境變量..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_info "創建環境配置文件..."
        cat > "$CONFIG_FILE" << EOF
# WhatsApp-Lark Bridge 配置
APP_NAME="$APP_NAME"
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# 服務配置
APP_HOST=0.0.0.0
APP_PORT=$PORT
WORKERS=4
TIMEOUT=300

# Lark API 配置
LARK_APP_ID=your_lark_app_id
LARK_APP_SECRET=your_lark_app_secret

# WhatsApp API 配置
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token

# 數據庫配置
DATABASE_URL=sqlite:///$APP_DIR/app.db

# Redis 配置（可選）
REDIS_URL=redis://localhost:6379/0

# 日誌配置
LOG_FILE=$LOG_DIR/error.log
ACCESS_LOG=$LOG_DIR/access.log
EOF
        chmod 600 "$CONFIG_FILE"
        log_success "環境配置文件創建完成"
    else
        log_info "環境配置文件已存在"
    fi
    
    # 加載環境變量
    export $(grep -v '^#' "$CONFIG_FILE" | xargs)
    
    log_success "環境變量配置完成"
}

# 配置 Supervisor
setup_supervisor() {
    log_info "配置 Supervisor..."
    
    SUPERVISOR_CONF="/etc/supervisor/conf.d/$APP_NAME.conf"
    
    cat > "$SUPERVISOR_CONF" << EOF
[program:$APP_NAME]
command=$VENV_DIR/bin/gunicorn -w \${WORKERS:-4} -b \${APP_HOST:-0.0.0.0}:\${APP_PORT:-5000} --timeout \${TIMEOUT:-300} --access-logfile \${ACCESS_LOG:-$LOG_DIR/access.log} --error-logfile \${LOG_FILE:-$LOG_DIR/error.log} scripts.app:app
directory=$APP_DIR
user=www-data
environment=PATH="$VENV_DIR/bin",APP_ENV="\${APP_ENV:-production}"
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=$LOG_DIR/supervisor_err.log
stdout_logfile=$LOG_DIR/supervisor_out.log
EOF
    
    # 重啟 Supervisor
    supervisorctl reread
    supervisorctl update
    supervisorctl restart $APP_NAME
    
    log_success "Supervisor 配置完成"
}

# 配置 Nginx
setup_nginx() {
    log_info "配置 Nginx..."
    
    NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
    
    cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向 HTTP 到 HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # 安全頭部
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 日誌
    access_log $LOG_DIR/nginx_access.log;
    error_log $LOG_DIR/nginx_error.log;
    
    # 靜態文件
    location /static {
        alias $APP_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 應用代理
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 超時設置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 健康檢查
    location /health {
        proxy_pass http://127.0.0.1:$PORT/health;
        access_log off;
    }
    
    # 指標端點
    location /metrics {
        proxy_pass http://127.0.0.1:$PORT/metrics;
        access_log off;
    }
}
EOF
    
    # 啟用站點
    ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/"
    
    # 測試配置
    nginx -t
    
    # 重啟 Nginx
    systemctl restart nginx
    
    log_success "Nginx 配置完成"
}

# 配置防火牆
setup_firewall() {
    log_info "配置防火牆..."
    
    # 安裝 ufw
    apt-get install -y ufw
    
    # 默認策略
    ufw default deny incoming
    ufw default allow outgoing
    
    # 允許端口
    ufw allow 22/tcp      # SSH
    ufw allow 80/tcp      # HTTP
    ufw allow 443/tcp     # HTTPS
    
    # 啟用防火牆
    ufw --force enable
    
    log_success "防火牆配置完成"
}

# 配置 SSL
setup_ssl() {
    log_info "配置 SSL 證書..."
    
    # 安裝 Certbot
    apt-get install -y certbot python3-certbot-nginx
    
    # 獲取證書
    certbot --nginx -d your-domain.com --non-interactive --agree-tos --email admin@example.com
    
    # 設置自動續訂
    echo "0 0 * * * certbot renew --quiet" | crontab -
    
    log_success "SSL 證書配置完成"
}

# 備份配置
backup_config() {
    log_info "開始備份..."
    
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    # 創建備份
    tar -czf "$BACKUP_FILE" \
        "$CONFIG_FILE" \
        "$APP_DIR/app.db" \
        "$LOG_DIR" \
        "$APP_DIR/scripts" \
        "$APP_DIR/templates" \
        2>/dev/null || true
    
    # 清理舊備份（保留最近7天）
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete
    
    log_success "備份完成：$BACKUP_FILE"
}

# 恢復配置
restore_config() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        log_error "請指定備份文件"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "備份文件不存在：$backup_file"
        exit 1
    fi
    
    log_info "開始恢復：$backup_file"
    
    # 停止服務
    supervisorctl stop $APP_NAME
    
    # 恢復文件
    tar -xzf "$backup_file" -C "$APP_DIR"
    
    # 啟動服務
    supervisorctl start $APP_NAME
    
    log_success "恢復完成"
}

# 監控服務
monitor_service() {
    log_info "檢查服務狀態..."
    
    # 檢查進程
    if supervisorctl status $APP_NAME | grep -q "RUNNING"; then
        log_success "服務正在運行"
    else
        log_error "服務未運行"
        supervisorctl status $APP_NAME
    fi
    
    # 檢查端口
    if netstat -tulpn | grep -q ":$PORT"; then
        log_success "端口 $PORT 正在監聽"
    else
        log_error "端口 $PORT 未監聽"
    fi
    
    # 檢查日誌
    if [ -f "$LOG_DIR/error.log" ]; then
        log_info "最近錯誤日誌："
        tail -10 "$LOG_DIR/error.log"
    fi
    
    # 檢查數據庫
    if [ -f "$APP_DIR/app.db" ]; then
        log_success "數據庫文件存在"
    else
        log_warning "數據庫文件不存在"
    fi
}

# 更新代碼
update_code() {
    log_info "更新代碼..."
    
    cd "$APP_DIR"
    
    if [ -d ".git" ]; then
        git pull origin main
        log_success "代碼更新完成"
    else
        log_warning "不是 Git 倉庫，跳過代碼更新"
    fi
    
    # 重新安裝依賴
    source "$VENV_DIR/bin/activate"
    pip install --upgrade -r scripts/requirements.txt
    
    # 重啟服務
    supervisorctl restart $APP_NAME
    
    log_success "更新完成"
}

# 清理日誌
clean_logs() {
    log_info "清理日誌..."
    
    # 壓縮舊日誌
    find "$LOG_DIR" -name "*.log" -mtime +30 -exec gzip {} \;
    
    # 刪除過舊日誌
    find "$LOG_DIR" -name "*.gz" -mtime +90 -delete
    
    log_success "日誌清理完成"
}

# 顯示幫助
show_help() {
    echo "WhatsApp-Lark Bridge 管理腳本"
    echo ""
    echo "用法：$0 [命令]"
    echo ""
    echo "命令："
    echo "  install         安裝和配置應用"
    echo "  start           啟動服務"
    echo "  stop            停止服務"
    echo "  restart         重啟服務"
    echo "  status          查看服務狀態"
    echo "  update          更新代碼和依賴"
    echo "  backup          備份配置"
    echo "  restore <file>  恢復配置"
    echo "  monitor         監控服務狀態"
    echo "  clean           清理日誌"
    echo "  help            顯示幫助"
    echo ""
}

# 主函數
main() {
    local command="$1"
    
    case "$command" in
        install)
            create_directories
            install_dependencies
            setup_python_env
            setup_environment
            setup_supervisor
            setup_nginx
            setup_firewall
            setup_ssl
            ;;
        start)
            supervisorctl start $APP_NAME
            ;;
        stop)
            supervisorctl stop $APP_NAME
            ;;
        restart)
            supervisorctl restart $APP_NAME
            ;;
        status)
            supervisorctl status $APP_NAME
            ;;
        update)
            update_code
            ;;
        backup)
            backup_config
            ;;
        restore)
            restore_config "$2"
            ;;
        monitor)
            monitor_service
            ;;
        clean)
            clean_logs
            ;;
        help|*)
            show_help
            ;;
    esac
}

# 執行主函數
main "$@"