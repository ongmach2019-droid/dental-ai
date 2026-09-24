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

# ៤. ភ្ជាប់ទៅ Google Sheets & Gemini (កំណត់តួនាទីឱ្យ AI ស្គាល់ច្បាស់)
@st.cache_resource
def init_services():
    credentials = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open("Dental_AI_Data")
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # បង្រៀន AI ឱ្យស្គាល់តួនាទី និងទម្រង់ទិន្នន័យជាក់លាក់
    system_prompt = """
    អ្នកគឺជា AI ជំនួយការគ្លីនិកពេទ្យធ្មេញដ៏ជំនាញ។ 
    หน้าที่របស់អ្នកគឺអានអត្ថបទ ឬរូបភាពដែលអ្នកប្រើប្រាស់បញ្ជូនមក (មិនថានៅក្នុងរូបភាពជាភាសាខ្មែរ ឬអង់គ្លេស) 
    ហើយទាញយកតម្លៃមកបំពេញក្នុងទម្រង់ JSON ឱ្យបានត្រឹមត្រូវបំផុត៖
    - "name": ឈ្មោះអ្នកជំងឺ (ត្រូវរក្សាទុកជាអក្សរខ្មែរ ឬឡាតាំងតាមប្រភព)
    - "age": អាយុ (ទាញយកជាខ្នាតលេខគត់ ឧ. 25)
    - "time": ម៉ោងណាត់ជួប (បើក្នុងប្រភពបញ្ជាក់ថា ព្រឹក/Morning/AM គឺកំណត់តម្លៃ 0; បើ ល្ងាច/រសៀល/Evening/PM គឺកំណត់តម្លៃ 1)
    - "cancelled": ធ្លាប់លុបការណាត់ពីមុនទេ (បើធ្លាប់/ເຄີຍលុប គឺកំណត់តម្លៃ 1; បើមិនធ្លាប់ ឬគ្មានបញ្ជាក់ គឺកំណត់តម្លៃ 0)
    
    សូមឆ្លើយតបមកវិញជា JSON សុទ្ធសាធ (Valid JSON) ដោយគ្មានអក្សរអធិប្បាយផ្សេងទៀតឡើយ។
    """
    
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=system_prompt
    )
    return sh.sheet1, model
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