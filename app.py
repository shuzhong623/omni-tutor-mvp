import streamlit as st
import google.generativeai as genai
import os

# ================= 配置区 =================
st.set_page_config(page_title="Omni-Tutor AI", layout="wide")
st.title("🌟 Omni-Tutor 全能AI老师 MVP版")

# 侧边栏：用户设置
with st.sidebar:
    st.header("⚙️ 用户设定")
    api_key = st.text_input("请输入你的 Gemini API Key:", type="password")
    user_level = st.selectbox("选择用户级别", ["Baby", "Pupil", "Student"])
    lang_mode = st.selectbox("语言模式", ["English Only", "Chinese Only", "Mixed Mode"])
    
    st.divider()
    st.info(f"当前模式: {user_level} | {lang_mode}")

# 实例化 Gemini
if api_key:
    genai.configure(api_key=api_key)
    # 使用 gemini-1.5-pro 以获得最强的多模态能力
    model = genai.GenerativeModel('gemini-1.5-pro')
else:
    st.warning("请在左侧输入 API Key 以开始教学")
    st.stop()

# ================= 人格 Prompt 库 =================
PERSONA_PROMPTS = {
    "Baby": "你是一个幼儿园老师。语速极慢，多用拟声词(Wow!, Boing!)，极高情绪价值，将错误轻量化。逻辑：感知->命名->模仿。",
    "Pupil": "你是一个幽默博学的大哥哥/大姐姐。采用任务驱动法，将知识点游戏化，鼓励用户问'为什么'。",
    "Student": "你是一个睿智客观的学术教练。采用苏格拉底式提问法，引导用户自行推导，强调批判性思维。"
}

def get_full_prompt(module, content):
    persona = PERSONA_PROMPTS[user_level]
    base = f"Role: You are Omni-Tutor. User Level: {user_level}. Language Mode: {lang_mode}. {persona}\n"
    
    if module == "知识星球":
        base += "Module: Knowledge Planet. Focus: Academic support and clear explanation."
    elif module == "语言学习":
        base += "Module: Language Master. Focus: Grammar correction, pronunciation guidance, and multimodal analysis."
    elif module == "陪玩伙伴":
        base += "Module: Playmate. Focus: Games, storytelling, and creativity."
    
    return f"{base}\n\nUser Request: {content}"

# ================= 三大模块 UI =================
tab1, tab2, tab3 = st.tabs(["🌍 知识星球", "📚 语言学习", "🎮 陪玩伙伴"])

# 模块1：知识星球
with tab1:
    st.header("知识星球 - 全学科辅导")
    q1 = st.text_area("想问老师什么学科的问题？")
    if st.button("提交问题", key="btn1"):
        with st.spinner("老师正在思考..."):
            response = model.generate_content(get_full_prompt("知识星球", q1))
            st.markdown(f"**Omni-Tutor:**\n\n{response.text}")

# 模块2：语言学习 (多模态核心)
with tab2:
    st.header("语言学习 - 多模态实验室")
    col1, col2 = st.columns(2)
    
    with col1:
        upload_file = st.file_uploader("上传课本照片、录音或教学视频", type=["jpg", "png", "mp3", "wav", "mp4", "mov"])
        text_input = st.text_input("对这个素材有什么要求？(例如：请翻译这段视频/纠正我的发音)")
        
    with col2:
        if upload_file and st.button("开始分析", key="btn2"):
            with st.spinner("老师正在分析素材..."):
                # 将上传的文件传递给 Gemini
                # 注意：Gemini 处理视频和音频需要将其上传到 File API
                # 为了 MVP 简化，这里直接传递 bytes (适用于图片)
                # 对于视频，实际部署需使用 genai.upload_file()
                
                # 简单处理：如果是图片直接传，如果是视频/音频，提示用户 (MVP限制)
                if upload_file.type.startswith("image"):
                    import PIL.Image
                    img = PIL.Image.open(upload_file)
                    response = model.generate_content([get_full_prompt("语言学习", text_input), img])
                    st.markdown(f"**Omni-Tutor:**\n\n{response.text}")
                else:
                    st.info("视频/音频分析功能在 MVP 版中需要通过 Google File API 上传，请尝试上传图片以验证逻辑。")
                    # (此处可扩展 genai.upload_file 逻辑)

# 模块3：陪玩伙伴
with tab3:
    st.header("陪玩伙伴 - 游戏与创意")
    play_request = st.text_input("想让老师陪你玩什么？(唱歌/画画/玩游戏)")
    if st.button("开始玩耍", key="btn3"):
        with st.spinner("老师准备好了！"):
            response = model.generate_content(get_full_prompt("陪玩伙伴", play_request))
            st.markdown(f"**Omni-Tutor:**\n\n{response.text}")
            if "画" in play_request or "draw" in play_request.lower():
                st.info("提示：此处可接入 DALL-E 3 或 Gemini Image Generation 插件生成图片。")
