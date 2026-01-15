"""
配置驱动的代理解析器
根据配置文件动态解析机场订阅，而不是使用固定的Python代码
"""
import re
from typing import List, Dict
from datetime import datetime, timezone, timedelta
from itertools import islice

from .config_schema import AirportConfig


class ConfigDrivenParser:
    """基于配置的解析器"""
    
    def __init__(self, airport_config: AirportConfig):
        self.config = airport_config
        self.parser_config = airport_config.parser_config
        self.info_config = airport_config.info_extractor
        
        # 编译国家名称替换的正则表达式
        if self.parser_config.country_name_mapping:
            pattern = '|'.join(
                re.escape(name) 
                for name in self.parser_config.country_name_mapping.keys()
            )
            self.country_pattern = re.compile(pattern)
        else:
            self.country_pattern = None
    
    def replace_country_names(self, text: str) -> str:
        """替换国家/地区名称"""
        if not self.country_pattern:
            return text
        
        def replacer(match):
            return self.parser_config.country_name_mapping[match.group(0)]
        
        return self.country_pattern.sub(replacer, text)
    
    def should_exclude_proxy(self, line: str) -> bool:
        """判断是否应该排除该代理节点"""
        line_lower = line.lower()
        for keyword in self.parser_config.exclude_keywords:
            if keyword.lower() in line_lower:
                return True
        return False
    
    def apply_name_replacements(self, line: str) -> str:
        """应用正则表达式替换规则"""
        result = line
        for replacement in self.parser_config.name_regex_replacements:
            pattern = replacement.get('pattern')
            repl = replacement.get('replacement', '')
            if pattern:
                result = re.sub(pattern, repl, result)
        return result
    
    def get_proxies_list(self, lines: List[str]) -> List[str]:
        """从配置文件中提取代理列表"""
        try:
            # 找到 [Proxy] 部分
            start_index = None
            for i, line in enumerate(lines):
                if line.strip() == "[Proxy]":
                    start_index = i + 1
                    break
            
            if start_index is None:
                return []
            
            # 提取代理节点直到下一个section
            proxy_list = []
            for line in islice(lines, start_index, None):
                line = line.strip()
                if line.startswith("["):
                    break
                if not line:
                    continue
                
                # 应用过滤规则
                if self.should_exclude_proxy(line):
                    continue
                
                # 替换国家名称
                line = self.replace_country_names(line)
                
                # 应用自定义替换规则
                line = self.apply_name_replacements(line)
                
                proxy_list.append(line)
            
            return proxy_list
        
        except Exception as e:
            print(f"解析代理列表时出错: {e}")
            return []
    
    def extract_info_by_keywords(self, lines: List[str], keywords: List[str]) -> str:
        """根据关键词提取信息"""
        start_index = None
        for i, line in enumerate(lines):
            if line.strip() == "[Proxy]":
                start_index = i + 1
                break
        
        if start_index is None:
            return ""
        
        for line in islice(lines, start_index, None):
            line = line.strip()
            if line.startswith("["):
                break
            
            for keyword in keywords:
                if keyword in line:
                    # 尝试提取信息
                    if "=" in line:
                        # 格式: name = value
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return line
                    elif "：" in line:
                        # 格式: 关键词：值
                        return line.split("：", 1)[1].strip()
                    else:
                        return line
        
        return ""
    
    def extract_info_by_pattern(self, lines: List[str], pattern: str) -> str:
        """根据正则表达式提取信息"""
        if not pattern:
            return ""
        
        compiled_pattern = re.compile(pattern)
        start_index = None
        
        for i, line in enumerate(lines):
            if line.strip() == "[Proxy]":
                start_index = i + 1
                break
        
        if start_index is None:
            return ""
        
        for line in islice(lines, start_index, None):
            line = line.strip()
            if line.startswith("["):
                break
            
            match = compiled_pattern.search(line)
            if match:
                return match.group(0) if not match.groups() else match.group(1)
        
        return ""
    
    def get_other_infos(self, lines: List[str]) -> Dict[str, str]:
        """提取其他信息（流量、重置日期、到期日期等）"""
        infos = {}
        
        # 提取流量信息
        if self.info_config.traffic_pattern:
            traffic = self.extract_info_by_pattern(
                lines, self.info_config.traffic_pattern
            )
        else:
            traffic = self.extract_info_by_keywords(
                lines, self.info_config.traffic_keywords
            )
        if traffic:
            infos["流量"] = traffic
        
        # 提取重置日期
        if self.info_config.reset_pattern:
            reset = self.extract_info_by_pattern(
                lines, self.info_config.reset_pattern
            )
        else:
            reset = self.extract_info_by_keywords(
                lines, self.info_config.reset_keywords
            )
        if reset:
            infos["重置"] = reset
        
        # 提取到期日期
        if self.info_config.expire_pattern:
            expire = self.extract_info_by_pattern(
                lines, self.info_config.expire_pattern
            )
        else:
            expire = self.extract_info_by_keywords(
                lines, self.info_config.expire_keywords
            )
        if expire:
            infos["到期"] = expire
        
        # 添加更新时间
        tz = timezone(timedelta(hours=self.config.timezone_offset))
        update_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        infos["更新"] = update_time
        
        return infos


def parse_with_config(lines: List[str], airport_config: AirportConfig):
    """使用配置解析订阅内容"""
    parser = ConfigDrivenParser(airport_config)
    proxy_list = parser.get_proxies_list(lines)
    other_infos = parser.get_other_infos(lines)
    return proxy_list, other_infos
