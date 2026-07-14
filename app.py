import streamlit as st
import requests
import json
import os
import time

# 1. 웹페이지 디자인 및 레이아웃 설정
st.set_page_config(page_title="미니 전광판", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f9fafb; }
    .stock-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        margin-bottom: 2px;
    }
    
    /* 콤팩트한 미니 카드 디자인 */
    .stock-card {
        background-color: white;
        border: 1px solid #e5e8eb;
        border-radius: 8px;
        padding: 8px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    
    /* 종목명 영역 스타일 */
    .stock-info {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .stock-name {
        font-size: 14px;
        font-weight: bold;
        color: #333d4b;
    }
    .stock-code {
        font-size: 11px;
        color: #8b95a1;
    }
    
    /* 가격 및 등락률 우측 배치 스타일 */
    .stock-values {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 14px;
        font-weight: bold;
    }
    
    /* 🚨 칼군무 동시 깜빡임 무한 루프 */
    @keyframes heartbeatUp {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #ffebed; border-color: #f04452; }
    }
    @keyframes heartbeatDown {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #e8f3ff; border-color: #3182f6; }
    }
    
    .blink-up-card {
        animation: heartbeatUp 1.0s infinite ease-in-out !important;
    }
    .blink-down-card {
        animation: heartbeatDown 1.0s infinite ease-in-out !important;
    }
    
    /* 스트림릿 기본 여백 줄이기 */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; }
    
    /* 체크박스 정렬 보정 */
    div[data-testid="stCheckbox"] {
        margin-bottom: 0px !important;
        margin-top: 0px !important;
        padding-bottom: 0px !important;
        padding-top: 0px !important;
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
st.sidebar.title("⭐ 관심 종목")

new_name = st.sidebar.text_input("종목명", placeholder="예: 삼성전자")
new_code = st.sidebar.text_input("종목코드", placeholder="예: 005930")
if st.sidebar.button("추가", use_container_width=True):
    if new_name and len(new_code) == 6 and new_code.isdigit():
        st.session_state.my_stocks[new_name] = {"code": new_code, "checked": True, "alert_active": True}
        save_stocks(st.session_state.my_stocks)
        st.rerun()

st.sidebar.markdown("---")

alert_limit = st.sidebar.number_input("알림 기준 (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.my_stocks.get("_alert_limit", 3.0)), step=0.1)
st.session_state.my_stocks["_alert_limit"] = alert_limit

st.sidebar.markdown("### 📊 표시 선택")
for name in list(st.session_state.my_stocks.keys()):
    if name.startswith("_"): continue
    col1, col2 = st.sidebar.columns([4, 1])
    is_checked = col1.checkbox(name, value=st.session_state.my_stocks[name]["checked"], key=f"chk_{st.session_state.my_stocks[name]['code']}")
    st.session_state.my_stocks[name]["checked"] = is_checked
    if col2.button("×", key=f"del_{st.session_state.my_stocks[name]['code']}"):
        del st.session_state.my_stocks[name]
        save_stocks(st.session_state.my_stocks)
        st.rerun()

if st.sidebar.button("💾 설정 저장", use_container_width=True):
    save_stocks(st.session_state.my_stocks)
    st.sidebar.success("설정 저장 완료!")

# ----------------- 우측: 전광판 영역 -----------------
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
            
            alert_class = ""
            
            if is_up:
                status_txt = f"+{cr:.2f}%"
                color = "#f04452"
                if info["alert_active"] and cr >= alert_limit:
                    alert_class = "blink-up-card"
            elif is_down:
                status_txt = f"-{abs(cr):.2f}%"
                color = "#3182f6"
                if info["alert_active"] and abs(cr) >= alert_limit:
                    alert_class = "blink-down-card"
            else:
                status_txt = f"{cr:.2f}%"
                color = "#4e5968"

            toss_url = f"https://www.tossinvest.com/?focusedProductCode=A{info['code']}"

            # 카드 내부에 정보와 체크박스를 가로로 한 줄에 깔끔하게 배치
            card_col, chk_col = st.columns([12, 1])
            
            with card_col:
                st.markdown(f"""
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
                """, unsafe_allow_html=True)
                
            with chk_col:
                # 카드 바로 옆에 알림 체크박스를 바짝 붙여 배치
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                info["alert_active"] = st.checkbox("", value=info["alert_active"], key=f"alert_{info['code']}", label_visibility="collapsed")
            
        time.sleep(4)
        st.rerun()
