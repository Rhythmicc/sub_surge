from QuickProject.Commander import Commander
from . import *

app = Commander(name)


def parse_host(content: str) -> str:
    host = ""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        if not line.strip():
            continue
        line = line.split()
        host += f"{line[0]} = {line[1]}\n"
    return host


@app.custom_complete("name")
def update():
    return [
        {"name": i, "icon": "✈️", "description": config.select(i)["show_name"]}
        for i in config.get_all()
    ]


def parse_node_list_only(name, url):
    import base64
    import urllib.parse

    node_list = []
    nodes = (
        base64.b64decode(
            requirePackage(
                "QuickStart_Rhy.NetTools.NormalDL",
                "normal_dl",
                real_name="QuickStart_Rhy",
            )(url, name, write_to_memory=True).decode("utf-8")
        )
        .decode("utf-8")
        .strip()
        .split("\n")
    )

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
        skip_cert_verify = "false"
        tfo = "false"
        udp_relay = "true"

        param_parts = [f"password={password}"]
        if sni:
            param_parts.append(f"sni={sni}")
        param_parts.append(f"skip-cert-verify={skip_cert_verify}")
        param_parts.append(f"tfo={tfo}")
        param_parts.append(f"udp-relay={udp_relay}")
        params_string = ", ".join(param_parts)
        node_list.append(f"{node_name} = {protocol}, {host}, {port}, {params_string}")
    return node_list


aim_regions = {
    "香港": "🇭🇰 香港",
    "日本": "🇯🇵 日本",
    "美国": "🇺🇸 美国",
    "新加坡": "🇸🇬 狮城",
    "英国": "🇬🇧 英国",
    "台湾": "🇨🇳 台湾",
}

def ask_and_save(name, key):
    airports_questions = {
        'reset_day': {
            "type": "input",
            "message": "请输入重置周期 (单位: 天, 默认: 30)",
            "default": "30",
        },
    }

    from . import _ask
    name_conf = config.select(name)
    val = name_conf.get(key)
    if not val:
        val = _ask(airports_questions.get(key, {"message": "请输入值", "type": "input"}))
    if not val:
        return None
    name_conf[key] = val
    config.update(name, name_conf)
    return val


@app.command()
def update(
    name: str,
    force: bool = False,
    disable_txcos: bool = False,
    __list_only: bool = False,
):
    """
    更新Surge配置文件

    :param name: 机场名称
    :param force: 是否强制更新
    """
    if os.path.exists(f".{name}.conf"):
        os.remove(f".{name}.conf")

    if force and os.path.exists(f"{name}.conf"):
        os.remove(f"{name}.conf")

    name_conf = config.select(name)
    path = None
    if name_conf.get("nodes_list"):
        node_list = parse_node_list_only(name, name_conf["url"])
        content = "[Proxy]\n" + "\n".join(node_list) + "\n["
        content = content.splitlines()
    else:
        if not (
            path := requirePackage(
                "QuickStart_Rhy.NetTools.NormalDL",
                "normal_dl",
                real_name="QuickStart_Rhy",
            )(name_conf["url"], name)
        ):
            from QuickProject import QproErrorString

            return QproDefaultConsole.print(
                QproErrorString, f"下载失败, 请检查链接是否正确"
            )

        with open(path, "r") as f:
            content = [i.strip() for i in f.readlines()]
    proxy_list = requirePackage(f".airports.{name}", "get_proxies_list")(content)
    other_infos = requirePackage(f".airports.{name}", "get_other_infos")(content)

    all_proxy_list = proxy_list.copy()
    pop_items = []
    for item in other_infos:
        for _id, line in enumerate(all_proxy_list):
            target = other_infos[item].strip()
            if target and target in line:
                proxy_list.remove(line)
                all_proxy_list[_id] = (
                    f'{item}: {other_infos[item].split("=")[0].strip()} = '
                    + "=".join(line.split("=")[1:]).strip()
                )
                pop_items.append(item)
                break
    if __list_only:
        if path:
            os.remove(path)
        return proxy_list
    
    with open(f".{name}.conf", "w") as f:
        # encode url
        from .template import conf_template, traffic_module_template, update_interval_template
        import urllib.parse
        import random
        info_url = urllib.parse.quote(name_conf["url"], safe="")
        color = f"#{random.randint(0, 0xFFFFFF):06X}"

        infos = {
            "cos_url": f"{config.select('txcos_domain')}/{config.select(name)['key']}",
            "proxies": "\n".join(all_proxy_list),
            "proxies_one_line": ",".join(
                [i.split("=")[0].strip() for i in proxy_list if i]
            ),
            "module_panel": traffic_module_template["panel"].format(name=name),
            "module_script": traffic_module_template["script"].format(
                name=name,
                url=info_url,
                reset=ask_and_save(name, "reset_day"),
                color=color,
            ),
            "update_interval": update_interval_template
        }

        infos["host"] = parse_host(
            requirePackage(
                "QuickStart_Rhy.NetTools.NormalDL",
                "normal_dl",
                real_name="QuickStart_Rhy",
            )(
                "https://raw.githubusercontent.com/maxiaof/github-hosts/refs/heads/master/hosts",
                write_to_memory=True,
            ).decode(
                "utf-8"
            )
        )

        regions = {}
        for i in proxy_list:
            for key in aim_regions:
                if key in i:
                    if aim_regions[key] not in regions:
                        regions[aim_regions[key]] = []
                    regions[aim_regions[key]].append(i.split("=")[0].strip())
                    break
        infos["regions"] = ",".join([i for i in regions])
        infos["region_strategy"] = "\n".join(
            [f"{i} = select,{i}最佳,{i}均衡,🔧 手动切换" for i in regions]
        )
        infos["region_auto"] = "\n".join(
            [
                f"{i}最佳 = url-test,{','.join(regions[i])},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50"
                for i in regions
            ]
            + [
                f"{i}均衡 = smart,{','.join(regions[i])},persistent=1"
                for i in regions
            ]
        )

        f.write(conf_template.format(**infos))

    if not disable_txcos and config.select("txcos_domain"):
        with QproDefaultStatus("正在上传配置文件"):
            from QuickStart_Rhy.API.TencentCloud import TxCOS

            TxCOS().upload(f".{name}.conf", key=config.select(name)["key"])
        requirePackage("QuickStart_Rhy", "remove")(f".{name}.conf")
        QproDefaultConsole.print(
            QproInfoString,
            f"更新成功, 链接: {config.select('txcos_domain')}/{config.select(name)['key']}",
        )
    else:
        import shutil

        shutil.move(f".{name}.conf", f"{name}.conf")
        QproDefaultConsole.print(QproInfoString, f"更新成功: {name}.conf")

    return proxy_list


@app.command()
def merge():
    from QuickProject import QproErrorString

    names = config.get_all()
    if not names:
        return QproDefaultConsole.print(QproErrorString, "没有机场配置, 请先注册机场")

    names = config.select("merge_airports")
    import datetime

    txcos_file = config.select("merge_key")

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proxy_list = [
        f"更新: {date} = trojan, example.com, 19757, password=info, sni=example.com, skip-cert-verify=true, tfo=true, udp-relay=true"
    ]

    for name in names:
        proxy = app.real_call("update", name, __list_only=True)
        proxy_list.extend(proxy)

    regions = {}
    for i in proxy_list:
        for key in aim_regions:
            if key in i:
                if aim_regions[key] not in regions:
                    regions[aim_regions[key]] = []
                regions[aim_regions[key]].append(i.split("=")[0].strip())
                break
    
    import random
    import urllib.parse
    from .template import conf_template, traffic_module_template, update_interval_template

    total_infos = {
        "cos_url": f"{config.select('txcos_domain')}/{txcos_file}",
        "proxies": "\n".join(proxy_list),
        "proxies_one_line": ",".join(
            [i.split("=")[0].strip() for i in proxy_list[1:] if i]
        ),
        "module_panel": '\n'.join(
            [traffic_module_template["panel"].format(name=name) for name in names]
        ),
        "module_script": '\n'.join(
            [traffic_module_template["script"].format(
                name=name,
                url=urllib.parse.quote(config.select(name)["url"], safe=""),
                reset=ask_and_save(name, "reset_day"),
                color=f"#{random.randint(0, 0xFFFFFF):06X}",
            ) for name in names]
        ),
        "update_interval": update_interval_template,
    }
    total_infos["regions"] = ",".join([i for i in regions])
    total_infos["region_strategy"] = "\n".join(
        [f"{i} = select,{i}最佳,{i}智能,🔧 手动切换" for i in regions]
    )
    total_infos["region_auto"] = "\n".join(
        [
            f"{i}最佳 = url-test,{','.join(regions[i])},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50"
            for i in regions
        ]
        + [
            f"{i}智能 = smart,{','.join(regions[i])},persistent=1"
            for i in regions
        ]
    )

    total_infos["host"] = parse_host(
        requirePackage(
            "QuickStart_Rhy.NetTools.NormalDL",
            "normal_dl",
            real_name="QuickStart_Rhy",
        )(
            "https://raw.githubusercontent.com/maxiaof/github-hosts/refs/heads/master/hosts",
            write_to_memory=True,
        ).decode(
            "utf-8"
        )
    )

    with open(f".merge.conf", "w") as f:
        f.write(conf_template.format(**total_infos))

    with QproDefaultStatus("正在上传配置文件"):
        from QuickStart_Rhy.API.TencentCloud import TxCOS

        TxCOS().upload(f".merge.conf", key=txcos_file)
    requirePackage("QuickStart_Rhy", "remove")(f".merge.conf")
    QproDefaultConsole.print(
        QproInfoString,
        f"更新成功, 链接: {config.select('txcos_domain')}/{txcos_file}",
    )


@app.command()
def register(name: str):
    """
    添加机场

    :param name: 机场名
    """
    from . import _ask

    cur_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "airports")
    if not os.path.exists(cur_path):
        os.mkdir(cur_path)
    airports = os.listdir(cur_path)

    if (name in airports or config.select(name)) and _ask(
        {"type": "confirm", "message": "此机场已注册, 是否覆盖?", "default": False}
    ):
        remove = requirePackage("QuickStart_Rhy", "remove")
        remove(os.path.join(airports, f"{name}.py"))
        config.update(name, None)

    values = {
        "url": _ask({"type": "input", "message": "输入机场订阅链接"}),
        "key": _ask({"type": "input", "message": "输入腾讯云对应存储位置"}),
        "show_name": _ask(
            {"type": "input", "message": "输入机场描述信息", "default": name}
        ),
        "custom_format": _ask({"type": "input", "message": "输入自定义格式化文件路径"}),
        "nodes_list": _ask(
            {
                "type": "confirm",
                "message": "是否为节点列表格式? (默认: 否)",
                "default": False,
            }
        ),
    }
    if not os.path.exists(values["custom_format"]):
        from QuickProject import QproErrorString

        return QproDefaultConsole.print(
            QproErrorString, "自定义格式化文件不存在, 请重新输入"
        )

    values["custom_format"] = os.path.abspath(values["custom_format"])
    import shutil

    shutil.copy(values["custom_format"], os.path.join(cur_path, f"{name}.py"))
    values.pop("custom_format")

    config.update(name, values)
    QproDefaultConsole.print(QproInfoString, "注册成功")


@app.command()
def unregister(name: str):
    """
    删除机场

    :param name: 机场名
    """
    from . import _ask

    cur_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "airports")
    if config.select(name) and _ask(
        {"type": "confirm", "message": "是否删除此机场?", "default": False}
    ):
        requirePackage("QuickStart_Rhy", "remove")(os.path.join(cur_path, f"{name}.py"))
        config.update(name, None)
        QproDefaultConsole.print(QproInfoString, "删除成功")


@app.custom_complete("airport")
def check():
    return [
        {"name": i, "icon": "✈️", "description": config.select(i)["show_name"]}
        for i in config.get_all()
    ]


@app.command()
def check(airport: str, key2: str = "", val: str = ""):
    """
    检查配置

    :param airport: 机场名
    :param key2: 键
    :param val: 值
    """
    if key2:
        config[airport][key2] = val
    else:
        QproDefaultConsole.print(config.select(airport))


@app.command()
def upgrade():
    """
    更新
    """
    with QproDefaultConsole.status('正在更新 "QuickStart_Rhy"'):
        external_exec(
            f"{user_pip} install git+https://github.com/Rhythmicc/sub_surge.git -U",
            True,
        )


def main():
    """
    注册为全局命令时, 默认采用main函数作为命令入口, 请勿将此函数用作它途.
    When registering as a global command, default to main function as the command entry, do not use it as another way.
    """
    app()


if __name__ == "__main__":
    main()
