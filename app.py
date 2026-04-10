import streamlit as st
import google.generativeai as genai
import os
import streamlit.components.v1 as components
import PIL.Image
import requests
import base64
from streamlit_mic_recorder import mic_recorder

# ================= 1. 页面配置与视觉样式 =================
st.set_page_config(page_title="Omni-Tutor Pro", layout="wide", page_icon="🌟")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #4A90E2; color: white; font-weight: bold; }
    .avatar-container { text-align: center; margin-bottom: 10px; }
    .response-box { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #4A90E2; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); font-size: 18px; line-height: 1.6; }
    .audio-container { margin-bottom: 15px; background: #eef2f6; padding: 10px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 侧边栏 =================
with st.sidebar:
    st.header("⚙️ 核心设置")
    gemini_key = st.text_input("Gemini API Key:", type="password")
    tts_key = st.text_input("Google TTS API Key:", type="password")
    target_model_name = "models/gemini-2.5-flash"
    user_level = st.selectbox("用户级别", ["Baby", "Pupil", "Student"])
    lang_mode = st.selectbox("语言模式", ["English Only", "Chinese Only", "Mixed Mode"])

if not gemini_key:
    st.warning("⚠️ 请输入 Gemini API Key 以激活")
    st.stop()

genai.configure(api_key=gemini_key)
model = genai.GenerativeModel(target_model_name)

# ================= 3. 核心功能 =================

def get_google_tts_audio(text):
    if not tts_key:
        return None
    try:
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={tts_key}"
        
        # --- 核心修改点：删除具体声音名称(name)，仅保留语言代码(languageCode) ---
        # 这样 Google 会自动为你选择当前账户可用且最匹配的默认声音，彻底避免 400 错误
        lang_code = "en-US" if lang_mode == "English Only" else "zh-CN"
        
        payload = {
            "input": {"text": text},
            "voice": {"languageCode": lang_code}, # 不再指定 name
            "audioConfig": {"audioEncoding": "MP3"}
        }
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            st.error(f"❌ TTS API 报错 ({response.status_code}): {response.text}")
            return None
        
        audio_content = response.json().get("audioContent")
        if audio_content:
            return base64.b64decode(audio_content)
    except Exception as e:
        st.error(f"TTS 系统故障: {e}")
        return None

def get_full_prompt(module, content, is_vision=False, is_audio=False):
    persona_map = {
        "Baby": "亲切的幼儿园老师。多用叠词，简单温暖。",
        "Pupil": "幽默博学的大哥哥/大姐姐。引导探索，知识游戏化。",
        "Student": "睿智学术教练。苏格拉底式启发，简洁专业。"
    }
    mode_instruction = ""
    if lang_mode == "Mixed Mode":
        mode_instruction = "CRITICAL: You MUST use 'Mixed Mode'. Integrate English keywords -> Translation -> Example sentence naturally."
    elif lang_mode == "English Only":
        mode_instruction = "STRICTLY use English only."

    constraint = "SAY ONLY THE WORDS YOU SPEAK. No stage directions. Start with mood tag: [HAPPY], [THINKING], [SURPRISED], [SERIOUS]."
    prompt = f"Role: Omni-Tutor. Level: {user_level}. Mode: {lang_mode}. Personality: {persona_map[user_level]}. Module: {module}. {mode_instruction} {constraint}"
    if is_vision: prompt += "\nVISION TASK: You see a photo. Interact with the objects."
    if is_audio: prompt += "\nAUDIO TASK: Analyze pronunciation. Correct and provide a 'Perfect Version'."
    return f"{prompt}\n\nUser: {content}"

def handle_ai_response(module, user_input, media=None, audio_data=None):
    with st.spinner("老师正在倾听并思考..."):
        try:
            is_vision = True if media else False
            is_audio = True if audio_data else False
            content_list = [get_full_prompt(module, user_input, is_vision, is_audio)]
            if media: content_list.append(media)
            if audio_data: content_list.append({"mime_type": "audio/wav", "data": audio_data})
            
            response = model.generate_content(content_list)
            full_text = response.text
            
            moods = {"HAPPY": "😊", "THINKING": "🤔", "SURPRISED": "😲", "SERIOUS": "🧐"}
            mood = "DEFAULT"
            for tag, emoji in moods.items():
                if f"[{tag}]" in full_text:
                    mood = tag
                    full_text = full_text.replace(f"[{tag}]", "").strip()
                    break
            
            st.markdown(f'<div class="avatar-container"><div style="font-size: 80px;">{moods.get(mood, "🌟")}</div></div>', unsafe_allow_html=True)
            
            audio_bytes = get_google_tts_audio(full_text)
            if audio_bytes:
                st.markdown('<div class="audio-container"><b>🎧 听听老师怎么说：</b></div>', unsafe_allow_html=True)
                st.audio(audio_bytes, format="audio/mp3")
            else:
                st.info("💡 提示：未能激活真人语音。请确认 API Key 已在 Cloud Console 中启用。")

            st.markdown(f'<div class="response-box">{full_text}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"错误: {e}")

# ================= 4. 主界面 =================
st.title("🌟 Omni-Tutor 全能AI老师 Pro")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🎙️ 语音/视觉互动", "📚 语言学习", "🌍 知识星球"])

with tab1:
    st.subheader("实时互动实验室")
    col1, col2 = st.columns(2)
    with col1:
        st.write("📸 **视觉捕捉**")
        img_file = st.camera_input("拍摄现场")
    with col2:
        st.write("🎤 **语音输入 (发音练习)**")
        audio_record = mic_recorder(start_prompt="点击开始录音", stop_prompt="停止录音", key='recorder')
    user_msg = st.text_input("你想对老师说什么？")
    if st.button("发送给老师"):
        media = PIL.Image.open(img_file) if img_file else None
        audio = audio_record['bytes'] if audio_record else None
        handle_ai_response("综合互动", user_msg if user_msg else "Please analyze!", media, audio)

with tab2:
    st.subheader("语言学习")
    up_file = st.file_uploader("上传照片", type=["jpg", "png"])
    up_req = st.text_input("要求")
    if st.button("分析"):
        img = PIL.Image.open(up_file) if up_file else None
        handle_ai_response("语言学习", up_req, img)

with tab3:
    st.subheader("知识星球")
    q = st.text_input("提问")
    if st.button("发送"):
        handle_ai_response("知识星球", q)
