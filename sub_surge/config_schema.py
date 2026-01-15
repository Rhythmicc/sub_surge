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
    
    # 机场配置列表
    airports: Dict[str, AirportConfig] = Field(
        default_factory=dict,
        description="机场配置字典，key为机场名称"
    )
