import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import requests
import streamlit as st
import gspread
from streamlit_autorefresh import st_autorefresh

# ១. កំណត់ទម្រង់វេបសាយ
st.set_page_config(page_title="AI ពេទ្យធ្មេញ", page_icon="🦷", layout="centered")

# ២. កូដ CSS រចនាទម្លាក់ Auto refresh ឱ្យមកក្រោមបន្តិច និងស្អាត
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Kantumruy Pro', sans-serif !important; }
    .stApp { background-color: #f8fafc; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 750px; }
    
    .auto-refresh-container {
        display: flex;
        justify-content: flex-end;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    
    div[data-testid="stToggle"] label p { font-size: 0px; }
    div[data-testid="stToggle"] label p::before { content: "🔄 Auto refresh"; font-size: 14px; margin-right: 5px; color: #64748b; font-weight: 500;}
    
    div.stButton > button {
        border-radius: 12px !important; font-weight: bold !important; height: 48px !important;
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important; color: white !important; border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ៣. ចំណងជើងវេបសាយ
st.markdown("<h2 style='text-align: center; color: #0f172a; margin-top: 0px; margin-bottom: 0px;'>🏥 AI ពេទ្យធ្មេញ</h2>", unsafe_allow_html=True)

# ៤. ប៊ូតុង Auto refresh
col_space, col_toggle = st.columns([6, 3])
with col_toggle:
    is_auto_refresh = st.toggle("Auto refresh", value=True, key="auto_ref")

if is_auto_refresh: 
    st_autorefresh(interval=10000, key="ar")

# ៥. ភ្ជាប់ទៅ Google Sheets (Cloud)
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

# ៦. បែងចែកជា Tab ពីរ
tab1, tab2 = st.tabs(["✨ បញ្ចូលទិន្នន័យ", "📊 បញ្ជីសង្ខេបតាមឈ្មោះ"])

with tab1:
    st.markdown("📝 **បញ្ចូលព័ត៌មានអ្នកជំងឺ**")
    
    # មុខងារស្វែងរកប្រវត្តិឈ្មោះស្វ័យប្រវត្តិ
    input_name = st.text_input("ឈ្មោះ", placeholder="ឧ. សុខា...")
    
    # កំណត់តម្លៃលំនាំដើម
    default_age = 25
    default_time = 0
    default_cancelled = 0
    
    # ពិនិត្យមើលក្នុង Database ថាតើឈ្មោះនេះធ្លាប់មានប្រវត្តិឬទេ
    if input_name and not df_ទិន្នន័យចាស់.empty:
        matched_rows = df_ទិន្នន័យចាស់[df_ទិន្នន័យចាស់['ឈ្មោះ'].str.strip().str.lower() == input_name.strip().lower()]
        if not matched_rows.empty:
            # ចាប់យក អាយុ ម៉ោងណាត់ និងប្រវត្តិលុបចុងក្រោយរបស់គាត់មកបំពេញ Auto
            default_age = int(matched_rows.iloc[-1]['អាយុ'])
            default_time = int(matched_rows.iloc[-1]['ម៉ោងណាត់'])
            if (matched_rows['ធ្លាប់លុបចោលការណាត់ពីមុន'] == 1).any():
                default_cancelled = 1
            
            st.info(f"💡 រកឃើញប្រវត្តិ៖ ប្រព័ន្ធបានទាញយក **អាយុ ({default_age})**, **ម៉ោងណាត់** និង **ប្រវត្តិខកខាន** របស់ '{input_name}' មកបំពេញជូនស្វ័យប្រវត្តិ!", icon="ℹ️")

    col1, col2 = st.columns(2)
    with col1: 
        អាយុ = st.number_input("អាយុ", min_value=1, max_value=100, value=default_age)
    with col2: 
        ម៉ោងណាត់ = st.selectbox("ម៉ោងណាត់", [0, 1], index=default_time, format_func=lambda x: "ព្រឹក ☀️" if x==0 else "ល្ងាច 🌙")
    
    ធ្លាប់លុប = st.radio("ធ្លាប់លុបការណាត់?", [0, 1], index=default_cancelled, format_func=lambda x: "ទេ ❌" if x==0 else "ធ្លាប់ ✅", horizontal=True)

    if st.button("💾 រក្សាទុកចូល Cloud", use_container_width=True):
        if input_name:
            if ai_model is not None:
                ការព្យាករណ៍ = ai_model.predict([[អាយុ, ម៉ោងណាត់, ធ្លាប់លុប]])[0]
            else:
                ការព្យាករណ៍ = 0
            
            សារ = f"⚠️ ព្រមាន៖ {input_name} អាចមិនមកតាមการណាត់!" if ការព្យាករណ៍==1 else f"✅ ធម្មតា៖ {input_name} នឹងមកតាមការណាត់。"
            st.error(សារ) if ការព្យាករណ៍==1 else st.success(សារ)
            send_telegram(សារ)
            worksheet.append_row([input_name, អាយុ, ម៉ោងណាត់, ធ្លាប់លុប, int(ការព្យាករណ៍)])
            st.info("រក្សាទុករួចរាល់!")
        else:
            st.warning("សូមបញ្ចូលឈ្មោះអ្នកជំងឺ!")

# ៧. ផ្ទាំងសង្ខេបតារាងតាមឈ្មោះ ព្រមទាំងប្រអប់ស្វែងរក (Filter) នៅ Tab 2
with tab2:
    st.markdown("📊 **តារាងសង្ខេបចំនួនដងមកព្យាបាលរបស់អតិថិជនម្នាក់ៗ**")
    if not df_ទិន្នន័យចាស់.empty and 'ឈ្មោះ' in df_ទិន្នន័យចាស់.columns:
        search_query = st.text_input("🔍 ស្វែងរកតាមឈ្មោះអ្នកជំងឺ", placeholder="វាយឈ្មោះទីនេះเพื่อ filter...", label_visibility="collapsed")
        
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