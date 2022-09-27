from QuickProject.Commander import Commander
from . import *

app = Commander()


@app.custom_complete("name")
def update():
    return [
        {"name": i, "icon": "✈️", "description": config.select(i)["show_name"]}
        for i in config.get_all()
    ]


@app.command()
def update(name: str):
    """
    更新Surge配置文件

    :param name: 机场名称
    """
    if not os.path.exists(".{name}.conf"):
        requirePackage(
            "QuickStart_Rhy.NetTools.NormalDL",
            "normal_dl",
            real_name="QuickStart_Rhy",
        )(config.select(name)["url"], f".{name}.conf")

    with open(f".{name}.conf", "r") as f:
        content = [i.strip() for i in f.readlines()]
    proxy_list = requirePackage(f".airports.{name}", "get_proxies_list")(content)
    other_infos = requirePackage(f".airports.{name}", "get_other_infos")(content)

    all_proxy_list = proxy_list.copy()
    for item in other_infos:
        for _id, line in enumerate(all_proxy_list):
            if other_infos[item].strip() in line:
                proxy_list.remove(line)
                all_proxy_list[_id] = (
                    f'{item}: {other_infos[item].split("=")[0].strip()} = '
                    + "=".join(line.split("=")[1:]).strip()
                )
                break
    with open(f".{name}.conf", "w") as f:
        infos = {
            "cos_url": f"{config.select('txcos_domain')}/{config.select(name)['key']}",
            "proxies": "\n".join(all_proxy_list),
            "infos": ",".join(
                [f'{i}: {other_infos[i].split("=")[0].strip()}' for i in other_infos]
            ),
            "proxies_one_line": ",".join(
                [i.split("=")[0].strip() for i in proxy_list if i]
            ),
            "proxies_one_line_hk": ",".join(
                [i.split("=")[0].strip() for i in proxy_list if "香港" in i]
            ),
            "proxies_one_line_jp": ",".join(
                [i.split("=")[0].strip() for i in proxy_list if "日本" in i]
            ),
            "proxies_one_line_us": ",".join(
                [i.split("=")[0].strip() for i in proxy_list if "美国" in i]
            ),
            "proxies_one_line_sg": ",".join(
                [i.split("=")[0].strip() for i in proxy_list if "新加坡" in i]
            ),
        }
        from .template import conf_template

        f.write(conf_template.format(**infos))
    with QproDefaultConsole.status("正在上传配置文件"):
        from QuickStart_Rhy.API.TencentCloud import TxCOS

        TxCOS().upload(f".{name}.conf", key=config.select(name)["key"])
    requirePackage("QuickStart_Rhy", "remove")(f".{name}.conf")
    QproDefaultConsole.print(
        QproInfoString,
        f"更新成功, 链接: {config.select('txcos_domain')}/{config.select(name)['key']}",
    )

    if copy := requirePackage("pyperclip", "copy", not_ask=True):
        copy(f"{config.select('txcos_domain')}/{config.select(name)['key']}")
        QproDefaultConsole.print(QproInfoString, f"链接已复制到剪贴板")


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


@app.command()
def complete():
    """
    生成补全脚本，并应用fig至.fig/autocomplete/src/
    """
    from . import _ask

    if _ask(
        {"type": "confirm", "message": "此操作会创建complete文件夹, 是否继续?", "default": False}
    ):
        from QuickProject.Qpro import gen_complete

        gen_complete("sub-surge")

        import shutil

        shutil.copyfile(
            "complete/fig/sub-surge.ts",
            os.path.join(user_root, ".fig/autocomplete/src/sub-surge.ts"),
        )
        QproDefaultConsole.print(QproInfoString, "补全脚本生成并应用成功")

        requirePackage("QuickStart_Rhy", "remove")("complete")


def main():
    """
    注册为全局命令时, 默认采用main函数作为命令入口, 请勿将此函数用作它途.
    When registering as a global command, default to main function as the command entry, do not use it as another way.
    """
    app()


if __name__ == "__main__":
    main()
