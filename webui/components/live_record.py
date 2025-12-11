import streamlit as st
from webui.utils.global_params import MediaType


# 删除视频字幕
def render_live_record_panel():
    """直播录频"""
    # 使用空列实现右对齐效果
    left_empty, right_content = st.columns([1, 1])  # 比例可以根据需要调整
    with right_content:
        if st.button("添加录屏"):
            add_one_video_config()

# 添加一组录屏配置
def add_one_video_config():
    line_wdg = st.columns([1,1])
    # 视频类型的选择
    media_values = [media_type.value for media_type in MediaType]
    with line_wdg[0]:
        selected_value = st.selectbox(
            "视频类型",
            index=0,
            options=media_values,
            key="live_record1"
        )


