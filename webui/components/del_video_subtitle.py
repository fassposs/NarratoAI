import os
import glob
import json
import time
import traceback
import streamlit as st
from loguru import logger

from app.config import config
from app.models.schema import VideoClipParams
from app.utils import utils, check_script
from webui.tools.generate_script_docu import generate_script_docu
from webui.tools.generate_script_short import generate_script_short
from webui.tools.generate_short_summary import generate_script_short_sunmmary


# 删除视频字幕
def render_del_video_subtitle_panel():
    """删除视频字幕"""
    with st.container(border=True):
        st.write("删除视频字幕")

        # 视频文件选择
        render_video_file()


# 渲染视频文件路径
def render_video_file():
    """渲染视频文件选择"""
    src_video_dic = {
        "--": "",
        "上传本地文件": "upload_local"
    }
    src_dir = utils.src_del_subtitle_video_dir()
    des_dir = utils.des_del_subtitle_video_dir()
    # 获取已有视频文件
    for suffix in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
        video_files = glob.glob(os.path.join(src_dir, suffix))
        for file in video_files:
            display_name = file.replace(config.root_dir, "")
            src_video_dic[display_name] = file

    cols = st.columns(3, vertical_alignment="bottom")
    with cols[0]:
        selected_value = st.selectbox(
            "视频源文件（1️⃣支持上传视频文件(限制2G) 2️⃣大文件建议直接导入 ./resource/src_no_title_videos 目录）",
            index=0,
            options=src_video_dic.keys(),
            key="del_video_subtitle_file_selection"
        )
    with cols[1]:
        bShow = True
        if selected_value in list(src_video_dic.keys())[:2]:
            bShow = False
        if st.button("删除选中", disabled=not bShow):
            file_path = src_video_dic[selected_value]
            # 删除文件
            try:
                os.remove(os.path.abspath(file_path))
                st.success(f"文件 {selected_value} 已删除")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"删除文件失败: {str(e)}")
    with cols[2]:
        if st.button("删除所有", disabled=not selected_value):
            # 删除所有文件
            try:
                for filename in os.listdir(src_dir):
                    file_path = os.path.join(src_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                st.success("所有文件已删除")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"删除文件失败: {str(e)}")

    # 选中了上传本地文件了
    if selected_value == "上传本地文件":
        uploaded_file = st.file_uploader(
            "上传本地文件",
            type=["mp4", "mov", "avi", "flv", "mkv"],
            accept_multiple_files=False,
        )

        # 选一个文件上传
        if uploaded_file is not None:
            video_file_path = os.path.join(src_dir, uploaded_file.name)
            # 获取文件名和文件扩展名
            file_name, file_extension = os.path.splitext(uploaded_file.name)

            if os.path.exists(video_file_path):
                timestamp = time.strftime("%Y%m%d%H%M%S")
                file_name_with_timestamp = f"{file_name}_{timestamp}"
                # 视频完整路径
                video_file_path = os.path.join(src_dir, file_name_with_timestamp + file_extension)

            with open(video_file_path, "wb") as f:
                f.write(uploaded_file.read())
                st.success("文件上传成功")
                time.sleep(1)
                st.rerun()

    cols = st.columns(2)
    with cols[0]:
        # 输入左上和右下的坐标
        px1 = st.number_input("左上角X坐标", value=st.session_state.get("del_video_subtitle_px1",0), key="del_video_subtitle_px1")
        py1 = st.number_input("左上角Y坐标", value=st.session_state.get("del_video_subtitle_py1",0), key="del_video_subtitle_py1")
    with cols[1]:
        # 输入左上和右下的坐标
        px2 = st.number_input("右下角X坐标", value=st.session_state.get("del_video_subtitle_px2",0), key="del_video_subtitle_px2")
        py2 = st.number_input("右下角Y坐标", value=st.session_state.get("del_video_subtitle_py2",0), key="del_video_subtitle_py2")
    # 显示已经处理了的文件列表============================================
    des_video_dic = {
        "--": ""
    }
    # 获取已有视频文件
    for suffix in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
        video_files = glob.glob(os.path.join(des_dir, suffix))
        for file in video_files:
            display_name = file.replace(config.root_dir, "")
            des_video_dic[display_name] = file

    cols = st.columns(3, vertical_alignment="bottom")
    with cols[0]:
        selected_value = st.selectbox(
            "处理后视频（./resource/des_del_title_videos 目录）",
            index=0,
            options=des_video_dic.keys(),
            key="del_video_subtitle_file_selection1"
        )
    with cols[1]:
        bShow = True
        if selected_value in list(des_video_dic.keys())[:1]:
            bShow = False
        if st.button("删除选中", key="del_des_file", disabled=not bShow):
            file_path = des_video_dic[selected_value]
            # 删除文件
            try:
                os.remove(file_path)
                st.success(f"文件 {selected_value} 已删除")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"删除文件失败: {str(e)}")

    with cols[2]:
        if st.button("删除所有", key="del_des_file1", disabled=not selected_value):
            # 删除所有文件
            try:
                for filename in os.listdir(src_dir):
                    file_path = os.path.join(src_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                st.success("所有文件已删除")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"删除文件失败: {str(e)}")

    # =========================第三排按钮
    selected_value = st.session_state.get("del_video_subtitle_file_selection", "")
    bShow = True
    if selected_value in list(src_video_dic.keys())[:2]:
        bShow = False
    if st.button("开始处理", use_container_width=True, type="primary", disabled=not bShow):
        del_video_subtitle()


# 去掉视频字幕
def del_video_subtitle():
    import cv2, tqdm
    import numpy as np
    import subprocess
    import shutil
    from PIL import Image
    # 读取文件
    video_path = st.session_state.get("del_video_subtitle_file_selection", "")
    if video_path == "--" or video_path == "上传本地文件":
        st.error("请选择要处理的视频")
        return
    video_path = os.path.join(utils.src_del_subtitle_video_dir(),os.path.basename(video_path))
    # 读取两个坐标位置
    p1 = (st.session_state.get("del_video_subtitle_px1", 0), st.session_state.get("del_video_subtitle_py1", 0))
    p2 = (st.session_state.get("del_video_subtitle_px2", 0), st.session_state.get("del_video_subtitle_py2", 0))
    if p1[0] == 0 or p1[1] == 0 or p2[0] == 0 or p2[1] == 0:
        st.error("请输入正确的坐标")
        return
    if p1[0] >= p2[0] or p1[1] >= p2[1]:
        st.error("请输入正确的坐标")
        return
    # 参数合法的话 缓存一下这几个坐标
    st.session_state["x1"] = p1[0]
    st.session_state["y1"] = p1[1]
    st.session_state["x2"] = p2[0]
    st.session_state["y2"] = p2[1]
    # 输出路径
    output_dir = utils.des_del_subtitle_video_dir()
    output_path = os.path.join(output_dir, os.path.basename(video_path))
    # 获取文件名和文件扩展名
    file_name, file_extension = os.path.splitext(output_path)

    if os.path.exists(output_path):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        file_name_with_timestamp = f"{file_name}_{timestamp}"
        # 视频完整路径
        output_path = os.path.join(output_dir, file_name_with_timestamp + file_extension)

    # 处理视频
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Error opening video file: {video_path}")
        return

    # 获取视频属性
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 创建一个临时文件，用于存放没有音频的视频
    temp_dir = utils.temp_dir()
    temp_video_path = os.path.join(temp_dir, "temp_no_audio.mp4")

    # 根据输出格式设置编解码器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # 用来存放处理后的视频
    out = cv2.VideoWriter(str(temp_video_path), fourcc, fps, (width, height))

    # 处理每一帧
    with tqdm.tqdm(total=total_frames, desc="Processing video frames") as pbar:
        frame_count = 0
        while cap.isOpened():
            start_time = time.time()  # 开始计时
            ret, frame = cap.read()
            if not ret:
                break

            read_frame_time = time.time()  # 读取帧完成时间

            # 创建一个掩码，标记出需要修复的区域
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            # 在掩码上绘制矩形区域
            cv2.rectangle(mask, p1, p2, 255, -1)
            # 使用inpaint方法修复图像
            result_image = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)

            convert_time = time.time()  # 转换完成时间

            # 转换回 OpenCV 格式并写入输出视频
            frame_result = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)

            pil_image = Image.fromarray(frame_result)

            # 写入帧
            out.write(result_image)

            # 更新进度
            frame_count += 1
            pbar.update(1)

            # 打印各步骤耗时（单位：毫秒）
            print(f"Frame {frame_count}: "
                  f"Read={int((read_frame_time - start_time) * 1000)}ms, "
                  f"Convert={int((convert_time - read_frame_time) * 1000)}ms, ")

    # Release resources
    cap.release()
    out.release()

    # 使用 FFmpeg 将处理后的视频与原始音频合并
    try:
        logger.info("将处理后的视频与原始音频合并...")

        # 使用 FFmpeg 将处理后的视频与原始音频合并
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_video_path),  # 无音频视频
            "-i", str(video_path),  # 带音频的原始视频
            "-c:v", "copy",  # 不重新编码的视频复制
            "-c:a", "aac",  # 高度兼容的 AAC 音频编码器
            "-map", "0:v:0",  # 表示选择第一个输入文件（处理后的视频）的第一个视频流
            "-map", "1:a:0",  # 表示选择第二个输入文件（原始视频）的第一个音频流
            "-shortest",  # 当最短路线结束时结束
            str(output_path)
        ]

        # 运行 FFmpeg
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("音视频融合成功完成!")
        st.rerun()
    except Exception as e:
        logger.error(f"音频/视频合并过程中出错: {str(e)}")
        # 如果出现错误，请使用无声视频
        shutil.copy(str(temp_video_path), str(output_path))
    finally:
        # 清理临时文件
        try:
            os.remove(str(temp_video_path))
        except:
            pass

    logger.info(f"input_path:{video_path}, output_path:{output_path}, overall_progress:100")
