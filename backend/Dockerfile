# 1. 가볍고 안정적인 파이썬 3.9 버전(Slim)을 베이스로 씁니다.
FROM python:3.9-slim

# 2. 작업 폴더를 만듭니다.
WORKDIR /app

# 3. 필요한 라이브러리 명세서를 복사하고 설치합니다.
# (캐싱 효과를 위해 requirements를 먼저 복사하는 것이 국룰입니다)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 나머지 소스 코드를 다 복사합니다.
COPY . .

# 5. 컨테이너가 켜질 때 실행할 명령어입니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]