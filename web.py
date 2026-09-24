import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import requests
import streamlit as st
import gspread
from streamlit_autorefresh import st_autorefresh
import google.generativeai as genai
from PIL import Image
import json
import streamlit.components.v1 as components

# ១. កំណត់ទម្រង់វេបសាយ
st.set_page_config(page_title="AI ពេទ្យធ្មេញ", page_icon="🦷", layout="centered")

for key in ['ស្កេន_ឈ្មោះ', 'ស្កេន_អាយុ', 'ស្កេន_ម៉ោង', 'ស្កេន_លុប']:
    if key not in st.session_state:
        st.session_state[key] = "" if key == 'ស្កេន_ឈ្មោះ' else (25 if key == 'ស្កេន_អាយុ' else 0)

# ២. កូដ CSS រចនាបែប Gemini Minimalist
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Kantumruy Pro', sans-serif !important; }
    .stApp { background-color: #f8fafc; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 750px; }
    
    div[data-testid="stToggle"] label p { font-size: 0px; }
    div[data-testid="stToggle"] label p::before { content: "🔄 Auto (10s)"; font-size: 14px; margin-right: 5px; color: gray;}
    
    div.stButton > button {
        border-radius: 12px !important; font-weight: bold !important; height: 48px !important;
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important; color: white !important; border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ៣. ផ្នែកក្បាល និង Auto Refresh
col_t1, col_t2 = st.columns([8, 2])
with col_t2: is_auto_refresh = st.toggle("Auto refresh", value=True, key="auto_ref")
if is_auto_refresh: st_autorefresh(interval=10000, key="ar")

st.markdown("<h2 style='text-align: center; color: #0f172a; margin-top: -20px; margin-bottom: 20px;'>🏥 AI ពេទ្យធ្មេញ</h2>", unsafe_allow_html=True)

# ៤. ភ្ជាប់ទៅ Google Sheets & Gemini
@st.cache_resource
def init_services():
    credentials = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open("Dental_AI_Data")
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    system_prompt = """
    អ្នកគឺជា AI ជំនួយការគ្លីនិកពេទ្យធ្មេញដ៏ជំនាញ។ 
    หน้าที่របស់អ្នកគឺអានអត្ថបទ ឬរូបភាពដែលអ្នកប្រើប្រាស់បញ្ជូនមក ហើយទាញយកតម្លៃមកបំពេញក្នុង JSON ឱ្យបានត្រឹមត្រូវ៖
    - "name": ឈ្មោះអ្នកជំងឺ (ជាភាសាខ្មែរ ឬឡាតាំង)
    - "age": អាយុ (ជាខ្នាតលេខគត់ ឧ. 25)
    - "time": ម៉ោងណាត់ជួប (បើ ព្រឹក/Morning ដាក់ 0; បើ ល្ងាច/Evening ដាក់ 1)
    - "cancelled": ធ្លាប់លុបការណាត់ពីមុនទេ (បើធ្លាប់ដាក់ 1; បើមិនធ្លាប់ដាក់ 0)
    សូមឆ្លើយតបមកវិញជា JSON សុទ្ធសាធ (Valid JSON) ដោយគ្មានអក្សរអធិប្បាយផ្សេងទៀតឡើយ។
    """
    model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=system_prompt)
    return sh.sheet1, model

worksheet, vision_model = init_services()

def train_ai():
    df = pd.DataFrame(worksheet.get_all_records())
    model = RandomForestClassifier()
    model.fit(df[['អាយុ', 'ម៉ោងណាត់', 'ធ្លាប់លុបចោលការណាត់ពីមុន']].values, df['លទ្ធផលជាក់ស្តែង'].values)
    return model, df

ai_model, df_ទិន្នន័យចាស់ = train_ai()

def send_telegram(message):
    bot_token = '8573963689:AAEX3OFDd4IKFqmMKUIOWlhKc8lHTg8v64M'  # <--- កុំភ្លេចដាក់ Token
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id=8805554075&text={message}"
    try: requests.get(url) 
    except: pass

# ៥. បន្ថែមប្រអប់និយាយដោយសំឡេង (Voice Record Component)
voice_html = """
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
    <button onclick="startListening()" style="background: #ef4444; color: white; border: none; padding: 10px 15px; border-radius: 10px; cursor: pointer; font-weight: bold; font-family: 'Kantumruy Pro', sans-serif;">
        🎙️ ចុចនិយាយ (Voice)
    </button>
    <span id="status" style="color: #64748b; font-size: 14px; font-family: 'Kantumruy Pro', sans-serif;">សូមចុចប៊ូតុងដើម្បីនិយាយជាភាសាខ្មែរ...</span>
</div>
<script>
function startListening() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'km-KH'; // កំណត់ភាសាខ្មែរ
    recognition.onstart = function() {
        document.getElementById('status').innerText = "🔴 កំពុងស្តាប់... សូមនិយាយ!";
    };
    recognition.onresult = function(event) {
        const speechToText = event.results[0][0].transcript;
        document.getElementById('status').innerText = "✅ ទទួលបាន៖ " + speechToText;
        // ส่งข้อมูลไปยัง Streamlit input (រក្សាទុកក្នុង Local Storage)
        const inputField = window.parent.document.querySelector('input[aria-label="prompt"]');
        if (inputField) {
            inputField.value = speechToText;
            inputField.dispatchEvent(new Event('input', { bubbles: true }));
        }
    };
    recognition.onerror = function(event) {
        document.getElementById('status').innerText = "❌ មានបញ្ហាក្នុងការស្តាប់ សូមព្យាយាមម្តងទៀត។";
    };
    recognition.start();
}
</script>
"""
components.html(voice_html, height=50)

# ៦. របារបញ្ជាឆ្លាតវៃ (GEMINI STYLE BAR)
with st.form(key='gemini_form', clear_on_submit=False):
    col_input, col_file, col_submit = st.columns([6, 1.2, 1.2], gap="small")
    with col_input:
        ប្រអប់អត្ថបទ = st.text_input("prompt", placeholder="សួរ AI ឬនិយាយ...", label_visibility="collapsed")
    with col_file:
        រូបភាព = st.file_uploader("file", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    with col_submit:
        បញ្ជូន = st.form_submit_button("⬆️ ស្កេន", use_container_width=True)

if បញ្ជូន and (ប្រអប់អត្ថបទ or រូបភាព):
    with st.spinner("AI កំពុងវិភាគ..."):
        try:
            សំណុំទិន្នន័យ = ["ទាញយកទិន្នន័យអ្នកជំងឺពីអត្ថបទ ឬរូបភាពនេះជា JSON:"]
            if ប្រអប់អត្ថបទ: សំណុំទិន្នន័យ.append(ប្រអប់អត្ថបទ)
            if រូបភាព: សំណុំទិន្នន័យ.append(Image.open(រូបភាព))
            
            ចម្លើយ = vision_model.generate_content(សំណុំទិន្នន័យ)
            អត្ថបទ_json = ចម្លើយ.text.replace("```json", "").replace("```", "").strip()
            ទិន្នន័យ = json.loads(អត្ថបទ_json)
            
            if "name" in ទិន្នន័យ: st.session_state.ស្កេន_ឈ្មោះ = ទិន្នន័យ["name"]
            if "age" in ទិន្នន័យ: st.session_state.ស្កេន_អាយុ = int(ទិន្នន័យ["age"])
            if "time" in ទិន្នន័យ: st.session_state.ស្កេន_ម៉ោង = int(ទិន្នន័យ["time"])
            if "cancelled" in ទិន្នន័យ: st.session_state.ស្កេន_លុប = int(ទិន្នន័យ["cancelled"])
            st.success("✅ AI បានទាញទិន្នន័យដាក់ចូល Form ខាងក្រោមរួចរាល់!")
        except:
            st.error("⚠️ AI មិនអាចអានទិន្នន័យបានទេ។ សូមព្យាយាមម្តងទៀត។")

st.divider()

# ៧. ទម្រង់ Auto-fill
st.markdown("📝 **ពិនិត្យ និងរក្សាទុកទិន្នន័យ**")
ឈ្មោះ = st.text_input("ឈ្មោះ", value=st.session_state.ស្កេន_ឈ្មោះ)
col1, col2 = st.columns(2)
with col1: អាយុ = st.number_input("អាយុ", min_value=1, max_value=100, value=st.session_state.ស្កេន_អាយុ)
with col2: ម៉ោងណាត់ = st.selectbox("ម៉ោងណាត់", [0, 1], index=st.session_state.ស្កεន_ម៉ោង if 'ស្កεន_ម៉ោង' in locals() else st.session_state.ស្កេន_ម៉ោង, format_func=lambda x: "ព្រឹក ☀️" if x==0 else "ល្ងាច 🌙")
ធ្លាប់លុប = st.radio("ធ្លាប់លុបការណាត់?", [0, 1], index=st.session_state.ស្កេន_លុប, format_func=lambda x: "ទេ ❌" if x==0 else "ធ្លាប់ ✅", horizontal=True)

if st.button("💾 រក្សាទុកចូល Cloud", use_container_width=True):
    if ឈ្មោះ:
        ការព្យាករណ៍ = ai_model.predict([[អាយុ, ម៉ោងណាត់, ធ្លាប់លុប]])[0]
        សារ = f"⚠️ ព្រមាន៖ {ឈ្មោះ} អាចមិនមកតាមការណាត់!" if ការព្យាករណ៍==1 else f"✅ ធម្មតា៖ {ឈ្មោះ} នឹងមកតាមការណាត់។"
        st.error(សារ) if ការព្យាករណ៍==1 else st.success(សារ)
        send_telegram(សារ)
        worksheet.append_row([ឈ្មោះ, អាយុ, ម៉ោងណាត់, ធ្លាប់លុប, int(ការព្យាករណ៍)])
        st.info("រក្សាទុករួចរាល់!")
        st.session_state.ស្កេន_ឈ្មោះ = ""
        st.session_state.ស្កេន_អាយុ = 25
    else:
        st.warning("សូមបញ្ចូលឈ្មោះអ្នកជំងឺ!")

st.divider()
st.dataframe(df_ទិន្នន័យចាស់, use_container_width=True)