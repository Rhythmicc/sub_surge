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


def surge_proxy_to_clash(surge_line: str) -> Dict:
    """
    将 Surge 代理配置转换为 Clash 格式
    
    支持的格式：
    - Shadowsocks: name = ss, server, port, encrypt-method=cipher, password=pwd
    - Trojan: name = trojan, server, port, password=pwd
    - VMess: name = vmess, server, port, username=uuid
    """
    if not surge_line or '=' not in surge_line:
        return None
    
    try:
        # 分割节点名和配置
        parts = surge_line.split('=', 1)
        if len(parts) != 2:
            return None
        
        name = parts[0].strip()
        config_str = parts[1].strip()
        
        # 分割配置参数
        params = [p.strip() for p in config_str.split(',')]
        if len(params) < 3:
            return None
        
        proxy_type = params[0].lower()
        server = params[1]
        port = int(params[2])
        
        # 解析参数字典
        param_dict = {}
        for param in params[3:]:
            if '=' in param:
                key, value = param.split('=', 1)
                param_dict[key.strip()] = value.strip()
        
        clash_proxy = {
            'name': name,
            'server': server,
            'port': port,
            'type': '',
            'udp': True
        }
        
        # Shadowsocks
        if proxy_type == 'ss':
            clash_proxy['type'] = 'ss'
            clash_proxy['cipher'] = param_dict.get('encrypt-method', 'aes-256-gcm')
            clash_proxy['password'] = param_dict.get('password', '')
        
        # Trojan
        elif proxy_type == 'trojan':
            clash_proxy['type'] = 'trojan'
            clash_proxy['password'] = param_dict.get('password', '')
            clash_proxy['sni'] = param_dict.get('sni', server)
            if 'skip-cert-verify' in param_dict:
                clash_proxy['skip-cert-verify'] = param_dict['skip-cert-verify'].lower() == 'true'
        
        # VMess
        elif proxy_type == 'vmess':
            clash_proxy['type'] = 'vmess'
            clash_proxy['uuid'] = param_dict.get('username', '')
            clash_proxy['alterId'] = int(param_dict.get('alter-id', '0'))
            clash_proxy['cipher'] = param_dict.get('encrypt-method', 'auto')
            if 'tls' in param_dict:
                clash_proxy['tls'] = param_dict['tls'].lower() == 'true'
        
        else:
            # 不支持的类型
            return None
        
        return clash_proxy
    
    except Exception as e:
        print(f"转换代理节点失败 {surge_line[:50]}: {e}")
        return None


def _get_rule_set_cache_path(url: str) -> str:
    """获取规则集缓存文件路径"""
    import hashlib
    import os
    from pathlib import Path
    
    # 使用 URL 的 MD5 作为缓存文件名
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    # 获取缓存目录
    cache_dir = os.environ.get('SUB_SURGE_CONFIG_DIR')
    if cache_dir:
        cache_dir = Path(cache_dir) / "rule_cache"
    else:
        cache_dir = Path.home() / ".sub-surge" / "rule_cache"
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir / f"{url_hash}.txt")


def _load_cached_rule_set(url: str, max_age_hours: int = 24) -> str:
    """
    从缓存加载规则集，如果缓存不存在或过期则返回 None
    
    参数:
        url: 规则集 URL
        max_age_hours: 缓存最大有效期（小时），默认 24 小时
    
    返回:
        规则集内容，如果缓存无效则返回 None
    """
    import os
    import time
    
    cache_path = _get_rule_set_cache_path(url)
    
    if not os.path.exists(cache_path):
        return None
    
    # 检查缓存是否过期
    file_mtime = os.path.getmtime(cache_path)
    current_time = time.time()
    age_hours = (current_time - file_mtime) / 3600
    
    if age_hours > max_age_hours:
        print(f"缓存已过期 ({age_hours:.1f}小时): {url}")
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"使用缓存 ({age_hours:.1f}小时): {url}")
        return content
    except Exception as e:
        print(f"读取缓存失败: {e}")
        return None


def _save_rule_set_cache(url: str, content: str):
    """保存规则集到缓存"""
    try:
        cache_path = _get_rule_set_cache_path(url)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"保存缓存失败: {e}")


def generate_clash_config(surge_content: str, include_rules: bool = True) -> str:
    """
    将 Surge 配置转换为 Clash 配置
    
    参数:
        surge_content: Surge 配置内容
        include_rules: 是否包含规则部分（下载并转换规则集）
    
    返回:
        Clash YAML 配置字符串
    """
    import yaml
    import httpx
    import re
    from .template import clash_template
    
    # 加载基础模板
    config = yaml.safe_load(clash_template)
    
    # 解析 Surge 配置，提取代理节点
    lines = surge_content.split('\n')
    proxies = []
    rule_set_lines = []
    hosts = {}
    surge_proxy_groups = []
    
    # 找到各个部分
    in_proxy_section = False
    in_proxy_group_section = False
    in_rule_section = False
    in_host_section = False
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped == "[Proxy]":
            in_proxy_section = True
            in_proxy_group_section = False
            in_rule_section = False
            in_host_section = False
            continue
        
        if line_stripped == "[Proxy Group]":
            in_proxy_section = False
            in_proxy_group_section = True
            in_rule_section = False
            in_host_section = False
            continue
        
        if line_stripped == "[Rule]":
            in_proxy_section = False
            in_proxy_group_section = False
            in_rule_section = True
            in_host_section = False
            continue
        
        if line_stripped == "[Host]":
            in_proxy_section = False
            in_proxy_group_section = False
            in_rule_section = False
            in_host_section = True
            continue
        
        if line_stripped.startswith("[") and line_stripped not in ["[Proxy]", "[Proxy Group]", "[Rule]", "[Host]"]:
            in_proxy_section = False
            in_proxy_group_section = False
            in_rule_section = False
            in_host_section = False
            continue
        
        # 提取代理节点
        if in_proxy_section and line_stripped and not line_stripped.startswith('#'):
            if line_stripped.upper() == 'DIRECT = DIRECT':
                continue
            
            clash_proxy = surge_proxy_to_clash(line_stripped)
            if clash_proxy:
                proxies.append(clash_proxy)
        
        # 提取策略组：格式为 "name = type,proxy1,proxy2,..."
        if in_proxy_group_section and line_stripped and not line_stripped.startswith('#'):
            if '=' in line_stripped:
                surge_proxy_groups.append(line_stripped)
        
        # 提取规则集（RULE-SET 行）
        if in_rule_section and line_stripped and not line_stripped.startswith('#'):
            if line_stripped.startswith('RULE-SET,'):
                rule_set_lines.append(line_stripped)
        
        # 提取 Host 映射：格式为 "IP = domain"
        if in_host_section and line_stripped and not line_stripped.startswith('#'):
            if '=' in line_stripped:
                parts = line_stripped.split('=', 1)
                if len(parts) == 2:
                    ip = parts[0].strip()
                    domain = parts[1].strip()
                    hosts[ip] = domain
    
    # 更新配置
    config['proxies'] = proxies
    
    # 获取所有节点名称
    proxy_names = [p['name'] for p in proxies]
    
    # 转换 Surge 策略组为 Clash 格式
    clash_proxy_groups = []
    
    for surge_group in surge_proxy_groups:
        try:
            # 解析 Surge 策略组：name = type,proxy1,proxy2,...
            parts = surge_group.split('=', 1)
            if len(parts) != 2:
                continue
            
            group_name = parts[0].strip()
            group_config = parts[1].strip()
            config_parts = [p.strip() for p in group_config.split(',')]
            
            if len(config_parts) < 1:
                continue
            
            group_type = config_parts[0]
            
            # 跳过特殊的分隔符策略组
            if '———' in group_name or '——' in group_name:
                continue
            
            clash_group = {
                'name': group_name,
                'type': 'select',  # Clash 默认使用 select
                'proxies': []
            }
            
            # 分离代理列表和参数
            proxies_list = []
            params = {}
            
            for item in config_parts[1:]:
                if '=' in item:
                    # 这是参数，格式为 key=value
                    key, value = item.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    params[key] = value
                else:
                    # 这是代理名称
                    proxies_list.append(item)
            
            # 处理策略组类型
            if group_type == 'select':
                clash_group['type'] = 'select'
            elif group_type == 'url-test':
                clash_group['type'] = 'url-test'
                # 从参数中读取，或使用默认值
                clash_group['url'] = params.get('url', 'http://www.gstatic.com/generate_204')
                clash_group['interval'] = int(params.get('interval', '300'))
                if 'tolerance' in params:
                    clash_group['tolerance'] = int(params['tolerance'])
            elif group_type == 'smart':
                # Surge smart 策略对应 Clash load-balance
                clash_group['type'] = 'load-balance'
                clash_group['url'] = params.get('url', 'http://www.gstatic.com/generate_204')
                clash_group['interval'] = int(params.get('interval', '300'))
                clash_group['strategy'] = 'consistent-hashing'
                # persistent 参数在 Clash 中不支持，忽略
            
            # 添加代理列表
            clash_group['proxies'] = proxies_list
            clash_proxy_groups.append(clash_group)
            
        except Exception as e:
            print(f"解析策略组失败 {surge_group[:50]}: {e}")
            continue
    
    # 如果成功解析了策略组，使用解析的策略组；否则使用模板的默认策略组
    if clash_proxy_groups:
        config['proxy-groups'] = clash_proxy_groups
    else:
        # 更新默认代理组
        if config.get('proxy-groups'):
            for group in config['proxy-groups']:
                if group['name'] == '🚀 手动切换':
                    group['proxies'] = ['♻️ 自动选择'] + proxy_names
                elif group['name'] == '♻️ 自动选择':
                    group['proxies'] = proxy_names
    
    # 处理规则集
    if include_rules and rule_set_lines:
        clash_rules = []
        
        # 获取所有策略组名称用于映射
        policy_names = set()
        if config.get('proxy-groups'):
            policy_names = {group['name'] for group in config['proxy-groups']}
        policy_names.add('DIRECT')
        policy_names.add('REJECT')
        
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            for rule_line in rule_set_lines:
                try:
                    # 解析 RULE-SET,URL,POLICY[,update-interval=xxx]
                    parts = rule_line.split(',')
                    if len(parts) < 3:
                        continue
                    
                    rule_url = parts[1].strip()
                    policy = parts[2].split(',')[0].strip()  # 去除可能的 update-interval
                    
                    # 尝试从缓存加载规则集内容
                    rule_content = _load_cached_rule_set(rule_url, max_age_hours=24)
                    
                    if rule_content is None:
                        # 缓存不存在或已过期，下载规则集
                        print(f"下载规则集: {rule_url}")
                        response = client.get(rule_url)
                        response.raise_for_status()
                        rule_content = response.text
                        # 保存到缓存
                        _save_rule_set_cache(rule_url, rule_content)
                    
                    # 将规则转换为 Clash 格式
                    for rule in rule_content.strip().split('\n'):
                        rule = rule.strip()
                        if not rule or rule.startswith('#'):
                            continue
                        
                        # 解析规则
                        rule_parts = rule.split(',')
                        if len(rule_parts) < 2:
                            continue
                        
                        rule_type = rule_parts[0].strip().upper()
                        
                        # 忽略 USER-AGENT 和 URL-REGEX 规则（Clash 不支持）
                        if rule_type in ['USER-AGENT', 'URL-REGEX']:
                            continue
                        
                        # 处理规则的策略部分
                        if len(rule_parts) >= 3:
                            # 规则已包含策略
                            original_policy = rule_parts[-1].strip()
                            # 检查是否有 no-resolve 选项
                            if len(rule_parts) >= 4 and rule_parts[-1].strip().lower() == 'no-resolve':
                                original_policy = rule_parts[-2].strip()
                                has_no_resolve = True
                            else:
                                has_no_resolve = rule_parts[-1].strip().lower() == 'no-resolve'
                                if has_no_resolve:
                                    original_policy = rule_parts[-2].strip() if len(rule_parts) >= 4 else policy
                            
                            # 如果原策略不在我们的策略组中，使用 rule-set 指定的策略
                            if original_policy not in policy_names:
                                original_policy = policy
                            
                            clash_rule = ','.join(rule_parts[:-1]) + f',{original_policy}'
                            clash_rules.append(clash_rule)
                        else:
                            # 规则不包含策略，添加策略
                            clash_rules.append(f"{rule},{policy}")
                
                except Exception as e:
                    print(f"处理规则集失败 {rule_url}: {e}")
                    continue
        
        # 添加规则到配置（在 GEOIP 和 MATCH 之前）
        if clash_rules:
            config['rules'] = clash_rules + config.get('rules', [])
    
    # 添加 Host 映射
    if hosts:
        config['hosts'] = hosts
    
    # 转换为 YAML
    return yaml.dump(config, allow_unicode=True, sort_keys=False)

