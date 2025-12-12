import os
import toml
import shutil
from loguru import logger

# 获取当前根目录
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
config_file = f"{root_dir}/record_config.toml"
version_file = f"{root_dir}/project_version"


def get_version_from_file():
    """从project_version文件中读取版本号"""
    try:
        if os.path.isfile(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return "0.1.0"  # 默认版本号
    except Exception as e:
        logger.error(f"读取版本号文件失败: {str(e)}")
        return "0.1.0"  # 默认版本号


def load_config():
    # fix: IsADirectoryError: [Errno 21] Is a directory: '/NarratoAI/config.toml'
    if os.path.isdir(config_file):
        shutil.rmtree(config_file)

    if not os.path.isfile(config_file):
        # 如果连example文件也没有，则创建一个空的配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            pass  # 创建空文件
        logger.info(f"create empty config.toml")

    logger.info(f"load config from file: {config_file}")

    try:
        _config_ = toml.load(config_file)
    except Exception as e:
        logger.warning(f"load config failed: {str(e)}, try to load as utf-8-sig")
        with open(config_file, mode="r", encoding="utf-8-sig") as fp:
            _cfg_content = fp.read()
            _config_ = toml.loads(_cfg_content)
    return _config_


def save_config():
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(toml.dumps(cfg))


cfg = load_config()
