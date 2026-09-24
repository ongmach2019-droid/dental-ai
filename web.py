import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import requests
import streamlit as st
import gspread
from streamlit_autorefresh import st_autorefresh
import google.generativeai as genai
from PIL import Image
import json
from streamlit_mic_recorder import speech_to_text  # បណ្ណាល័យស្តាប់សំឡេងថ្មី

# ១. កំណត់ទម្រង់វេបសាយ
st.set_page_config(page_title="AI ពេទ្យធ្មេញ", page_icon="🦷", layout="centered")

# អង្គចងចាំសម្រាប់ Auto-fill
for key in ['ស្កេន_ឈ្មោះ', 'ស្កេន_អាយុ', 'ស្កេន_ម៉ោង', 'ស្កេន_លុប']:
    if key not in st.session_state:
        st.session_state[key] = "" if key == 'ស្កេន_ឈ្មោះ' else (25 if key == 'ស្កេន_អាយុ' else 0)

# ២. កូដ CSS ធ្វើឱ្យវេបសាយស្រឡះ និងស្អាត (លុបអក្សរច្រើនៗចេញ)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Kantumruy Pro', sans-serif !important; }
    .stApp { background-color: #f8fafc; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 750px; }
    
    /* លាក់អក្សររបស់កុងតាក់ Auto Refresh */
    div[data-testid="stToggle"] label p { font-size: 0px; }
    div[data-testid="stToggle"] label p::before { content: "🔄 Auto (10s)"; font-size: 14px; margin-right: 5px; color: gray;}
    
    /* តម្រឹមប៊ូតុង Gemini Bar ឱ្យស្មើគ្នា */
    div[data-testid="column"] > div { margin-top: 1px; }
    
    div.stButton > button {
        border-radius: 10px !important; font-weight: bold !important; height: 42px !important;
        background: #0ea5e9 !important; color: white !important; border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ៣. ផ្នែកក្បាល និង Auto Refresh
col_t1, col_t2 = st.columns([8, 2])
with col_t2: is_auto_refresh = st.toggle("Auto refresh", value=True, key="auto_ref")
if is_auto_refresh: st_autorefresh(interval=10000, key="ar")

st.markdown("<h2 style='text-align: center; color: #0f172a; margin-top: -20px; margin-bottom: 25px;'>🏥 AI ពេទ្យធ្មេញ</h2>", unsafe_allow_html=True)

# ៤. ភ្ជាប់ទៅ Google Sheets & Gemini
@st.cache_resource
def init_services():
    credentials = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open("Dental_AI_Data")
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return sh.sheet1, genai.GenerativeModel('gemini-1.5-flash')

worksheet, vision_model = init_services()

def train_ai():
    df = pd.DataFrame(worksheet.get_all_records())
    model = RandomForestClassifier()
    model.fit(df[['អាយុ', 'ម៉ោងណាត់', 'ធ្លាប់លុបចោលការណាត់ពីមុន']].values, df['លទ្ធផលជាក់ស្តែង'].values)
    return model, df

ai_model, df_ទិន្នន័យចាស់ = train_ai()

def send_telegram(message):
    bot_token = '8573963689:AAEX3OFDd4IKFqmMKUIOWlhKc8lHTg8v64M'  # <--- ដាក់ Token នៅទីនេះ
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id=8805554075&text={message}"
    try: requests.get(url) 
    except: pass

# ៥. របារបញ្ជាឆ្លាតវៃ (GEMINI BAR) - ស្អាត ខ្លី មិនមានអក្សរច្រើន
c1, c2, c3, c4 = st.columns([1, 6, 1.2, 1.2], gap="small")
with c1:
    with st.popover("📎"): # ប៊ូតុងរូបកៀបឯកសារ សម្រាប់ដាក់រូបភាព
        រូបភាព = st.file_uploader("", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
with c3:
    # ប៊ូតុងមីក្រូហ្វូន ចុចដើម្បីនិយាយ រួចចុច 🛑 ដើម្បីបញ្ឈប់ វានឹងលោតចេញជាអក្សរ
    សំឡេង = speech_to_text(language='km-KH', start_prompt="🎙️", stop_prompt="🛑", use_container_width=True, key='STT')
with c2:
    អត្ថបទ_បច្ចុប្បន្ន = សំឡេង if សំឡេង else ""
    ប្រអប់អត្ថបទ = st.text_input("", value=អត្ថបទ_បច្ចុប្បន្ន, placeholder="សួរ AI ឬនិយាយ...", label_visibility="collapsed")
with c4:
    បញ្ជូន = st.button("⬆️", use_container_width=True)

if បញ្ជូន and (ប្រអប់អត្ថបទ or រូបភាព):
    with st.spinner("AI កំពុងគិត..."):
        try:
            សំណុំទិន្នន័យ = ["""ទាញយកទិន្នន័យអ្នកជំងឺចេញពីអត្ថបទឬរូបភាពនេះ ហើយសរសេរចេញជាទម្រង់ JSON សុទ្ធ: {"name": "ឈ្មោះ", "age": លេខ, "time": ម៉ោងណាត់(0=ព្រឹក, 1=ល្ងាច), "cancelled": ធ្លាប់លុប(0=ទេ, 1=ធ្លាប់)}"""]
            if ប្រអប់អត្ថបទ: សំណុំទិន្នន័យ.append(ប្រអប់អត្ថបទ)
            if រូបភាព: សំណុំទិន្នន័យ.append(Image.open(រូបភាព))
            
            ចម្លើយ = vision_model.generate_content(សំណុំទិន្នន័យ)
            ទិន្នន័យ = json.loads(ចម្លើយ.text.replace("```json", "").replace("```", "").strip())
            
            if "name" in ទិន្នន័យ: st.session_state.ស្កេន_ឈ្មោះ = ទិន្នន័យ["name"]
            if "age" in ទិន្នន័យ: st.session_state.ស្កេន_អាយុ = int(ទិន្នន័យ["age"])
            if "time" in ទិន្នន័យ: st.session_state.ស្កេន_ម៉ោង = int(ទិន្នន័យ["time"])
            if "cancelled" in ទិន្នន័យ: st.session_state.ស្កេន_លុប = int(ទិន្នន័យ["cancelled"])
        except:
            st.error("សូមទោស AI ចាប់ទិន្នន័យមិនបានច្បាស់ទេ។")

st.divider()

# ៦. ទម្រង់ Auto-fill (ខ្លីៗ ស្រឡះភ្នែក)
ឈ្មោះ = st.text_input("ឈ្មោះ", value=st.session_state.ស្កេន_ឈ្មោះ)
col1, col2 = st.columns(2)
with col1: អាយុ = st.number_input("អាយុ", min_value=1, max_value=100, value=st.session_state.ស្កេន_អាយុ)
with col2: ម៉ោងណាត់ = st.selectbox("ម៉ោងណាត់", [0, 1], index=st.session_state.ស្កេន_ម៉ោង, format_func=lambda x: "ព្រឹក ☀️" if x==0 else "ល្ងាច 🌙")
ធ្លាប់លុប = st.radio("ធ្លាប់លុបការណាត់?", [0, 1], index=st.session_state.ស្កេន_លុប, format_func=lambda x: "ទេ ❌" if x==0 else "ធ្លាប់ ✅", horizontal=True)

if st.button("💾 រក្សាទុកទិន្នន័យ", use_container_width=True):
    if ឈ្មោះ:
        ការព្យាករណ៍ = ai_model.predict([[អាយុ, ម៉ោងណាត់, ធ្លាប់លុប]])[0]
        សារ = f"⚠️ ព្រមាន៖ {ឈ្មោះ} អាចមិនមក!" if ការព្យាករណ៍==1 else f"✅ {ឈ្មោះ} នឹងមក។"
        st.error(សារ) if ការព្យាករណ៍==1 else st.success(សារ)
        send_telegram(សារ)
        worksheet.append_row([ឈ្មោះ, អាយុ, ម៉ោងណាត់, ធ្លាប់លុប, int(ការព្យាករណ៍)])
        st.info("រក្សាទុករួចរាល់!")
    else:
        st.warning("សូមបញ្ចូលឈ្មោះ!")

st.divider()
# ៧. បង្ហាញបញ្ជីអ្នកជំងឺខាងក្រោម
st.dataframe(df_ទិន្នន័យចាស់, use_container_width=True)