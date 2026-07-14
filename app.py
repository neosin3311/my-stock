import streamlit as st
import requests
import json
import os
import time

# 1. 웹페이지 레이아웃 설정
st.set_page_config(page_title="미니 전광판", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f9fafb; }
    
    /* 🚨 [수정 핵심] 헤더 바의 배경과 높이만 지우고, 사이드바 열기 화살표(>)는 정상 노출되도록 패치 */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0px !important;
    }
    /* 사이드바 열기 버튼을 화면 상단 왼쪽 구석에 배치 */
    button[data-testid="collapsedSidebarCollapsedUIButton"] {
        top: 8px !important;
        left: 8px !important;
        background-color: white !important;
        border: 1px solid #e5e8eb !important;
        border-radius: 4px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        z-index: 999999 !important;
    }
    
    div[data-testid="stMainBlockContainer"] {
        padding-top: 0px !important;
        margin-top: 0px !important;
    }
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 0.5rem !important; 
        max-width: 280px !important; /* 주식 항목 가로 길이 제한 */
        margin: 0 auto !important;   /* 화면 중앙 정렬 */
        padding-left: 5px !important;
        padding-right: 5px !important;
    }
    
    /* [체크박스 맨 앞으로 고정] 한 줄 유지 레이아웃 */
    .stock-row-fixed {
        display: flex;
        align-items: center;
        width: 100%;
        margin-bottom: 5px;
        gap: 6px;
    }
    .front-checkbox-container {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        flex-shrink: 0;
    }
    
    /* 주가 카드 스타일 */
    .stock-link {
        text-decoration: none !important;
        color: inherit !important;
        flex-grow: 1;
        min-width: 0;
    }
    .stock-card {
        background-color: white;
        border: 1px solid #e5e8eb;
        border-radius: 6px;
        padding: 5px 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.01);
        width: 100%;
        box-sizing: border-box;
    }
    .stock-info {
        display: flex;
        align-items: center;
        gap: 4px;
        min-width: 0;
    }
    .stock-name {
        font-size: 11px;
        font-weight: bold;
        color: #333d4b;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .stock-code {
        font-size: 8px;
        color: #8b95a1;
        white-space: nowrap;
    }
    .stock-values {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 11px;
        font-weight: bold;
        white-space: nowrap;
    }
    
    /* 1초 주기 동시 깜빡임 */
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
    
    /* 좌측 사이드바 메뉴 압축 */
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
    div[data-testid="stNumberInput"], div[data-testid="stTextInput"] { margin-bottom: 2px !important; }
    .stTextInput input, .stNumberInput input { padding: 4px 8px !important; height: 28px !important; font-size: 12px !important; }
    div[data-testid="stCheckbox"] { margin: 0px !important; padding: 0px !important; }
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
st.markdown("<h4 style='font-size: 13px; margin: 0 0 6px 0; color: #333d4b;'>📊 실시간 주가</h4>", unsafe_allow_html=True)

def get_stock_data(code):
    url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        if res.status_code == 200:
            item = res.json()['result']['areas'][0]['datas'][0]
            return {"price": int(item['nv']), "cv": int(item['cv']), "cr": float(item['cr']), "rf": int(item['rf'])}
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
            
            alert_class = ""
            if is_up:
                status_txt = f"+{cr:.2f}%"
                color = "#f04452"
                if info["alert_active"] and cr >= alert_limit: alert_class = "blink-up"
            elif is_down:
                status_txt = f"-{abs(cr):.2f}%"
                color = "#3182f6"
                if info["alert_active"] and abs(cr) >= alert_limit: alert_class = "blink-down"
            else:
                status_txt = f"{cr:.2f}%"
                color = "#4e5968"

            toss_url = f"https://www.tossinvest.com/?focusedProductCode=A{info['code']}"

            st.markdown(f"""
                <div class="stock-row-container">
                    <div class="stock-row-fixed">
                        <div class="front-checkbox-container">
            """, unsafe_allow_html=True)
            
            info["alert_active"] = st.checkbox("", value=info["alert_active"], key=f"alert_{info['code']}", label_visibility="collapsed")
            
            st.markdown(f"""
                        </div>
                        <a href="{toss_url}" target="_blank" class="stock-link">
                            <div class="stock-card {alert_class}">
                                <div class="stock-info">
                                    <span class="stock-name">{name}</span>
                                    <span class="stock-code">{info['code']}</span>
                                </div>
                                <div class="stock-values" style="color: {color};">
                                    <span>{price:,}원</span>
                                    <span>{status_txt}</span>
                                </div>
                            </div>
                        </a>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        time.sleep(4)
        st.rerun()
