# sub_surge

帮你在本地生成Surge的配置表（需要 Surge v5及以上版本）：

1. 支持热门地区（香港、台湾、日本、美国、英国、新加坡）的最佳和智能策略。
2. 自动配置GitHub Host，避免DNS污染。

## Install

```shell
pip3 install git+https://github.com/Rhythmicc/sub_surge.git -U
```

## Usage

```shell
sub_surge
```

注册机场时，需要创建个py文件，并实现如下两个函数:

1. `get_proxies_list`函数用于格式化节点名称，标记节点的国家/地区，处理后的节点列表会利用`main.py`中的`aim_regions`字典进行识别;
2. `get_other_infos`函数用于获取其他信息（如流量、重置时间、到期时间等）;

在当前版本中，`其他信息`会被自动去除，并使用[模组](https://github.com/Rabbit-Spec/Surge/tree/Master/Module/Panel/Sub-info)来获取机场基本信息。

以下是两个函数的示例实现，可以直接用于Nexitally：

```python
import re

def get_proxies_list(lines: list):
    proxy_list = []

    country_map = {
        "Hong Kong": "香港",
        "USA": "美国",
        "Japan": "日本",
        "Netherlands": "荷兰",
        "Russia": "俄罗斯",
        "Germany": "德国",
        "France": "法国",
        "Switzerland": "瑞士",
        "UK": "英国",
        "Bulgaria": "保加利亚",
        "Austria": "奥地利",
        "Ireland": "爱尔兰",
        "Turkey": "土耳其",
        "Italy": "意大利",
        "Hungary": "匈牙利",
        "Korea": "韩国",
        "Taiwan": "台湾",
        "Canada": "加拿大",
        "Australia": "澳大利亚",
        "Brazil": "巴西",
        "India": "印度",
        "Indonesia": "印度尼西亚",
        "Argentina": "阿根廷",
        "Chile": "智利",
        "Singapore": "新加坡",
        "Sweden": "瑞典"
    }

    pattern = re.compile('|'.join(re.escape(name) for name in country_map.keys()))
    def replace_country_names(match):
        return country_map[match.group(0)]

    try:
        start_index = lines.index("[Proxy]") + 1
    except ValueError:
        return proxy_list

    for line in lines[start_index:]:
        if line.startswith("["):
            break
        lower_line = line.lower()
        if "direct" in lower_line or "premium" in lower_line:
            continue
        processed_line = pattern.sub(replace_country_names, line)
        proxy_list.append(processed_line.strip())

    return proxy_list


def get_other_infos(lines: list):
    infos = {"流量": "", "重置": "", "到期": ""}
    index = lines.index("[Proxy]") + 1
    while not lines[index].startswith("["):
        if "G |" in lines[index]:
            infos["流量"] = lines[index].strip()
        elif "Reset" in lines[index]:
            infos["重置"] = lines[index].strip().split("：")[1].strip()
        elif "Date" in lines[index]:
            infos["到期"] = lines[index].strip().split("：")[1].strip()
        if all(infos.values()):
            break
        index += 1
    # 当前时间
    import datetime

    # 使用上海时区
    timedelta = datetime.timedelta(hours=8)

    infos["更新"] = datetime.datetime.now().astimezone(datetime.timezone(timedelta)).strftime("%Y-%m-%d %H:%M:%S")
    return infos
```

## Developer

自定义规则集合，修改`template.py`中的配置表模板即可，你可以基于ACL4SSR项目中Clash的配置规则来自定义，填写配置表链接即可。
