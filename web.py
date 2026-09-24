import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import requests
import streamlit as st
import gspread
from streamlit_autorefresh import st_autorefresh
import google.generativeai as genai
from PIL import Image
import json

# ១. កំណត់ទម្រង់វេបសាយ 
st.set_page_config(page_title="AI ពេទ្យធ្មេញ", page_icon="🦷", layout="centered")

# ២. បង្កើតអង្គចងចាំ (Session State) សម្រាប់ផ្ទុកទិន្នន័យដែល AI ស្កេនបាន
if 'ស្កេន_ឈ្មោះ' not in st.session_state: st.session_state.ស្កេន_ឈ្មោះ = ""
if 'ស្កេន_អាយុ' not in st.session_state: st.session_state.ស្កេន_អាយុ = 25
if 'ស្កេន_ម៉ោង' not in st.session_state: st.session_state.ស្កេន_ម៉ោង = 0
if 'ស្កេន_លុប' not in st.session_state: st.session_state.ស្កេន_លុប = 0

# ៣. កូដរចនា CSS កម្រិតខ្ពស់
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Kantumruy Pro', sans-serif !important; }
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
    .main .block-container {
        background-color: #ffffff; padding: 2rem 2.5rem !important;
        border-radius: 20px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0;
    }
    header[data-testid="stHeader"] { background: transparent !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #f1f5f9; padding: 5px; border-radius: 12px; gap: 10px; border: none; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px !important; padding: 8px 20px !important; background-color: transparent; }
    .stTabs [aria-selected="true"] { background-color: #ffffff !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important; color: #0284c7 !important; font-weight: 600 !important; }
    
    /* រចនាប្រអប់ Smart AI */
    .ai-box { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 20px; border-radius: 15px; border: 1px dashed #7dd3fc; margin-bottom: 20px; }
    
    div.stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important; color: white !important; border: none !important; border-radius: 12px !important;
        height: 50px !important; font-size: 16px !important; font-weight: 600 !important; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.2) !important; transition: all 0.3s ease !important; margin-top: 5px !important;
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3) !important; }
    
    /* លាក់អក្សរ (10s) របស់ Toggle */
    div[data-testid="stToggle"] label p { font-size: 0px; }
    div[data-testid="stToggle"] label p::before { content: "🔄 Auto refresh"; font-size: 16px; margin-right: 5px;}
    div[data-testid="stToggle"] label p::after { content: " (10)"; animation: countdown 10s step-end infinite; color: #10b981; font-weight: bold; font-size: 16px; }
    @keyframes countdown { 0%{content:" (10)";} 10%{content:" (9)";} 20%{content:" (8)";} 30%{content:" (7)";} 40%{content:" (6)";} 50%{content:" (5)";} 60%{content:" (4)";} 70%{content:" (3)";} 80%{content:" (2)";} 90%{content:" (1)";} 100%{content:" (0)";} }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: #0c4a6e; text-align: center; font-size: 30px; margin-bottom: 0px;'>🏥 ប្រព័ន្ធ AI ពេទ្យធ្មេញ</h1>", unsafe_allow_html=True)

col_t1, col_t2 = st.columns([7, 3])
with col_t2: is_auto_refresh = st.toggle("Auto refresh", value=True, key="is_auto_refresh")
if is_auto_refresh: st_autorefresh(interval=10000, key="auto_refresh")

# ៤. ភ្ជាប់ទៅកាន់ Google Sheets & Gemini
@st.cache_resource
def init_services():
    credentials = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open("Dental_AI_Data")
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return sh.sheet1, genai.GenerativeModel('gemini-1.5-flash')

worksheet, vision_model = init_services()

def train_ai():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    X = df[['អាយុ', 'ម៉ោងណាត់', 'ធ្លាប់លុបចោលការណាត់ពីមុន']]
    y = df['លទ្ធផលជាក់ស្តែង']
    model = RandomForestClassifier()
    model.fit(X.values, y.values)
    return model, df

ai_model, df_ទិន្នន័យចាស់ = train_ai()

def send_telegram_message(message):
    bot_token = '8573963689:AAEX3OFDd4IKFqmMKUIOWlhKc8lHTg8v64M'  # <--- កុំភ្លេចដាក់ Token
    chat_id = '8805554075'
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
    try: requests.get(url) 
    except: pass

def save_to_gsheets(ឈ្មោះ, អាយុ, ម៉ោងណាត់, ធ្លាប់លុប, លទ្ធផលជាក់ស្តែង):
    try:
        worksheet.append_row([ឈ្មោះ, អាយុ, ម៉ោងណាត់, ធ្លាប់លុប, លទ្ធផលជាក់ស្តែង])
        return True, ""
    except Exception as e: return False, str(e)

tab1, tab2 = st.tabs(["✨ ប្រអប់បញ្ជា AI", "📊 បញ្ជីអ្នកជំងឺ (Cloud)"])

with tab1:
    # --- ផ្នែកប្រអប់បញ្ជា AI ដ៏ឆ្លាតវៃ (Smart Prompt Box) ---
    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.markdown("**🤖 ប្រាប់ AI ឱ្យបំពេញទិន្នន័យជំនួសអ្នក**")
    
    ប្រអប់អត្ថបទ = st.text_area("សរសេរ ឬបញ្ចេញសំឡេង (Voice) នៅទីនេះ 💬", placeholder="ឧ. កត់ឈ្មោះ កញ្ញា សុខា អាយុ ២៥ ឆ្នាំ ណាត់ពេលព្រឹក គាត់ធ្លាប់លុបការណាត់ពីមុន...", height=80)
    រូបភាព = st.file_uploader("ឬ បញ្ចូលរូបភាពឯកសារ 🖼️", type=["jpg", "png", "jpeg"])
    
    if st.button("✨ បញ្ជូនទៅកាន់ AI ឱ្យបំពេញទិន្នន័យ", use_container_width=True):
        if ប្រអប់អត្ថបទ == "" and រូបភាព is None:
            st.warning("⚠️ សូមបញ្ចូលអត្ថបទ ឬរូបភាពជាមុនសិន!")
        else:
            with st.spinner("🧠 AI កំពុងគិត និងទាញយកទិន្នន័យ..."):
                try:
                    # បញ្ជាឱ្យ AI ទាញទិន្នន័យចេញមកជាទម្រង់គំរូ JSON ជាក់លាក់
                    ការណែនាំ = """
                    អ្នកគឺជាជំនួយការពេទ្យធ្មេញដ៏ឆ្លាតវៃ។ សូមទាញយកទិន្នន័យពីអត្ថបទ ឬរូបភាពនេះ រួចឆ្លើយតបជាទម្រង់ JSON សុទ្ធ ដោយគ្មានអក្សរផ្សេងបន្ថែម។
                    ទម្រង់ដែលចង់បានគឺ {"name": "ឈ្មោះ", "age": លេខ, "time": លេខម៉ោង, "cancelled": លេខធ្លាប់លុប}
                    - name: ឈ្មោះអ្នកជំងឺ (ជាភាសាខ្មែរ)
                    - age: អាយុ (ជាលេខ)
                    - time: បើពេលព្រឹក ដាក់ 0, បើពេលល្ងាច/រសៀល ដាក់ 1
                    - cancelled: បើធ្លាប់លុបការណាត់ ដាក់ 1, បើមិនធ្លាប់ ឬមិនមានបញ្ជាក់ ដាក់ 0
                    """
                    សំណុំទិន្នន័យ = [ការណែនាំ]
                    if ប្រអប់អត្ថបទ != "": សំណុំទិន្នន័យ.append(ប្រអប់អត្ថបទ)
                    if រូបភាព is not None: សំណុំទិន្នន័យ.append(Image.open(រូបភាព))
                    
                    ចម្លើយ = vision_model.generate_content(សំណុំទិន្នន័យ)
                    
                    # បំប្លែងចម្លើយរបស់ AI ទៅជាទិន្នន័យ
                    អត្ថបទ_json = ចម្លើយ.text.replace("```json", "").replace("```", "").strip()
                    ទិន្នន័យ = json.loads(អត្ថបទ_json)
                    
                    if "name" in ទិន្នន័យ: st.session_state.ស្កេន_ឈ្មោះ = ទិន្នន័យ["name"]
                    if "age" in ទិន្នន័យ and str(ទិន្នន័យ["age"]).isdigit(): st.session_state.ស្កេន_អាយុ = int(ទិន្នន័យ["age"])
                    if "time" in ទិន្នន័យ and ទិន្នន័យ["time"] in [0, 1]: st.session_state.ស្កេន_ម៉ោង = ទិន្នន័យ["time"]
                    if "cancelled" in ទិន្នន័យ and ទិន្នន័យ["cancelled"] in [0, 1]: st.session_state.ស្កេន_លុប = ទិន្នន័យ["cancelled"]
                    
                    st.success("✅ AI បានទាញទិន្នន័យមកបំពេញក្នុងទម្រង់ខាងក្រោមរួចរាល់! សូមពិនិត្យមើល។")
                except Exception as e:
                    st.error("⚠️ AI មិនអាចចាប់យកទិន្នន័យបានច្បាស់ទេ។ សូមសាកល្បងវាយប្រាប់វាម្តងទៀត។")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider() # គូសបន្ទាត់ខណ្ឌ
    
    # --- ផ្នែកទម្រង់ (Form) ដែល AI នឹងបំពេញដោយស្វ័យប្រវត្តិ ---
    st.markdown("📝 **ពិនិត្យ និងបញ្ជូនទិន្នន័យចូល Google Sheets**")
    ឈ្មោះ = st.text_input("ឈ្មោះអ្នកជំងឺ", value=st.session_state.ស្កេន_ឈ្មោះ, placeholder="ឧ. សុខា...")
    col1, col2 = st.columns(2)
    with col1: អាយុ = st.number_input("អាយុ", min_value=1, max_value=100, value=st.session_state.ស្កេន_អាយុ)
    with col2: ម៉ោងណាត់ = st.selectbox("ម៉ោងណាត់ជួប", options=[0, 1], index=st.session_state.ស្កេន_ម៉ោង, format_func=lambda x: "ព្រឹក ☀️" if x==0 else "ល្ងាច 🌙")
    ធ្លាប់លុប = st.radio("តើធ្លាប់លុបចោលការណាត់ពីមុនទេ?", options=[0, 1], index=st.session_state.ស្កេន_លុប, format_func=lambda x: "ទេ ❌" if x==0 else "ធ្លាប់ ✅", horizontal=True)
    
    if st.button("💾 វិភាគ និងរក្សាទុកទិន្នន័យ", use_container_width=True):
        if ឈ្មោះ == "": st.warning("⚠️ សូមបញ្ចូលឈ្មោះអ្នកជំងឺជាមុនសិន!")
        else:
            with st.spinner('កំពុងរក្សាទុក...'):
                ការព្យាករណ៍ = ai_model.predict([[អាយុ, ម៉ោងណាត់, ធ្លាប់លុប]])
                លទ្ធផល_ai = int(ការព្យាករណ៍[0]) 
                
                if លទ្ធផល_ai == 1:
                    សារ = f"⚠️ សញ្ញាព្រមាន៖ អ្នកជំងឺឈ្មោះ {ឈ្មោះ} អាចនឹងមិនមកតាមការណាត់ទេ!"
                    st.error(សារ, icon="🚨")
                else:
                    សារ = f"✅ ធម្មតា៖ អ្នកជំងឺឈ្មោះ {ឈ្មោះ} ទំនងជានឹងមកតាមការណាត់។"
                    st.success(សារ, icon="✅")
                    
                send_telegram_message(សារ)
                តើជោគជ័យទេ, បញ្ហា = save_to_gsheets(ឈ្មោះ, អាយុ, ម៉ោងណាត់, ធ្លាប់លុប, លទ្ធផល_ai)
                if តើជោគជ័យទេ: 
                    st.info("រក្សាទុកចូល Cloud ស្វ័យប្រវត្តិជោគជ័យ!", icon="☁️")
                    st.session_state.ស្កេន_ឈ្មោះ = "" 
                    st.session_state.ស្កេន_អាយុ = 25
                    st.session_state.ស្កេន_ម៉ោង = 0
                    st.session_state.ស្កេន_លុប = 0
                else: st.error(f"បរាជ័យក្នុងការរក្សាទុក! មូលហេតុ៖ {បញ្ហា}", icon="❌")

with tab2:
    st.metric(label="ចំនួនអ្នកជំងឺសរុប (នាក់)", value=f"{len(df_ទិន្នន័យចាស់)}")
    st.dataframe(df_ទិន្នន័យចាស់, use_container_width=True)