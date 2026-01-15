"""
订阅更新器
使用配置驱动的方式更新机场订阅
"""
import os
import base64
import urllib.parse
from typing import Dict, List

from .config_schema import AirportConfig, GlobalConfig
from .parser import parse_with_config
from .template import conf_template, traffic_module_template

from QuickProject import QproDefaultConsole


def download_subscription(url: str, name: str) -> str:
    """下载订阅内容"""
    try:
        import httpx
        
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            content = response.text
        
        return content
    except Exception as e:
        raise Exception(f"下载订阅失败: {str(e)}")


def parse_node_list(url: str, name: str) -> List[str]:
    """解析节点列表格式的订阅"""
    try:
        import httpx
        
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            content = response.content
        
        decoded = base64.b64decode(content).decode('utf-8')
        nodes = decoded.strip().split('\n')
        
        node_list = []
        for node in nodes:
            parsed_url = urllib.parse.urlparse(node)
            protocol = parsed_url.scheme
            host = parsed_url.hostname
            port = parsed_url.port
            password = parsed_url.username
            name_encoded = parsed_url.fragment
            node_name = urllib.parse.unquote(name_encoded)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            sni = query_params.get("sni", [None])[0]
            
            param_parts = [f"password={password}"]
            if sni:
                param_parts.append(f"sni={sni}")
            param_parts.append("skip-cert-verify=false")
            param_parts.append("tfo=false")
            param_parts.append("udp-relay=true")
            
            params_string = ", ".join(param_parts)
            node_list.append(f"{node_name} = {protocol}, {host}, {port}, {params_string}")
        
        return node_list
    except Exception as e:
        raise Exception(f"解析节点列表失败: {str(e)}")


def parse_host_list(content: str) -> str:
    """解析hosts文件"""
    host = ""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            host += f"{parts[0]} = {parts[1]}\n"
    return host


def update_airport(
    airport_config: AirportConfig, 
    global_config: GlobalConfig,
    disable_upload: bool = False
) -> Dict:
    """更新机场订阅"""
    
    try:
        # 下载订阅内容
        if airport_config.is_node_list:
            proxy_list = parse_node_list(airport_config.url, airport_config.name)
            lines = ["[Proxy]"] + proxy_list + ["["]
            other_infos = {}
        else:
            content = download_subscription(airport_config.url, airport_config.name)
            lines = [line.strip() for line in content.splitlines()]
            
            # 使用配置驱动的解析器
            proxy_list, other_infos = parse_with_config(lines, airport_config)
        
        # 处理信息节点
        all_proxy_list = proxy_list.copy()
        for _, info_value in other_infos.items():
            if not info_value:
                continue

            # 寻找匹配的代理节点并替换为信息节点
            for _, line in enumerate(all_proxy_list):
                if info_value in line:
                    proxy_list.remove(line)
                    break
        
        # 生成配置文件
        import random
        
        # 生成面板颜色
        if airport_config.panel_color:
            color = airport_config.panel_color
        else:
            color = f"#{random.randint(0, 0xFFFFFF):06X}"
        
        # URL编码
        encoded_url = urllib.parse.quote(airport_config.url, safe="")
        
        # 区域分组
        aim_regions = {
            "香港": "🇭🇰 香港",
            "日本": "🇯🇵 日本",
            "美国": "🇺🇸 美国",
            "新加坡": "🇸🇬 狮城",
            "英国": "🇬🇧 英国",
            "台湾": "🇨🇳 台湾",
        }
        
        regions = {}
        for proxy in proxy_list:
            for key, display_name in aim_regions.items():
                if key in proxy:
                    if display_name not in regions:
                        regions[display_name] = []
                    regions[display_name].append(proxy.split("=")[0].strip())
                    break
        
        # 下载hosts
        import httpx
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(
                    "https://raw.githubusercontent.com/maxiaof/github-hosts/refs/heads/master/hosts"
                )
                response.raise_for_status()
                hosts_content = response.text
            host_config = parse_host_list(hosts_content)
        except Exception as e:
            # 如果下载失败，使用空配置
            host_config = ""
        
        # 生成规则集配置
        rule_sets_lines = []
        for rule in global_config.rule_sets:
            if rule.enabled:
                rule_sets_lines.append(
                    f"RULE-SET,{rule.url},{rule.policy},update-interval={rule.update_interval}"
                )
        rule_sets_config = "\n".join(rule_sets_lines)
        
        # 构建配置参数
        config_params = {
            "cos_url": f"{global_config.txcos_domain}/{airport_config.key}",
            "proxies": "\n".join(proxy_list),
            "proxies_one_line": ",".join([p.split("=")[0].strip() for p in proxy_list if p]),
            "module_panel": traffic_module_template["panel"].format(name=airport_config.name, update_interval=global_config.interval),
            "module_script": traffic_module_template["script"].format(
                name=airport_config.name,
                url=encoded_url,
                reset=airport_config.reset_day,
                color=color,
            ),
            "update_interval": global_config.interval,
            "host": host_config,
            "regions": ",".join(regions.keys()),
            "region_strategy": "\n".join([
                f"{region} = select,{region}最佳,{region}智能,🔧 手动切换" 
                for region in regions
            ]),
            "region_auto": "\n".join([
                f"{region}最佳 = url-test,{','.join(regions[region])},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50"
                for region in regions
            ] + [
                f"{region}智能 = smart,{','.join(regions[region])},persistent=1"
                for region in regions
            ]),
            "rule_sets": rule_sets_config
        }
        
        # 生成配置文件
        conf_content = conf_template.format(**config_params)
        
        # 保存临时文件
        temp_file = f".{airport_config.name}.conf"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(conf_content)
        
        # 上传到腾讯云COS
        if not disable_upload and global_config.txcos_domain:
            try:
                from QuickStart_Rhy.API.TencentCloud import TxCOS
                TxCOS().upload(temp_file, key=airport_config.key)
                os.remove(temp_file)
                
                result_url = f"{global_config.txcos_domain}/{airport_config.key}"
            except Exception as e:
                print(f"上传到COS失败: {e}")
                # 保存本地文件
                import shutil
                shutil.move(temp_file, f"{airport_config.name}.conf")
                result_url = f"{airport_config.name}.conf"
        else:
            # 保存本地文件
            import shutil
            shutil.move(temp_file, f"{airport_config.name}.conf")
            result_url = f"{airport_config.name}.conf"
        
        return {
            "success": True,
            "url": result_url,
            "proxy_count": len(proxy_list),
            "regions": list(regions.keys()),
            "infos": other_infos
        }
    
    except Exception as e:
        QproDefaultConsole.print(f"更新机场 {airport_config.name} 失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


def merge_airports(
    airport_names: List[str],
    config_manager
) -> Dict:
    """合并多个机场配置"""
    global_config = config_manager.get_global_config()
    
    try:
        import random
        
        all_proxies = []
        
        # 收集所有机场的代理
        for name in airport_names:
            airport = config_manager.get_airport(name)
            if not airport:
                continue
            
            # 更新单个机场（不上传）
            result = update_airport(airport, global_config, disable_upload=True)
            if result.get("success"):
                # 读取生成的配置文件
                conf_file = f"{name}.conf"
                if os.path.exists(conf_file):
                    with open(conf_file, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f.readlines()]
                    
                    proxy_list, _ = parse_with_config(lines, airport)
                    renamed_list = []
                    for item in proxy_list:
                        parts = item.split("=", 1)
                        if len(parts) == 2:
                            original_name = parts[0].strip()
                            if original_name == 'DIRECT':
                                continue
                            rest = parts[1]
                            new_name = f"{name}-{original_name}"
                            item = f"{new_name} = {rest}"
                        renamed_list.append(item)

                    all_proxies.extend(renamed_list)
                    
                    os.remove(conf_file)

        # 区域分组
        aim_regions = {
            "香港": "🇭🇰 香港",
            "日本": "🇯🇵 日本",
            "美国": "🇺🇸 美国",
            "新加坡": "🇸🇬 狮城",
            "英国": "🇬🇧 英国",
            "台湾": "🇨🇳 台湾",
        }
        
        regions = {}
        for proxy in all_proxies:  # 跳过第一个更新信息节点
            for key, display_name in aim_regions.items():
                if key in proxy:
                    if display_name not in regions:
                        regions[display_name] = []
                    regions[display_name].append(proxy.split("=")[0].strip())
                    break
        
        # 生成合并配置
        import httpx
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(
                    "https://raw.githubusercontent.com/maxiaof/github-hosts/refs/heads/master/hosts"
                )
                response.raise_for_status()
                hosts_content = response.text
            host_config = parse_host_list(hosts_content)
        except Exception as e:
            # 如果下载失败，使用空配置
            host_config = ""
        
        # 生成面板配置
        panel_configs = []
        script_configs = []
        for name in airport_names:
            airport = config_manager.get_airport(name)
            if not airport:
                continue
            
            encoded_url = urllib.parse.quote(airport.url, safe="")
            color = airport.panel_color or f"#{random.randint(0, 0xFFFFFF):06X}"
            
            panel_configs.append(
                traffic_module_template["panel"].format(name=name, update_interval=global_config.interval)
            )
            script_configs.append(
                traffic_module_template["script"].format(
                    name=name,
                    url=encoded_url,
                    reset=airport.reset_day,
                    color=color,
                )
            )
        
        # 生成规则集配置
        rule_sets_lines = []
        for rule in global_config.rule_sets:
            if rule.enabled:
                rule_sets_lines.append(
                    f"RULE-SET,{rule.url},{rule.policy},update-interval={rule.update_interval}"
                )
        rule_sets_config = "\n".join(rule_sets_lines)
        
        config_params = {
            "cos_url": f"{global_config.txcos_domain}/{global_config.merge_key}",
            "proxies": "\n".join(all_proxies),
            "proxies_one_line": ",".join([p.split("=")[0].strip() for p in all_proxies[1:] if p]),
            "module_panel": "\n".join(panel_configs),
            "module_script": "\n".join(script_configs),
            "update_interval": global_config.interval,
            "host": host_config,
            "regions": ",".join(regions.keys()),
            "region_strategy": "\n".join([
                f"{region} = select,{region}最佳,{region}智能,🔧 手动切换" 
                for region in regions
            ]),
            "region_auto": "\n".join([
                f"{region}最佳 = url-test,{','.join(regions[region])},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50"
                for region in regions
            ] + [
                f"{region}智能 = smart,{','.join(regions[region])},persistent=1"
                for region in regions
            ]),
            "rule_sets": rule_sets_config
        }
        
        conf_content = conf_template.format(**config_params)
        
        # 保存并上传
        temp_file = ".merge.conf"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(conf_content)
        
        if global_config.txcos_domain:
            from QuickStart_Rhy.API.TencentCloud import TxCOS
            TxCOS().upload(temp_file, key=global_config.merge_key)
            os.remove(temp_file)
            
            result_url = f"{global_config.txcos_domain}/{global_config.merge_key}"
        else:
            import shutil
            shutil.move(temp_file, "merge.conf")
            result_url = "merge.conf"
        
        return {
            "success": True,
            "url": result_url,
            "airport_count": len(airport_names),
            "proxy_count": len(all_proxies) - 1,
            "regions": list(regions.keys())
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
