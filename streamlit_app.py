import streamlit as st
import random
import time
import datetime
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from pytz import timezone
import json

# ✅ 구글 시트 연결
@st.cache_resource
def connect_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    json_key = json.loads(st.secrets["google_sheets"]["service_account"])
    sheet_id = st.secrets["google_sheets"]["sheet_id"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

# ✅ 문제 정의
basic_deriv = [
    ("\\frac{d}{dx}\\left( \\sin x \\right)", "cos x", ["cos x", "-cos x", "sin x", "-sin x"]),
    ("\\frac{d}{dx}\\left( \\ln x \\right)", "1/x", ["1/x", "ln x", "x", "x ln x"]),
    ("\\frac{d}{dx}\\left( e^x \\right)", "e^x", ["e^x", "x e^x", "ln x", "1/x"]),
    ("\\frac{d}{dx}\\left( x^5 \\right)", "5x^4", ["5x^4", "4x^5", "x^4", "5x^3"]),
    ("\\frac{d}{dx}\\left( \\sqrt{x} \\right)", "1/(2√x)", ["1/(2√x)", "√x", "1/x", "x²"]),
]
applied_deriv = [
    ("y = (3x² - 4x + 1)^5", "연쇄법칙", ["연쇄법칙", "곱의 법칙", "역함수 미분", "합의 법칙"]),
    ("x = t² + 1, y = t³ - t ⇒ dy/dx ?", "dy/dt ÷ dx/dt", ["dy/dt ÷ dx/dt", "dy * dx", "dy - dx", "dx/dt ÷ dy/dt"]),
    ("x² + y² = 25 ⇒ dy/dx ?", "-x/y", ["-x/y", "x/y", "2x + 2y", "1"]),
    ("y = √[3]{x+2}", "연쇄법칙 or 일반 미분", ["연쇄법칙", "역함수 미분", "적분", "상수함수"]),
    ("y = sin(2x² + 1)", "cos(u)·du/dx", ["cos(u)·du/dx", "sin(u)·du/dx", "cos x", "tan u"]),
]

# ✅ 세션 상태 초기화
defaults = {
    "nickname": None,
    "current_q": 0,
    "score": 0,
    "questions": None,
    "answered": False,
    "question_start_time": None,
    "times": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

sheet = connect_sheet()
import os
import random

# 🎉 앱 제목
st.title("🧠 미분법 공식 암기 게임")

# 🖼️ 랜덤 짤 표시
def show_random_image():
    image_folder = ".streamlit/images"
    supported_formats = (".jpg", ".jpeg", ".png", ".gif")

    images = [f for f in os.listdir(image_folder) if f.lower().endswith(supported_formats)]
    if images:
        selected = random.choice(images)
        st.image(os.path.join(image_folder, selected), width=500)

# 👋 간단한 설명
st.info("문제를 풀면서 미분 공식을 재미있게 익혀보세요!")

# 👤 닉네임 입력
st.subheader("닉네임 입력")
nickname = st.text_input("닉네임을 입력하세요 (최대 3자)", max_chars=3)

if nickname and len(nickname) <= 3:
    st.session_state.nickname = nickname
    st.rerun()
    show_random_image()

elif nickname:
    st.error("닉네임은 3자 이하로 입력해주세요.")
st.stop()




# # ✅ 닉네임 변경
# with st.sidebar:
#     st.write(f"👋 안녕하세요, **{st.session_state.nickname}** 님!")
#     if st.button("🔁 닉네임 변경하기"):
#         for key in list(st.session_state.keys()):
#             del st.session_state[key]
#         st.rerun()

# ✅ 문제 셔플
if st.session_state.questions is None:
    all_questions = basic_deriv + applied_deriv
    random.shuffle(all_questions)
    st.session_state.questions = all_questions

questions = st.session_state.questions

# ✅ 문제 풀이
if st.session_state.current_q < len(questions):
    q_num = st.session_state.current_q
    q = questions[q_num]

    st.markdown(f"### 문제 {q_num + 1} / {len(questions)}")
    st.progress(q_num / len(questions))
    st.latex(q[0])

    # 시간 기록 시작
    if st.session_state.question_start_time is None:
        st.session_state.question_start_time = time.time()

    # 보기 선택
    selected = st.radio(
        "정답을 고르세요:",
        q[2],
        index=None,
        key=f"q_{q_num}",
        disabled=st.session_state.answered
    )

    # 선택되면 채점
    if selected is not None and not st.session_state.answered:
        st.session_state.answered = True
        elapsed = time.time() - st.session_state.question_start_time
        st.session_state.times.append(elapsed)

        if selected == q[1]:
            st.session_state.score += 1
            st.success("✅ 정답입니다!")
        else:
            st.error(f"❌ 틀렸습니다. 정답은: **{q[1]}**")

    # 다음 문제 버튼
    if st.session_state.answered:
        if st.button("➡️ 다음 문제로"):
            st.session_state.current_q += 1
            st.session_state.answered = False
            st.session_state.question_start_time = None
            st.rerun()

# ✅ 게임 종료
else:
    total_elapsed = sum(st.session_state.times)
    st.success(f"🎉 게임 완료! 총 점수: {st.session_state.score} / {len(questions)}")
    st.info(f"🕒 총 소요 시간: {total_elapsed:.2f}초 (풀이 시간만 측정)")

    now = datetime.datetime.now(timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([
        st.session_state.nickname,
        st.session_state.score,
        round(total_elapsed, 2),
        now
    ])
    st.balloons()

    # ✅ 랭킹 표시
    df = pd.DataFrame(sheet.get_all_records())
    df['걸린시간'] = pd.to_numeric(df['걸린시간'], errors='coerce')
    df_best = df.sort_values(by=['점수', '걸린시간'], ascending=[False, True])
    df_best = df_best.groupby('닉네임', as_index=False).first()
    ranking = df_best.sort_values(by=['점수', '걸린시간'], ascending=[False, True]).head(10)

    st.subheader("🏆 랭킹 Top 10")
    st.dataframe(ranking)

    if st.button("🔄 다시 시작하기"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
