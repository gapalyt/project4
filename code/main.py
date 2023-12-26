# main.py
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
from PIL import Image
import folium
from folium.plugins import MarkerCluster, AntPath
from folium import CustomIcon, IFrame
from streamlit_folium import st_folium
import pandas as pd
import geopy.distance
import sqlite3
import hashlib
from sklearn.ensemble import RandomForestClassifier
import joblib

# page setting
st.set_page_config(
    page_title="Hito Signal",
    page_icon="📱",
    layout="wide",
)

# css
with open('style.css') as f:
  st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

######################## Login ###########################

# DB Management
conn = sqlite3.connect('login.db')
c = conn.cursor()

def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False

def create_usertable():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')

def add_userdata(username,password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data

def view_all_users():
	c.execute('SELECT * FROM userstable')
	data = c.fetchall()
	return data

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'username' not in st.session_state:
    st.session_state.username = ''

# 로그인 함수
def login(username, password):
    # 로그인 로직 구현
    create_usertable()
    hashed_pswd = make_hashes(password)
    result = login_user(username,check_hashes(password,hashed_pswd)) 
    if result:
        st.session_state.username = username
        st.session_state['logged_in'] = True
    else:
        st.warning("Incorrect Username/Password")

def use_username():
    if st.session_state.username:
        return st.session_state.username
    else:
        st.write("로그인해주세요")

# 로그인 화면
def render_login_page():
    st.title("Login")
    username = st.text_input("사용자 이름")
    password = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        login(username, password)  # 로그인 함수 호출
    if st.button("회원가입"):
        sign_up()

# 회원가입
def sign_up():
    st.subheader("Create New Account")
    new_user = st.text_input("새로운 사용자 이름")
    new_password = st.text_input("새로운 비밀번호", type="password")

    if st.button("만들기"):
      create_usertable()
      add_userdata(new_user,make_hashes(new_password))
      st.success("회원가입이 완료되었습니다")
      st.info("로그인을 진행해주세요")

######################## Map ###########################

# 서울과 원주의 기준 위치
SEOUL_LOCATION = (37.5665, 126.9780)
WONJU_LOCATION = (37.342847, 127.920361)

# 아이콘 경로
USER_ICON_PATH = "logo/hito.png"
HOSPITAL_ICON_PATH = "logo/todang.png"

# 초기 지도 설정 함수
def create_map(location, zoom_start=12):
    m = folium.Map(location=location, zoom_start=zoom_start)
    icon = CustomIcon(USER_ICON_PATH, icon_size=(80, 80))
    folium.Marker(location, popup="사용자 위치", icon=icon).add_to(m)
    return m

# 병원 데이터 불러오기 함수
def load_hospital_data(filepath):
    df = pd.read_excel(filepath)
    return df[['병원명', '소재지', '전화번호', '좌표(Y)', '좌표(X)']]

# 병원 마커 추가 함수
def add_hospital_markers(map_object, hospital_data):
    marker_cluster = MarkerCluster().add_to(map_object)
    for _, row in hospital_data.iterrows():
        iframe = IFrame(f"{row['병원명']}<br>{row['전화번호']}", width=200, height=100)
        popup = folium.Popup(iframe, max_width=200)
        icon = CustomIcon(HOSPITAL_ICON_PATH, icon_size=(40, 40))
        folium.Marker(
            location=[row['좌표(Y)'], row['좌표(X)']],
            popup=popup,
            icon=icon
        ).add_to(marker_cluster)

# 거리 계산 함수
def calculate_distance(loc1, loc2):
    return geopy.distance.distance(loc1, loc2).km

# 병원 데이터에 거리 정보 추가 함수
def add_distance_info(hospital_data, location):
    hospital_data['거리'] = hospital_data.apply(
        lambda row: calculate_distance(location, (row['좌표(Y)'], row['좌표(X)'])),
        axis=1
    )
    return hospital_data

# 병원 데이터 필터링 함수
def filter_hospitals(data, close, medium, all):
    if close and medium and all:
        return data
    elif close and medium:
        return data[data['거리'] <= 10]
    elif medium and all:
        return data[data['거리'] > 2]
    elif close:
        return data[data['거리'] <= 2]
    elif medium:
        return data[(data['거리'] > 2) & (data['거리'] <= 10)]
    elif all:
        return data
    else:
        return pd.DataFrame(columns=data.columns)

# 병원 검색 결과 처리 함수
def handle_hospital_search(hospital_data, search_query):
    if search_query:
        return hospital_data[hospital_data['병원명'].str.contains(search_query)]
    else:
        return pd.DataFrame(columns=hospital_data.columns)

######################## Model ##########################

df=pd.read_csv('data/merged_df.csv')
# SQLite 연결
conn = sqlite3.connect('finaldb.db')
# DataFrame을 SQLite 테이블로 저장
df.to_sql('mytable', conn, index=False, if_exists='replace')
# 연결 종료
conn.close()

def agegroup2cluster(agegroup):
    if 10 <= agegroup <= 30:
        return '10-30'
    elif 40 <= agegroup <= 60:
        return '40-60'
    else:
        return '60+'    

def get_user_age_group():
    id = use_username()
    df = pd.read_csv('data/merged_df.csv')
    user_data = df[df['username'] == id]
    if not user_data.empty:
        return user_data.iloc[0]['나이대']
    else:
        return None

def get_prediction_result():
    conn = sqlite3.connect('finaldb.db')
    id = use_username()
    if id:
        if isinstance(id, str):
            query = f"SELECT * FROM mytable WHERE username = '{id}'"
        else:
            query = f"SELECT * FROM mytable WHERE username = {id}"
        
        patient_data = pd.read_sql(query, conn)
        conn.close()

        progress_bar = st.progress(0)
        features = patient_data[['성별', '나이대', '입원 횟수', '봄_방문_횟수', '여름_방문_횟수', '가을_방문_횟수', '겨울_방문_횟수', 'A04', 'A05', 'A08', 'A09', 'A15', 'A16', 'A18', 'A31', 'A48', 'A49', 'A53', 'A54', 'A56', 'A59', 'A60', 'A63', 'A64', 'A69', 'A74', 'B00', 'B02', 'B07', 'B15', 'B17', 'B18', 'B24', 'B30', 'B33', 'B34', 'B35', 'B36', 'B37', 'B49', 'B85', 'B86', 'B88', 'B90', 'B97', 'B98', 'C09', 'C13', 'C16', 'C18', 'C20', 'C22', 'C24', 'C32', 'C34', 'C43', 'C44', 'C49', 'C50', 'C53', 'C54', 'C56', 'C61', 'C64', 'C67', 'C73', 'C77', 'C78', 'C79', 'C83', 'C85', 'C88', 'C90', 'C92', 'D00', 'D01', 'D05', 'D06', 'D10', 'D11', 'D12', 'D13', 'D14', 'D16', 'D17', 'D18', 'D21', 'D22', 'D23', 'D24', 'D25', 'D27', 'D28', 'D29', 'D30', 'D31', 'D32', 'D33', 'D34', 'D35', 'D36', 'D37', 'D39', 'D44', 'D47', 'D48', 'D50', 'D51', 'D52', 'D53', 'D61', 'D62', 'D64', 'D68', 'D69', 'D72', 'D75', 'E02', 'E03', 'E04', 'E05', 'E06', 'E07', 'E10', 'E11', 'E13', 'E14', 'E16', 'E20', 'E21', 'E22', 'E23', 'E27', 'E28', 'E29', 'E50', 'E53', 'E55', 'E56', 'E58', 'E66', 'E78', 'E79', 'E83', 'E86', 'E87', 'E89', 'G20', 'G24', 'G25', 'G31', 'G32', 'G40', 'G43', 'G44', 'G45', 'G46', 'G47', 'G50', 'G51', 'G53', 'G54', 'G55', 'G56', 'G57', 'G58', 'G59', 'G60', 'G62', 'G63', 'G64', 'G80', 'G81', 'G82', 'G83', 'G90', 'G93', 'G95', 'G99', 'H00', 'H01', 'H02', 'H04', 'H05', 'H06', 'H10', 'H11', 'H13', 'H15', 'H16', 'H17', 'H18', 'H19', 'H20', 'H25', 'H26', 'H27', 'H28', 'H30', 'H31', 'H33', 'H34', 'H35', 'H36', 'H40', 'H43', 'H44', 'H47', 'H50', 'H52', 'H53', 'H57', 'H60', 'H61', 'H62', 'H65', 'H66', 'H67', 'H68', 'H69', 'H71', 'H72', 'H73', 'H74', 'H81', 'H83', 'H90', 'H91', 'H92', 'H93', 'I05', 'I20', 'I21', 'I25', 'I26', 'I33', 'I34', 'I35', 'I42', 'I45', 'I47', 'I48', 'I49', 'I50', 'I51', 'I60', 'I61', 'I63', 'I64', 'I65', 'I66', 'I67', 'I69', 'I70', 'I73', 'I74', 'I78', 'I79', 'I80', 'I82', 'I83', 'I84', 'I86', 'I87', 'I88', 'I89', 'I95', 'I97', 'I99', 'J00', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06', 'J09', 'J10', 'J11', 'J15', 'J18', 'J20', 'J21', 'J22', 'J30', 'J31', 'J32', 'J33', 'J34', 'J35', 'J36', 'J37', 'J38', 'J39', 'J40', 'J41', 'J42', 'J43', 'J44', 'J45', 'J46', 'J47', 'J82', 'J84', 'J90', 'J93', 'J98', 'K01', 'K02', 'K03', 'K04', 'K05', 'K07', 'K08', 'K09', 'K11', 'K12', 'K13', 'K14', 'K20', 'K21', 'K22', 'K25', 'K26', 'K27', 'K29', 'K30', 'K31', 'K35', 'K40', 'K50', 'K51', 'K52', 'K56', 'K57', 'K58', 'K59', 'K60', 'K61', 'K62', 'K63', 'K64', 'K65', 'K66', 'K70', 'K71', 'K73', 'K74', 'K75', 'K76', 'K80', 'K81', 'K82', 'K83', 'K85', 'K86', 'K92', 'L01', 'L02', 'L03', 'L04', 'L05', 'L08', 'L13', 'L20', 'L21', 'L23', 'L24', 'L25', 'L27', 'L28', 'L29', 'L30', 'L40', 'L42', 'L43', 'L50', 'L51', 'L53', 'L56', 'L57', 'L60', 'L63', 'L64', 'L65', 'L66', 'L70', 'L71', 'L72', 'L73', 'L74', 'L80', 'L81', 'L82', 'L84', 'L85', 'L89', 'L90', 'L91', 'L98', 'M00', 'M05', 'M06', 'M10', 'M12', 'M13', 'M14', 'M15', 'M16', 'M17', 'M18', 'M19', 'M20', 'M21', 'M22', 'M23', 'M24', 'M25', 'M32', 'M35', 'M40', 'M41', 'M43', 'M45', 'M46', 'M47', 'M48', 'M49', 'M50', 'M51', 'M53', 'M54', 'M60', 'M61', 'M62', 'M65', 'M66', 'M67', 'M70', 'M71', 'M72', 'M75', 'M76', 'M77', 'M79', 'M80', 'M81', 'M82', 'M83', 'M84', 'M85', 'M86', 'M87', 'M89', 'M92', 'M93', 'M94', 'M96', 'M99', 'N00', 'N02', 'N03', 'N04', 'N05', 'N10', 'N12', 'N13', 'N17', 'N18', 'N20', 'N21', 'N28', 'N30', 'N31', 'N32', 'N34', 'N39', 'N40', 'N41', 'N43', 'N45', 'N46', 'N48', 'N60', 'N61', 'N62', 'N63', 'N64', 'N70', 'N71', 'N72', 'N73', 'N74', 'N75', 'N76', 'N77', 'N80', 'N81', 'N83', 'N84', 'N85', 'N86', 'N87', 'N91', 'N92', 'N93', 'N94', 'N95', 'N97', 'Q18', 'Q21', 'Q28', 'Q44', 'Q61', 'Q85', 'R00', 'R03', 'R04', 'R05', 'R06', 'R07', 'R09', 'R10', 'R11', 'R12', 'R13', 'R14', 'R17', 'R19', 'R20', 'R21', 'R22', 'R23', 'R25', 'R26', 'R29', 'R30', 'R31', 'R32', 'R35', 'R39', 'R41', 'R42', 'R43', 'R45', 'R49', 'R50', 'R51', 'R52', 'R53', 'R55', 'R56', 'R59', 'R60', 'R61', 'R63', 'R68', 'R73', 'R76', 'R79', 'R80', 'R81', 'R82', 'R87', 'R91', 'R92', 'R93', 'R94', 'S00', 'S01', 'S02', 'S03', 'S05', 'S06', 'S07', 'S09', 'S11', 'S13', 'S14', 'S20', 'S21', 'S22', 'S23', 'S27', 'S30', 'S31', 'S32', 'S33', 'S34', 'S40', 'S41', 'S42', 'S43', 'S46', 'S50', 'S51', 'S52', 'S53', 'S54', 'S56', 'S60', 'S61', 'S62', 'S63', 'S64', 'S65', 'S66', 'S67', 'S68', 'S69', 'S70', 'S71', 'S72', 'S73', 'S76', 'S80', 'S81', 'S82', 'S83', 'S84', 'S86', 'S87', 'S90', 'S91', 'S92', 'S93', 'S96', 'S97', 'T00', 'T01', 'T14', 'T15', 'T16', 'T17', 'T18', 'T20', 'T21', 'T22', 'T23', 'T24', 'T25', 'T29', 'T30', 'T31', 'T63', 'T67', 'T70', 'T78', 'T79', 'T81', 'T84', 'T85', 'T88', 'T91', 'Z00', 'Z01', 'Z03', 'Z04', 'Z08', 'Z09', 'Z11', 'Z12', 'Z13', 'Z20', 'Z30', 'Z31', 'Z32', 'Z33', 'Z34', 'Z35', 'Z39', 'Z46', 'Z47', 'Z48', 'Z50', 'Z51', 'Z54', 'Z71', 'Z90', 'Z94', 'Z95', 'Z96', 'Z98', '질환우세질병_5', '비질환우세질병_5', '질환우세질병_2', '비질환우세질병_2']]
        model = joblib.load('catboost_model .pkl')
        progress_bar.progress(50)

        prediction = model.predict(features)
        # 테스트 세트에 대한 클래스별 예측 확률 출력
        class_1_probabilities = model.predict_proba(features)[:, 1]
        # risk_classification = classify_risk(class_1_probabilities[0])
        # classify_class = classify_High_blood_pressure(prediction[0])
        # classify_class = classify_High_blood_pressure(prediction[0])
        progress_bar.progress(100)
        return(class_1_probabilities[0])

######################## Main ###########################

def render_main_page():
    custom_css = """
    <style>
        .css-1d391kg {
            flex-direction: column;
        }
        .stSidebar {
            width: 100%;
            height: auto;
            position: relative;
            top: 0;
            flex-direction: row;
        }
        .css-1outpf7 {
            flex-direction: column;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # sidebar
    with st.sidebar:
      selected = option_menu(
        menu_title=None,
        options=["고혈압 지수 검사", "고혈압 정보", "내 주변 병원 찾기", "내 기록"],
        icons=["house", "activity", "hospital", "clipboard2-heart"],
        menu_icon="cast",
        default_index=0,
      )
    

    hito_signal = Image.open('logo/logo.png')
    logo, logout_btn = st.columns([0.8, 0.2])
    logo.image(hito_signal, output_format='PNG')
    with logout_btn:
        if st.button("Log Out"):
          st.session_state['logged_in'] = False

    # st.markdown(f"""
    # <nav style="display:flex;justify-content:space-between;align-items:center;padding:10px;background-color:#ffffff;">
    #     <img <img src="https://github.com/DohaLim/hitosignal/blob/main/logo.png?raw=true" style="height:50px;">
    #     <ul style="display:flex;list-style:none;margin:0;padding:0;">
    #         <!-- 각 메뉴 항목 -->
    #         <li style="padding:0 10px;"><a href="#" style="text-decoration:none;color:black;">고혈압 지수 검사</a></li>
    #         <li style="padding:0 10px;"><a href="http://localhost:8502/" style="text-decoration:none;color:black;">고혈압 정보</a></li>
    #         <li style="padding:0 10px;"><a href="#" style="text-decoration:none;color:black;">내 주변 병원 찾기</a></li>
    #     </ul>
    #     <button onclick="location.href='로그아웃_경로';" style="border:none;background-color:#f1f1f1;color:black;padding:10px;cursor:pointer;">Log Out</button>
    # </nav>
    # """, unsafe_allow_html=True)

##################################### service ########################################

    if selected == "고혈압 지수 검사":
        st.title("Welcome to Hito Signal")
        st.image('infographic/intro.png', output_format='PNG')
        st.image('infographic/intro2.png', output_format='PNG')
        st.header("나는 만성 고혈압일까?")

        if st.button("👉내 만성 고혈압 위험지수 확인해보기"):
            if st.session_state.username:
                prediction = get_prediction_result()
                age_group = get_user_age_group()
                age_cluster = agegroup2cluster(age_group)

                # 텍스트 크기 조정
                html_template = f"""
                <div style="font-family: sans-serif; text-align: center; margin-bottom: 20px;">
                    <h1 style="font-size: 2em;">당신의 고혈압 위험도 점수는 {prediction:.2f}점입니다.</h1>
                </div>
                """

                # HTML 템플릿을 Streamlit에 표시
                st.markdown(html_template, unsafe_allow_html=True)

                # 이미지 파일을 PIL 이미지 객체로 불러옴
                def load_image(image_path):
                    return Image.open(image_path)

                # 위험군 결정 로직
                risk_group, image_file, age_image_file, method_image_file = '', '', '', ''
                if prediction < 0.3:
                    risk_group = '저위험군'
                elif prediction < 0.5:
                    risk_group = '중저위험군'
                elif prediction == 0.5:
                    risk_group = '중위험군'
                elif prediction < 0.7:
                    risk_group = '중고위험군'
                else:
                    risk_group = '고위험군'
                image_file = load_image(f"infographic/{risk_group}.png")

                # 연령대별 이미지 결정 로직
                age_cluster_dict = {'10-30': '청년층', '40-60': '중년층', '60+': '고령층'}
                age_image_file = load_image(f"infographic/{age_cluster_dict[age_cluster]}.png")

                # 예방법 또는 합병증 이미지 결정 로직
                method_group = '예방법' if risk_group in ['저위험군', '중저위험군', '중위험군'] else '합병증'
                method_image_file = load_image(f"infographic/{method_group}.png")

                # 이미지를 표시할 컨테이너를 생성하고 이미지 배치
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.image(image_file)  # 캡션 제거
                with col2:
                    st.image(age_image_file)  # 캡션 제거

                # 예방법 또는 합병증 이미지 표시
                st.image(method_image_file, use_column_width=True)  # 캡션 제거

            else:
                st.warning("로그인해주세요")
          
##################################### Information ########################################

    if selected == "고혈압 정보":
        st.image('infographic/info1.png', output_format='PNG')
        st.image('infographic/info2.png', output_format='PNG')
        st.image('infographic/info3.png', output_format='PNG')
        st.image('infographic/info4.png', output_format='PNG')
        st.image('infographic/info5.png', output_format='PNG')
      
##################################### Hospital ########################################
    if selected == "내 주변 병원 찾기":
        if 'current_location' not in st.session_state:
            st.session_state['current_location'] = SEOUL_LOCATION

        if 'hospital_data' not in st.session_state:
            st.session_state['hospital_data'] = load_hospital_data("data/고혈압 우수 병원 좌표.xlsx")
            st.session_state['hospital_data'] = add_distance_info(st.session_state['hospital_data'], SEOUL_LOCATION)

        # 병원 필터링 탭
        tab1, tab2, tab3 = st.tabs(["현재 위치", "병원 필터링", "병원 목록"])

        with tab1:
            if st.button("이동"):
                st.session_state['current_location'] = WONJU_LOCATION
                st.session_state['hospital_data'] = add_distance_info(st.session_state['hospital_data'], WONJU_LOCATION)

        with tab2:
            close_distance = st.checkbox("거리가 가까운 순(2km 이내)")
            medium_distance = st.checkbox("거리가 먼 순(2km~10km)")
            all_distance = st.checkbox("전체")
            filtered_hospital_data = filter_hospitals(st.session_state['hospital_data'], close_distance, medium_distance, all_distance)

        with tab3:
            # 병원 검색 기능
            search_query = st.text_input("병원 검색")
            search_results = handle_hospital_search(st.session_state['hospital_data'], search_query)
            selected_hospital = st.selectbox("검색 결과", [''] + search_results['병원명'].tolist())

            # 검색 결과 또는 선택된 병원에 따라 데이터프레임 표시
            if search_query and not selected_hospital:
                sorted_search_results = search_results.sort_values(by='거리')
                st.dataframe(sorted_search_results[['병원명', '소재지', '전화번호', '거리']].reset_index(drop=True), width=700, height=200)
            elif selected_hospital:
                selected_hospital_data = st.session_state['hospital_data'][st.session_state['hospital_data']['병원명'] == selected_hospital]
                st.dataframe(selected_hospital_data[['병원명', '소재지', '전화번호', '거리']].reset_index(drop=True), width=700, height=200)
            else:
                sorted_filtered_data = filtered_hospital_data.sort_values(by='거리')
                st.dataframe(sorted_filtered_data[['병원명', '소재지', '전화번호', '거리']].reset_index(drop=True), width=700, height=200)

        # 선택한 병원의 마커만 지도에 표시
        if selected_hospital:
            selected_hospital_data = st.session_state['hospital_data'][st.session_state['hospital_data']['병원명'] == selected_hospital]
            m = create_map([selected_hospital_data['좌표(Y)'].values[0], selected_hospital_data['좌표(X)'].values[0]])
            add_hospital_markers(m, selected_hospital_data)
        else:
            m = create_map(st.session_state['current_location'])
            if close_distance or medium_distance or all_distance:
                add_hospital_markers(m, filtered_hospital_data)

        st_folium(m, width=700, height=400)

##################################### My Record ########################################
    if selected == "내 기록":
        col1, col2, col3 = st.columns(3)
        col1.metric("수축기 혈압", "125 mmHg", "-1.2 mmHg")
        col2.metric("이완기 혈압", "83 mmHg", "-1.0 mmHg")
        col3.metric("몸무게", "72 kg", "-1.5 kg")

        st.subheader("내 건강관리 캘린더")
        mode = st.selectbox(
            "Calendar Mode:",
            (
                "daygrid",
                "list",
            ),
        )
        events = [
            {
                "title": "출석 체크",
                "color": "#ADD8E6",
                "start": "2023-11-03",
                "end": "2023-11-03",
                "resourceId": "a",
            },
            {
                "title": "출석 체크",
                "color": "#ADD8E6",
                "start": "2023-11-02",
                "end": "2023-11-02",
                "resourceId": "b",
            },
            {
                "title": "출석 체크",
                "color": "#ADD8E6",
                "start": "2023-11-21",
                "end": "2023-11-21",
                "resourceId": "c",
            },
            {
                "title": "출석 체크",
                "color": "#ADD8E6",
                "start": "2023-11-23",
                "end": "2023-11-23",
                "resourceId": "d",
            },
            {
                "title": "출석 체크",
                "color": "#ADD8E6",
                "start": "2023-11-29",
                "end": "2023-11-29",
                "resourceId": "e",
            },
            {
                "title": "출석 체크",
                "color": "#ADD8E6",
                "start": "2023-11-17",
                "end": "2023-11-17",
                "resourceId": "f",
            },
            {
                "title": "출석 체크",
                "color": "#ADD8E6",
                "start": "2023-11-01",
                "end": "2023-11-01",
                "resourceId": "a",
            },
            {
                "title": "건강한 식습관 유지 성공",
                "color": "#3D9DF3",
                "start": "2023-11-01T07:30:00",
                "end": "2023-11-01T10:30:00",
                "resourceId": "b",
            },
            {
                "title": "운동하기",
                "color": "#3DD56D",
                "start": "2023-11-02T10:40:00",
                "end": "2023-11-02T12:30:00",
                "resourceId": "c",
            },
            {
                "title": "운동하기",
                "color": "#FF4B4B",
                "start": "2023-11-03T08:30:00",
                "end": "2023-11-03T10:30:00",
                "resourceId": "d",
            },
            {
                "title": "일어나서 물 마시기",
                "color": "#3DD56D",
                "start": "2023-11-21T07:30:00",
                "end": "2023-11-21T10:30:00",
                "resourceId": "e",
            },
            {
                "title": "운동하기",
                "color": "#3D9DF3",
                "start": "2023-11-23T10:40:00",
                "end": "2023-11-23T12:30:00",
                "resourceId": "f",
            },
            {
                "title": "건강한 식습관 유지 성공",
                "color": "#FF4B4B",
                "start": "2023-11-17T08:30:00",
                "end": "2023-11-17T10:30:00",
                "resourceId": "a",
            },
            {
                "title": "일어나서 물 마시기",
                "color": "#3D9DF3",
                "start": "2023-11-29T09:30:00",
                "end": "2023-11-29T11:30:00",
                "resourceId": "b",
            },
            {
                "title": "운동하기",
                "color": "#3DD56D",
                "start": "2023-11-17T10:30:00",
                "end": "2023-11-17T12:30:00",
                "resourceId": "c",
            },
            {
                "title": "건강한 식습관 가지기",
                "color": "#FF6C6C",
                "start": "2023-11-29T13:30:00",
                "end": "2023-11-29T14:30:00",
                "resourceId": "d",
            }
        ]
        calendar_resources = [
            {"id": "a", "building": "Building A", "title": "Room A"},
            {"id": "b", "building": "Building A", "title": "Room B"},
            {"id": "c", "building": "Building B", "title": "Room C"},
            {"id": "d", "building": "Building B", "title": "Room D"},
            {"id": "e", "building": "Building C", "title": "Room E"},
            {"id": "f", "building": "Building C", "title": "Room F"},
        ]

        calendar_options = {
            "editable": "true",
            "navLinks": "true",
            "resources": calendar_resources,
        }

        if mode == "daygrid":
            calendar_options = {
                **calendar_options,
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "dayGridDay,dayGridWeek,dayGridMonth",
                },
                "initialDate": "2023-07-01",
                "initialView": "dayGridMonth",
            }
        elif mode == "list":
            calendar_options = {
                **calendar_options,
                "initialDate": "2023-07-01",
                "initialView": "listMonth",
            }

        state = calendar(
            events=st.session_state.get("events", events),
            options=calendar_options,
            custom_css="""
            .fc-event-past {
                opacity: 0.8;
            }
            .fc-event-time {
                font-style: italic;
            }
            .fc-event-title {
                font-weight: 700;
            }
            .fc-toolbar-title {
                font-size: 2rem;
            }
            """,
            key=mode,
        )

        if state.get("eventsSet") is not None:
            st.session_state["events"] = state["eventsSet"]


        st.subheader("내 병원 진료기록")
        df = pd.read_excel('data/past_data.xlsx')
        id = use_username()
        patient_df = df[df['username']==id].reset_index(drop=True)
        st.table(patient_df)

        

    

#화면 전환 로직
if st.session_state['logged_in']:
    render_main_page()
else:
    render_login_page()

# if __name__ == '__main__':
#   render_main_page()
