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
        transition: transform 0.1s, box-shadow 0.2s;
    }
    .stock-card:hover { 
        background-color: #f2f4f6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transform: translateY(-1px);
    }
    
    /* 🚨 PC 시스템 시간(초)에 맞춰 100% 강제 동기화되는 CSS 애니메이션 */
    @keyframes systemBlinkUp {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #ffebed; border-color: #f04452; }
    }
    @keyframes systemBlinkDown {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #e8f3ff; border-color: #3182f6; }
    }
    
    /* 
       재생 시작 시간을 음수(-) 값으로 밀어 넣어 
       현재 PC 시각의 초 단위 위치와 애니메이션 재생 주기를 강제로 일치시킵니다.
    */
    .blink-up-card {
        animation: systemBlinkUp 1.0s infinite ease-in-out !important;
        animation-delay: calc(var(--start-delay, 0s)) !important;
    }
    .blink-down-card {
        animation: systemBlinkDown 1.0s infinite ease-in-out !important;
        animation-delay: calc(var(--start-delay, 0s)) !important;
    }
    
    .block-container { padding-top: 2rem !important; }
    </style>

    <script>
    // 스트림릿이 화면을 갱신할 때마다 실시간으로 PC의 현재 시각(초+밀리초)을 계산하여 CSS 속성 주입
    function syncBlinkTime() {
        const root = document.documentElement;
        if (root) {
            const now = new Date();
            // 현재 초와 밀리초를 소수점으로 환산 (예: 45.23초)
            const currentSeconds = now.getSeconds() + (now.getMilliseconds() / 1000);
            // 애니메이션 주기인 1초 기준 딜레이를 음수로 심어 타이밍 일치
            const delay = -(currentSeconds % 1.0);
            root.style.setProperty('--start-delay', delay + 's');
        }
    }
    // 최초 실행 및 스트림릿 다시 렌더링 시 즉시 동기화 적용
    syncBlinkTime();
    </script>
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
st.title("📊 실시간 주가 모니터 전광판")

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
                status_txt = f"▲ {cv:,} (+{cr:.2f}%)"
                color = "#f04452"
                if info["alert_active"] and cr >= alert_limit:
                    alert_class = "blink-up-card"
            elif is_down:
                status_txt = f"▼ {abs(cv):,} (-{abs(cr):.2f}%)"
                color = "#3182f6"
                if info["alert_active"] and abs(cr) >= alert_limit:
                    alert_class = "blink-down-card"
            else:
                status_txt = f"{cv:,} ({cr:.2f}%)"
                color = "#4e5968"

            toss_url = f"https://www.tossinvest.com/?focusedProductCode=A{info['code']}"

            st.markdown(f"""
                <a href="{toss_url}" target="_blank" class="stock-link">
                    <div class="stock-card {alert_class}">
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
            
        time.sleep(4)
        st.rerun()
