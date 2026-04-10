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
    .avatar-container { text-align: center; margin-bottom: 20px; }
    .response-box { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #4A90E2; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); font-size: 18px; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 侧边栏：密钥与设定 =================
with st.sidebar:
    st.header("⚙️ 核心设置")
    gemini_key = st.text_input("Gemini API Key:", type="password")
    tts_key = st.text_input("Google TTS API Key:", type="password")
    
    target_model_name = "models/gemini-2.5-flash"
    user_level = st.selectbox("用户级别", ["Baby", "Pupil", "Student"])
    lang_mode = st.selectbox("语言模式", ["English Only", "Chinese Only", "Mixed Mode"])
    
    st.divider()
    st.markdown(f"**状态**: `{user_level}` | `{lang_mode}`")

if not gemini_key:
    st.warning("⚠️ 请输入 Gemini API Key 以激活")
    st.stop()

genai.configure(api_key=gemini_key)
model = genai.GenerativeModel(target_model_name)

# ================= 3. 核心功能模块 =================

# --- 高质量 Google Cloud TTS 函数 ---
def speak_with_google_tts(text):
    if not tts_key:
        st.info("未配置 TTS Key，将使用基础机器音。")
        # 回退到基础浏览器语音
        lang = 'en-US' if lang_mode == "English Only" else 'zh-CN'
        js_code = f"<script>var msg = new SpeechSynthesisUtterance({repr(text)}); msg.lang = '{lang}'; window.speechSynthesis.speak(msg);</script>"
        components.html(js_code, height=0)
        return

    try:
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={tts_key}"
        # 根据模式选择语音类型
        voice_name = "en-US-Neural2-F" if lang_mode == "English Only" else "zh-CN-Neural2-A"
        payload = {
            "input": {"text": text},
            "voice": {"languageCode": "en-US" if lang_mode == "English Only" else "zh-CN", "name": voice_name},
            "audioConfig": {"audioEncoding": "MP3"}
        }
        response = requests.post(url, json=payload)
        audio_content = response.json().get("audioContent")
        if audio_content:
            audio_bytes = base64.b64decode(audio_content)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.error(f"TTS 播放失败: {e}")

# --- 增强版 Prompt (强制 Mixed Mode) ---
def get_full_prompt(module, content, is_vision=False, is_audio=False):
    persona_map = {
        "Baby": "亲切的幼儿园老师。多用叠词，简单温暖。",
        "Pupil": "幽默博学的大哥哥/大姐姐。引导探索，知识游戏化。",
        "Student": "睿智学术教练。苏格拉底式启发，简洁专业。"
    }
    
    # 核心修改：强制 Mixed Mode 逻辑
    mode_instruction = ""
    if lang_mode == "Mixed Mode":
        mode_instruction = """
        CRITICAL TEACHING RULE: You MUST use 'Mixed Mode'. 
        Even if the user speaks Chinese, you must:
        1. Introduce 1-3 relevant English keywords or phrases in your answer.
        2. Provide the English word -> Chinese translation -> Example sentence.
        3. Encourage the user to repeat the English part.
        Make it a natural part of the conversation, not a dictionary list.
        """
    elif lang_mode == "English Only":
        mode_instruction = "STRICTLY use English only. Adjust vocabulary for the user level."

    constraint = "SAY ONLY THE WORDS YOU SPEAK. No stage directions like (smiling) or [HAPPY]. Start your response with a mood tag like [HAPPY], [THINKING], [SURPRISED], [SERIOUS]."
    
    prompt = f"Role: Omni-Tutor. Level: {user_level}. Mode: {lang_mode}. Personality: {persona_map[user_level]}. Module: {module}. {mode_instruction} {constraint}"
    
    if is_vision:
        prompt += "\nVISION TASK: You see a photo. Naturally integrate the visual objects into your teaching."
    if is_audio:
        prompt += "\nAUDIO TASK: You are listening to the user's pronunciation. Please analyze the grammar, fluency, and pronunciation. Correct the mistakes and provide a 'Perfect Version' for the user to mimic."
        
    return f"{prompt}\n\nUser: {content}"

# ================= 4. 主界面 =================
st.title("🌟 Omni-Tutor 全能AI老师 Pro")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🎙️ 语音/视觉互动", "📚 语言学习", "🌍 知识星球"])

def handle_ai_response(module, user_input, media=None, audio_data=None):
    with st.spinner("老师正在倾听并思考..."):
        try:
            is_vision = True if media else False
            is_audio = True if audio_data else False
            
            # 构建多模态输入列表
            content_list = [get_full_prompt(module, user_input, is_vision, is_audio)]
            if media: content_list.append(media)
            if audio_data: 
                # Gemini 2.5 处理音频文件的格式
                content_list.append({"mime_type": "audio/wav", "data": audio_data})
                
            response = model.generate_content(content_list)
            full_text = response.text
            
            # 情绪处理
            moods = {"HAPPY": "😊", "THINKING": "🤔", "SURPRISED": "😲", "SERIOUS": "🧐"}
            mood = "DEFAULT"
            for tag, emoji in moods.items():
                if f"[{tag}]" in full_text:
                    mood = tag
                    full_text = full_text.replace(f"[{tag}]", "").strip()
                    break
            
            st.markdown(f'<div class="avatar-container"><div style="font-size: 80px;">{moods.get(mood, "🌟")}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-box">{full_text}</div>', unsafe_allow_html=True)
            
            # 使用 Google Cloud TTS 播放
            speak_with_google_tts(full_text)
            
        except Exception as e:
            st.error(f"错误: {e}")

# --- 模块 1：综合互动 (相机 + 麦克风) ---
with tab1:
    st.subheader("实时互动实验室")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("📸 **视觉捕捉**")
        img_file = st.camera_input("拍摄现场")
    
    with col2:
        st.write("🎤 **语音输入 (发音练习)**")
        audio_record = mic_recorder(start_prompt="点击开始录音", stop_prompt="停止录音", key='recorder')
    
    user_msg = st.text_input("你想对老师说什么？", placeholder="例如：老师，我的发音对吗？")
    
    if st.button("发送给老师"):
        media = PIL.Image.open(img_file) if img_file else None
        audio = audio_record['bytes'] if audio_record else None
        handle_ai_response("综合互动", user_msg if user_msg else "Please analyze my photo or audio!", media, audio)

# --- 模块 2：语言学习 ---
with tab2:
    st.subheader("语言学习 - 深度分析")
    up_file = st.file_uploader("上传照片", type=["jpg", "png"])
    up_req = st.text_input("要求")
    if st.button("开始分析"):
        img = PIL.Image.open(up_file) if up_file else None
        handle_ai_response("语言学习", up_req, img)

# --- 模块 3：知识星球 ---
with tab3:
    st.subheader("知识星球 - 全学科辅导")
    q = st.text_input("提问")
    if st.button("发送"):
        handle_ai_response("知识星球", q)
