"""
新的配置管理器
使用JSON格式存储配置，支持配置驱动的机场管理
"""
import os
import json
from typing import Optional, Dict, List
from pathlib import Path

from .config_schema import GlobalConfig, AirportConfig


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # 默认配置路径到用户根目录的 .sub-surge 目录
            # 支持通过环境变量 SUB_SURGE_CONFIG_DIR 自定义
            from pathlib import Path
            custom_dir = os.environ.get('SUB_SURGE_CONFIG_DIR')
            if custom_dir:
                config_dir = Path(custom_dir)
            else:
                config_dir = Path.home() / ".sub-surge"
            config_dir.mkdir(exist_ok=True)
            config_path = str(config_dir / "config.json")
        
        self.config_path = config_path
        self.config: GlobalConfig = self._load_config()
    
    def _load_config(self) -> GlobalConfig:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            # 创建默认配置
            config = GlobalConfig()
            self._save_config(config)
            return config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return GlobalConfig(**data)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return GlobalConfig()
    
    def _save_config(self, config: Optional[GlobalConfig] = None):
        """保存配置文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(
                    config.dict(),
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def add_airport(self, airport_config: AirportConfig) -> bool:
        """添加机场配置"""
        try:
            self.config.airports[airport_config.name] = airport_config
            self._save_config()
            return True
        except Exception as e:
            print(f"添加机场配置失败: {e}")
            return False
    
    def remove_airport(self, name: str) -> bool:
        """删除机场配置"""
        try:
            if name in self.config.airports:
                del self.config.airports[name]
                self._save_config()
                return True
            return False
        except Exception as e:
            print(f"删除机场配置失败: {e}")
            return False
    
    def get_airport(self, name: str) -> Optional[AirportConfig]:
        """获取机场配置"""
        return self.config.airports.get(name)
    
    def list_airports(self) -> List[str]:
        """列出所有机场名称"""
        return list(self.config.airports.keys())
    
    def update_airport(self, name: str, **kwargs) -> bool:
        """更新机场配置"""
        try:
            if name not in self.config.airports:
                return False
            
            airport = self.config.airports[name]
            for key, value in kwargs.items():
                if hasattr(airport, key):
                    setattr(airport, key, value)
            
            self._save_config()
            return True
        except Exception as e:
            print(f"更新机场配置失败: {e}")
            return False
    
    def get_global_config(self) -> GlobalConfig:
        """获取全局配置"""
        return self.config
    
    def update_global_config(self, **kwargs) -> bool:
        """更新全局配置"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            self._save_config()
            return True
        except Exception as e:
            print(f"更新全局配置失败: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """导出配置到指定路径"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.config.dict(),
                    f,
                    indent=2,
                    ensure_ascii=False
                )
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """从指定路径导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.config = GlobalConfig(**data)
            self._save_config()
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
