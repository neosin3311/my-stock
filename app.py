import streamlit as st
import requests
import json
import os
import time

# 1. 웹페이지 디자인 및 레이아웃 설정
st.set_page_config(page_title="실시간 주가 전광판", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f9fafb; }
    .stock-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        margin-bottom: 4px;
    }
    .stock-card {
        background-color: white;
        border: 1px solid #e5e8eb;
        border-radius: 12px;
        padding: 16px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    /* 상태별 배경색 고정 스타일 */
    .bg-up { background-color: #ffebed !important; border-color: #f04452 !important; }
    .bg-down { background-color: #e8f3ff !important; border-color: #3182f6 !important; }
    .bg-white { background-color: #ffffff !important; border-color: #e5e8eb !important; }
    
    .block-container { padding-top: 2rem !important; }
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

# 세션 상태 초기화
if "my_stocks" not in st.session_state:
    st.session_state.my_stocks = load_stocks()
if "blink_state" not in st.session_state:
    st.session_state.blink_state = True
if "last_api_check" not in st.session_state:
    st.session_state.last_api_check = 0.0
if "cached_data" not in st.session_state:
    st.session_state.cached_data = {}

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
st.title("📊 실시간 주가 모니터 전광판")

def get_stock_data(code):
    url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        if res.status_code == 200:
            item = res.json()['result']['areas'][0]['datas'][0]
            return {"price": int(item['nv']), "cv": int(item['cv']), "cr": float(item['cr']), "rf": int(item['rf'])}
    except: return None

# API 데이터 수집은 4초마다 진행하여 부하를 줄임
current_time = time.time()
if current_time - st.session_state.last_api_check >= 4.0 or not st.session_state.cached_data:
    for name, info in st.session_state.my_stocks.items():
        if name.startswith("_") or not info["checked"]: continue
        api_res = get_stock_data(info["code"])
        if api_res:
            st.session_state.cached_data[info["code"]] = api_res
    st.session_state.last_api_check = current_time

# 💡 핵심: 하나의 변수로 켜짐/꺼짐 신호를 제어하여 전 종목의 색상 타이밍을 하나로 묶음
st.session_state.blink_state = not st.session_state.blink_state

placeholder = st.empty()

with placeholder.container():
    for name, info in st.session_state.my_stocks.items():
        if name.startswith("_") or not info["checked"]: continue
        
        data = st.session_state.cached_data.get(info["code"])
        if not data: continue
        
        price = data["price"]
        cv = data["cv"]
        cr = data["cr"]
        rf = data["rf"]
        
        is_up = rf in [1, 2]
        is_down = rf in [4, 5]
        
        card_class = "bg-white"
        
        if is_up:
            status_txt = f"▲ {cv:,} (+{cr:.2f}%)"
            color = "#f04452"
            if info["alert_active"] and cr >= alert_limit:
                card_class = "bg-up" if st.session_state.blink_state else "bg-white"
        elif is_down:
            status_txt = f"▼ {abs(cv):,} (-{abs(cr):.2f}%)"
            color = "#3182f6"
            if info["alert_active"] and abs(cr) >= alert_limit:
                card_class = "bg-down" if st.session_state.blink_state else "bg-white"
        else:
            status_txt = f"{cv:,} ({cr:.2f}%)"
            color = "#4e5968"

        toss_url = f"https://www.tossinvest.com/?focusedProductCode=A{info['code']}"

        st.markdown(f"""
            <a href="{toss_url}" target="_blank" class="stock-link">
                <div class="stock-card {card_class}">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 16px; font-weight: bold; color: #333d4b;">{name}</span>
                        <span style="font-size: 12px; color: #8b95a1;">({info['code']})</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 18px; font-weight: bold; color: {color};">{price:,} 원</span><br>
                        <span style="font-size: 13px; font-weight: bold; color: {color};">{status_txt}</span>
                    </div>
                </div>
            </a>
        """, unsafe_allow_html=True)
        
        info["alert_active"] = st.checkbox("알림 활성화", value=info["alert_active"], key=f"alert_{info['code']}")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 0.5초 주기로 강제 새로고침을 수행해 백엔드 변수 동기화 작동
time.sleep(0.5)
st.rerun()
