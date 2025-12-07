import streamlit as st
from streamlit_option_menu import option_menu
from custom_log import init_log

# 初始化配置 - 必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="AI工具集合",
    page_icon="📽️",
    layout="wide",
    initial_sidebar_state="auto"
)

with st.sidebar:
    selected = option_menu(
        menu_title="",  # 菜单标题（可选）
        options=["首页","基础设置","视频生成", "视频去掉字幕", ],  # 菜单项列表
        icons=["house", "gear", "bar-chart", "info-circle"],  # 图标列表（可选）
        default_index=0,  # 默认选中项索引
    )

if selected == "首页":
    st.write("欢迎来到首页！")
elif selected == "数据分析":
    st.write("这里是数据分析页面")
else:
    st.write("这是设置页面")

# 主函数入口
def main():
    """主函数"""
    init_log()
    init_global_state()

    # ===== 显式注册 LLM 提供商（最佳实践）=====
    # 在应用启动时立即注册，确保所有 LLM 功能可用
    if 'llm_providers_registered' not in st.session_state:
        try:
            from app.services.llm.providers import register_all_providers
            register_all_providers()
            st.session_state['llm_providers_registered'] = True
            logger.info("✅ LLM 提供商注册成功")
        except Exception as e:
            logger.error(f"❌ LLM 提供商注册失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            st.error(f"⚠️ LLM 初始化失败: {str(e)}\n\n请检查配置文件和依赖是否正确安装。")
            # 不抛出异常，允许应用继续运行（但 LLM 功能不可用）

    # 检测FFmpeg硬件加速，但只打印一次日志（使用 session_state 持久化）
    if 'hwaccel_logged' not in st.session_state:
        st.session_state['hwaccel_logged'] = False

    hwaccel_info = ffmpeg_utils.detect_hardware_acceleration()
    if not st.session_state['hwaccel_logged']:
        if hwaccel_info["available"]:
            logger.info(f"FFmpeg硬件加速检测结果: 可用 | 类型: {hwaccel_info['type']} | 编码器: {hwaccel_info['encoder']} | 独立显卡: {hwaccel_info['is_dedicated_gpu']}")
        else:
            logger.warning(f"FFmpeg硬件加速不可用: {hwaccel_info['message']}, 将使用CPU软件编码")
        st.session_state['hwaccel_logged'] = True

    # 仅初始化基本资源，避免过早地加载依赖PyTorch的资源
    # 检查是否能分解utils.init_resources()为基本资源和高级资源(如依赖PyTorch的资源)
    try:
        utils.init_resources()
    except Exception as e:
        logger.warning(f"资源初始化时出现警告: {e}")

    st.title(f"Narrato:blue[AI]:sunglasses: 📽️")
    st.write(tr("Get Help"))

    # 首先渲染不依赖PyTorch的UI部分
    # 渲染基础设置面板
    basic_settings.render_basic_settings(tr)

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

if __name__ == "__main__":
    main()