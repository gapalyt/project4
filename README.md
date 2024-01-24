# 만성질환자 (당뇨병, 고혈압) 선제 대응 예측 및 내 주변 우수병원 추천 AI 서비스 개발



## 기술 및 사용한 라이브러리

- Python, Pandas, Numpy, Folium, PyCaret, SQLite3, Geopy, hashlib, sklearn, joblib, Tableau, Excel, Streamlit

## 🗓️ 기간

- 2차 현장 프로젝트: 10월19일 ~ 12월 1일

## 📋 프로젝트 추진 배경

- 최근 고혈압, 당뇨와 같은 만성질환 발병률이 높아지고 있고, 20·30대 젊은 만성질환 환자 또한 증가함에 따라 만성질환 조기 발견 및 적기 치료를 위한 예측 및 관리 도구가 필요해진 상황

## 📝 프로젝트 목적

- 환자의 진료내역을 이용해 만성질환 예측 AI 모델을 개발하여 진료내역이 있는 전 국민 누구나 터치 한 번으로 간편하게 만성질환 발병 가능성 확인
- 만성질환 관리 방법 안내 및 근처 우수 병원을 추천 받을 수 있는 서비스를 제작하여 적기 치료를 통한 전 국민 보건 향상을 목적으로 함

## 📃 프로젝트 내용

- 고혈압 발병률 예측 AI 모델 개발
    - 질환자, 비질환자 3만여 명의 진료 내역 데이터 이용
    - logistic regression, ExtraTrees, Catboost, LightGBM 머신러닝 모델 이용하여 AI 모델 개발
      ![image](https://github.com/gapalyt/project4/assets/72669002/71d99e57-482f-44c5-a5c7-e2617bd16a09)
    - 약 7000개의 질환 데이터에 대한 탐색적 데이터 분석을 기반으로 가설 검증을 통해 데이터셋 구 
      축, 논문을 바탕으로 3개의 파생변수를 생성하여 경우의 수를 조합 후 모델링 진행
- 서비스 제공을 위한 웹앱 개발
    - ![image](https://github.com/gapalyt/project4/assets/72669002/7a37f612-53c6-4d1f-aeb3-df235c4ce356)
    - 원클릭 고혈압 진단 및 병원 추천 서비스 “HITOSIGNAL” 
      건강보험심사평가원의 캐릭터인 히토(히라토끼)/HITO가 사용자에게 고혈압 위험 신호를 보낸다는 
      아이디어로 착안된 만성질환 예측 및 우수 병원 추천 서비스
    - 웹 기능 1 : 고혈압 발병 위험도 확인
      ![image](https://github.com/gapalyt/project4/assets/72669002/c531d9f6-32ec-4629-96e1-5d4ec8e92667)
      고혈압 발병확률과 사용자 연령대 및 성별의 고혈압 유병률을 나타내고 , 위험도 별 경고 메시지를
      알려주는 페이지
    - 웹 기능 2 : 사용자 맞춤 고혈압 관리 및 정보 제공
      ![image](https://github.com/gapalyt/project4/assets/72669002/b53cd821-8220-426c-b620-5182a776b817)
      고혈압 정보 및 통계, 사용자별 고혈압 관리를 위한 수치 기록과 건강관리 체크리스트 등을
      제공한 페이지
    -  웹 기능 3 : 우수 병원 연계 추천
    - ![image](https://github.com/gapalyt/project4/assets/72669002/51bfe138-8da8-4bdb-b31e-1a81395ec984)
    - 현재 사용자 위치를 기반으로 거리별 병원 목록을 나타내며, 병원 검색 등을 위한 페이지

## 💁‍♀️ 담당한 역할

- 데이터 EDA 및 전처리
- 모델링
- 웹앱 개발
