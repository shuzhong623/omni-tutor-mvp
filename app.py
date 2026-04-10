import streamlit as st
import google.generativeai as genai
import os
import streamlit.components.v1 as components

# ================= 1. 页面配置与样式 =================
st.set_page_config(page_title="Omni-Tutor AI", layout="wide", page_icon="🌟")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #4A90E2; color: white; }
    .avatar-container { text-align: center; margin-bottom: 20px; }
    .response-box { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #4A90E2; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 侧边栏设定 =================
with st.sidebar:
    st.header("⚙️ 用户设定")
    api_key = st.text_input("请输入你的 Gemini API Key:", type="password")
    
    # --- 新增：模型选择下拉框，用于排查 NotFound 错误 ---
    model_option = st.selectbox(
        "选择模型版本 (如果报错NotFound请尝试切换)", 
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    )
    
    user_level = st.selectbox("选择用户级别", ["Baby", "Pupil", "Student"])
    lang_mode = st.selectbox("语言模式", ["English Only", "Chinese Only", "Mixed Mode"])
    
    st.divider()
    st.markdown(f"**当前状态**\n\n模型: `{model_option}`\n级别: `{user_level}`\n模式: `{lang_mode}`")

# ================= 3. 核心逻辑配置 =================
if api_key:
    genai.configure(api_key=api_key)
    # 使用用户选择的模型名称
    try:
        model = genai.GenerativeModel(model_option)
    except Exception as e:
        st.error(f"模型初始化失败: {e}")
        st.stop()
else:
    st.warning("⚠️ 请在左侧输入 API Key 以激活 AI 老师")
    st.stop()

# --- 情感头像映射表 ---
AVATARS = {"HAPPY": "😊", "THINKING": "🤔", "SURPRISED": "😲", "SERIOUS": "🧐", "DEFAULT": "🌟"}

def speak_text(text):
    lang = 'en-US' if lang_mode == "English Only" else 'zh-CN' if lang_mode == "Chinese Only" else 'zh-CN'
    js_code = f"""<script>var msg = new SpeechSynthesisUtterance({repr(text)}); msg.lang = '{lang}'; window.speechSynthesis.speak(msg);</script>"""
    components.html(js_code, height=0)

def get_full_prompt(module, content):
    persona_map = {
        "Baby": "幼儿园老师。语速极慢，多用拟声词(Wow!, Boing!)，极高情绪价值，将错误轻量化。逻辑：感知->命名->模仿。",
        "Pupil": "幽默博学的大哥哥/大姐姐。采用任务驱动法，将知识点游戏化，鼓励用户问'为什么'。",
        "Student": "睿智客观的学术教练。采用苏格拉底式提问法，引导用户自行推导，强调批判性思维。"
    }
    prompt = f"Role: You are Omni-Tutor. User Level: {user_level}. Language Mode: {lang_mode}. Personality: {persona_map[user_level]} Current Module: {module}. CRITICAL REQUIREMENT: Start your response with exactly one of these mood tags: [HAPPY], [THINKING], [SURPRISED], [SERIOUS]. Then provide your answer."
    return f"{prompt}\n\nUser Request: {content}"

# ================= 4. 主界面 UI =================
st.title("🌟 Omni-Tutor 全能AI老师")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🌍 知识星球", "📚 语言学习", "🎮 陪玩伙伴"])

def handle_ai_response(module, user_input, media=None):
    with st.spinner("老师正在思考..."):
        try:
            content_list = [get_full_prompt(module, user_input)]
            if media:
                content_list.append(media)
            
            response = model.generate_content(content_list)
            full_text = response.text
            
            mood = "DEFAULT"
            for tag in AVATARS.keys():
                if f"[{tag}]" in full_text:
                    mood = tag
                    full_text = full_text.replace(f"[{tag}]", "").strip()
                    break
            
            st.markdown(f'<div class="avatar-container"><div style="font-size: 80px;">{AVATARS[mood]}</div><p style="color: gray;">Omni-Tutor 此时心情: {mood}</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-box">{full_text}</div>', unsafe_allow_html=True)
            speak_text(full_text)
            
        except google.api_core.exceptions.NotFound:
            st.error(f"❌ 模型 `{model_option}` 在你的 API Key 中不可用。请尝试在左侧切换另一个模型版本。")
        except Exception as e:
            st.error(f"发生未知错误: {e}")

# --- 模块 1, 2, 3 ---
with tab1:
    st.subheader("🌍 知识星球")
    q1 = st.text_input("想请教老师什么问题？")
    if st.button("发送", key="btn1"):
        handle_ai_response("知识星球", q1)

with tab2:
    st.subheader("📚 语言学习")
    upload_file = st.file_uploader("上传照片", type=["jpg", "png"])
    text_input = st.text_input("要求")
    if st.button("分析", key="btn2"):
        media_data = None
        if upload_file:
            import PIL.Image
            media_data = PIL.Image.open(upload_file)
        handle_ai_response("语言学习", text_input, media_data)

with tab3:
    st.subheader("🎮 陪玩伙伴")
    play_request = st.text_input("想玩什么？")
    if st.button("开始", key="btn3"):
        handle_ai_response("陪玩伙伴", play_request)

# 导入缺失的异常类
import google.api_core.exceptions
