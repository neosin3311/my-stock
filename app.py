import streamlit as st
import requests
import json
import os
import time

# 1. 웹페이지 디자인 및 레이아웃 설정 (토스증권 테마)
st.set_page_config(page_title="실시간 주가 전광판", layout="wide")

# CSS를 주입하여 기존 토스 스타일의 UI를 완벽하게 재현합니다.
st.markdown("""
    <style>
    .reportview-container { background-color: #f9fafb; }
    .stock-card {
        background-color: white;
        border: 1px solid #e5e8eb;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .stock-card:hover { background-color: #f2f4f6; }
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

# ----------------- 우측: 전광판 영역 (백엔드 직통 호출) -----------------
st.title("📊 실시간 주가 모니터 전광판")

def get_stock_data(code):
    # 브라우저가 아닌 파이썬 서버가 직접 네이버 금융을 호출하므로 100% 안 막히고 가져옵니다.
    url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
        if res.status_code == 200:
            item = res.json()['result']['areas'][0]['datas'][0]
            return {"price": item['nv'], "cv": item['cv'], "cr": item['cr'], "rf": item['rf']}
    except: return None

# 화면 갱신을 위한 빈 캔버스 정의
placeholder = st.empty()

# 4초 주기로 실시간 갱신 루프 구동
while True:
    with placeholder.container():
        for name, info in st.session_state.my_stocks.items():
            if name.startswith("_") or not info["checked"]: continue
            
            data = get_stock_data(info["code"])
            if not data: continue
            
            is_up = data["rf"] in [1, 2]
            is_down = data["rf"] in [4, 5]
            
            if is_up:
                status_txt = f"▲ {data['cv']:,} (+{data['cr']:.2f}%)"
                color = "#f04452" # 토스 상승 레드
                bg_style = "background-color: #ffebed;" if (info["alert_active"] and data["cr"] >= alert_limit) else "background-color: white;"
            elif is_down:
                status_txt = f"▼ {data['cv']:,} (-{data['cr']:.2f}%)"
                color = "#3182f6" # 토스 하락 블루
                bg_style = "background-color: #e8f3ff;" if (info["alert_active"] and data["cr"] >= alert_limit) else "background-color: white;"
            else:
                status_txt = f"{data['cv']:,} ({data['cr']:.2f}%)"
                color = "#4e5968"
                bg_style = "background-color: white;"

            # 토스증권 상세페이지 이동 링크 주소
            toss_url = f"https://www.tossinvest.com/?focusedProductCode=A{info['code']}"

            # 카드 한 줄 배치 및 링크 연결
            st.markdown(f"""
                <a href="{toss_url}" target="_blank" style="text-decoration: none; color: inherit;">
                    <div class="stock-card" style="{bg_style}">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 14px; font-weight: bold; color: #333d4b;">{name}</span>
                            <span style="font-size: 11px; color: #8b95a1;">({info['code']})</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 14px; font-weight: bold; color: {color};">{data['price']:,} 원</span><br>
                            <span style="font-size: 12px; font-weight: bold; color: {color};">{status_txt}</span>
                        </div>
                    </div>
                </a>
            """, unsafe_allow_html=True)
            
            # 카드 바로 밑에 개별 알림 체크박스 배치
            info["alert_active"] = st.checkbox("알림 켜기", value=info["alert_active"], key=f"alert_{info['code']}")
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
            
        time.sleep(4)
        st.rerun()