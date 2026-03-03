"""FastAPI后端服务
提供REST API接口，用于管理机场配置
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
import logging
import asyncio
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor

from .config_manager import ConfigManager
from .config_schema import AirportConfig, GlobalConfig
from .parser import parse_with_config


# 配置日志系统 - 使用用户根目录的 .sub-surge 目录
# 支持通过环境变量 SUB_SURGE_CONFIG_DIR 自定义
from pathlib import Path
custom_dir = os.environ.get('SUB_SURGE_CONFIG_DIR')
if custom_dir:
    log_dir = Path(custom_dir) / "logs"
else:
    log_dir = Path.home() / ".sub-surge" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'sub-surge.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Surge订阅配置管理API", version="2.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置管理器
config_manager = ConfigManager()

# Web目录路径 - web 目录现在在 sub_surge 包内部
web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

# 挂载静态文件目录
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

# 自动更新任务状态
auto_update_task = None
auto_update_running = False

# 2FA 认证
import secrets
import hashlib
from datetime import datetime, timedelta
import pyotp
import qrcode
from io import BytesIO
import base64

totp_secret = None  # TOTP 密钥
totp_binded = False  # 是否已绑定 2FA
valid_sessions = {}  # 有效的会话令牌，格式：{token: expiry_time}


def get_config_dir():
    """获取配置目录路径"""
    from pathlib import Path
    custom_dir = os.environ.get('SUB_SURGE_CONFIG_DIR')
    if custom_dir:
        config_dir = Path(custom_dir)
    else:
        config_dir = Path.home() / ".sub-surge"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def ensure_totp_secret():
    """确保 TOTP 密钥存在，如果不存在则生成新的"""
    global totp_secret, totp_binded
    try:
        config_dir = get_config_dir()
        user_config_path = config_dir / "user_config.json"
        
        # 加载或创建配置文件
        if user_config_path.exists():
            with open(user_config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
        else:
            user_config = {}
        
        # 检查 TOTP 密钥是否存在
        if 'totp_secret' not in user_config or not user_config['totp_secret']:
            # 生成新的 TOTP 密钥
            new_totp_secret = pyotp.random_base32()
            user_config['totp_secret'] = new_totp_secret
            user_config['totp_created_at'] = datetime.now().isoformat()
            user_config['totp_binded'] = False
            
            # 保存配置文件
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(user_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"TOTP 密钥不存在，已生成新密钥")
            totp_secret = new_totp_secret
            totp_binded = False
        else:
            totp_secret = user_config.get('totp_secret')
            totp_binded = user_config.get('totp_binded', False)
    except Exception as e:
        logger.error(f"确保 TOTP 密钥失败: {e}")


def load_totp_config():
    """从配置文件加载 TOTP 配置"""
    global totp_secret, totp_binded
    ensure_totp_secret()


def generate_session_token():
    """生成一个新的会话令牌"""
    return secrets.token_urlsafe(32)


def verify_session_token(token: str) -> bool:
    """验证会话令牌是否有效"""
    global valid_sessions
    
    if not token or token not in valid_sessions:
        return False
    
    # 检查令牌是否过期
    if datetime.now() > valid_sessions[token]:
        del valid_sessions[token]
        return False
    
    return True


def generate_qr_code(data: str) -> str:
    """生成二维码并返回 base64 编码的图片"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


# 应用启动时加载 TOTP 配置
load_totp_config()


# 请求模型
class AddAirportRequest(BaseModel):
    name: str
    url: str
    key: str
    reset_day: int = 30
    is_node_list: bool = False
    exclude_keywords: Optional[List[str]] = None
    country_mapping: Optional[Dict[str, str]] = None
    name_regex_replacements: Optional[List[Dict[str, str]]] = None
    info_keywords: Optional[Dict[str, List[str]]] = None


class Verify2FARequest(BaseModel):
    """验证 2FA 验证码请求"""
    code: str


class UpdateGlobalConfigRequest(BaseModel):
    txcos_domain: Optional[str] = None
    interval: Optional[int] = None
    merge_key: Optional[str] = None
    merge_airports: Optional[List[str]] = None
    ai_api_key: Optional[str] = None
    ai_base_url: Optional[str] = None
    ai_model: Optional[str] = None
    rule_sets: Optional[List[Dict]] = None


class RuleSetRequest(BaseModel):
    """规则集请求"""
    name: str
    url: str
    policy: str
    enabled: bool = True
    update_interval: int = 86400


# 2FA 认证相关接口
@app.get("/api/2fa/status")
async def get_2fa_status():
    """获取 2FA 绑定状态"""
    global totp_binded
    return {"binded": totp_binded}


@app.get("/api/2fa/setup")
async def setup_2fa():
    """获取 2FA 设置信息（密钥和二维码）"""
    global totp_secret, totp_binded
    
    # 如果已经绑定，不允许重新设置
    if totp_binded:
        raise HTTPException(status_code=400, detail="2FA 已绑定，请先解绑")
    
    # 确保密钥存在
    ensure_totp_secret()
    
    # 生成 TOTP URI
    totp = pyotp.TOTP(totp_secret)
    app_name = "SubSurge"
    user_identifier = "user@subsurge"  # 可以自定义
    
    provisioning_uri = totp.provisioning_uri(
        name=user_identifier,
        issuer_name=app_name
    )
    
    # 生成二维码
    qr_code = generate_qr_code(provisioning_uri)
    
    return {
        "secret": totp_secret,
        "qr_code": qr_code,
        "provisioning_uri": provisioning_uri
    }


@app.post("/api/2fa/verify")
async def verify_2fa(request: Verify2FARequest):
    """验证 2FA 验证码并绑定"""
    global totp_secret, totp_binded, valid_sessions
    
    if not totp_secret:
        raise HTTPException(status_code=400, detail="TOTP 密钥不存在")
    
    # 验证 TOTP 代码
    totp = pyotp.TOTP(totp_secret)
    if not totp.verify(request.code, valid_window=1):
        raise HTTPException(status_code=401, detail="验证码错误")
    
    # 如果尚未绑定，则标记为已绑定
    if not totp_binded:
        try:
            config_dir = get_config_dir()
            user_config_path = config_dir / "user_config.json"
            
            with open(user_config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            user_config['totp_binded'] = True
            user_config['totp_binded_at'] = datetime.now().isoformat()
            
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(user_config, f, indent=2, ensure_ascii=False)
            
            totp_binded = True
            logger.info("2FA 已成功绑定")
        except Exception as e:
            logger.error(f"保存 2FA 绑定状态失败: {e}")
            raise HTTPException(status_code=500, detail=f"绑定失败: {str(e)}")
    
    # 生成会话令牌
    session_token = generate_session_token()
    expiry = datetime.now() + timedelta(days=30)
    valid_sessions[session_token] = expiry
    
    logger.info("2FA 验证成功，已生成会话令牌")
    return {
        "message": "验证成功",
        "token": session_token
    }


# API 路由
@app.get("/")
async def root():
    """返回前端页面"""
    logger.debug("访问首页")
    index_path = os.path.join(web_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Surge订阅配置管理API", "version": "2.0.0"}


@app.get("/app.js")
async def get_app_js():
    """返回前端JS文件"""
    js_path = os.path.join(web_dir, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/favicon.ico")
async def get_favicon():
    """返回网站图标"""
    ico_path = os.path.join(web_dir, "favicon.ico")
    if os.path.exists(ico_path):
        return FileResponse(ico_path, media_type="image/x-icon")
    raise HTTPException(status_code=404, detail="File not found")


def verify_token_from_request(request: Request) -> str:
    """验证请求中的令牌，如果无效则抛出异常"""
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少授权令牌")
    
    token = auth_header[7:]  # 去掉 "Bearer " 前缀
    
    if not verify_session_token(token):
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    
    return token


@app.get("/api/config")
async def get_config(token: str = Depends(verify_token_from_request)):
    """获取全局配置"""
    return config_manager.get_global_config().dict()


@app.put("/api/config")
async def update_config(request: UpdateGlobalConfigRequest, token: str = Depends(verify_token_from_request)):
    """更新全局配置"""
    update_data = request.dict(exclude_none=True)
    if config_manager.update_global_config(**update_data):
        return {"message": "配置更新成功"}
    raise HTTPException(status_code=500, detail="配置更新失败")


@app.get("/api/config/export")
async def export_config(token: str = Depends(verify_token_from_request)):
    """导出配置"""
    return config_manager.get_global_config().dict()


@app.post("/api/config/import")
async def import_config(config_data: GlobalConfig, token: str = Depends(verify_token_from_request)):
    """导入配置"""
    try:
        config_manager.config = config_data
        config_manager._save_config()
        return {"message": "配置导入成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置导入失败: {str(e)}")


@app.get("/api/airports")
async def list_airports(token: str = Depends(verify_token_from_request)):
    """获取所有机场配置"""
    return config_manager.get_global_config().dict()


@app.get("/api/airports/{name}")
async def get_airport(name: str, token: str = Depends(verify_token_from_request)):
    """获取指定机场配置"""
    airport = config_manager.get_airport(name)
    if not airport:
        raise HTTPException(status_code=404, detail="机场不存在")
    return airport.dict()


@app.post("/api/airports")
async def add_airport(request: AddAirportRequest, token: str = Depends(verify_token_from_request)):
    """添加机场配置（基于AI分析结果）"""
    # 检查机场是否已存在
    if config_manager.get_airport(request.name):
        raise HTTPException(status_code=400, detail="机场名称已存在")
    
    # 创建机场配置（不使用模板）
    airport_data = {
        "name": request.name,
        "url": request.url,
        "key": request.key,
        "reset_day": request.reset_day,
        "is_node_list": request.is_node_list,
        "parser_config": {
            "exclude_keywords": request.exclude_keywords or [],
            "country_name_mapping": request.country_mapping or {},
            "name_regex_replacements": request.name_regex_replacements or []
        },
        "info_extractor": request.info_keywords or {
            "traffic_keywords": ["Bandwidth", "流量"],
            "reset_keywords": ["Reset", "重置"],
            "expire_keywords": ["Date", "到期"]
        }
    }
    
    try:
        airport = AirportConfig(**airport_data)
        if config_manager.add_airport(airport):
            return {"message": "机场添加成功", "airport": airport.dict()}
        raise HTTPException(status_code=500, detail="机场添加失败")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置验证失败: {str(e)}")


@app.put("/api/airports/{name}")
async def update_airport_config(name: str, request: AddAirportRequest, token: str = Depends(verify_token_from_request)):
    """更新机场配置"""
    if not config_manager.get_airport(name):
        raise HTTPException(status_code=404, detail="机场不存在")
    
    try:
        # 创建更新的机场配置
        airport_data = {
            "name": request.name,
            "url": request.url,
            "key": request.key,
            "reset_day": request.reset_day,
            "is_node_list": request.is_node_list,
            "parser_config": {
                "exclude_keywords": request.exclude_keywords or [],
                "country_name_mapping": request.country_mapping or {},
                "name_regex_replacements": request.name_regex_replacements or []
            },
            "info_keywords": request.info_keywords or {
                "traffic_keywords": ["Bandwidth", "流量"],
                "reset_keywords": ["Reset", "重置"],
                "expire_keywords": ["Date", "到期"]
            }
        }
        
        airport = AirportConfig(**airport_data)
        config_manager.config.airports[name] = airport
        config_manager._save_config()
        return {"message": "机场配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置更新失败: {str(e)}")


@app.delete("/api/airports/{name}")
async def delete_airport(name: str, token: str = Depends(verify_token_from_request)):
    """删除机场配置"""
    if config_manager.remove_airport(name):
        return {"message": "机场删除成功"}
    raise HTTPException(status_code=404, detail="机场不存在")


@app.post("/api/airports/{name}/update")
async def update_airport_subscription(name: str, token: str = Depends(verify_token_from_request)):
    """更新机场订阅"""
    airport = config_manager.get_airport(name)
    if not airport:
        raise HTTPException(status_code=404, detail="机场不存在")
    
    try:
        # 在线程池中执行阻塞的更新逻辑
        from .updater import update_airport
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            update_airport, 
            airport, 
            config_manager.get_global_config()
        )
        return {"message": "订阅更新成功", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"订阅更新失败: {str(e)}")


@app.post("/api/airports/{name}/convert-clash")
async def convert_to_clash(name: str, token: str = Depends(verify_token_from_request)):
    """
    将指定机场的 Surge 配置转换为 Clash 格式
    
    返回 Clash 配置的下载链接
    """
    airport = config_manager.get_airport(name)
    if not airport:
        raise HTTPException(status_code=404, detail="机场不存在")
    
    global_config = config_manager.get_global_config()
    
    # 检查腾讯云配置
    if not global_config.txcos_domain:
        raise HTTPException(status_code=400, detail="未配置腾讯云对象存储")
    
    try:
        import httpx
        from .parser import generate_clash_config
        
        # 下载 Surge 配置
        surge_url = f"{global_config.txcos_domain}/{airport.key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(surge_url)
            response.raise_for_status()
            surge_content = response.text
        
        # 转换为 Clash 格式
        clash_content = generate_clash_config(surge_content, include_rules=True)
        
        # 保存并上传
        import os
        clash_temp_file = f".{airport.name}_clash.yaml"
        with open(clash_temp_file, 'w', encoding='utf-8') as f:
            f.write(clash_content)
        
        # 上传到腾讯云
        from QuickStart_Rhy.API.TencentCloud import TxCOS
        clash_key = airport.clash_key or f"{airport.key.rsplit('.', 1)[0]}_clash.yaml"
        
        def upload_clash():
            TxCOS().upload(clash_temp_file, key=clash_key)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, upload_clash)
        os.remove(clash_temp_file)
        
        clash_url = f"{global_config.txcos_domain}/{clash_key}"
        
        # 更新机场配置，保存 Clash 链接
        airport.enable_clash = True
        airport.clash_key = clash_key
        config_manager.add_airport(airport)
        
        return {
            "message": "转换成功",
            "clash_url": clash_url,
            "surge_url": surge_url
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


@app.post("/api/merge")
async def merge_subscriptions(request: dict, token: str = Depends(verify_token_from_request)):
    """合并订阅"""
    # 从请求体获取要合并的机场列表，如果没有则使用全局配置
    airports_to_merge = request.get("airports") or config_manager.get_global_config().merge_airports
    
    if not airports_to_merge:
        raise HTTPException(status_code=400, detail="未选择要合并的机场")
    
    try:
        from .updater import merge_airports
        # 在线程池中执行阻塞的合并逻辑
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            merge_airports,
            airports_to_merge,
            config_manager
        )
        return {"message": "订阅合并成功", "result": result}
    except Exception as e:
        # print trace
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"订阅合并失败: {str(e)}")


@app.post("/api/analyze")
async def analyze_subscription_url(request: dict, token: str = Depends(verify_token_from_request)):
    """
    分析订阅链接或订阅内容，自动推荐配置
    
    请求体:
    {
        "url": "订阅链接",  // 可选（与content二选一）
        "content": "订阅内容",  // 可选（与url二选一）
        "use_ai": true  // 可选，默认true，是否使用AI增强分析
    }
    
    返回:
    {
        "is_node_list": bool,
        "country_mapping": {...},
        "exclude_keywords": [...],
        "confidence": 0.8,
        "suggestions": {...},
        "analysis": {...},
        "analysis_method": "ai" | "static" | "error"  // 分析方法
    }
    """
    from .analyzer import analyze_subscription
    
    url = request.get("url")
    content = request.get("content")
    use_ai = request.get("use_ai", True)  # 默认启用AI
    
    if not url and not content:
        raise HTTPException(status_code=400, detail="必须提供url或content参数")
    
    try:
        result = analyze_subscription(url=url, content=content, use_ai=use_ai)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/preview")
async def preview_subscription(request: dict, token: str = Depends(verify_token_from_request)):
    """
    预览订阅内容（下载并解码）
    
    请求体:
    {
        "url": "订阅链接"
    }
    
    返回:
    {
        "content": "解码后的订阅内容",
        "is_base64": bool,
        "line_count": int,
        "preview": "前50行内容"
    }
    """
    url = request.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="缺少URL参数")
    
    try:
        import httpx
        import base64
        
        # 下载订阅内容
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            raw_content = response.content
        
        if not raw_content:
            raise HTTPException(status_code=400, detail="无法下载订阅内容")
        
        # 智能判断是否需要Base64解码
        # 优先尝试直接解析为UTF-8（大多数情况是明文）
        try:
            decoded = raw_content.decode('utf-8', errors='strict')
            is_base64 = False
            
            # 检查是否是明文格式（包含Surge/Clash特征）
            has_surge_markers = any(marker in decoded for marker in ['[Proxy]', '[Proxy Group]', 'proxies:', '= ss,', '= vmess,', '= trojan,'])
            
            # 如果没有明显的配置标记，且内容看起来像base64，尝试解码
            if not has_surge_markers and len(decoded) > 100:
                # 检查是否全是base64字符（允许少量换行和空格）
                content_without_whitespace = decoded.replace('\n', '').replace('\r', '').replace(' ', '')
                base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
                if len(content_without_whitespace) > 0 and all(c in base64_chars for c in content_without_whitespace):
                    try:
                        decoded_b64 = base64.b64decode(content_without_whitespace).decode('utf-8', errors='ignore')
                        # 验证解码后的内容是否更像配置文件
                        if any(marker in decoded_b64 for marker in ['[Proxy]', 'proxies:', 'ss://', 'vmess://', 'trojan://']):
                            decoded = decoded_b64
                            is_base64 = True
                    except:
                        pass  # 解码失败，保持原内容
        except UnicodeDecodeError:
            # UTF-8解码失败，尝试Base64解码
            try:
                decoded = base64.b64decode(raw_content).decode('utf-8', errors='ignore')
                is_base64 = True
            except:
                # Base64也失败，强制转换
                decoded = raw_content.decode('utf-8', errors='ignore')
                is_base64 = False
        
        lines = decoded.split('\n')
        line_count = len(lines)
        # 不再限制行数，返回完整内容
        preview = decoded  # 完整预览
        
        return {
            "content": decoded,
            "is_base64": is_base64,
            "line_count": line_count,
            "preview": preview
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@app.post("/api/airports/config-preview")
async def get_airport_config_preview(request: dict, token: str = Depends(verify_token_from_request)):
    """
    根据当前规则生成机场配置预览（不下载订阅，使用占位符代替真实节点）

    请求体:
    {
        "name": "机场名称",
        "url": "订阅链接",
        "key": "存储路径",
        "reset_day": 30
    }

    返回:
    {
        "preview": "完整的Surge配置预览文本",
        "rule_count": int,
        "cos_url": "将生成的订阅URL"
    }
    """
    import urllib.parse
    from .template import traffic_module_template, conf_template

    global_config = config_manager.get_global_config()

    name = request.get("name") or "示例机场"
    url = request.get("url") or ""
    key = request.get("key") or "airport/example.conf"
    reset_day = int(request.get("reset_day") or 30)

    # 生成 COS URL
    if global_config.txcos_domain:
        cos_url = f"{global_config.txcos_domain.rstrip('/')}/{key}"
    else:
        cos_url = f"<未配置COS域名>/{key}"

    update_interval = global_config.interval or 43200

    # 生成 Panel 和 Script 部分
    module_panel = traffic_module_template['panel'].format(
        name=name, update_interval=update_interval
    )
    encoded_url = urllib.parse.quote(url, safe="") if url else "%3C%E8%AE%A2%E9%98%85%E9%93%BE%E6%8E%A5%3E"
    module_script = traffic_module_template['script'].format(
        name=name,
        update_interval=update_interval,
        url=encoded_url,
        reset=reset_day,
        color="#5AC8FA"
    )

    # 生成规则集部分（基于当前全局配置中已启用的规则）
    rule_sets_lines = []
    enabled_rules = []
    for rule in global_config.rule_sets:
        if rule.enabled:
            rule_sets_lines.append(
                f"RULE-SET,{rule.url},{rule.policy},update-interval={rule.update_interval}"
            )
            enabled_rules.append({"name": rule.name, "policy": rule.policy})
    rule_sets_str = "\n".join(rule_sets_lines) if rule_sets_lines else "# 暂无规则集配置"

    # 地区分组（使用系统默认区域）
    region_list = ["🇭🇰 香港", "🇯🇵 日本", "🇺🇸 美国", "🇸🇬 狮城", "🇬🇧 英国", "🇨🇳 台湾"]
    regions_str = ",".join(region_list)

    region_strategy = "\n".join([
        f"{r} = select,{r}最佳,{r}智能,🔧 手动切换"
        for r in region_list
    ])
    region_auto = "\n".join(
        [f"{r}最佳 = url-test,<{r}节点...>,url=http://www.gstatic.com/generate_204,interval=300,tolerance=50"
         for r in region_list]
        + [f"{r}智能 = smart,<{r}节点...>,persistent=1"
           for r in region_list]
    )

    # 代理节点占位符
    placeholder_proxies = (
        f"# ↓ 此处将自动填入来自 [{name}] 的节点（更新订阅后生成）\n"
        f"# 示例：香港 01 = ss, hk.example.com, 443, encrypt-method=chacha20-ietf-poly1305, password=xxx"
    )
    placeholder_one_line = f"# {name} 的所有节点（逗号分隔）"

    try:
        preview_config = conf_template.format(
            cos_url=cos_url,
            update_interval=update_interval,
            module_panel=module_panel,
            module_script=module_script,
            proxies=placeholder_proxies,
            proxies_one_line=placeholder_one_line,
            regions=regions_str,
            region_strategy=region_strategy,
            region_auto=region_auto,
            rule_sets=rule_sets_str,
            host="# 将从 GitHub 自动加载最新 Hosts 配置"
        )
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"配置模板渲染失败: {str(e)}")

    return {
        "preview": preview_config,
        "rule_count": len(enabled_rules),
        "cos_url": cos_url,
        "update_interval": update_interval
    }


import httpx

class CheckAvailabilityRequest(BaseModel):
    names: List[str]

@app.post("/api/check-availabilities")
async def check_availabilities(request: CheckAvailabilityRequest, token: str = Depends(verify_token_from_request)):
    """检测机场配置链接的连通性"""
    global_conf = config_manager.get_global_config()
    domain = global_conf.txcos_domain
    
    if not domain:
        # 如果没有配置域名，返回错误
        return {name: {"status": "fail", "code": "无域名配置"} for name in request.names}
    
    # 确保域名格式正确
    base_url = domain.rstrip('/')
    if not base_url.startswith('http'):
        base_url = f"https://{base_url}"
    
    results = {}
    
    async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
        for name in request.names:
            airport = config_manager.get_airport(name)
            if not airport:
                results[name] = {"status": "fail", "code": "404"}
                continue
            
            # 构造完整URL
            target_url = f"{base_url}/{airport.key}"
            
            try:
                # 使用HEAD请求检测
                response = await client.head(target_url)
                
                # 如果HEAD不允许(405)，尝试GET
                if response.status_code == 405:
                    response = await client.get(target_url)
                
                if response.status_code == 200:
                    results[name] = {"status": "ok", "code": 200}
                else:
                    results[name] = {"status": "fail", "code": response.status_code}
            except httpx.RequestError as e:
                results[name] = {"status": "fail", "code": "Network Error"}
            except Exception as e:
                 results[name] = {"status": "fail", "code": str(e)}
                 
    return results


@app.get("/api/ai-models")
async def get_ai_models(token: str = Depends(verify_token_from_request)):
    """
    获取OpenRouter可用的AI模型列表
    优先从缓存获取，缓存1小时
    """
    import httpx
    from datetime import datetime, timedelta
    
    # 简单的内存缓存
    cache_key = "_openrouter_models_cache"
    cache_time_key = "_openrouter_models_cache_time"
    
    # 检查缓存
    if hasattr(app.state, cache_key):
        cache_time = getattr(app.state, cache_time_key, None)
        if cache_time and datetime.now() - cache_time < timedelta(hours=1):
            return getattr(app.state, cache_key)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://openrouter.ai/api/v1/models")
            
            if response.status_code != 200:
                # 返回默认模型列表
                return get_default_models()
            
            data = response.json()
            models = data.get("data", [])
            
            # 过滤和格式化模型
            formatted_models = []
            for model in models:
                model_id = model.get("id", "")
                pricing = model.get("pricing", {})
                
                # 判断是否免费
                is_free = (
                    ":free" in model_id or
                    (pricing.get("prompt") == "0" and pricing.get("completion") == "0")
                )
                
                # 提取厂商信息
                vendor = model_id.split('/')[0] if '/' in model_id else "other"
                
                formatted_models.append({
                    "id": model_id,
                    "name": model.get("name", model_id),
                    "description": model.get("description", ""),
                    "context_length": model.get("context_length", 0),
                    "pricing": {
                        "prompt": pricing.get("prompt", "0"),
                        "completion": pricing.get("completion", "0")
                    },
                    "is_free": is_free,
                    "vendor": vendor
                })
            
            # 缓存结果
            setattr(app.state, cache_key, formatted_models)
            setattr(app.state, cache_time_key, datetime.now())
            
            return formatted_models
            
    except Exception as e:
        print(f"获取OpenRouter模型列表失败: {e}")
        # 返回默认模型列表
        return get_default_models()


def get_default_models():
    """返回默认的模型列表（作为后备）"""
    return [
        {
            "id": "google/gemini-2.0-flash-exp:free",
            "name": "Google Gemini 2.0 Flash Exp",
            "description": "免费模型，速度快",
            "context_length": 1000000,
            "pricing": {"prompt": "0", "completion": "0"},
            "is_free": True,
            "vendor": "google"
        },
        {
            "id": "google/gemini-flash-1.5",
            "name": "Google Gemini 1.5 Flash",
            "description": "免费模型，稳定可靠",
            "context_length": 1000000,
            "pricing": {"prompt": "0", "completion": "0"},
            "is_free": True,
            "vendor": "google"
        },
        {
            "id": "meta-llama/llama-3.2-3b-instruct:free",
            "name": "Meta Llama 3.2 3B",
            "description": "开源免费模型",
            "context_length": 131072,
            "pricing": {"prompt": "0", "completion": "0"},
            "is_free": True,
            "vendor": "meta-llama"
        },
        {
            "id": "anthropic/claude-3.5-sonnet",
            "name": "Claude 3.5 Sonnet",
            "description": "高性能模型",
            "context_length": 200000,
            "pricing": {"prompt": "0.000003", "completion": "0.000015"},
            "is_free": False,
            "vendor": "anthropic"
        },
        {
            "id": "openai/gpt-4o",
            "name": "GPT-4o",
            "description": "OpenAI最新模型",
            "context_length": 128000,
            "pricing": {"prompt": "0.0000025", "completion": "0.00001"},
            "is_free": False,
            "vendor": "openai"
        },
        {
            "id": "meta-llama/llama-3.3-70b-instruct",
            "name": "Meta Llama 3.3 70B",
            "description": "经济型大模型",
            "context_length": 131072,
            "pricing": {"prompt": "0.00000035", "completion": "0.0000014"},
            "is_free": False,
            "vendor": "meta-llama"
        }
    ]


async def auto_update_task_func():
    """自动更新任务"""
    global auto_update_running
    logger.info("自动更新任务已启动")
    
    while auto_update_running:
        try:
            global_config = config_manager.get_global_config()
            interval = global_config.interval or 3600
            
            logger.info(f"等待 {interval} 秒后执行下次更新...")
            await asyncio.sleep(interval)
            
            if not auto_update_running:
                break
            
            logger.info("开始自动更新所有机场订阅...")
            
            # 更新所有机场
            from .updater import update_airport, merge_airports
            
            airports = config_manager.list_airports()
            for airport_name in airports:
                try:
                    airport = config_manager.get_airport(airport_name)
                    if airport:
                        logger.info(f"更新机场: {airport_name}")
                        # 在线程池中执行阻塞的更新操作
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            None,
                            update_airport,
                            airport,
                            global_config
                        )
                        if result.get('success'):
                            logger.info(f"机场 {airport_name} 更新成功")
                        else:
                            logger.error(f"机场 {airport_name} 更新失败: {result.get('error')}")
                except Exception as e:
                    logger.error(f"更新机场 {airport_name} 时出错: {str(e)}")
            
            # 如果配置了合并订阅，则执行合并
            if global_config.merge_airports and len(global_config.merge_airports) > 0:
                try:
                    logger.info(f"合并订阅: {global_config.merge_airports}")
                    # 在线程池中执行阻塞的合并操作
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        merge_airports,
                        global_config.merge_airports,
                        config_manager
                    )
                    if result.get('success'):
                        logger.info("订阅合并成功")
                    else:
                        logger.error(f"订阅合并失败: {result.get('error')}")
                except Exception as e:
                    logger.error(f"合并订阅时出错: {str(e)}")
                    
            logger.info("自动更新完成")
            
        except Exception as e:
            logger.error(f"自动更新任务出错: {str(e)}")
            await asyncio.sleep(60)  # 出错后等待1分钟再试
    
    logger.info("自动更新任务已停止")


@app.on_event("startup")
async def startup_event():
    """服务启动时执行"""
    global auto_update_task, auto_update_running
    
    logger.info("Surge订阅管理服务启动")
    logger.info(f"日志目录: {log_dir}")
    
    # 启动自动更新任务
    auto_update_running = True
    auto_update_task = asyncio.create_task(auto_update_task_func())
    logger.info("自动更新任务已创建")


@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭时执行"""
    global auto_update_task, auto_update_running
    
    logger.info("正在停止自动更新任务...")
    auto_update_running = False
    
    if auto_update_task:
        auto_update_task.cancel()
        try:
            await auto_update_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Surge订阅管理服务已停止")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "auto_update_running": auto_update_running,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/logs")
async def get_logs(lines: int = 100, token: str = Depends(verify_token_from_request)):
    """获取最近的日志"""
    try:
        log_file = log_dir / 'sub-surge.log'
        if not log_file.exists():
            return {"logs": []}
        
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return {"logs": recent_lines}
    except Exception as e:
        logger.error(f"读取日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"读取日志失败: {str(e)}")


@app.get("/api/policies")
async def get_policies(token: str = Depends(verify_token_from_request)):
    """获取可用的策略列表"""
    from .template import FIXED_POLICIES, REGION_POLICIES
    return {
        "fixed": FIXED_POLICIES,
        "regions": REGION_POLICIES,
        "all": FIXED_POLICIES + REGION_POLICIES
    }


@app.get("/api/rule-sets")
async def get_rule_sets(token: str = Depends(verify_token_from_request)):
    """获取所有规则集"""
    from .config_schema import RuleSet
    return [rule.dict() for rule in config_manager.get_global_config().rule_sets]


@app.post("/api/rule-sets")
async def add_rule_set(rule: RuleSetRequest, token: str = Depends(verify_token_from_request)):
    """添加规则集"""
    from .config_schema import RuleSet
    try:
        new_rule = RuleSet(**rule.dict())
        config_manager.config.rule_sets.append(new_rule)
        config_manager._save_config()
        return {"message": "规则集添加成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"添加失败: {str(e)}")


@app.put("/api/rule-sets/{index}")
async def update_rule_set(index: int, rule: RuleSetRequest, token: str = Depends(verify_token_from_request)):
    """更新规则集"""
    from .config_schema import RuleSet
    try:
        if index < 0 or index >= len(config_manager.config.rule_sets):
            raise HTTPException(status_code=404, detail="规则集不存在")
        
        config_manager.config.rule_sets[index] = RuleSet(**rule.dict())
        config_manager._save_config()
        return {"message": "规则集更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新失败: {str(e)}")


@app.delete("/api/rule-sets/{index}")
async def delete_rule_set(index: int, token: str = Depends(verify_token_from_request)):
    """删除规则集"""
    try:
        if index < 0 or index >= len(config_manager.config.rule_sets):
            raise HTTPException(status_code=404, detail="规则集不存在")
        
        del config_manager.config.rule_sets[index]
        config_manager._save_config()
        return {"message": "规则集删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除失败: {str(e)}")


@app.post("/api/rule-sets/reorder")
async def reorder_rule_sets(request: dict, token: str = Depends(verify_token_from_request)):
    """重新排序规则集"""
    from .config_schema import RuleSet
    try:
        indices = request.get("indices", [])
        if len(indices) != len(config_manager.config.rule_sets):
            raise HTTPException(status_code=400, detail="索引数量不匹配")
        
        new_order = [config_manager.config.rule_sets[i] for i in indices]
        config_manager.config.rule_sets = new_order
        config_manager._save_config()
        return {"message": "规则集排序成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"排序失败: {str(e)}")


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """启动服务器"""
    import uvicorn
    logger.info(f"启动服务器: {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
