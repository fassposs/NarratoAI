from enum import Enum


# 视频枚举类型
class MediaType(Enum):
    FLV = "FLV"
    MKV = "MKV"
    TS = "TS"
    MP4 = "MP4"
    MP3_AUDIO = "MP3音频"
    M4A_AUDIO = "M4A音频"
    MP3 = "MP3"
    M4A = "M4A"


# 视频清晰度枚举类型
class VideoQuality(Enum):
    ORIGINAL = "原画"
    BLU_RAY = "蓝光"
    SUPER_HD = "超清"
    HD = "高清"
    SD = "标清"
    SMOOTH = "流畅"


# 任务状态枚举类型
class TaskStatus(Enum):
    PAUSED = "已暂停"
    RUNNING = "运行中"
