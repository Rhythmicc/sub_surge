# sub_surge

帮你在本地生成Surge的配置表，支持热门地区（香港、台湾、日本、美国、英国、新加坡）的最佳和负载均衡策略。

## Install

```shell
pip3 install git+https://github.com/Rhythmicc/sub_surge.git -U
```

## Usage

```shell
sub_surge --help
```

注册机场时，需要实现两个函数，以下是参考实现：

```python
def get_proxies_list(lines: list):
    proxy_list = []
    index = lines.index('[Proxy]') + 1
    while not lines[index].startswith('['):
        if 'Direct' in lines[index]:
            index += 1
            continue
        if 'Hong Kong' in lines[index]:
            lines[index] = lines[index].replace('Hong Kong', '香港')
        elif 'USA' in lines[index]:
            lines[index] = lines[index].replace('USA', '美国')
        elif 'Japan' in lines[index]:
            lines[index] = lines[index].replace('Japan', '日本')
        elif 'Netherlands' in lines[index]:
            lines[index] = lines[index].replace('Netherlands', '荷兰')
        elif 'Russia' in lines[index]:
            lines[index] = lines[index].replace('Russia', '俄罗斯')
        elif 'Germany' in lines[index]:
            lines[index] = lines[index].replace('Germany', '德国')
        elif 'France' in lines[index]:
            lines[index] = lines[index].replace('France', '法国')
        elif 'Switzerland' in lines[index]:
            lines[index] = lines[index].replace('Switzerland', '瑞士')
        elif 'UK' in lines[index]:
            lines[index] = lines[index].replace('UK', '英国')
        elif 'Sweeden' in lines[index]:
            lines[index] = lines[index].replace('Sweeden', '瑞典')
        elif 'Bulgaria' in lines[index]:
            lines[index] = lines[index].replace('Bulgaria', '保加利亚')
        elif 'Austria' in lines[index]:
            lines[index] = lines[index].replace('Austria', '奥地利')
        elif 'Ireland' in lines[index]:
            lines[index] = lines[index].replace('Ireland', '爱尔兰')
        elif 'Turkey' in lines[index]:
            lines[index] = lines[index].replace('Turkey', '土耳其')
        elif 'Italy' in lines[index]:
            lines[index] = lines[index].replace('Italy', '意大利')
        elif 'Hungary' in lines[index]:
            lines[index] = lines[index].replace('Hungary', '匈牙利')
        elif 'Korea' in lines[index]:
            lines[index] = lines[index].replace('Korea', '韩国')
        elif 'Taiwan' in lines[index]:
            lines[index] = lines[index].replace('Taiwan', '台湾')
        elif 'Canada' in lines[index]:
            lines[index] = lines[index].replace('Canada', '加拿大')
        elif 'Australia' in lines[index]:
            lines[index] = lines[index].replace('Australia', '澳大利亚')
        elif 'Brazil' in lines[index]:
            lines[index] = lines[index].replace('Brazil', '巴西')
        elif 'India' in lines[index]:
            lines[index] = lines[index].replace('India', '印度')
        elif 'Indonesia' in lines[index]:
            lines[index] = lines[index].replace('Indonesia', '印度尼西亚')
        elif 'Argentina' in lines[index]:
            lines[index] = lines[index].replace('Argentina', '阿根廷')
        elif 'Chile' in lines[index]:
            lines[index] = lines[index].replace('Chile', '智利')
        elif 'Singapore' in lines[index]:
            lines[index] = lines[index].replace('Singapore', '新加坡')
        proxy_list.append(lines[index].strip())
        index += 1
    return proxy_list


def get_other_infos(lines: list):
    infos = {
        '流量': '',
        '重置': '',
        '到期': ''
    }
    index = lines.index('[Proxy]') + 1
    while not lines[index].startswith('['):
        if 'GB |' in lines[index]:
            infos['流量'] = lines[index].strip()
        elif 'Reset' in lines[index]:
            infos['重置'] = lines[index].strip().split(':')[1].strip()
        elif 'Date' in lines[index]:
            infos['到期'] = lines[index].strip().split(':')[1].strip()
        if all(infos.values()):
            break
        index += 1
    return infos
```

## Developer

自定义规则集合，修改`template.py`中的配置表模板即可，你可以基于ACL4SSR项目中Clash的配置规则来自定义，填写配置表链接即可。
