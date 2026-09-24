import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import requests
import streamlit as st
import gspread
from streamlit_autorefresh import st_autorefresh

# ១. កំណត់ទម្រង់វេបសាយ 
st.set_page_config(page_title="AI ពេទ្យធ្មេញ", page_icon="🦷", layout="centered")

# ២. កូដរចនា CSS ដើម្បីទាញវេបសាយឱ្យខិតទៅលើកប់ និងបង្រួមចន្លោះ
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Kantumruy Pro', sans-serif !important; }
    .stApp { background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); }
    
    /* នេះគឺជាកូដទាញវេបសាយឱ្យខិតឡើងលើ (លុបចន្លោះទទេរ) */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 2rem 2.5rem !important;
        border-radius: 20px; 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    /* លាក់របារពណ៌សរបស់ Streamlit ខាងលើគេបន្តិចដើម្បីចំណេញកន្លែង */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    .stTabs [data-baseweb="tab-list"] { background-color: #f1f5f9; padding: 5px; border-radius: 12px; gap: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px !important; padding: 5px 20px !important; background-color: transparent; }
    .stTabs [aria-selected="true"] { background-color: #ffffff !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important; color: #0284c7 !important; font-weight: 600 !important; }
    
    div.stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        color: white !important; border: none !important; border-radius: 12px !important;
        height: 50px !important; font-size: 18px !important; font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3) !important; transition: all 0.3s ease !important;
        margin-top: 5px !important;
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4) !important; }
    </style>
""", unsafe_allow_html=True)

# ៣. ផ្ទៃវេបសាយ (UI) - រៀបចំណងជើងមុនគេ
st.markdown("<h1 style='color: #0c4a6e; text-align: center; font-size: 30px; margin-bottom: 0px;'>🏥 ប្រព័ន្ធ AI ពេទ្យធ្មេញ</h1>", unsafe_allow_html=True)

# ៤. កុងតាក់ Auto Refresh ដាក់នៅកណ្តាលរាងតូចស្អាតចំណេញកន្លែង
col1, col2, col3 = st.columns([3, 2, 3])
with col2:
    is_auto_refresh = st.toggle("🔄 Auto refresh (10s)", value=True)

if is_auto_refresh:
    st_autorefresh(interval=10000, key="auto_refresh")

# ៥. ភ្ជាប់ទៅកាន់ Google Sheets (Cloud)
@st.cache_resource
def init_gsheets():
    credentials = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open("Dental_AI_Data")
    return sh.sheet1

worksheet = init_gsheets()

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
    bot_token = '8573963689:AAEX3OFDd4IKFqmMKUIOWlhKc8lHTg8v64M'  # <--- ដាក់ Token នៅទីនេះ
    chat_id = '8805554075'
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
    try: requests.get(url) 
    except: pass

def save_to_gsheets(ឈ្មោះ, អាយុ, ម៉ោងណាត់, ធ្លាប់លុប, លទ្ធផលជាក់ស្តែង):
    try:
        worksheet.append_row([ឈ្មោះ, អាយុ, ម៉ោងណាត់, ធ្លាប់លុប, លទ្ធផលជាក់ស្តែង])
        return True, "ជោគជ័យ"
    except Exception as e: return False, str(e)

tab1, tab2 = st.tabs(["📝 បញ្ចូលទិន្នន័យថ្មី", "📊 បញ្ជីអ្នកជំងឺ (Cloud)"])

with tab1:
    # ខ្ញុំបានលុបការចុះបន្ទាត់ (<br>) ចោលទាំងអស់ដើម្បីឱ្យវារួញចូលគ្នា
    ឈ្មោះ = st.text_input("ឈ្មោះអ្នកជំងឺ", placeholder="ឧ. សុខា...")
    col1, col2 = st.columns(2)
    with col1: អាយុ = st.number_input("អាយុ", min_value=1, max_value=100, value=25)
    with col2: ម៉ោងណាត់ = st.selectbox("ម៉ោងណាត់ជួប", options=[0, 1], format_func=lambda x: "ព្រឹក ☀️" if x==0 else "ល្ងាច 🌙")
    ធ្លាប់លុប = st.radio("តើធ្លាប់លុបចោលការណាត់ពីមុនទេ?", options=[0, 1], format_func=lambda x: "ទេ ❌" if x==0 else "ធ្លាប់ ✅", horizontal=True)
    
    if st.button("✨ វិភាគ និងផ្ញើលទ្ធផល", use_container_width=True):
        if ឈ្មោះ == "": st.warning("⚠️ សូមបញ្ចូលឈ្មោះអ្នកជំងឺជាមុនសិន!")
        else:
            with st.spinner('🤖 កំពុងវិភាគ និងទាក់ទងទៅ Google Sheets...'):
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
                if តើជោគជ័យទេ: st.info("រក្សាទុកចូល Google Sheets ស្វ័យប្រវត្តិជោគជ័យ!", icon="☁️")
                else: st.error(f"បរាជ័យក្នុងការរក្សាទុក! មូលហេតុ៖ {បញ្ហា}", icon="❌")

with tab2:
    st.metric(label="ចំនួនអ្នកជំងឺសរុប (នាក់)", value=f"{len(df_ទិន្នន័យចាស់)}")
    st.dataframe(df_ទិន្នន័យចាស់, use_container_width=True)