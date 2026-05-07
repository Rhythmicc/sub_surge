"""
订阅内容分析器
自动分析订阅内容，推荐配置参数
支持OpenRouter AI增强分析（通过Web界面配置）
"""
import asyncio
import binascii
from datetime import datetime
import re
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlsplit
import base64
import httpx


DEFAULT_NODE_HEALTH_TIMEOUT = 3.0
DEFAULT_NODE_HEALTH_LIMIT = 50
DEFAULT_NODE_HEALTH_CONCURRENCY = 20


async def fetch_subscription_content(url: str) -> bytes:
    """异步下载订阅内容"""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


def decode_subscription_content(raw_content: Any) -> Tuple[str, bool]:
    """智能解码订阅内容，并标记原始内容是否为 Base64 订阅"""
    if raw_content is None:
        return "", False

    normalized_content = raw_content.encode('utf-8') if isinstance(raw_content, str) else raw_content
    decoded = ""
    is_base64 = False

    if isinstance(normalized_content, bytes):
        try:
            decoded = normalized_content.decode('utf-8', errors='strict')

            has_config_markers = any(
                marker in decoded
                for marker in ['[Proxy]', '[Proxy Group]', 'proxies:', '= ss,', '= vmess,', '= trojan,']
            )

            if not has_config_markers and len(decoded) > 100:
                content_clean = decoded.replace('\n', '').replace('\r', '').replace(' ', '')
                base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
                if content_clean and all(char in base64_chars for char in content_clean):
                    try:
                        decoded_b64 = base64.b64decode(content_clean).decode('utf-8', errors='ignore')
                        if any(marker in decoded_b64 for marker in ['[Proxy]', 'proxies:', 'ss://', 'vmess://', 'trojan://']):
                            decoded = decoded_b64
                            is_base64 = True
                    except (binascii.Error, ValueError):
                        pass
        except UnicodeDecodeError:
            try:
                decoded = base64.b64decode(normalized_content).decode('utf-8', errors='ignore')
                is_base64 = True
            except (binascii.Error, ValueError):
                decoded = normalized_content.decode('utf-8', errors='ignore')
                is_base64 = False
    else:
        decoded = str(normalized_content)

    return decoded, is_base64


def _decode_base64_text(payload: str) -> Optional[str]:
    """兼容标准和 URL-safe 的 Base64 解码"""
    normalized = payload.strip()
    if not normalized:
        return None

    padding = (-len(normalized)) % 4
    if padding:
        normalized += '=' * padding

    for decoder in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            return decoder(normalized).decode('utf-8', errors='ignore')
        except (binascii.Error, ValueError):
            continue

    return None


def _extract_endpoint_from_surge_line(line: str) -> Optional[Dict[str, Any]]:
    """从 Surge [Proxy] 行中提取节点地址"""
    if '=' not in line:
        return None

    name_part, config_part = line.split('=', 1)
    params = [item.strip() for item in config_part.split(',')]
    if len(params) < 3:
        return None

    try:
        port = int(params[2])
    except ValueError:
        return None

    return {
        "name": name_part.strip() or f"{params[1]}:{params[2]}",
        "protocol": params[0].lower(),
        "server": params[1].strip().strip('[]'),
        "port": port,
    }


def _extract_endpoint_from_uri(line: str) -> Optional[Dict[str, Any]]:
    """从 ss/vmess/trojan 等 URI 中提取节点地址"""
    line = line.strip()
    if '://' not in line:
        return None

    protocol = line.split('://', 1)[0].lower()
    name = unquote(line.split('#', 1)[1]) if '#' in line else ""

    if protocol == 'vmess':
        encoded = line.split('://', 1)[1].split('#', 1)[0]
        decoded = _decode_base64_text(encoded)
        if not decoded:
            return None

        try:
            payload = json.loads(decoded)
            server = (payload.get('add') or payload.get('server') or '').strip().strip('[]')
            port = int(payload.get('port'))
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

        return {
            "name": name or payload.get('ps') or f"{server}:{port}",
            "protocol": protocol,
            "server": server,
            "port": port,
        }

    if protocol == 'ss':
        fragment_free = line.split('#', 1)[0]
        parsed = urlsplit(fragment_free)

        if parsed.hostname and parsed.port:
            return {
                "name": name or f"{parsed.hostname}:{parsed.port}",
                "protocol": protocol,
                "server": parsed.hostname.strip('[]'),
                "port": parsed.port,
            }

        encoded = fragment_free.split('://', 1)[1].split('?', 1)[0]
        decoded = _decode_base64_text(encoded)
        if not decoded:
            return None

        parsed_decoded = urlsplit(f"//{decoded}")
        if not parsed_decoded.hostname or not parsed_decoded.port:
            return None

        return {
            "name": name or f"{parsed_decoded.hostname}:{parsed_decoded.port}",
            "protocol": protocol,
            "server": parsed_decoded.hostname.strip('[]'),
            "port": parsed_decoded.port,
        }

    parsed = urlsplit(line)
    if not parsed.hostname or not parsed.port:
        return None

    return {
        "name": name or f"{parsed.hostname}:{parsed.port}",
        "protocol": protocol,
        "server": parsed.hostname.strip('[]'),
        "port": parsed.port,
    }


def extract_node_candidates(decoded_content: str) -> List[Dict[str, Any]]:
    """从订阅文本中提取可探测的节点列表"""
    nodes: List[Dict[str, Any]] = []
    in_proxy_section = False

    for raw_line in decoded_content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(('#', ';', '//')):
            continue

        if line == '[Proxy]':
            in_proxy_section = True
            continue

        if line.startswith('[') and line != '[Proxy]':
            in_proxy_section = False
            continue

        endpoint = None
        if in_proxy_section:
            endpoint = _extract_endpoint_from_surge_line(line)
        elif line.startswith(('ss://', 'vmess://', 'trojan://', 'vless://', 'hysteria://', 'hysteria2://', 'tuic://')):
            endpoint = _extract_endpoint_from_uri(line)

        if endpoint:
            nodes.append(endpoint)

    return nodes


def analyze_subscription_raw(raw_content: Any, url: str = None, use_ai: bool = True) -> Dict:
    """基于原始订阅内容进行分析"""
    if not raw_content:
        return {
            "error": "无法获取订阅内容",
            "confidence": 0
        }

    try:
        decoded, is_base64 = decode_subscription_content(raw_content)
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
        except Exception:
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


async def inspect_subscription_node_health(
    url: str = None,
    content: Any = None,
    raw_content: Any = None,
    max_nodes: int = DEFAULT_NODE_HEALTH_LIMIT,
    timeout: float = DEFAULT_NODE_HEALTH_TIMEOUT,
) -> Dict[str, Any]:
    """检测订阅内节点入口的连通性，不等同于真实代理可用性验证"""
    report = {
        "probe_type": "tcp-connect",
        "verification_level": "entry",
        "verification_label": "入口连通性",
        "proxy_capable": False,
        "note": "当前结果仅表示节点入口是否接受 TCP 连接，不能证明认证、转发链路或出口可用性。",
        "recommendation": "如果要判断节点是否真的可代理出站，需要借助 Clash.Meta、sing-box、Xray 等代理内核加载节点后，再通过实际请求验证。",
        "checked_at": datetime.utcnow().replace(microsecond=0).isoformat() + 'Z',
        "total_nodes": 0,
        "tested_nodes": 0,
        "healthy_count": 0,
        "unhealthy_count": 0,
        "average_latency_ms": None,
        "limited": False,
        "results": [],
    }

    try:
        if raw_content is None:
            if content is not None:
                raw_content = content
            elif url:
                raw_content = await fetch_subscription_content(url)
            else:
                report["error"] = "必须提供 url、content 或 raw_content"
                return report

        decoded_content, _ = decode_subscription_content(raw_content)
        nodes = extract_node_candidates(decoded_content)
        report["total_nodes"] = len(nodes)

        if not nodes:
            report["error"] = "未检测到可探测的节点地址"
            return report

        selected_nodes = nodes[:max_nodes]
        report["limited"] = len(nodes) > max_nodes

        semaphore = asyncio.Semaphore(DEFAULT_NODE_HEALTH_CONCURRENCY)

        async def probe(node: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                started_at = time.perf_counter()
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(node["server"], node["port"]),
                        timeout=timeout,
                    )
                    latency_ms = max(int((time.perf_counter() - started_at) * 1000), 1)
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:
                        pass

                    return {
                        **node,
                        "status": "ok",
                        "latency_ms": latency_ms,
                        "error": None,
                    }
                except asyncio.TimeoutError:
                    return {
                        **node,
                        "status": "fail",
                        "latency_ms": None,
                        "error": "timeout",
                    }
                except OSError as exc:
                    return {
                        **node,
                        "status": "fail",
                        "latency_ms": None,
                        "error": str(exc),
                    }

        results = await asyncio.gather(*(probe(node) for node in selected_nodes))
        healthy = [item for item in results if item["status"] == "ok"]

        report["results"] = results
        report["tested_nodes"] = len(results)
        report["healthy_count"] = len(healthy)
        report["unhealthy_count"] = len(results) - len(healthy)
        if healthy:
            report["average_latency_ms"] = round(
                sum(item["latency_ms"] for item in healthy if item["latency_ms"] is not None) / len(healthy)
            )

        return report
    except Exception as exc:
        report["error"] = str(exc)
        return report


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
        if content is not None:
            raw_content = content.encode('utf-8') if isinstance(content, str) else content
        elif url:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                raw_content = response.content
        else:
            return {
                "error": "必须提供url或content参数",
                "confidence": 0
            }

        return analyze_subscription_raw(raw_content=raw_content, url=url, use_ai=use_ai)
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
