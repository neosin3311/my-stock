import streamlit as st
import requests
import json
import os
import time

# 1. 웹페이지 디자인 및 레이아웃 설정 (토스증권 테마 적용)
st.set_page_config(page_title="실시간 주가 전광판", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 스타일 */
    .stApp { background-color: #f9fafb; }
    
    /* 기본 카드 디자인 (클릭하면 토스증권 상세페이지로 새창 이동) */
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
        transition: transform 0.1s, box-shadow 0.2s;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .stock-card:hover { 
        background-color: #f2f4f6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transform: translateY(-1px);
    }
    
    /* 🚨 브라우저 글로벌 시간축에 완벽히 동기화시키는 깜빡임 효과 */
    @keyframes blinkUp {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #ffebed; border-color: #f04452; }
    }
    @keyframes blinkDown {
        0%, 100% { background-color: #ffffff; border-color: #e5e8eb; }
        50% { background-color: #e8f3ff; border-color: #3182f6; }
    }
    
    /* 
       모든 카드가 제각각 타이머를 돌리지 않고, 
       브라우저의 절대적인 글로벌 타임라인 시계를 똑같이 공유하여 
       정확히 같은 순간에 반응하도록 강제 통일합니다.
    */
    .blink-up-card {
        animation: blinkUp 1.2s infinite ease-in-out !important;
        animation-delay: calc(0s - var(--timeline-offset, 0s)) !important;
        animation-timeline: auto !important;
    }
    .blink-down-card {
        animation: blinkDown 1.2s infinite ease-in-out !important;
        animation-delay: calc(0s - var(--timeline-offset, 0s)) !important;
        animation-timeline: auto !important;
    }
    
    /* 스트림릿 기본 요소 간격 조정 */
    .block-container { padding-top: 2rem !important; }
    </style>
    
    <script>
    // 브라우저의 실제 페이지 로드 시간 기준으로 CSS의 딜레이 편차를 제로(0)로 묶어주는 헬퍼 스크립트
    const root = document.documentElement;
    if (root) {
        // 브라우저가 열린 시점(절대 시간)을 변수로 심어서 CSS 애니메이션 타이밍을 강제 동기화시킵니다.
        const pageLoadTime = performance.now() / 1000;
        root.style.setProperty('--timeline-offset', pageLoadTime + 's');
    }
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

# ----------------- 우측: 전광판 영역 (네이버 금융 실시간 API 직통 연동) -----------------
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

# 화면 전체 갱신을 위한 빈 캔버스 정의
placeholder = st.empty()

# 4초 주기로 실시간 데이터를 읽어와 렌더링
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
            
            # 상승/하락 글자 및 색상 배치
            if is_up:
                status_txt = f"▲ {cv:,} (+{cr:.2f}%)"
                color = "#f04452" # 토스 레드
                alert_class = "blink-up-card" if (info["alert_active"] and cr >= alert_limit) else ""
            elif is_down:
                status_txt = f"▼ {cv:,} (-{cv:,}%)" if cv != 0 else f"▼ {cv:,} (-{cr:.2f}%)"
                # API 데이터 매칭 오류 방지 보정
                status_txt = f"▼ {abs(cv):,} (-{abs(cr):.2f}%)"
                color = "#3182f6" # 토스 블루
                alert_class = "blink-down-card" if (info["alert_active"] and abs(cr) >= alert_limit) else ""
            else:
                status_txt = f"{cv:,} ({cr:.2f}%)"
                color = "#4e5968"
                alert_class = ""

            toss_url = f"https://www.tossinvest.com/?focusedProductCode=A{info['code']}"

            # 주가 카드 디자인을 화면에 출력
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
            
            # 알림 스위치
            info["alert_active"] = st.checkbox("알림 활성화", value=info["alert_active"], key=f"alert_{info['code']}")
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
            
        time.sleep(4)
        st.rerun()
