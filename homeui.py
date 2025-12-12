import os
import streamlit as st
from streamlit_option_menu import option_menu
from custom_log import init_log
from app.config import config
from app.utils import utils
from app.utils import ffmpeg_utils
from webui.components import basic_settings, video_settings, audio_settings, subtitle_settings, script_settings, \
    system_settings, del_video_subtitle, live_record
from app.models.schema import VideoClipParams

logger = None


def init_global_state():
    """初始化全局状态"""
    if 'video_clip_json' not in st.session_state:
        st.session_state['video_clip_json'] = []
    if 'video_plot' not in st.session_state:
        st.session_state['video_plot'] = ''
    if 'ui_language' not in st.session_state:
        st.session_state['ui_language'] = config.ui.get("language", utils.get_system_locale())
    # 移除subclip_videos初始化 - 现在使用统一裁剪策略


def tr(key):
    """翻译函数"""
    i18n_dir = os.path.join(os.path.dirname(__file__), "webui", "i18n")
    locales = utils.load_locales(i18n_dir)
    loc = locales.get(st.session_state['ui_language'], {})
    return loc.get("Translation", {}).get(key, key)


def render_generate_button():
    """渲染生成按钮和处理逻辑"""
    if st.button(tr("Generate Video"), use_container_width=True, type="primary"):
        from app.services import task as tm
        from app.services import state as sm
        from app.models import const
        import threading
        import time
        import uuid

        config.save_config()

        # 移除task_id检查 - 现在使用统一裁剪策略，不再需要预裁剪
        # 直接检查必要的文件是否存在
        if not st.session_state.get('video_clip_json_path'):
            st.error(tr("脚本文件不能为空"))
            return
        if not st.session_state.get('video_origin_path'):
            st.error(tr("视频文件不能为空"))
            return

        # 获取所有参数
        script_params = script_settings.get_script_params()
        video_params = video_settings.get_video_params()
        audio_params = audio_settings.get_audio_params()
        subtitle_params = subtitle_settings.get_subtitle_params()

        # 合并所有参数
        all_params = {
            **script_params,
            **video_params,
            **audio_params,
            **subtitle_params
        }

        # 创建参数对象
        params = VideoClipParams(**all_params)

        # 生成一个新的task_id用于本次处理
        task_id = str(uuid.uuid4())

        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()

        def run_task():
            try:
                tm.start_subclip_unified(
                    task_id=task_id,
                    params=params
                )
            except Exception as e:
                logger.error(f"任务执行失败: {e}")
                sm.state.update_task(task_id, state=const.TASK_STATE_FAILED, message=str(e))

        # 在新线程中启动任务
        thread = threading.Thread(target=run_task)
        thread.start()

        # 轮询任务状态
        while True:
            task = sm.state.get_task(task_id)
            if task:
                progress = task.get("progress", 0)
                state = task.get("state")

                # 更新进度条
                progress_bar.progress(progress / 100)
                status_text.text(f"Processing... {progress}%")

                if state == const.TASK_STATE_COMPLETE:
                    status_text.text(tr("视频生成完成"))
                    progress_bar.progress(1.0)

                    # 显示结果
                    video_files = task.get("videos", [])
                    try:
                        if video_files:
                            player_cols = st.columns(len(video_files) * 2 + 1)
                            for i, url in enumerate(video_files):
                                player_cols[i * 2 + 1].video(url)
                    except Exception as e:
                        logger.error(f"播放视频失败: {e}")

                    st.success(tr("视频生成完成"))
                    break

                elif state == const.TASK_STATE_FAILED:
                    st.error(f"任务失败: {task.get('message', 'Unknown error')}")
                    break

            time.sleep(0.5)


# 主函数入口
def main():
    """主函数"""
    if 'global_state_initialized' not in st.session_state:
        global logger
        logger = init_log()
        # 初始化配置 - 必须是第一个 Streamlit 命令
        st.set_page_config(
            page_title="AI工具集合",
            page_icon="📽️",
            layout="wide",
            initial_sidebar_state="auto"
        )
        init_global_state()
        st.session_state['global_state_initialized'] = True

    with st.sidebar:
        selected = option_menu(
            menu_title="",  # 菜单标题（可选）
            options=["首页", "基础设置", "视频生成", "视频去掉字幕", "直播录屏" ],  # 菜单项列表
            icons=["house", "gear", "bar-chart", "info-circle", "info-circle"],  # 图标列表（可选）
            default_index=0,  # 默认选中项索引
        )

    # ===== 显式注册 LLM 提供商（最佳实践）=====
    # 在应用启动时立即注册，确保所有 LLM 功能可用
    # if 'llm_providers_registered' not in st.session_state:
    #     try:
    #         from app.services.llm.providers import register_all_providers
    #         # 注册所有的llm
    #         register_all_providers()
    #         st.session_state['llm_providers_registered'] = True
    #         logger.info("✅ LLM 提供商注册成功")
    #     except Exception as e:
    #         logger.error(f"❌ LLM 提供商注册失败: {str(e)}")
    #         import traceback
    #         logger.error(traceback.format_exc())
    #         st.error(f"⚠️ LLM 初始化失败: {str(e)}\n\n请检查配置文件和依赖是否正确安装。")
    #         # 不抛出异常，允许应用继续运行（但 LLM 功能不可用）
    #
    # # 检测FFmpeg硬件加速，但只打印一次日志（使用 session_state 持久化）
    # if 'hwaccel_logged' not in st.session_state:
    #     # 检测ffmpeg是否可用
    #     hwaccel_info = ffmpeg_utils.detect_hardware_acceleration()
    #     if hwaccel_info["available"]:
    #         logger.info(f"FFmpeg硬件加速检测结果: 可用 | 类型: {hwaccel_info['type']} | 编码器: {hwaccel_info['encoder']} | 独立显卡: {hwaccel_info['is_dedicated_gpu']}")
    #     else:
    #         logger.warning(f"FFmpeg硬件加速不可用: {hwaccel_info['message']}, 将使用CPU软件编码")
    #     st.session_state['hwaccel_logged'] = True
    #
    # if "init_resources" not in st.session_state:
    #     st.session_state["init_resources"] = True
    #     # 仅初始化基本资源，避免过早地加载依赖PyTorch的资源
    #     # 检查是否能分解utils.init_resources()为基本资源和高级资源(如依赖PyTorch的资源)
    #     try:
    #         utils.init_resources()
    #     except Exception as e:
    #         logger.warning(f"资源初始化时出现警告: {e}")

    # st.title(f"Narrato:blue[AI]:sunglasses: 📽️")
    # st.write("帮助")

    if selected == "首页":
        st.title("欢迎来到首页！")
    elif selected == "基础设置":
        st.title("模型基础设置")
        # 渲染基础设置面板
        basic_settings.render_basic_settings(tr)
    elif selected == "视频生成":
        st.title("视频生成")
        # 渲染主面板
        panel = st.columns(3)
        with panel[0]:
            script_settings.render_script_panel(tr)
        with panel[1]:
            audio_settings.render_audio_panel(tr)
        with panel[2]:
            video_settings.render_video_panel(tr)
            subtitle_settings.render_subtitle_panel(tr)

        # 放到最后渲染可能使用PyTorch的部分
        # 渲染系统设置面板
        with panel[2]:
            system_settings.render_system_panel(tr)

        # 放到最后渲染生成按钮和处理逻辑
        render_generate_button()
    elif selected == "视频去掉字幕":
        st.title("去掉视频字幕")
        del_video_subtitle.render_del_video_subtitle_panel()
    elif selected == "直播录屏":
        st.title("直播录屏")
        live_record.render_live_record_panel()


if __name__ == "__main__":
    main()
