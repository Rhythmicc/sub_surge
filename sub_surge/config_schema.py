"""
配置驱动的机场格式化配置Schema
支持通过配置文件定义机场的格式化规则，而不是通过Python代码
"""
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, validator


class ProxyParserConfig(BaseModel):
    """代理节点解析配置"""
    
    # 节点名称替换规则
    country_name_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="国家/地区名称映射，如 'Hong Kong' -> '香港'"
    )
    
    # 节点过滤规则
    exclude_keywords: List[str] = Field(
        default_factory=list,
        description="排除包含这些关键词的节点，如 ['direct', 'premium']"
    )
    
    # 节点名称正则替换
    name_regex_replacements: List[Dict[str, str]] = Field(
        default_factory=list,
        description="正则表达式替换规则，如 [{'pattern': r'\\s+', 'replacement': ' '}]"
    )


class InfoExtractorConfig(BaseModel):
    """信息提取配置"""
    
    traffic_keywords: List[str] = Field(
        default=["Bandwidth", "G |"],
        description="流量信息关键词"
    )
    
    reset_keywords: List[str] = Field(
        default=["Reset", "重置"],
        description="重置日期关键词"
    )
    
    expire_keywords: List[str] = Field(
        default=["Date", "到期"],
        description="到期日期关键词"
    )
    
    # 信息提取正则表达式
    traffic_pattern: Optional[str] = Field(
        None,
        description="流量信息提取正则"
    )
    
    reset_pattern: Optional[str] = Field(
        None,
        description="重置日期提取正则"
    )
    
    expire_pattern: Optional[str] = Field(
        None,
        description="到期日期提取正则"
    )


class AirportConfig(BaseModel):
    """机场配置"""
    
    # 基本信息
    name: str = Field(..., description="机场名称")
    url: str = Field(..., description="订阅链接")
    key: str = Field(..., description="腾讯云COS存储路径")
    
    # 配置类型
    is_node_list: bool = Field(
        default=False,
        description="是否为节点列表格式（需要base64解码）"
    )
    
    # 解析配置
    parser_config: ProxyParserConfig = Field(
        default_factory=ProxyParserConfig,
        description="代理节点解析配置"
    )
    
    # 信息提取配置
    info_extractor: InfoExtractorConfig = Field(
        default_factory=InfoExtractorConfig,
        description="信息提取配置"
    )
    
    # 其他配置
    reset_day: int = Field(default=30, description="流量重置周期（天）")
    timezone_offset: int = Field(default=8, description="时区偏移（小时）")
    panel_color: Optional[str] = Field(None, description="面板颜色（十六进制）")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("机场名称不能为空")
        return v.strip()
    
    @validator('url')
    def validate_url(cls, v):
        if not v or not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError("订阅链接必须是有效的HTTP/HTTPS URL")
        return v


class RuleSet(BaseModel):
    """规则集配置"""
    name: str = Field(..., description="规则集名称")
    url: str = Field(..., description="规则集URL")
    policy: str = Field(..., description="策略名称")
    enabled: bool = Field(default=True, description="是否启用")
    update_interval: int = Field(default=86400, description="更新间隔（秒）")


class GlobalConfig(BaseModel):
    """全局配置"""
    
    txcos_domain: Optional[str] = Field(None, description="腾讯云对象存储域名")
    interval: int = Field(default=3600, description="订阅更新间隔（秒）")
    merge_key: str = Field(default="merge.conf", description="合并配置文件名")
    merge_airports: List[str] = Field(default_factory=list, description="要合并的机场列表")
    
    # AI配置
    ai_api_key: Optional[str] = Field(None, description="OpenRouter API密钥")
    ai_base_url: str = Field(
        default="https://openrouter.ai/api/v1/chat/completions",
        description="AI API端点URL"
    )
    ai_model: str = Field(
        default="google/gemini-2.0-flash-exp:free",
        description="AI模型名称"
    )
    
    # 规则集配置
    rule_sets: List[RuleSet] = Field(default_factory=lambda: [
        RuleSet(name="日本域名", url="https://raw.githubusercontent.com/Rhythmicc/ACL4SSR/master/Clash/jp.list", policy="🇯🇵 日本", enabled=False),
        RuleSet(name="美国域名", url="https://raw.githubusercontent.com/Rhythmicc/ACL4SSR/master/Clash/us.list", policy="🇺🇸 美国", enabled=True),
        RuleSet(name="直连域名", url="https://raw.githubusercontent.com/Rhythmicc/ACL4SSR/master/Clash/direct.list", policy="DIRECT", enabled=True),
        RuleSet(name="局域网", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/LocalAreaNetwork.list", policy="🎯 全球直连", enabled=True),
        RuleSet(name="解禁", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/UnBan.list", policy="🎯 全球直连", enabled=True),
        RuleSet(name="广告拦截", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanAD.list", policy="🛑 全球拦截", enabled=True),
        RuleSet(name="应用净化", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanProgramAD.list", policy="🍃 应用净化", enabled=True),
        RuleSet(name="谷歌FCM", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/GoogleFCM.list", policy="📢 谷歌FCM", enabled=True),
        RuleSet(name="谷歌CN", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/GoogleCN.list", policy="🎯 全球直连", enabled=True),
        RuleSet(name="Steam CN", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/SteamCN.list", policy="🎯 全球直连", enabled=True),
        RuleSet(name="微软服务", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Microsoft.list", policy="Ⓜ️ 微软服务", enabled=True),
        RuleSet(name="苹果服务", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Apple.list", policy="🍎 苹果服务", enabled=True),
        RuleSet(name="Telegram", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Telegram.list", policy="📲 电报信息", enabled=True),
        RuleSet(name="国外媒体", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyMedia.list", policy="🌍 国外媒体", enabled=True),
        RuleSet(name="代理精简", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyLite.list", policy="🚀 节点选择", enabled=True),
        RuleSet(name="国内域名", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaDomain.list", policy="🎯 全球直连", enabled=True),
        RuleSet(name="国内IP", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaCompanyIp.list", policy="🎯 全球直连", enabled=True),
        RuleSet(name="Bing", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Bing.list", policy="Ⓜ️ 微软Bing", enabled=True),
        RuleSet(name="OneDrive", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/OneDrive.list", policy="Ⓜ️ 微软云盘", enabled=True),
        RuleSet(name="AI平台", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/AI.list", policy="💬 Ai平台", enabled=True),
        RuleSet(name="OpenAI", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/OpenAi.list", policy="💬 Ai平台", enabled=True),
        RuleSet(name="网易云音乐", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/NetEaseMusic.list", policy="🎯 全球直连", enabled=True),
        RuleSet(name="Epic", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Epic.list", policy="🎮 游戏平台", enabled=True),
        RuleSet(name="Origin", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Origin.list", policy="🎮 游戏平台", enabled=True),
        RuleSet(name="Sony", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Sony.list", policy="🎮 游戏平台", enabled=True),
        RuleSet(name="Steam", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Steam.list", policy="🎮 游戏平台", enabled=True),
        RuleSet(name="任天堂", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Nintendo.list", policy="🎮 游戏平台", enabled=True),
        RuleSet(name="YouTube", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/YouTube.list", policy="📹 油管视频", enabled=True),
        RuleSet(name="Netflix", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Netflix.list", policy="🎥 奈飞视频", enabled=True),
        RuleSet(name="巴哈姆特", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Bahamut.list", policy="📺 巴哈姆特", enabled=True),
        RuleSet(name="哔哩哔哩港澳台", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/BilibiliHMT.list", policy="📺 哔哩哔哩", enabled=True),
        RuleSet(name="哔哩哔哩", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Bilibili.list", policy="📺 哔哩哔哩", enabled=True),
        RuleSet(name="国内媒体", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaMedia.list", policy="🌏 国内媒体", enabled=True),
        RuleSet(name="GFW列表", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyGFWlist.list", policy="🚀 节点选择", enabled=True),
        RuleSet(name="下载工具", url="https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Download.list", policy="🎯 全球直连", enabled=True),
    ], description="规则集列表")
    
    # 机场配置列表
    airports: Dict[str, AirportConfig] = Field(
        default_factory=dict,
        description="机场配置字典，key为机场名称"
    )
