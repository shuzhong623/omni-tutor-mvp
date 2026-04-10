import streamlit as st
import google.generativeai as genai
import os
import streamlit.components.v1 as components
import PIL.Image

# ================= 1. 页面配置与视觉样式 =================
st.set_page_config(page_title="Omni-Tutor AI", layout="wide", page_icon="🌟")

# 优化 UI 界面，让它看起来更像一个教育 App
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #4A90E2; color: white; font-weight: bold; }
    .avatar-container { text-align: center; margin-bottom: 20px; }
    .response-box { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #4A90E2; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); font-size: 18px; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 侧边栏：用户设定 =================
with st.sidebar:
    st.header("⚙️ 用户设定")
    api_key = st.text_input("请输入 Gemini API Key:", type="password")
    
    # 锁定你测试成功的最高版本模型
    target_model_name = "models/gemini-2.5-flash"
    st.info(f"驱动模型: `{target_model_name}`")
    
    user_level = st.selectbox("选择用户级别", ["Baby", "Pupil", "Student"])
    lang_mode = st.selectbox("语言模式", ["English Only", "Chinese Only", "Mixed Mode"])
    
    st.divider()
    st.markdown(f"**当前状态**\n\n级别: `{user_level}`\n模式: `{lang_mode}`")

# ================= 3. 核心 AI 逻辑配置 =================
if api_key:
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(target_model_name)
    except Exception as e:
        st.error(f"模型初始化失败: {e}")
        st.stop()
else:
    st.warning("⚠️ 请在左侧输入 API Key 以激活 AI 老师")
    st.stop()

# 情感头像映射
AVATARS = {"HAPPY": "😊", "THINKING": "🤔", "SURPRISED": "😲", "SERIOUS": "🧐", "DEFAULT": "🌟"}

# 语音合成函数 (调用浏览器内置 TTS)
def speak_text(text):
    lang = 'en-US' if lang_mode == "English Only" else 'zh-CN'
    # 剔除情绪标签，只读正文
    clean_text = text.replace("[HAPPY]", "").replace("[THINKING]", "").replace("[SURPRISED]", "").replace("[SERIOUS]", "")
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance({repr(clean_text)});
        msg.lang = '{lang}';
        window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

# 优化后的 Prompt 生成 (彻底解决“剧本模式”问题)
def get_full_prompt(module, content, is_vision=False):
    persona_map = {
        "Baby": "你是一个超级亲切的幼儿园老师。请直接用最简单、最温暖的语言说话，多用叠词（如：小眼睛、亮亮的）和感叹词。不要写任何动作描述，直接对孩子说话。",
        "Pupil": "你是一个幽默博学的大哥哥/大姐姐。说话要像在和好朋友聊天，鼓励对方探索，把知识点变成有趣的谜题。直接对话，不要写剧本提示。",
        "Student": "你是一个睿智客观的学术教练。说话简洁、专业，多用启发式提问引导学生思考。直接提供学术引导，禁止输出动作描述。"
    }
    
    # 强力约束指令：禁止输出括号里的动作描述
    strict_constraint = """
    IMPORTANT RULE: 
    1. DO NOT include any stage directions, mood descriptions, or actions in parentheses (e.g., NO '(smiling)', NO '(slowly)').
    2. ONLY output the words you would actually say aloud to the user.
    3. If you feel an emotion, express it through your words, not by describing the emotion in brackets.
    """
    
    prompt = f"Role: Omni-Tutor. Level: {user_level}. Mode: {lang_mode}. Personality: {persona_map[user_level]}. Module: {module}. {strict_constraint}"
    
    if is_vision:
        prompt += "\nVISION TASK: You are seeing a photo from the user's camera. Naturally talk about what you see. Interact with the objects in the image."
    
    prompt += "\nREQUIREMENT: Start your response with exactly one mood tag: [HAPPY], [THINKING], [SURPRISED], [SERIOUS]."
    
    return f"{prompt}\n\nUser: {content}"

# 统一响应处理函数
def handle_ai_response(module, user_input, media=None):
    with st.spinner("老师正在观察并思考..."):
        try:
            is_vision = True if media else False
            content_list = [get_full_prompt(module, user_input, is_vision)]
            if media: 
                content_list.append(media)
                
            response = model.generate_content(content_list)
            full_text = response.text
            
            # 提取情绪标签
            mood = "DEFAULT"
            for tag in AVATARS.keys():
                if f"[{tag}]" in full_text:
                    mood = tag
                    full_text = full_text.replace(f"[{tag}]", "").strip()
                    break
            
            # 显示头像
            st.markdown(f'<div class="avatar-container"><div style="font-size: 80px;">{AVATARS[mood]}</div><p style="color: gray;">Omni-Tutor 此时心情: {mood}</p></div>', unsafe_allow_html=True)
            
            # 显示对话卡片
            st.markdown(f'<div class="response-box">{full_text}</div>', unsafe_allow_html=True)
            
            # 触发声音
            speak_text(full_text)
            
        except Exception as e:
            st.error(f"老师在思考时出了点小问题: {e}")

# ================= 4. 主界面 UI =================
st.title("🌟 Omni-Tutor 实时互动版")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📷 实时互动 (模拟直播)", "📚 语言学习", "🌍 知识星球"])

# 模块 1：实时互动 (相机拍照)
with tab1:
    st.subheader("模拟直播互动")
    st.write("点击下方相机拍照，AI 老师会立即看到你并开始对话")
    
    img_file = st.camera_input("捕捉现场画面")
    user_msg = st.text_input("你想对老师说什么？", placeholder="例如：老师你看我手里拿的是什么？")
    
    if st.button("发送给老师"):
        if img_file:
            img = PIL.Image.open(img_file)
            handle_ai_response("直播互动", user_msg if user_msg else "Look at my picture and start a conversation!", img)
        else:
            handle_ai_response("直播互动", user_msg)

# 模块 2：语言学习 (上传图片)
with tab2:
    st.subheader("语言学习 - 多模态实验室")
    col1, col2 = st.columns([1, 1])
    with col1:
        upload_file = st.file_uploader("上传照片", type=["jpg", "png", "jpeg"])
        text_input = st.text_input("对素材的要求", placeholder="例如：请翻译这段话并纠正我的语法")
    with col2:
        if st.button("开始分析"):
            media_data = None
            if upload_file:
                media_data = PIL.Image.open(upload_file)
            handle_ai_response("语言学习", text_input, media_data)

# 模块 3：知识星球 (文字问答)
with tab3:
    st.subheader("知识星球 - 全学科辅导")
    q = st.text_input("想请教老师什么问题？", placeholder="例如：为什么天空是蓝色的？")
    if st.button("发送"):
        handle_ai_response("知识星球", q)
