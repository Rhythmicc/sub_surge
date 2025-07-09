import os
import json
from QuickProject import user_root, user_lang, QproDefaultConsole, QproInfoString, _ask

enable_config = True
config_path = os.path.join(user_root, ".sub_surge_config")

questions = {
    "txcos_domain": {"type": "input", "message": "请输入腾讯云对象存储服务的域名 (没有则跳过)"},
    "interval": {
        "type": "input",
        "message": "请输入订阅更新间隔 (单位: 秒)",
        "default": "3600",
    },
    'merge_key': {
        "type": "input",
        "message": "请输入合并后的配置文件名 (没有则使用默认: merge.conf)",
        "default": "merge.conf",
    },
    "merge_airports": {
        "type": "input",
        "message": "请输入要合并的机场 (多个用逗号分隔)",
        "default": "",
    },
    'reset_day': {
        "type": "input",
        "message": "请输入重置周期 (单位: 天, 默认: 30)",
        "default": "30",
    }
}

def format_answer(question):
    if question == 'merge_airports':
        return _ask(questions[question]).replace("，", ",").replace(" ", "").split(",")
    return _ask(questions[question]).strip() or questions[question].get("default", "")

def init_config():
    with open(config_path, "w") as f:
        json.dump(
            {i: format_answer(i) for i in questions}, f, indent=4, ensure_ascii=False
        )
    QproDefaultConsole.print(
        QproInfoString,
        f'Config file has been created at: "{config_path}"'
        if user_lang != "zh"
        else f'配置文件已创建于: "{config_path}"',
    )


class sub_surgeConfig:
    def __init__(self):
        if not os.path.exists(config_path):
            init_config()
        with open(config_path, "r") as f:
            self.config = json.load(f)

    def select(self, key):
        if key not in self.config and key in questions:
            self.update(key, format_answer(key))
        return self.config.get(key, None)

    def update(self, key, value):
        if not value and key in self.config:
            self.config.pop(key)
        elif key and value:
            self.config[key] = value
        with open(config_path, "w") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_all(self):
        res = list(self.config.keys())
        res.remove("txcos_domain")
        res.remove("merge_key")
        res.remove("merge_airports")
        res.remove("interval")
        return res
