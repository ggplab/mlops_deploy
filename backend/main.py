from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import math
import time
from datetime import datetime
from collections import deque
import numpy as np
from sklearn.linear_model import LinearRegression # <-- ML 모델 소환

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- [In-Memory Database] ---
# 최근 30개의 데이터만 기억하는 저장소 (Queue)
# 모델이 학습할 '데이터셋' 역할을 합니다.
data_buffer = deque(maxlen=30) 

def generate_fake_temperature():
    now = time.time()
    base_temp = 65.0
    cycle = 10 * math.sin(now / 10)
    noise = random.uniform(-1.5, 1.5)
    return round(base_temp + cycle + noise, 2)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.get("/current-temp")
def get_current_temp():
    temp = generate_fake_temperature()
    
    # [핵심] 생성된 데이터를 버리지 않고 '학습 데이터'로 저장합니다.
    data_buffer.append(temp)
    
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": temp,
        "status": "DANGER" if temp > 72 else "NORMAL"
    }

@app.get("/predict-temp")
def get_prediction():
    """
    [Real ML Model Serving]
    저장된 최근 데이터(data_buffer)를 사용하여 
    선형 회귀 모델을 '실시간으로' 학습시키고 미래를 예측합니다.
    """
    
    # 1. 학습 데이터가 충분한지 확인 (최소 10개 이상)
    if len(data_buffer) < 10:
        return {"forecast": [], "message": "데이터 수집 중... (최소 10개 필요)"}

    # 2. 데이터 전처리 (Scikit-Learn이 좋아하는 형태로 변환)
    # X: 시간(인덱스) [0, 1, 2, ... N]
    # y: 온도 값
    y = np.array(data_buffer)
    X = np.arange(len(y)).reshape(-1, 1)

    # 3. 모델 학습 (Training)
    # "최근 데이터의 추세(기울기)를 배워라"
    model = LinearRegression()
    model.fit(X, y)

    # 4. 미래 예측 (Inference)
    # 현재 시점 이후 10스텝(Future X)을 만듭니다.
    next_steps = np.arange(len(y), len(y) + 10).reshape(-1, 1)
    predictions = model.predict(next_steps)

    return {"forecast": np.round(predictions, 2).tolist()}