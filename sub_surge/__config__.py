import os
import json
from QuickProject import user_root, user_lang, QproDefaultConsole, QproInfoString, _ask

enable_config = True
config_path = os.path.join(user_root, ".sub_surge_config")

questions = {
    "txcos_domain": {"type": "input", "message": "请输入腾讯云对象存储 (COS) 服务的域名"},
    "interval": {
        "type": "input",
        "message": "请输入订阅更新间隔 (单位: 秒)",
        "default": "3600",
    },
}


def init_config():
    with open(config_path, "w") as f:
        json.dump(
            {i: _ask(questions[i]) for i in questions}, f, indent=4, ensure_ascii=False
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
            self.update(key, _ask(questions[key]))
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
        res.remove("interval")
        return res
