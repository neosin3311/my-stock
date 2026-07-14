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
    
    /* 🚨 자바스크립트가 시스템 시계에 맞춰 실시간으로 주입할 등락 색상 클래스 */
    .bg-up-sync { background-color: #ffebed !important; border-color: #f04452 !important; }
    .bg-down-sync { background-color: #e8f3ff !important; border-color: #3182f6 !important; }
    
    .block-container { padding-top: 2rem !important; }
    </style>

    <script>
    // 기존에 돌고 있던 루프가 있다면 중복 실행 방지를 위해 제거
    if (window.blinkAnimationId) {
        cancelAnimationFrame(window.blinkAnimationId);
    }

    function runBlinkSync() {
        // PC 내부 시스템 시계의 현재 밀리초를 가져옵니다.
        const now = new Date();
        const ms = now.getMilliseconds();
        
        # 매 초의 전반부 0.5초(500ms 미만) 동안 켜지고, 후반부 0.5초 동안 꺼지도록 동기화
        const isOn = ms < 500; 

        // 화면에 있는 모든 알림 대상 카드를 긁어옵니다.
        const upCards = document.querySelectorAll('.sync-blink-up');
        upCards.forEach(card => {
            if (isOn) card.classList.add('bg-up-sync');
            else card.classList.remove('bg-up-sync');
        });

        const downCards = document.querySelectorAll('.sync-blink-down');
        downCards.forEach(card => {
            if (isOn) card.classList.add('bg-down-sync');
            else card.classList.remove('bg-down-sync');
        });

        // 모니터 주사율(초당 60회 이상)에 맞춰 가장 부드럽고 정확하게 실시간 루프 실행
        window.blinkAnimationId = requestAnimationFrame(runBlinkSync);
    }

    // 스트림릿 새로고침과 상관없이 자바스크립트 엔진 즉시 가동
    runBlinkSync();
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
            
            # 자바스크립트 추적용 고정 식별자 배치
            sync_class = ""
            
            if is_up:
                status_txt = f"▲ {cv:,} (+{cr:.2f}%)"
                color = "#f04452"
                if info["alert_active"] and cr >= alert_limit:
                    sync_class = "sync-blink-up"
            elif is_down:
                status_txt = f"▼ {abs(cv):,} (-{abs(cr):.2f}%)"
                color = "#3182f6"
                if info["alert_active"] and abs(cr) >= alert_limit:
                    sync_class = "sync-blink-down"
            else:
                status_txt = f"{cv:,} ({cr:.2f}%)"
                color = "#4e5968"

            toss_url = f"https://www.tossinvest.com/?focusedProductCode=A{info['code']}"

            st.markdown(f"""
                <a href="{toss_url}" target="_blank" class="stock-link">
                    <div class="stock-card {sync_class}">
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
