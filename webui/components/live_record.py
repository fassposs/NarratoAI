import streamlit as st
from webui.utils.global_params import MediaType, VideoQuality, TaskStatus
from app.config import record_config
from app.record_platform import Douyin
import urllib

# 最大标识索引,初始化的时候就得设置好
max_index = len(record_config.cfg)


# 删除视频字幕
def render_live_record_panel():
    """直播录频"""
    # 创建一个右对齐的容器
    button_container = st.container(horizontal_alignment="right")
    with button_container:
        if st.button("添加录屏"):
            global max_index
            add_one_video_conf(max_index)
            max_index += 1

    # 显示已经配置的数据
    show_saved_configs()


# 添加一组录屏配置
def add_one_video_conf(i):
    add_config = {
        "record_url": "",
        "record_type": MediaType.MP4.value,
        "record_quality": VideoQuality.ORIGINAL.value
    }

    # 保存配置
    record_config.cfg[str(i)] = add_config
    record_config.save_config()


# 显示已经存在的配置数据
def show_saved_configs():
    for i, data_conf in record_config.cfg.items():
        key_url = f"live_record_url_{i}"
        key_media = f"live_record_{i}"
        key_quality = f"live_record_quality_{i}"
        key_status = f"task_status_{i}"

        # 创建一行数据
        line_wdg = st.columns([1, 1, 1, 1, 1, 1, 1, 1], vertical_alignment="bottom")
        # 输入url
        with line_wdg[0]:
            st.text_input("录屏地址", key=key_url, placeholder="请输入录屏地址", value=data_conf.get("record_url", ""), on_change=on_change_save, args=(i,))

        # 视频类型的选择
        media_values = [media_type.value for media_type in MediaType]
        with line_wdg[1]:
            st.selectbox(
                "视频类型",
                index=[item.value for item in MediaType].index(data_conf.get("record_type", MediaType.FLV.value)),
                options=media_values,
                key=key_media,
                on_change=on_change_save,
                args=(i,)
            )

        # 视频质量的选择
        quality_values = [quality_type.value for quality_type in VideoQuality]
        with line_wdg[2]:
            st.selectbox(
                "视频质量",
                index=[item.value for item in VideoQuality].index(data_conf.get("record_quality", VideoQuality.ORIGINAL.value)),
                options=quality_values,
                key=key_quality,
                on_change=on_change_save,
                args=(i,)
            )

        # 显示当前状态的label
        with line_wdg[3]:
            if key_status not in st.session_state:
                st.session_state[key_status] = TaskStatus.PAUSED.value
            st.markdown(f"<p style='color:blue; text-align: center;'>状态:{st.session_state[key_status]}</p>", unsafe_allow_html=True)

        # 添加启动按钮
        with line_wdg[4]:
            if st.button("启动录制", key="start_record"):
                # TODO: 实现启动录制逻辑
                pass

        # 添加暂停按钮
        with line_wdg[5]:
            if st.button("暂停录制", key="pause_record"):
                # TODO: 实现暂停录制逻辑
                pass

        # 添加删除按钮
        with line_wdg[6]:
            if st.button("删除配置", key="delete_btn"):
                # TODO: 实现删除逻辑
                del record_config.cfg[str(i)]
                record_config.save_config()
                st.rerun()


# 配置改变了保存
def on_change_save(i):
    key_url = f"live_record_url_{i}"
    key_media = f"live_record_{i}"
    key_quality = f"live_record_quality_{i}"
    record_config.cfg[str(i)] = {
        "record_url": st.session_state[key_url],
        "record_type": st.session_state[key_media],
        "record_quality": st.session_state[key_quality]
    }
    record_config.save_config()


# 启动录屏
def start_record(i):
    key_url = f"live_record_url_{i}"
    record_url = st.session_state.get(key_url, "")
    if len(record_url) < 8:
        st.error("url参数错误")
        return
    # 当前状态
    key_status = f"task_status_{i}"
    if st.session_state[key_status] == TaskStatus.RUNNING.value:
        st.error("当前已经在运行了")
        return

    # 获取录像信息
    record_obj = Douyin()


