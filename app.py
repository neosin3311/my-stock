import streamlit as st
import requests
import json
import os
import time

# 1. 웹페이지 디자인 및 레이아웃 설정 (모바일/작은 창에서도 완벽히 찌그러지며 줄어들도록 개선)
st.set_page_config(page_title="미니 전광판", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 폰트 세팅 */
    .stApp { background-color: #f9fafb; }
    
    /* 1. 상단 잘림 현상 원천 방지 (기본 여백 제거) */
    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 1rem !important; 
        max-width: 100% !important;
    }
    
    /* 2. 브라우저 크기를 줄이면 메뉴와 카드가 모두 함께 쪼그라들도록 반응형 CSS 구현 */
    @media (max-width: 1200px) {
        .mini-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
    }
    
    /* 링크 기본 스타일 무력화 */
    .stock-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        width: 100%;
    }
    
    /* 콤팩트 미니 카드 디자인 */
    .stock-card {
        background-color: white;
        border: 1px solid #e5e8eb;
        border-radius: 8px;
        padding: 8px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        width: 100%;
        box-sizing: border-box;
    }
    
    .stock-info {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .stock-name {
        font-size: 13px;
        font-weight: bold;
        color: #333d4b;
        white-space: nowrap;
    }
    .stock-code {
        font-size: 10px;
        color: #8b95a1;
    }
    
    .stock-values {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        font-weight: bold;
        white-space: nowrap;
    }
    
    /* 🚨 칼군무 동시 깜빡임 전역 규칙 */
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
    
    /* 왼쪽 사이드바 메뉴 전체적인 컴팩트 스케일링 */
    section[data-testid="stSidebar"] {
        width: 20% !important; /* 화면 가로폭의 딱 1/5 가량으로 강제 축소 */
        min-width: 200px !important;
    }
    section[data-testid="stSidebar"] .stWidgetForm {
        padding: 5px !important;
    }
    section[data-testid="stSidebar"] h1 {
        font-size: 1.2rem !important;
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

# ----------------- 좌측: 콤팩트 설정 사이드바 (화면의 1/5 가량 크기) -----------------
st.sidebar.markdown("### ⭐ 관심 종목")

new_name = st.sidebar.text_input("종목명", placeholder="예: 삼성전자", key="input_name")
new_code = st.sidebar.text_input("종목코드", placeholder="예: 005930", key="input_code")
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
    st.sidebar.success("설정 완료!")

# ----------------- 우측: 전광판 영역 (중복 오류 원천 제거) -----------------
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

# 💡 화면이 아래로 늘어나거나 중복 카드들이 누적되지 않도록 완전히 새로 그리는 빈 컨테이너 적용
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

            # 기존의 큰 카드 컴포넌트를 완전히 삭제하고 미니 레이아웃 하나로 단일 통일했습니다.
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
                # 우측 미니 스위치 정밀 배치
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                info["alert_active"] = st.checkbox("", value=info["alert_active"], key=f"alert_{info['code']}", label_visibility="collapsed")
            
        time.sleep(4)
        st.rerun()
