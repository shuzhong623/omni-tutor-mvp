import streamlit as st
import google.generativeai as genai
import os
import streamlit.components.v1 as components
import google.api_core.exceptions

# ================= 1. 页面配置 =================
st.set_page_config(page_title="Omni-Tutor Diagnostic", layout="wide")

st.title("🛠️ Omni-Tutor API 诊断工具")
st.info("此版本旨在查明你的 API Key 到底支持哪些模型。")

# ================= 2. 侧边栏 =================
with st.sidebar:
    st.header("🔑 密钥验证")
    api_key = st.text_input("请输入你的 Gemini API Key:", type="password")

# ================= 3. 诊断逻辑 =================
if api_key:
    genai.configure(api_key=api_key)
    
    st.subheader("🔍 步骤 1: 探测可用模型列表")
    if st.button("开始扫描可用模型"):
        try:
            # 核心诊断指令：获取当前 Key 支持的所有模型
            available_models = genai.list_models()
            
            st.success("✅ 成功连接到 Google 服务器！")
            st.write("你的 API Key 目前可以使用的模型列表如下：")
            
            model_list = []
            for m in available_models:
                st.markdown(f"- **{m.name}** (支持的操作: {m.supported_generation_methods})")
                model_list.append(m.name)
            
            st.session_state['available_models'] = model_list
            
        except google.api_core.exceptions.Unauthenticated:
            st.error("❌ 认证失败：API Key 错误或已失效。请检查 Key 是否复制完整。")
        except google.api_core.exceptions.PermissionDenied:
            st.error("❌ 权限被拒绝：你的账户可能没有权限访问 Generative AI API。请检查 Google AI Studio 中的 API 状态。")
        except Exception as e:
            st.error(f"❌ 发生未知错误: {e}")

    # 如果探测到了模型，则显示测试区
    if 'available_models' in st.session_state:
        st.divider()
        st.subheader("🧪 步骤 2: 快速模型测试")
        test_model = st.selectbox("从列表中选择一个模型进行测试:", st.session_state['available_models'])
        test_input = st.text_input("输入一个简单的词（如 'Hello'）测试:", "Hello")
        
        if st.button("发送测试请求"):
            try:
                temp_model = genai.GenerativeModel(model_name=test_model)
                response = temp_model.generate_content(test_input)
                st.success(f"🎉 测试成功！模型 `{test_model}` 工作正常。")
                st.write(f"AI 回复: {response.text}")
            except Exception as e:
                st.error(f"❌ 该模型测试失败: {e}")
else:
    st.warning("请在左侧输入 API Key 以开始诊断。")

st.markdown("---")
st.markdown("""
**如果扫描结果为空或报错，请检查：**
1. 您是否在 [Google AI Studio](https://aistudio.google.com/) 创建的 Key？
2. 您的 Google 账号是否处于支持的国家/地区？
3. 您是否在 AI Studio 中点击了 'Create API key in new project'？
""")
