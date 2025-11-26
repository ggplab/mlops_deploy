import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px

# --- [설정] ---
# Docker Compose 배포 시에는 'http://backend:8000'으로 변경해야 함
API_URL = "http://backend-service:8000"

st.set_page_config(page_title="공장 온도 모니터링", layout="wide")

st.title("🏭 실시간 사출 성형기 온도 관제 시스템")
st.markdown("---")

# 레이아웃 구성 (2단)
col1, col2 = st.columns([1, 2])

# 데이터를 저장할 공간 (세션 스테이트 활용)
if "history" not in st.session_state:
    st.session_state["history"] = []

# --- [메인 루프] ---
# Streamlit을 실시간 대시보드처럼 쓰기 위한 placeholder
placeholder = st.empty()

# 'Stop' 버튼을 누르기 전까지 계속 갱신
if st.button('모니터링 시작/중지'):
    while True:
        try:
            # 1. FastAPI에서 데이터 가져오기
            res_current = requests.get(f"{API_URL}/current-temp")
            res_predict = requests.get(f"{API_URL}/predict-temp")
            

            if res_current.status_code == 200 and res_predict.status_code == 200:
                data = res_current.json()
                preds = res_predict.json().get('forecast', []) # 혹시 키가 없어도 에러 안 나게 get 사용
                
                curr_temp = data['temperature']
                curr_time = data['timestamp']
                status = data['status']

                # 데이터 누적
                st.session_state["history"].append({"time": curr_time, "temp": curr_temp})
                if len(st.session_state["history"]) > 30:
                    st.session_state["history"].pop(0)
                
                df = pd.DataFrame(st.session_state["history"])

                # --- [화면 그리기 수정됨] ---
                with placeholder.container():
                    # (1) 상단 지표 (Metric)
                    m_col1, m_col2, m_col3 = st.columns(3)

                    # 예측 데이터가 있을 때만 계산
                    if len(preds) > 0:
                        pred_msg = f"{preds[-1]} °C"
                        delta_msg = f"{preds[0] - curr_temp:.1f} 예상"
                    else:
                        pred_msg = "학습 데이터 수집 중..."
                        delta_msg = "0"

                    m_col1.metric(label="현재 설비 온도", value=f"{curr_temp} °C", delta=delta_msg)
                    m_col2.metric(label="상태", value=status, delta_color="inverse" if status == "DANGER" else "normal")
                    m_col3.metric(label="모델 예측(10분 후)", value=pred_msg)

                    # (2) 경고 메시지
                    if status == "DANGER":
                        st.error("🚨 [경고] 설비 온도가 임계치를 초과했습니다! 냉각수를 확인하세요.")
                    else:
                        st.success("✅ 설비가 정상 가동 중입니다.")

                    # (3) 차트 시각화
                    fig = px.line(df, x='time', y='temp', title='실시간 온도 추이', markers=True)
                    
                    # 예측값이 있다면 차트에 덧그리기 (선택사항)
                    if len(preds) > 0:
                        # 미래 시간축 생성 (간단히 구현)
                        # 현재 마지막 시간에서 1분씩 더한다고 가정 등 시각화 로직 추가 가능
                        pass 

                    st.plotly_chart(fig, use_container_width=True)

            else:
                st.error("백엔드 서버와 통신 실패")

        except Exception as e:
            st.error(f"연결 오류: {e}")
            # 백엔드가 안 켜져있을 때 계속 재시도하지 않도록 잠시 대기
            time.sleep(1)

        # 1초마다 갱신
        time.sleep(1)