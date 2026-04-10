 import streamlit as st
import google.generativeai as genai
import os
import streamlit.components.v1 as components

# ================= 1. 页面配置与样式 =================
st.set_page_config(page_title="Omni-Tutor AI", layout="wide", page_icon="🌟")

# 自定义 CSS 提升视觉效果
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #4A90E2; color: white; }
    .avatar-container { text-align: center; margin-bottom: 20px; }
    .avatar-image { width: 150px; height: 150px; border-radius: 50%; border: 5px solid #4A90E2; }
    .response-box { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #4A90E2; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 侧边栏设定 =================
with st.sidebar:
    st.header("⚙️ 用户设定")
    api_key = st.text_input("请输入你的 Gemini API Key:", type="password")
    user_level = st.selectbox("选择用户级别", ["Baby", "Pupil", "Student"])
    lang_mode = st.selectbox("语言模式", ["English Only", "Chinese Only", "Mixed Mode"])
    
    st.divider()
    st.markdown(f"**当前状态**\n\n级别: `{user_level}`\n模式: `{lang_mode}`")

# ================= 3. 核心逻辑配置 =================
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
else:
    st.warning("⚠️ 请在左侧输入 API Key 以激活 AI 老师")
    st.stop() # 只有输入Key后才会显示下方内容

# --- 情感头像映射表 ---
# 这里使用 Emoji 占位，如果你有图片URL，可以将 Emoji 替换为 'https://...jpg'
AVATARS = {
    "HAPPY": "😊",       # 开心/鼓励
    "THINKING": "🤔",    # 思考/分析
    "SURPRISED": "😲",   # 惊讶/好奇
    "SERIOUS": "🧐",     # 严肃/纠错
    "DEFAULT": "🌟"      # 默认
}

# --- 语音合成函数 (JavaScript 注入) ---
def speak_text(text):
    # 简单的 JS 脚本，调用浏览器内置的 TTS
    # 根据语言模式自动选择语音（英文用 'en-US', 中文用 'zh-CN'）
    lang = 'en-US' if lang_mode == "English Only" else 'zh-CN' if lang_mode == "Chinese Only" else 'zh-CN'
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance({repr(text)});
        msg.lang = '{lang}';
        window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

# --- 人格 Prompt 生成 ---
def get_full_prompt(module, content):
    persona_map = {
        "Baby": "幼儿园老师。语速极慢，多用拟声词(Wow!, Boing!)，极高情绪价值，将错误轻量化。逻辑：感知->命名->模仿。",
        "Pupil": "幽默博学的大哥哥/大姐姐。采用任务驱动法，将知识点游戏化，鼓励用户问'为什么'。",
        "Student": "睿智客观的学术教练。采用苏格拉底式提问法，引导用户自行推导，强调批判性思维。"
    }
    
    # 要求 AI 在回答最前面加上情绪标签 [HAPPY], [THINKING], [SURPRISED], [SERIOUS]
    prompt = f"""
    Role: You are Omni-Tutor. User Level: {user_level}. Language Mode: {lang_mode}.
    Personality: {persona_map[user_level]}
    Current Module: {module}.
    
    CRITICAL REQUIREMENT: Start your response with exactly one of these mood tags: [HAPPY], [THINKING], [SURPRISED], [SERIOUS]. 
    Then provide your answer.
    """
    return f"{prompt}\n\nUser Request: {content}"

# ================= 4. 主界面 UI =================
st.title("🌟 Omni-Tutor 全能AI老师")
st.markdown("---")

# 选项卡
tab1, tab2, tab3 = st.tabs(["🌍 知识星球", "📚 语言学习", "🎮 陪玩伙伴"])

# 统一的响应处理函数
def handle_ai_response(module, user_input, media=None):
    with st.spinner("老师正在思考..."):
        # 构建多模态输入
        content_list = [get_full_prompt(module, user_input)]
        if media:
            content_list.append(media)
            
        response = model.generate_content(content_list)
        full_text = response.text
        
        # 1. 提取情绪标签
        mood = "DEFAULT"
        for tag in AVATARS.keys():
            if f"[{tag}]" in full_text:
                mood = tag
                full_text = full_text.replace(f"[{tag}]", "").strip()
                break
        
        # 2. 显示头像
        st.markdown(f"""
            <div class="avatar-container">
                <div style="font-size: 80px;">{AVATARS[mood]}</div>
                <p style="color: gray;">Omni-Tutor 此时心情: {mood}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # 3. 显示回答
        st.markdown(f'<div class="response-box">{full_text}</div>', unsafe_allow_html=True)
        
        # 4. 触发语音
        speak_text(full_text)

# --- 模块1：知识星球 ---
with tab1:
    st.subheader("🌍 知识星球 - 全学科辅导")
    q1 = st.text_input("想请教老师什么问题？", placeholder="例如：为什么天空是蓝色的？")
    if st.button("发送", key="btn1"):
        handle_ai_response("知识星球", q1)

# --- 模块2：语言学习 ---
with tab2:
    st.subheader("📚 语言学习 - 多模态实验室")
    col1, col2 = st.columns([1, 1])
    with col1:
        upload_file = st.file_uploader("上传课本照片、音频或视频", type=["jpg", "png", "mp3", "wav", "mp4", "mov"])
        text_input = st.text_input("对素材的要求", placeholder="例如：请翻译这段话并纠正我的语法")
    with col2:
        if st.button("开始分析", key="btn2"):
            media_data = None
            if upload_file:
                if upload_file.type.startswith("image"):
                    import PIL.Image
                    media_data = PIL.Image.open(upload_file)
                else:
                    st.info("视频/音频分析需通过 Google File API (MVP版请先尝试图片)")
            
            handle_ai_response("语言学习", text_input, media_data)

# --- 模块3：陪玩伙伴 ---
with tab3:
    st.subheader("🎮 陪玩伙伴 - 创意与游戏")
    play_request = st.text_input("想让老师陪你做什么？", placeholder="例如：跟我玩个英语猜谜游戏")
    if st.button("开始玩耍", key="btn3"):
        handle_ai_response("陪玩伙伴", play_request)
