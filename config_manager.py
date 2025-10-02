import os
import json
import platform
from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.config_file = self._get_config_path()
        self.default_config = {
            "audio_folder": "",
            "segment_duration": 30,
            "advanced_processing": True,
            "output_folder": "",
            "window_geometry": "650x500"
        }
        self.config = self.load_config()
    
    def _get_config_path(self):
        """获取配置文件路径"""
        system = platform.system()
        if system == "Windows":
            config_dir = Path(os.environ.get("APPDATA", "")) / "AudioSplitter"
        elif system == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "AudioSplitter"
        else:  # Linux and others
            config_dir = Path.home() / ".config" / "audiosplitter"
        
        # 创建配置目录（如果不存在）
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"
    
    def load_config(self):
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 确保所有默认键都存在
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                return self.default_config.copy()
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载配置文件时出错: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """保存配置"""
        if config is not None:
            self.config = config
        
        try:
            # 创建配置目录（如果不存在）
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存配置文件时出错: {e}")
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
    
    def update(self, updates):
        """批量更新配置"""
        self.config.update(updates)
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self.default_config.copy()
        self.save_config()
        return self.config