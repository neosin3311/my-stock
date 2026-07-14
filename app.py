import streamlit as st
import requests
import json
import os
import time

# 1. 웹페이지 레이아웃 및 콤팩트 디자인 설정
st.set_page_config(page_title="미니 전광판", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f9fafb; }
    
    /* 상단 잘림 해결 및 모바일/미니 창 반응형 가로 폭 제어 */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    div[data-testid="stMainBlockContainer"] {
        padding-top: 0px !important;
        margin-top: 0px !important;
    }
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 0.5rem !important; 
        max-width: 340px !important; /* 창이 커져도 위젯 형태의 아담한 너비(340px)로 유지 */
        padding-left: 10px !important;
        padding-right: 10px !important;
        margin: 0 auto !important;
    }
    
    /* 🚨 [정렬 완전 고정] 카드와 체크박스가 무슨 일이 있어도 가로로 붙어있도록 유동 레이아웃 설계 */
    .compact-stock-row {
        display: flex;
        align-items: center;
        width: 100%;
        margin-bottom: 6px;
        background-color: white;
        border: 1px solid #e5e8eb;
        border-radius: 6px;
        padding: 6px 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.01);
        box-sizing: border-box;
        gap: 8px;
    }
    
    .stock-click-area {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-grow: 1;
        min-width: 0;
        text-decoration: none !important;
        color: inherit !important;
    }
    
    .stock-info {
        display: flex;
        align-items: center;
        gap: 5px;
        min-width: 0;
    }
    .stock-name {
        font-size: 12px;
        font-weight: bold;
        color: #333d4b;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .stock-code {
        font-size: 9px;
        color: #8b95a1;
        white-space: nowrap;
    }
    .stock-values {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: bold;
        white-space: nowrap;
    }
    
    /* 🚨 체크박스가 카드 내부 오른쪽 끝에 강제로 끼어있게 고정 */
    .custom-checkbox-container {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        flex-shrink: 0; /* 창이 좁아져도 체크박스 영역이 절대로 뭉개지지 않음 */
    }
    
    /* 1초 주기 동시 깜빡임 CSS */
    @keyframes heartbeatUp {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #ffebed; border-color: #f04452; }
    }
    @keyframes heartbeatDown {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #e8f3ff; border-color: #3182f6; }
    }
    .blink-up { animation: heartbeatUp 1.0s infinite ease-in-out !important; }
    .blink-down { animation: heartbeatDown 1.0s infinite ease-in-out !important; }
    
    /* 좌측 사이드바 메뉴 콤팩트 다이어트 */
    section[data-testid="stSidebar"] {
        width: 20% !important;
        min-width: 210px !important;
    }
    div[data-testid="stSidebarUserContent"] {
        padding-top: 0.5rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        gap: 0.1rem !important;
    }
    div[data-testid="stNumberInput"], div[data-testid="stTextInput"] {
        margin-bottom: 2px !important;
    }
    div[data-testid="stNumberInput"] > label, div[data-testid="stTextInput"] > label {
        margin-bottom: 1px !important;
        font-size: 11px !important;
    }
    .stTextInput input, .stNumberInput input {
        padding: 4px 8px !important;
        height: 28px !important;
        font-size: 12px !important;
    }
    section[data-testid="stSidebar"] h3 {
        font-size: 14px !important;
        margin-top: 5px !important;
        margin-bottom: 5px !important;
    }
    .stButton button {
        padding: 2px 10px !important;
        height: 28px !important;
        font-size: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

SAVE_FILE = "my_stocks_web.json"

def load_stocks():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {
        "삼성전자": {"code": "005930", "checked": True, "alert_active": True},
        "SK하이닉스": {"code": "000660", "checked": True, "alert_active": True},
        "현대차": {"code": "005380", "checked": True, "alert_active": False},
        "카카오": {"code": "035720", "checked": True, "alert_active": False},
        "_alert_limit": 3.0
    }

def save_stocks(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "my_stocks" not in st.session_state:
    st.session_state.my_stocks = load_stocks()

# ----------------- 좌측: 설정 사이드바 -----------------
st.sidebar.markdown("### ⭐ 관심 종목")

c1, c2 = st.sidebar.columns(2)
new_name = c1.text_input("종목명", placeholder="삼성전자", key="in_name")
new_code = c2.text_input("코드", placeholder="005930", key="in_code")

if st.sidebar.button("종목 추가", use_container_width=True):
    if new_name and len(new_code) == 6 and new_code.isdigit():
        st.session_state.my_stocks[new_name] = {"code": new_code, "checked": True, "alert_active": True}
        save_stocks(st.session_state.my_stocks)
        st.rerun()

st.sidebar.markdown("<div style='margin: 2px 0; border-bottom: 1px solid #e5e8eb;'></div>", unsafe_allow_html=True)

alert_limit = st.sidebar.number_input("알림 기준 (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.my_stocks.get("_alert_limit", 3.0)), step=0.1)
st.session_state.my_stocks["_alert_limit"] = alert_limit

st.sidebar.markdown("### 📊 표시 선택")
for name in list(st.session_state.my_stocks.keys()):
    if name.startswith("_"): continue
    col1, col2 = st.sidebar.columns([4, 1])
    is_checked = col1.checkbox(name, value=st.session_state.my_stocks[name]["checked"], key=f"chk_{st.session_state.my_stocks[name]['code']}")
    st.session_state.my_stocks[name]["checked"] = is_checked
    if col2.button("×", key=f"del_{st.session_state.my_stocks[name]['code']}", use_container_width=True):
        del st.session_state.my_stocks[name]
        save_stocks(st.session_state.my_stocks)
        st.rerun()

if st.sidebar.button("💾 설정 저장", use_container_width=True):
    save_stocks(st.session_state.my_stocks)
    st.sidebar.success("저장 완료")

# ----------------- 우측: 실시간 미니 전광판 메인 영역 -----------------
st.markdown("### 📊 실시간 주가")

def get_stock_data(code):
    url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        if res.status_code == 200:
            item = res.json()['result']['areas'][0]['datas'][0]
            return {
                "price": int(item['nv']), 
                "cv": int(item['cv']), 
                "cr": float(item['cr']), 
                "rf": int(item['rf'])
            }
    except: return None

placeholder = st.empty()

while True:
    with placeholder.container():
        for name, info in st.session_state.my_stocks.items():
            if name.startswith("_") or not info["checked"]: continue
            
            data = get_stock_data(info["code"])
            if not data: continue
            
            price = data["price"]
            cv = data["cv"]
            cr = data["cr"]
            rf = data["rf"]
            
            is_up = rf in [1, 2]
            is_down = rf in [4, 5]
            
            # 깜빡이 타겟 스타일 지정
            alert_class = ""
            if is_up:
                status_txt = f"+{cr:.2f}%"
                color = "#f04452"
                if info["alert_active"] and cr >= alert_limit:
                    alert_class = "blink-up"
            elif is_down:
                status_txt = f"-{abs(cr):.2f}%"
                color = "#3182f6"
                if info["alert_active"] and abs(cr) >= alert_limit:
                    alert_class = "blink-down"
            else:
                status_txt = f"{cr:.2f}%"
                color = "#4e5968"

            toss_url = f"https://www.tossinvest.com/?focusedProductCode=A{info['code']}"

            # 🛠️ [정렬 버그 완벽 패치] 단일 HTML 틀 안에서 카드 내용과 체크박스를 양방향 가로 정렬합니다.
            st.markdown(f"""
                <div class="compact-stock-row {alert_class}">
                    <a href="{toss_url}" target="_blank" class="stock-click-area">
                        <div class="stock-info">
                            <span class="stock-name">{name}</span>
                            <span class="stock-code">{info['code']}</span>
                        </div>
                        <div class="stock-values" style="color: {color};">
                            <span>{price:,}원</span>
                            <span>{status_txt}</span>
                        </div>
                    </a>
                    <div class="custom-checkbox-container">
            """, unsafe_allow_html=True)
            
            # 스트림릿 고유 체크박스가 안전하게 튕김 없이 결합됩니다.
            info["alert_active"] = st.checkbox("", value=info["alert_active"], key=f"alert_{info['code']}", label_visibility="collapsed")
            
            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        time.sleep(4)
        st.rerun()
