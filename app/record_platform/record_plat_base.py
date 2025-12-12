class Base:
    def __init__(self, **kwargs):
        self.record_url = kwargs.get("record_url")
        self.record_quality = kwargs.get("record_quality")
        self.cookies = kwargs.get("cookies")
