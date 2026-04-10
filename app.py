import streamlit as st
import google.generativeai as genai
import os
import streamlit.components.v1 as components
import PIL.Image

# ================= 1. 页面配置 =================
st.set_page_config(page_title="Omni-Tutor Live-Sim", layout="wide", page_icon="🌟")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #4A90E2; color: white; font-weight: bold; }
    .avatar-container { text-align: center; margin-bottom: 20px; }
    .response-box { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #4A90E2; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 侧边栏 =================
with st.sidebar:
    st.header("⚙️ 用户设定")
    api_key = st.text_input("Gemini API Key:", type="password")
    target_model_name = "models/gemini-2.5-flash"
    user_level = st.selectbox("用户级别", ["Baby", "Pupil", "Student"])
    lang_mode = st.selectbox("语言模式", ["English Only", "Chinese Only", "Mixed Mode"])

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(target_model_name)
else:
    st.warning("⚠️ 请输入 API Key")
    st.stop()

# ================= 3. 核心逻辑 =================
AVATARS = {"HAPPY": "😊", "THINKING": "🤔", "SURPRISED": "😲", "SERIOUS": "🧐", "DEFAULT": "🌟"}

def speak_text(text):
    lang = 'en-US' if lang_mode == "English Only" else 'zh-CN'
    clean_text = text.replace("[HAPPY]", "").replace("[THINKING]", "").replace("[SURPRISED]", "").replace("[SERIOUS]", "")
    js_code = f"<script>var msg = new SpeechSynthesisUtterance({repr(clean_text)}); msg.lang = '{lang}'; window.speechSynthesis.speak(msg);</script>"
    components.html(js_code, height=0)

def get_full_prompt(module, content, is_vision=False):
    persona_map = {
        "Baby": "幼儿园老师。语速极慢，拟声词多，高情绪价值。逻辑：感知->命名->模仿。",
        "Pupil": "幽默博学的大哥哥/大姐姐。任务驱动，知识游戏化。",
        "Student": "睿智学术教练。苏格拉底式提问，引导推导。"
    }
    prompt = f"Role: Omni-Tutor. Level: {user_level}. Mode: {lang_mode}. Personality: {persona_map[user_level]}. Module: {module}."
    if is_vision:
        prompt += "\nSPECIAL TASK: You are looking at the user's real-time camera snapshot. Describe what you see, ask questions about the objects, and relate it to learning."
    prompt += "\nREQUIREMENT: Start with mood tag: [HAPPY], [THINKING], [SURPRISED], [SERIOUS]."
    return f"{prompt}\n\nUser: {content}"

def handle_ai_response(module, user_input, media=None):
    with st.spinner("老师正在观察..."):
        try:
            is_vision = True if media else False
            content_list = [get_full_prompt(module, user_input, is_vision)]
            if media: content_list.append(media)
            
            response = model.generate_content(content_list)
            full_text = response.text
            
            mood = "DEFAULT"
            for tag in AVATARS.keys():
                if f"[{tag}]" in full_text:
                    mood = tag
                    full_text = full_text.replace(f"[{tag}]", "").strip()
                    break
            
            st.markdown(f'<div class="avatar-container"><div style="font-size: 80px;">{AVATARS[mood]}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-box">{full_text}</div>', unsafe_allow_html=True)
            speak_text(full_text)
        except Exception as e:
            st.error(f"错误: {e}")

# ================= 4. 主界面 =================
st.title("🌟 Omni-Tutor 实时模拟版")

tab1, tab2, tab3 = st.tabs(["📷 实时互动 (模拟直播)", "📚 语言学习", "🌍 知识星球"])

with tab1:
    st.subheader("模拟直播互动")
    st.write("点击下方相机拍照，AI 老师会立即看到你并开始对话")
    
    # --- 核心升级：实时相机输入 ---
    img_file = st.camera_input("捕捉现场画面")
    
    user_msg = st.text_input("你想对老师说什么？", placeholder="例如：老师你看我手里拿的是什么？")
    
    if st.button("发送给老师"):
        if img_file:
            img = PIL.Image.open(img_file)
            handle_ai_response("直播互动", user_msg if user_msg else "Look at my picture and start a conversation!", img)
        else:
            handle_ai_response("直播互动", user_msg)

with tab2:
    st.subheader("语言学习")
    upload = st.file_uploader("上传照片", type=["jpg", "png"])
    req = st.text_input("要求")
    if st.button("分析"):
        img = PIL.Image.open(upload) if upload else None
        handle_ai_response("语言学习", req, img)

with tab3:
    st.subheader("知识星球")
    q = st.text_input("提问")
    if st.button("发送"):
        handle_ai_response("知识星球", q)
