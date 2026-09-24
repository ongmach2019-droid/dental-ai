import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import requests
import streamlit as st
import gspread
from streamlit_autorefresh import st_autorefresh

# ១. កំណត់ទម្រង់វេបសាយ
st.set_page_config(page_title="AI ពេទ្យធ្មេញ", page_icon="🦷", layout="centered")

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

st.markdown("<h2 style='text-align: center; color: #0f172a; margin-top: -20px; margin-bottom: 15px;'>🏥 AI ពេទ្យធ្មេញ</h2>", unsafe_allow_html=True)

# ៤. ភ្ជាប់ទៅ Google Sheets (Cloud)
@st.cache_resource
def init_services():
    credentials = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open("Dental_AI_Data")
    return sh.sheet1

worksheet = init_services()

def train_ai():
    data = worksheet.get_all_records()
    if not data:
        return None, pd.DataFrame(columns=['ឈ្មោះ', 'អាយុ', 'ម៉ោងណាត់', 'ធ្លាប់លុបចោលការណាត់ពីមុន', 'លទ្ធផលជាក់ស្តែង'])
    df = pd.DataFrame(data)
    model = RandomForestClassifier()
    model.fit(df[['អាយុ', 'ម៉ោងណាត់', 'ធ្លាប់លុបចោលការណាត់ពីមុន']].values, df['លទ្ធផលជាក់ស្តែង'].values)
    return model, df

ai_model, df_ទិន្នន័យចាស់ = train_ai()

def send_telegram(message):
    bot_token = '8573963689:AAEX3OFDd4IKFqmMKUIOWlhKc8lHTg8v64M'  # <--- កុំភ្លេចដាក់ Token
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id=8805554075&text={message}"
    try: requests.get(url) 
    except: pass

# ៥. បែងចែកជា Tab ពីរ (លុបប្រអប់ AI ចោលទាំងស្រុង ប្រើទម្រង់ធម្មតាវិញ)
tab1, tab2 = st.tabs(["✨ បញ្ចូលទិន្នន័យ", "📊 បញ្ជីសង្ខេបតាមឈ្មោះ"])

with tab1:
    st.markdown("📝 **បញ្ចូលព័ត៌មានអ្នកជំងឺ**")
    ឈ្មោះ = st.text_input("ឈ្មោះ", placeholder="ឧ. សុខា...")
    col1, col2 = st.columns(2)
    with col1: អាយុ = st.number_input("អាយុ", min_value=1, max_value=100, value=25)
    with col2: ម៉ោងណាត់ = st.selectbox("ម៉ោងណាត់", [0, 1], format_func=lambda x: "ព្រឹក ☀️" if x==0 else "ល្ងាច 🌙")
    ធ្លាប់លុប = st.radio("ធ្លាប់លុបការណាត់?", [0, 1], format_func=lambda x: "ទេ ❌" if x==0 else "ធ្លាប់ ✅", horizontal=True)

    if st.button("💾 រក្សាទុកចូល Cloud", use_container_width=True):
        if ឈ្មោះ:
            if ai_model is not None:
                ការព្យាករណ៍ = ai_model.predict([[អាយុ, ម៉ោងណាត់, ធ្លាប់លុប]])[0]
            else:
                ការព្យាករណ៍ = 0
            
            សារ = f"⚠️ ព្រមាន៖ {ឈ្មោះ} អាចមិនមកតាមការណាត់!" if ការព្យាករណ៍==1 else f"✅ ធម្មតា៖ {ឈ្មោះ} នឹងមកតាមការណាត់。"
            st.error(សារ) if ការព្យាករណ៍==1 else st.success(សារ)
            send_telegram(សារ)
            worksheet.append_row([ឈ្មោះ, អាយុ, ម៉ោងណាត់, ធ្លាប់លុប, int(ការព្យាករណ៍)])
            st.info("រក្សាទុករួចរាល់!")
        else:
            st.warning("សូមបញ្ចូលឈ្មោះអ្នកជំងឺ!")

# ៦. ផ្ទាំងសង្ខេបតារាងតាមឈ្មោះ ព្រមទាំងប្រអប់ស្វែងរក (Filter) នៅ Tab 2
with tab2:
    st.markdown("📊 **តារាងសង្ខេបចំនួនដងមកព្យាបាលរបស់អតិថិជនម្នាក់ៗ**")
    if not df_ទិន្នន័យចាស់.empty and 'ឈ្មោះ' in df_ទិន្នន័យចាស់.columns:
        search_query = st.text_input("🔍 ស្វែងរកតាមឈ្មោះអ្នកជំងឺ", placeholder="វាយឈ្មោះទីនេះដើម្បី filter...", label_visibility="collapsed")
        
        df_grouped = df_ទិន្នន័យចាស់.groupby('ឈ្មោះ').agg(
            អាយុ=('អាយុ', 'first'),
            ចំនួនដងមកសរុប=('ឈ្មោះ', 'count'),
            ធ្លាប់លុបការណាត់ពីមុន=('ធ្លាប់លុបចោលការណាត់ពីមុន', 'sum'),
            លទ្ធផលជាក់ស្តែង=('លទ្ធផលជាក់ស្តែង', 'sum')
        ).reset_index()
        
        if search_query:
            df_grouped = df_grouped[df_grouped['ឈ្មោះ'].str.contains(search_query, case=False, na=False)]
        
        st.metric(label="ចំនួនអតិថិជនបង្ហាញសរុប (នាក់)", value=f"{len(df_grouped)}")
        st.dataframe(df_grouped, use_container_width=True)
    else:
        st.info("មិនទាន់មានទិន្នន័យនៅលើ Cloud ទេ។ សូមបញ្ចូលទិន្នន័យដំបូងនៅ Tab ទី ១ ជាមុនសិន។")