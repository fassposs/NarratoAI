class Base:
    def __init__(self, **kwargs):
        self.record_url = kwargs.get("record_url")
        self.record_quality = kwargs.get("record_quality")
        # 视频类型
        self.record_type = kwargs.get("record_type")
        # 视频分段时间(秒)
        self.record_split_time = kwargs.get("record_split_time")
        self.cookies = kwargs.get("cookies")
