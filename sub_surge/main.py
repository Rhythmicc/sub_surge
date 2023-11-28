from QuickProject.Commander import Commander
from . import *

app = Commander(name)


@app.custom_complete("name")
def update():
    return [
        {"name": i, "icon": "✈️", "description": config.select(i)["show_name"]}
        for i in config.get_all()
    ]


@app.command()
def update(name: str, copy: bool = False):
    """
    更新Surge配置文件

    :param name: 机场名称
    :param copy: 是否复制到剪贴板
    """
    if os.path.exists(f".{name}.conf"):
        os.remove(f".{name}.conf")

    if not (
        path := requirePackage(
            "QuickStart_Rhy.NetTools.NormalDL",
            "normal_dl",
            real_name="QuickStart_Rhy",
        )(config.select(name)["url"], f".{name}.conf")
    ):
        return QproDefaultConsole.print(QproErrorString, f"下载失败, 请检查链接是否正确")

    with open(path, "r") as f:
        content = [i.strip() for i in f.readlines()]
    proxy_list = requirePackage(f".airports.{name}", "get_proxies_list")(content)
    other_infos = requirePackage(f".airports.{name}", "get_other_infos")(content)

    all_proxy_list = proxy_list.copy()
    pop_items = []
    for item in other_infos:
        for _id, line in enumerate(all_proxy_list):
            if other_infos[item].strip() in line:
                proxy_list.remove(line)
                all_proxy_list[_id] = (
                    f'{item}: {other_infos[item].split("=")[0].strip()} = '
                    + "=".join(line.split("=")[1:]).strip()
                )
                pop_items.append(item)
                break
    for item in other_infos:
        if item in pop_items:
            continue
        all_proxy_list.insert(
            len(pop_items),
            f"{item}: {other_infos[item]} = trojan, example.com, 19757, password=info, sni=example.com, skip-cert-verify=true, tfo=true, udp-relay=true",
        )
    with open(f".{name}.conf", "w") as f:
        infos = {
            "cos_url": f"{config.select('txcos_domain')}/{config.select(name)['key']}",
            "proxies": "\n".join(all_proxy_list),
            "infos": ",".join(
                [f'{i}: {other_infos[i].split("=")[0].strip()}' for i in other_infos]
            ),
            "proxies_one_line": ",".join(
                [i.split("=")[0].strip() for i in proxy_list if i]
            )
        }

        regions = {}
        aim_regions = {
            '香港': '🇭🇰 香港',
            '日本': '🇯🇵 日本',
            '美国': '🇺🇸 美国',
            '新加坡': '🇸🇬 狮城',
            '英国': '🇬🇧 英国',
            '台湾': '🇨🇳 台湾',
        }
        for i in proxy_list:
            for key in aim_regions:
                if key in i:
                    if aim_regions[key] not in regions:
                        regions[aim_regions[key]] = []
                    regions[aim_regions[key]].append(i.split("=")[0].strip())
                    break
        infos['regions'] = ",".join([i for i in regions])
        infos['region_strategy'] = "\n".join(
            [f"{i} = select,{i}最佳,{i}均衡,🔧 手动切换" for i in regions]
        )
        infos['region_auto'] = "\n".join(
            [f"{i}最佳 = url-test,{','.join(regions[i])},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50" for i in regions] + 
            [f"{i}均衡 = load-balance,{','.join(regions[i])},persistent=1" for i in regions]
        )

        from .template import conf_template

        f.write(conf_template.format(**infos))

    if config.select('txcos_domain'):
        with QproDefaultStatus("正在上传配置文件"):
            from QuickStart_Rhy.API.TencentCloud import TxCOS

            TxCOS().upload(f".{name}.conf", key=config.select(name)["key"])
        requirePackage("QuickStart_Rhy", "remove")(f".{name}.conf")
        QproDefaultConsole.print(
            QproInfoString,
            f"更新成功, 链接: {config.select('txcos_domain')}/{config.select(name)['key']}",
        )

        if copy and (cp := requirePackage("pyperclip", "copy", not_ask=True)):
            try:
                cp(f"{config.select('txcos_domain')}/{config.select(name)['key']}")
                QproDefaultConsole.print(QproInfoString, f"链接已复制到剪贴板")
            except Exception as e:
                from QuickProject import QproErrorString

                QproDefaultConsole.print(QproErrorString, f"复制链接失败: {repr(e)}")
    else:
        import shutil
        shutil.move(f".{name}.conf", f"{name}.conf")
        QproDefaultConsole.print(QproInfoString, f"更新成功: {name}.conf")


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
        "show_name": _ask({"type": "input", "message": "输入机场描述信息", "default": name}),
        "custom_format": _ask({"type": "input", "message": "输入自定义格式化文件路径"}),
    }
    if not os.path.exists(values["custom_format"]):
        from QuickProject import QproErrorString

        return QproDefaultConsole.print(QproErrorString, "自定义格式化文件不存在, 请重新输入")

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
