from QuickProject.Commander import Commander
from QuickProject import QproDefaultConsole, QproInfoString, QproErrorString, _ask
import sys
import os
from pathlib import Path


name = "sub-surge"
app = Commander(name)


def get_user_config_path():
    """获取用户配置文件路径"""
    custom_dir = os.environ.get('SUB_SURGE_CONFIG_DIR')
    if custom_dir:
        config_dir = Path(custom_dir)
    else:
        config_dir = Path.home() / ".sub-surge"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "user_config.json"


def load_user_config():
    """加载用户配置"""
    import json
    config_path = get_user_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_user_config(config):
    """保存用户配置"""
    import json
    config_path = get_user_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def check_first_run():
    """检查是否首次运行，如果是则引导用户配置"""
    config_dir = Path.home() / ".sub-surge"
    config_file = config_dir / "config.json"
    first_run_marker = config_dir / ".initialized"
    
    if first_run_marker.exists():
        return
    
    QproDefaultConsole.print(QproInfoString, "欢迎使用 sub-surge！")
    QproDefaultConsole.print(QproInfoString, "检测到首次运行，需要进行初始化配置。")
    
    # 创建配置目录
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "logs").mkdir(exist_ok=True)
    
    QproDefaultConsole.print(QproInfoString, f"配置目录已创建: {config_dir}")
    QproDefaultConsole.print(QproInfoString, f"配置文件路径: {config_file}")
    QproDefaultConsole.print(QproInfoString, f"日志目录: {config_dir / 'logs'}")
    
    # 询问是否需要修改配置目录
    change_dir = _ask({
        "type": "confirm",
        "message": "是否需要修改配置目录位置？（默认: ~/.sub-surge）",
        "default": False
    })
    
    if change_dir:
        custom_dir = _ask({
            "type": "input",
            "message": "请输入自定义配置目录的完整路径："
        })
        
        if custom_dir:
            custom_path = Path(custom_dir).expanduser()
            if not custom_path.exists():
                custom_path.mkdir(parents=True, exist_ok=True)
            
            # 设置环境变量供后续使用
            os.environ['SUB_SURGE_CONFIG_DIR'] = str(custom_path)
            QproDefaultConsole.print(QproInfoString, f"已设置配置目录为: {custom_path}")
            QproDefaultConsole.print(QproInfoString, "注意：后续运行需要设置环境变量 SUB_SURGE_CONFIG_DIR")
    
    # 配置默认端口
    default_port = _ask({
        "type": "input",
        "message": "请输入 Web 服务默认端口（直接回车使用 8000）：",
        "default": "8000"
    })
    
    try:
        port = int(default_port)
        if 1 <= port <= 65535:
            user_config = load_user_config()
            user_config['default_port'] = port
            save_user_config(user_config)
            QproDefaultConsole.print(QproInfoString, f"已设置默认端口为: {port}")
        else:
            QproDefaultConsole.print(QproErrorString, "端口号无效，将使用默认值 8000")
    except ValueError:
        QproDefaultConsole.print(QproErrorString, "端口号格式错误，将使用默认值 8000")
    
    # 创建标记文件
    first_run_marker.touch()
    
    QproDefaultConsole.print(QproInfoString, "初始化完成！现在启动服务...")


@app.command()
def serve(host: str = "0.0.0.0", port: int = -1):
    """
    启动Web管理界面
    
    :param host: 监听地址
    :param port: 监听端口（不指定则使用配置的默认端口）
    """
    # 检查首次运行
    check_first_run()
    
    # 如果没有指定端口，尝试从配置读取
    if port == -1:
        user_config = load_user_config()
        port = user_config.get('default_port', 8000)
    
    QproDefaultConsole.print(QproInfoString, f"启动Web管理界面: http://{host}:{port}")
    
    try:
        from .api import start_server
        start_server(host, port)
    except KeyboardInterrupt:
        QproDefaultConsole.print(QproInfoString, "服务已停止")
    except Exception as e:
        QproDefaultConsole.print(QproErrorString, f"启动失败: {e}")


@app.command()
def update(name: str, local: bool = False):
    """
    更新机场订阅
    
    :param name: 机场名称
    :param local: 只保存到本地，不上传到云端
    """
    from .config_manager import ConfigManager
    from .updater import update_airport
    
    config_manager = ConfigManager()
    airport = config_manager.get_airport(name)
    
    if not airport:
        QproDefaultConsole.print(QproErrorString, f"机场 {name} 不存在")
        return
    
    QproDefaultConsole.print(QproInfoString, f"正在更新 {airport.name}...")
    
    global_config = config_manager.get_global_config()
    result = update_airport(airport, global_config, disable_upload=local)
    
    if result.get('success'):
        QproDefaultConsole.print(
            QproInfoString,
            f"更新成功！\n"
            f"  节点数量: {result.get('proxy_count')}\n"
            f"  区域: {', '.join(result.get('regions', []))}\n"
            f"  链接: {result.get('url')}"
        )
    else:
        QproDefaultConsole.print(QproErrorString, f"更新失败: {result.get('error')}")


@app.command()
def merge():
    """合并多个机场配置"""
    from .config_manager import ConfigManager
    from .updater import merge_airports
    
    config_manager = ConfigManager()
    global_config = config_manager.get_global_config()
    
    if not global_config.merge_airports:
        QproDefaultConsole.print(QproErrorString, "未配置要合并的机场，请先在配置中设置")
        return
    
    QproDefaultConsole.print(QproInfoString, f"正在合并机场: {', '.join(global_config.merge_airports)}")
    
    result = merge_airports(global_config.merge_airports, config_manager)
    
    if result.get('success'):
        QproDefaultConsole.print(
            QproInfoString,
            f"合并成功！\n"
            f"  机场数量: {result.get('airport_count')}\n"
            f"  节点数量: {result.get('proxy_count')}\n"
            f"  区域: {', '.join(result.get('regions', []))}\n"
            f"  链接: {result.get('url')}"
        )
    else:
        QproDefaultConsole.print(QproErrorString, f"合并失败: {result.get('error')}")


@app.command()
def list_airports():
    """列出所有机场"""
    from .config_manager import ConfigManager
    
    config_manager = ConfigManager()
    airports = config_manager.list_airports()
    
    if not airports:
        QproDefaultConsole.print(QproInfoString, "暂无机场配置")
        return
    
    QproDefaultConsole.print(QproInfoString, f"共有 {len(airports)} 个机场:\n")
    
    for name in airports:
        airport = config_manager.get_airport(name)
        print(f"  ✈️  {airport.name}")
        print(f"      订阅: {airport.url[:60]}...")
        print(f"      存储: {airport.key}")
        print()


@app.command()
def add(
    name: str,
    url: str,
    key: str,
    template: str = "generic",
    reset_day: int = 30
):
    """
    添加机场配置
    
    :param name: 机场名称
    :param url: 订阅链接
    :param key: 存储路径
    :param template: 模板类型 (generic/nexitaly)
    :param reset_day: 重置周期（天）
    """
    from .config_manager import ConfigManager
    
    config_manager = ConfigManager()
    
    if config_manager.get_airport(name):
        QproDefaultConsole.print(QproErrorString, f"机场 {name} 已存在")
        return
    
    airport = config_manager.create_airport_from_template(
        name=name,
        url=url,
        key=key,
        template=template
    )
    
    if airport:
        QproDefaultConsole.print(QproInfoString, f"机场 {name} 添加成功")
    else:
        QproDefaultConsole.print(QproErrorString, "添加失败")


@app.command()
def remove(name: str):
    """
    删除机场配置
    
    :param name: 机场名称
    """
    from .config_manager import ConfigManager
    from . import _ask
    
    config_manager = ConfigManager()
    
    if not config_manager.get_airport(name):
        QproDefaultConsole.print(QproErrorString, f"机场 {name} 不存在")
        return
    
    if _ask({"type": "confirm", "message": f"确定要删除机场 {name} 吗？", "default": False}):
        if config_manager.remove_airport(name):
            QproDefaultConsole.print(QproInfoString, f"机场 {name} 已删除")
        else:
            QproDefaultConsole.print(QproErrorString, "删除失败")


@app.command()
def config(key: str = None, value: str = None):
    """
    查看或修改全局配置
    
    :param key: 配置键
    :param value: 配置值
    """
    from .config_manager import ConfigManager
    import json
    
    config_manager = ConfigManager()
    global_config = config_manager.get_global_config()
    
    if key is None:
        # 显示所有配置
        QproDefaultConsole.print(QproInfoString, "全局配置:")
        print(json.dumps(global_config.dict(), indent=2, ensure_ascii=False))
        return
    
    if value is None:
        # 显示指定配置
        if hasattr(global_config, key):
            print(f"{key}: {getattr(global_config, key)}")
        else:
            QproDefaultConsole.print(QproErrorString, f"配置项 {key} 不存在")
        return
    
    # 修改配置
    if config_manager.update_global_config(**{key: value}):
        QproDefaultConsole.print(QproInfoString, f"配置 {key} 已更新为 {value}")
    else:
        QproDefaultConsole.print(QproErrorString, "配置更新失败")


@app.command()
def export(path: str = "sub-surge-config.json"):
    """
    导出配置到文件
    
    :param path: 导出文件路径
    """
    from .config_manager import ConfigManager
    
    config_manager = ConfigManager()
    
    if config_manager.export_config(path):
        QproDefaultConsole.print(QproInfoString, f"配置已导出到: {path}")
    else:
        QproDefaultConsole.print(QproErrorString, "导出失败")


@app.command()
def import_config(path: str):
    """
    从文件导入配置
    
    :param path: 导入文件路径
    """
    from .config_manager import ConfigManager
    
    config_manager = ConfigManager()
    
    if config_manager.import_config(path):
        QproDefaultConsole.print(QproInfoString, f"配置已从 {path} 导入")
    else:
        QproDefaultConsole.print(QproErrorString, "导入失败")


@app.command()
def info(name: str):
    """
    查看机场详细信息
    
    :param name: 机场名称
    """
    from .config_manager import ConfigManager
    import json
    
    config_manager = ConfigManager()
    airport = config_manager.get_airport(name)
    
    if not airport:
        QproDefaultConsole.print(QproErrorString, f"机场 {name} 不存在")
        return
    
    QproDefaultConsole.print(QproInfoString, f"机场信息: {airport.name}\n")
    print(json.dumps(airport.dict(), indent=2, ensure_ascii=False))


def main():
    app()


if __name__ == "__main__":
    main()
