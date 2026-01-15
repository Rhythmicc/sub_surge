"""
订阅内容分析器
自动分析订阅内容，推荐配置参数
支持OpenRouter AI增强分析（通过Web界面配置）
"""
import re
import json
from typing import Dict, List, Optional
import base64
import httpx


def analyze_subscription(url: str = None, use_ai: bool = True, content: str = None) -> Dict:
    """
    分析订阅链接或订阅内容，自动推荐配置
    
    Args:
        url: 订阅链接（与content二选一）
        use_ai: 是否使用AI分析
        content: 直接提供的订阅内容（与url二选一）
    
    Returns:
        {
            "is_node_list": bool,
            "country_mapping": dict,
            "exclude_keywords": list,
            "confidence": float,  # 置信度 0-1
            "suggestions": {
                "name": str,
                "info_keywords": dict
            }
        }
    """
    try:
        # 获取订阅内容
        if content:
            # 使用直接提供的内容
            raw_content = content.encode('utf-8') if isinstance(content, str) else content
        elif url:
            # 下载订阅内容
            from QuickStart_Rhy.NetTools.NormalDL import normal_dl
            raw_content = normal_dl(url, "temp_analyze", write_to_memory=True)
        else:
            return {
                "error": "必须提供url或content参数",
                "confidence": 0
            }
        
        if not raw_content:
            return {
                "error": "无法获取订阅内容",
                "confidence": 0
            }
        
        # 智能判断是否需要Base64解码
        # 优先尝试直接解析为UTF-8（大多数订阅是明文）
        if isinstance(raw_content, bytes):
            try:
                decoded = raw_content.decode('utf-8', errors='strict')
                is_base64 = False
                
                # 检查是否是明文格式（包含Surge/Clash特征）
                has_config_markers = any(marker in decoded for marker in ['[Proxy]', '[Proxy Group]', 'proxies:', '= ss,', '= vmess,', '= trojan,'])
                
                # 如果没有明显的配置标记，且内容看起来像base64编码，尝试解码
                if not has_config_markers and len(decoded) > 100:
                    content_clean = decoded.replace('\n', '').replace('\r', '').replace(' ', '')
                    base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
                    if len(content_clean) > 0 and all(c in base64_chars for c in content_clean):
                        try:
                            decoded_b64 = base64.b64decode(content_clean).decode('utf-8', errors='ignore')
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
                    decoded = raw_content.decode('utf-8', errors='ignore')
                    is_base64 = False
        else:
            # 已经是字符串
            decoded = raw_content
            is_base64 = False
        
        lines = decoded.split('\n')
        
        # 分析结果
        result = {
            "template": "generic",
            "is_node_list": False,
            "country_mapping": {},
            "exclude_keywords": [],
            "confidence": 0.5,
            "suggestions": {
                "name": "",
                "info_keywords": {}
            },
            "analysis": {
                "node_count": 0,
                "countries": [],
                "has_info_section": False,
                "format_type": "unknown"
            }
        }
        
        # 检测格式
        if '[Proxy]' in decoded:
            result["analysis"]["format_type"] = "surge"
            result["is_node_list"] = False
        elif is_base64 and any(line.startswith(('ss://', 'vmess://', 'trojan://')) for line in lines):
            result["analysis"]["format_type"] = "node_list"
            result["is_node_list"] = True
        
        # 分析节点
        countries_found = set()
        node_count = 0
        
        # 检测国家名称
        country_patterns = {
            # 英文
            "Hong Kong": "香港",
            "USA": "美国", 
            "United States": "美国",
            "Japan": "日本",
            "Singapore": "新加坡",
            "Taiwan": "台湾",
            "UK": "英国",
            "United Kingdom": "英国",
            "Korea": "韩国",
            "Germany": "德国",
            "France": "法国",
            "Canada": "加拿大",
            "Australia": "澳大利亚",
            "Netherlands": "荷兰",
            "Russia": "俄罗斯",
            "Switzerland": "瑞士",
            "Bulgaria": "保加利亚",
            "Austria": "奥地利",
            "Ireland": "爱尔兰",
            "Turkey": "土耳其",
            "Italy": "意大利",
            "Hungary": "匈牙利",
            "Brazil": "巴西",
            "India": "印度",
            "Indonesia": "印度尼西亚",
            "Argentina": "阿根廷",
            "Chile": "智利",
            "Sweden": "瑞典"
        }
        
        for line in lines:
            # 检测节点
            if '=' in line or line.startswith(('ss://', 'vmess://', 'trojan://')):
                node_count += 1
                
                # 检测国家
                for en_name, zh_name in country_patterns.items():
                    if en_name.lower() in line.lower():
                        countries_found.add(en_name)
        
        result["analysis"]["node_count"] = node_count
        result["analysis"]["countries"] = sorted(list(countries_found))
        
        # 检测信息关键词
        info_keywords = {
            "traffic": [],
            "reset": [],
            "expire": []
        }
        
        for line in lines:
            line_lower = line.lower()
            if 'bandwidth' in line_lower or 'traffic' in line_lower:
                info_keywords["traffic"].append("Bandwidth")
                result["analysis"]["has_info_section"] = True
            if 'g |' in line_lower:
                info_keywords["traffic"].append("G |")
                result["analysis"]["has_info_section"] = True
            if 'reset' in line_lower:
                info_keywords["reset"].append("Reset")
                result["analysis"]["has_info_section"] = True
            if 'date' in line_lower or 'expire' in line_lower or '到期' in line:
                info_keywords["expire"].append("Date")
                result["analysis"]["has_info_section"] = True
        
        # 去重
        for key in info_keywords:
            info_keywords[key] = list(set(info_keywords[key]))
        
        result["suggestions"]["info_keywords"] = info_keywords
        
        # 生成国家映射（只包含检测到的国家）
        result["country_mapping"] = {
            en: zh for en, zh in country_patterns.items()
            if en in countries_found
        }
        
        # 静态分析的置信度
        result["confidence"] = 0.7 if len(countries_found) > 10 else 0.6
        
        # 推荐排除关键词
        common_exclude = ["direct", "premium", "expired", "traffic-exceed"]
        result["exclude_keywords"] = common_exclude
        
        # 推荐机场名称（从URL中提取）
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # 提取域名主要部分
            domain_parts = domain.split('.')
            if len(domain_parts) > 1:
                result["suggestions"]["name"] = domain_parts[-2].capitalize()
        except:
            pass
        
        # 如果启用AI增强分析，则调用OpenRouter
        if use_ai:
            try:
                ai_result = analyze_with_ai(decoded, result)
                if ai_result:
                    # 合并AI分析结果
                    result.update(ai_result)
                    result["confidence"] = max(result.get("confidence", 0.5), 0.9)
                    result["analysis_method"] = "ai"
            except Exception as e:
                # AI分析失败，使用静态分析结果
                result["ai_error"] = str(e)
                result["analysis_method"] = "static"
        else:
            result["analysis_method"] = "static"
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "template": "generic",
            "confidence": 0,
            "suggestions": {},
            "analysis_method": "error"
        }


def analyze_with_ai(content: str, static_analysis: Dict) -> Optional[Dict]:
    """
    使用OpenRouter AI分析订阅内容
    配置AI API Key和模型请访问前端管理界面
    """
    # 从配置文件读取AI设置
    from .config_manager import ConfigManager
    config_manager = ConfigManager()
    global_config = config_manager.get_global_config()
    
    api_key = global_config.ai_api_key
    api_url = global_config.ai_base_url
    model = global_config.ai_model
    
    if not api_key:
        print("⚠️  未配置AI API Key，请在Web界面的【全局配置】中配置")
        return None
    
    # 提取代理节点行（而不是前50行所有内容）
    # 节点格式示例：
    # - Surge: 节点名 = trojan, host, port, password=xxx, ...
    # - node_list: ss://xxx, vmess://xxx, trojan://xxx
    lines = content.split('\n')
    proxy_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        # Surge格式的节点定义
        if any(protocol in line for protocol in ['= ss,', '= vmess,', '= trojan,', '= hysteria2,', '= hysteria,', '= tuic,']):
            proxy_lines.append(line_stripped)
        # node_list格式（URL形式）
        elif line_stripped.startswith(('ss://', 'vmess://', 'trojan://', 'hysteria://', 'hysteria2://', 'tuic://')):
            proxy_lines.append(line_stripped)
        # Clash格式
        elif line_stripped.startswith('- {') or (line_stripped.startswith('- name:') and 'type:' in content):
            proxy_lines.append(line_stripped)
    
    # 提取节点名称
    node_names = []
    for line in proxy_lines:
        # Surge格式：节点名 = 协议, host, port, ...
        if ' = ' in line and any(proto in line for proto in ['ss,', 'vmess,', 'trojan,', 'hysteria2,', 'hysteria,', 'tuic,']):
            node_name = line.split(' = ')[0].strip()
            node_names.append(node_name)
        # node_list格式：提取最后一个#后的名称，或整个URL
        elif line.startswith(('ss://', 'vmess://', 'trojan://', 'hysteria://', 'hysteria2://', 'tuic://')):
            if '#' in line:
                node_name = line.split('#')[-1].strip()
            else:
                node_name = line
            node_names.append(node_name)
        # Clash格式
        elif 'name:' in line:
            parts = line.split('name:')
            if len(parts) > 1:
                node_name = parts[1].split('\n')[0].strip()
                node_names.append(node_name)
    
    sample = ', '.join(node_names)
    sample_note = f"（共 {len(node_names)} 个节点）"
    
    # 构建提示词
    prompt = f"""分析以下Surge/Clash代理节点，自动生成完整的配置建议。

**核心目标：节点名称国家/地区映射**
将每个节点的名称重新映射为其对应的国家/地区名称，例如：
- 输入: "[深圳联通入口] 中国台湾 省际专线" → 输出: "台湾" 或 "台湾 [联通]"
- 输入: "🇯🇵 Tokyo 01" → 输出: "日本东京"
- 输入: "HK-Premium-01" → 输出: "香港"

节点名称 {sample_note}:
```
{sample}
```

静态分析结果参考:
- 检测到 {static_analysis.get('analysis', {}).get('node_count', 0)} 个节点
- 格式: {static_analysis.get('analysis', {}).get('format_type')}
- 预分析的机场名: {static_analysis.get('suggestions', {}).get('name', '')}

请分析并返回JSON格式的完整配置建议，必须包含以下字段：
1. suggested_name: string （建议的机场名称，简短易记）
2. country_mapping: object （完整的国家名称映射表）
    - 通常，节点名可能包含如下内容：Emoji国旗, 国家/地区, 运营商, 节点号等其他信息。
    - 请生成映射，保留其中的"国家/地区（中文）", "运营商"信息，具体规则如下:
        1. 简单样例："🇨🇳 [深圳电信入口] 中国台湾 省际专线" 应映射为 "台湾 [电信]"，。
        2. 如果节点名称同时包含了国家和城市/省份等，如 "USA Seattle 01"，则映射为 {{"USA Seattle 01": "美国西雅图 01"}}。
        3. 但对于相同地区但有多个节点的情况：
            - "USA Seattle 01" 和 "USA Seattle 02"，则只生成一个地区映射: {{"USA Seattle": "美国西雅图"}}。
            - "Hong Kong 01" 和 "Hong Kong 02"，则生成映射为 {{"Hong Kong": "香港"}}。
        4. 如果一些地区只有一个节点，如 "Chile 01"，则生成映射为 {{"Chile 01": "智利"}}。
    - 请务必保证是“节点名的子字符串”到“重命名”的映射。
    - 这个字段会被 Python 的 `re.compile` 使用。
3. exclude_keywords: array of strings （建议排除的关键词，用于过滤节点）
4. info_keywords: object （信息提取关键词配置，格式: {{"traffic": ["流量相关的关键词"], "reset": ["重置时间相关的关键词"], "expire": ["到期日期相关的关键词"]}}）
    - 请务必识别节点名称中可能包含的流量、重置时间、到期日期等关键词，它们将从节点中移除以避免干扰。
    - 每次更新时，用户的流量、重置时间、到期日期尽管会在节点名称中出现，但节点名称可能变化，最好能够给出准确且简洁的关键词列表。
    - 流量信息可能不会显式的带有“流量”二字，还可能是“G”、"GB"等单位。
5. special_notes: string （特殊注意事项和建议）
6. confidence: number 0-1 （分析置信度）

注意事项：
- country_mapping 必须包含所有检测到的国家
- info_keywords 要根据实际订阅信息格式定制
- exclude_keywords 建议包含 expired、traffic-exceed 等常见关键词

请直接返回JSON，不要包含其他说明文字。"""
    
    # 调用OpenRouter API
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/rhythmicc/sub-surge",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "response_format": {"type": "json_object"},  # 强制JSON输出
                    "temperature": 0.3,  # 降低随机性
                }
            )
            
            if response.status_code != 200:
                return None
            
            result = response.json()
            ai_content = result["choices"][0]["message"]["content"]
            
            # 解析AI返回的JSON
            ai_analysis = json.loads(ai_content)
            
            # 转换为我们的格式（AI直接生成完整配置）
            return {
                "suggestions": {
                    "name": ai_analysis.get("suggested_name", static_analysis["suggestions"].get("name", "")),
                    "info_keywords": ai_analysis.get("info_keywords", {}),
                    "special_notes": ai_analysis.get("special_notes", "")
                },
                "country_mapping": ai_analysis.get("country_mapping", static_analysis.get("country_mapping", {})),
                "exclude_keywords": ai_analysis.get("exclude_keywords", []),
                "confidence": ai_analysis.get("confidence", 0.9)
            }
            
    except Exception as e:
        print(f"AI analysis failed: {e}")
        return None


def generate_ai_prompt(analysis: Dict) -> str:
    """生成AI提示，用于进一步优化配置"""
    
    prompt = f"""分析以下订阅链接的特征，推荐最佳配置：

节点数量: {analysis.get('analysis', {}).get('node_count', 0)}
检测到的国家: {', '.join(analysis.get('analysis', {}).get('countries', []))}
格式类型: {analysis.get('analysis', {}).get('format_type', 'unknown')}
包含流量信息: {analysis.get('analysis', {}).get('has_info_section', False)}

当前推荐:
- 模板: {analysis.get('template')}
- 节点列表格式: {analysis.get('is_node_list')}
- 置信度: {analysis.get('confidence')}

请给出配置建议：
1. 推荐的机场名称
2. 是否需要调整模板
3. 需要添加的特殊配置
4. 信息提取关键词建议
"""
    
    return prompt
