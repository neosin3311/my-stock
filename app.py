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
    
    /* 1. 우측 메인 영역 상단 잘림 현상 방지 및 여백 최소화 */
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 0.5rem !important; 
        max-width: 100% !important;
    }
    
    /* 2. 좌측 메뉴(사이드바) 여백 대폭 줄여 위로 바짝 붙이기 */
    section[data-testid="stSidebar"] {
        width: 20% !important;
        min-width: 190px !important;
    }
    section[data-testid="stSidebar"] .stWidgetForm {
        padding: 2px !important;
    }
    /* 사이드바 내부 아이템 간격(Gap) 최소화 */
    div[data-testid="stSidebarUserContent"] {
        padding-top: 1rem !important;
        gap: 0.2rem !important;
    }
    /* 입력창 및 위젯들의 세로 높이와 여백 축소 */
    div[data-testid="stNumberInput"], div[data-testid="stTextInput"] {
        margin-bottom: 4px !important;
    }
    div[data-testid="stNumberInput"] > label, div[data-testid="stTextInput"] > label {
        margin-bottom: 2px !important;
        font-size: 12px !important;
    }
    
    /* 3. 우측 미니 주가 카드 스타일 */
    .stock-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        width: 100%;
        margin-bottom: 3px;
    }
    .stock-card {
        background-color: white;
        border: 1px solid #e5e8eb;
        border-radius: 6px;
        padding: 6px 10px;
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
        gap: 5px;
    }
    .stock-name {
        font-size: 12px;
        font-weight: bold;
        color: #333d4b;
    }
    .stock-code {
        font-size: 9px;
        color: #8b95a1;
    }
    .stock-values {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        font-weight: bold;
    }
    
    /* 4. 1초 주기 동시 깜빡임 CSS */
    @keyframes heartbeatUp {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #ffebed; border-color: #f04452; }
    }
    @keyframes heartbeatDown {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #e8f3ff; border-color: #3182f6; }
    }
    .blink-up-card { animation: heartbeatUp 1.0s infinite ease-in-out !important; }
    .blink-down-card { animation: heartbeatDown 1.0s infinite ease-in-out !important; }
    
    /* 스트림릿 체크박스 자체의 불필요한 마진 제거 */
    div[data-testid="stCheckbox"] {
        margin: 0px !important;
        padding: 0px !important;
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

# ----------------- 좌측: 상단 밀착형 콤팩트 사이드바 -----------------
st.sidebar.markdown("### ⭐ 관심 종목")

new_name = st.sidebar.text_input("종목명", placeholder="예: 삼성전자", key="in_name")
new_code = st.sidebar.text_input("종목코드", placeholder="예: 005930", key="in_code")
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

# 누적 현상을 완전히 막기 위해 빈 화면 공간(Placeholder) 하나만 사용합니다.
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

            # 🛠️ 예전 큰 카드 렌더링 코드를 완전히 삭제하고 오직 미니 가로 배열로만 고정 출력합니다.
            card_col, chk_col = st.columns([15, 1])
            
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
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                info["alert_active"] = st.checkbox("", value=info["alert_active"], key=f"alert_{info['code']}", label_visibility="collapsed")
            
        time.sleep(4)
        st.rerun()
