from app.record_platform.record_plat_base import Base
from ab_sign import ab_sign
import urllib, requests, json
from webui.utils.global_params import VideoQuality


class Douyin(Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.req_web_headers = {
            'cookie': 'ttwid=1%7C2iDIYVmjzMcpZ20fcaFde0VghXAA3NaNXE_SLR68IyE%7C1761045455'
                      '%7Cab35197d5cfb21df6cbb2fa7ef1c9262206b062c315b9d04da746d0b37dfbc7d',
            'referer': 'https://live.douyin.com/335354047186',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/116.0.5845.97 Safari/537.36 Core/1.116.567.400 QQBrowser/19.7.6764.400',
        }
        self.req_web_params = {
            "aid": "6383",
            "app_name": "douyin_web",
            "live_id": "1",
            "device_platform": "web",
            "language": "zh-CN",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "116.0.0.0",
            "web_rid": 0,
            'msToken': '',
        }

    # 开始记录
    def start_record(self):
        json_data = self.get_douyin_web_stream_data()
        port_info = self.get_douyin_stream_url(json_data)

    def get_douyin_web_stream_data(self):
        # 给一些默认的参数
        if self.cookies:
            self.req_web_headers['cookie'] = self.cookies

        try:
            web_rid = self.record_url.split('?')[0].split('live.douyin.com/')[-1]
            self.req_web_params["web_rid"] = web_rid

            api = f'https://live.douyin.com/webcast/room/web/enter/?{urllib.parse.urlencode(self.req_web_params)}'
            a_bogus = ab_sign(urllib.parse.urlparse(api).query, self.req_web_headers['user-agent'])
            api += "&a_bogus=" + a_bogus
            try:
                json_str = requests.get(url=api, headers=self.req_web_headers)
                if not json_str:
                    raise Exception("it triggered risk control")
                json_data = json.loads(json_str.text)['data']
                if not json_data['data']:
                    raise Exception(f"{self.record_url} VR live is not supported")
                room_data = json_data['data'][0]
                room_data['anchor_name'] = json_data['user']['nickname']
            except Exception as e:
                raise Exception(f"Douyin web data fetch error, because {e}.")

            # 状态2标识直播中
            if room_data['status'] == 2:
                if 'stream_url' not in room_data:
                    raise RuntimeError(
                        "The live streaming type or gameplay is not supported on the computer side yet, please use the "
                        "app to share the link for recording."
                    )
                live_core_sdk_data = room_data['stream_url']['live_core_sdk_data']
                pull_datas = room_data['stream_url']['pull_datas']
                if live_core_sdk_data:
                    if pull_datas:
                        key = list(pull_datas.keys())[0]
                        json_str = pull_datas[key]['stream_data']
                    else:
                        json_str = live_core_sdk_data['pull_data']['stream_data']
                    json_data = json.loads(json_str)
                    if 'origin' in json_data['data']:
                        stream_data = live_core_sdk_data['pull_data']['stream_data']
                        origin_data = json.loads(stream_data)['data']['origin']['main']
                        sdk_params = json.loads(origin_data['sdk_params'])
                        origin_hls_codec = sdk_params.get('VCodec') or ''

                        origin_url_list = json_data['data']['origin']['main']
                        origin_m3u8 = {'ORIGIN': origin_url_list["hls"] + '&codec=' + origin_hls_codec}
                        origin_flv = {'ORIGIN': origin_url_list["flv"] + '&codec=' + origin_hls_codec}
                        hls_pull_url_map = room_data['stream_url']['hls_pull_url_map']
                        flv_pull_url = room_data['stream_url']['flv_pull_url']
                        room_data['stream_url']['hls_pull_url_map'] = {**origin_m3u8, **hls_pull_url_map}
                        room_data['stream_url']['flv_pull_url'] = {**origin_flv, **flv_pull_url}
        except Exception as e:
            print(f"Error message: {e} Error line: {e.__traceback__.tb_lineno}")
            room_data = {'anchor_name': ""}
        return room_data

    def get_douyin_stream_url(self, json_data: dict) -> dict:
        # 作者
        anchor_name = json_data.get('anchor_name')

        result = {
            "anchor_name": anchor_name,
            "is_live": False,
        }

        status = json_data.get("status", 4)

        if status == 2:
            # 获取url的列表
            stream_url = json_data['stream_url']
            # flv链接列表
            flv_url_dict = stream_url['flv_pull_url']
            flv_url_list: list = list(flv_url_dict.values())
            # m3u8链接列表
            m3u8_url_dict = stream_url['hls_pull_url_map']
            m3u8_url_list: list = list(m3u8_url_dict.values())

            # 增加到5个
            while len(flv_url_list) < 5:
                flv_url_list.append(flv_url_list[-1])
                m3u8_url_list.append(m3u8_url_list[-1])

            quality_index = [item.value for item in VideoQuality].index(self.record_quality)
            video_quality = "OB"
            m3u8_url = m3u8_url_list[quality_index]
            flv_url = flv_url_list[quality_index]
            ok = self.get_response_status(url=m3u8_url)
            if not ok:
                index = quality_index + 1 if quality_index < 4 else quality_index - 1
                m3u8_url = m3u8_url_list[index]
                flv_url = flv_url_list[index]
            result |= {
                'is_live': True,
                'title': json_data['title'],
                'quality': video_quality,
                'm3u8_url': m3u8_url,
                'flv_url': flv_url,
                'record_url': m3u8_url or flv_url,
            }
        return result

    # 试探是否可以正常访问
    def get_response_status(self, url: str, timeout: int = 10) -> bool:
        """使用requests探测流媒体URL"""
        try:
            response = requests.head(url, timeout=10)
            return response.status_code == 200
        except:
            return False

    # 开始录像
    def record_video(self, port_info):
        user_agent = ("Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 ("
                                              "KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile "
                                              "Safari/537.36")
        rw_timeout = "50000000"
        analyzeduration = "40000000"
        probesize = "20000000"
        bufsize = "15000k"
        max_muxing_queue_size = "2048"

        ffmpeg_command = [
            'ffmpeg', "-y",
            "-v", "verbose",
            "-rw_timeout", rw_timeout,
            "-loglevel", "error",
            "-hide_banner",
            "-user_agent", user_agent,
            "-protocol_whitelist", "rtmp,crypto,file,http,https,tcp,tls,udp,rtp,httpproxy",
            "-thread_queue_size", "1024",
            "-analyzeduration", analyzeduration,
            "-probesize", probesize,
            "-fflags", "+discardcorrupt",
            "-re", "-i", real_url,
            "-bufsize", bufsize,
            "-sn", "-dn",
            "-reconnect_delay_max", "60",
            "-reconnect_streamed", "-reconnect_at_eof",
            "-max_muxing_queue_size", max_muxing_queue_size,
            "-correct_ts_overflow", "1",
            "-avoid_negative_ts", "1"
        ]

if __name__ == "__main__":
    test_data = {
        "record_url": "https://live.douyin.com/745964462470",
        "record_quality": 1
    }
    test_obj = Douyin(**test_data)
    test_obj.start_record()
