import streamlit as st
import random
import time
import datetime
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from pytz import timezone
import json
import os
import numpy as np

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

sheet = connect_sheet()

# basic_deriv = [
#     ("\\frac{d}{dx}\\left( \\sin x \\right)", "cos x", ["cos x", "-cos x", "sin x", "-sin x"]),
#     ("\\frac{d}{dx}\\left( \\cos x \\right)", "-sin x", ["-sin x", "cos x", "-cos x", "sin x"]),
#     ("\\frac{d}{dx}\\left( \\tan x \\right)", "sec² x", ["sec² x", "sec x", "sin x", "tan x"]),
#     ("\\frac{d}{dx}\\left( \\sec x \\right)", "sec x tan x", ["sec x tan x", "sec x", "tan x", "cos x"]),
#     ("\\frac{d}{dx}\\left( \\ln x \\right)", "1/x", ["1/x", "ln x", "x", "x ln x"]),
#     ("\\frac{d}{dx}\\left( e^x \\right)", "e^x", ["e^x", "x e^x", "ln x", "1/x"]),
#     ("\\frac{d}{dx}\\left( x^5 \\right)", "5x^4", ["5x^4", "4x^5", "x^4", "5x^3"]),
#     ("\\frac{d}{dx}\\left( \\sqrt{x} \\right)", "1/(2√x)", ["1/(2√x)", "√x", "1/x", "x²"]),
#     ("\\frac{d}{dx}\\left( \\frac{1}{g(x)} \\right)", "-g'(x)/(g(x))²", ["-g'(x)/(g(x))²", "1/g(x)", "-1/g(x)", "g'(x)/g(x)"]),
#     ("\\frac{d}{dx}\\left( \\frac{f(x)}{g(x)} \\right)", "(f'(x)g(x) - f(x)g'(x)) / (g(x))²", [
#         "(f'(x)g(x) - f(x)g'(x)) / (g(x))²",
#         "(f'(x)g(x) + f(x)g'(x)) / (g(x))²",
#         "(f(x)g(x))' / (g(x))²",
#         "(f(x)/g(x))'"
#     ]),
# ]


# applied_deriv = [
#     ("y = (3x^2 - 4x + 1)^5", "\\frac{d}{dx}[(3x^2 - 4x + 1)^5] = 5(3x^2 - 4x + 1)^4 · (6x - 4)", [
#         "5(3x^2 - 4x + 1)^4 · (6x - 4)",
#         "5(3x^2 - 4x + 1)^5",
#         "(3x^2 - 4x + 1)^4",
#         "6x - 4"
#     ]),
#     ("y = \\sin(2x^2 + 1)", "\\cos(2x^2 + 1) · 4x", [
#         "\\cos(2x^2 + 1) · 4x",
#         "\\sin(2x^2 + 1) · 4x",
#         "2x · \\cos(x)",
#         "\\tan(2x^2 + 1)"
#     ]),
#     ("y = \\sqrt[3]{x+2}", "\\frac{1}{3\\sqrt[3]{(x+2)^2}}", [
#         "\\frac{1}{3\\sqrt[3]{(x+2)^2}}",
#         "\\frac{1}{2\\sqrt{x+2}}",
#         "\\sqrt[3]{x+2}",
#         "\\frac{d}{dx}(x+2)"
#     ]),
#     ("x = t^2 + 1, y = t^3 - t \\Rightarrow \\frac{dy}{dx} = ?", "\\frac{dy/dt}{dx/dt} = \\frac{3t^2 - 1}{2t}", [
#         "\\frac{3t^2 - 1}{2t}",
#         "3t^2 - 1",
#         "2t",
#         "\\frac{2t}{3t^2 - 1}"
#     ]),
#     ("x^2 + y^2 = 25 \\Rightarrow \\frac{dy}{dx} = ?", "-\\frac{x}{y}", [
#         "-\\frac{x}{y}",
#         "\\frac{x}{y}",
#         "2x + 2y",
#         "1"
#     ]),
# ]

import pandas as pd

def load_questions_from_sheet():
    try:
        # 구글 시트 연결
        client = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(st.secrets["google_sheets"]["service_account"]),
            ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        ))
        sheet_id = st.secrets["google_sheets"]["sheet_id"]

        # 시트 불러오기
        active_sheet = client.open_by_key(sheet_id).worksheet("active")
        question_sheet = client.open_by_key(sheet_id).worksheet("questions")

        # 활성화된 ID 가져오기
        active_data = active_sheet.get_all_records()
        active_ids = [row['id'].strip() for row in active_data if row.get('active', '').strip().lower() == 'on']

        # 문제 불러오기
        question_data = question_sheet.get_all_records()
        parsed_questions = []

        for row in question_data:
            if row.get("유형", "").strip() != "4지선다":
                continue

            question_id = row.get("id", "").strip()
            if question_id not in active_ids:
                continue

            question_text = row.get("문제", "").strip()
            options_raw = row.get("선지", "")
            hint = row.get("힌트", "").strip()
            question_type = row.get("문제유형", "").strip()

            try:
                options = eval(options_raw) if isinstance(options_raw, str) else options_raw
                if isinstance(options, list) and len(options) >= 2:
                    correct_answer = options[0]
                    parsed_questions.append({
                        "문제": question_text,
                        "정답": correct_answer,
                        "선지": options,
                        "힌트": hint,
                        "문제유형": question_type,
                        "ID": question_id
                    })
            except Exception as parse_error:
                st.warning(f"⚠️ 선지 파싱 실패: {question_text}")

        return pd.DataFrame(parsed_questions)

    except Exception as e:
        st.error(f"❌ 문제 불러오기 실패: {e}")
        return pd.DataFrame()  # 빈 DataFrame 반환


# ✅ 세션 초기화
defaults = {
    "nickname": None,
    "game_started": False,
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

# ✅ 랜덤 짤 출력
def show_random_image():
    image_folder = ".streamlit/images"
    supported_formats = (".jpg", ".jpeg", ".png", ".gif")
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(supported_formats)]
    if images:
        selected = random.choice(images)
        st.image(os.path.join(image_folder, selected), width=400)

# ✅ 대문 페이지 (닉네임 입력 + 게임 시작)
if not st.session_state.nickname or not st.session_state.game_started:
    st.title("🧠 미분법 공식 암기 게임")
    st.info("문제를 풀면서 미분 공식을 재미있게 익혀보세요!")


    st.subheader("👤 닉네임 입력")
    nickname = st.text_input("닉네임을 입력하세요 (최대 3자)", max_chars=3)
    show_random_image()

    if nickname:
        if len(nickname) > 3:
            st.error("닉네임은 3자 이하로 입력해주세요.")
        else:
            if st.button("🚀 게임 시작하기"):
                st.session_state.nickname = nickname
                st.session_state.game_started = True

                # 준비 메세지 출력
                with st.spinner("🎯 준비되셨나요? 게임을 시작합니다!"):
                    st.warning("⚠️ 한 번 제출한 정답은 변경할 수 없습니다!")
                    for i in reversed(range(1, 4)):
                        st.info(f"⏳ {i}...")
                        time.sleep(1)
                st.rerun()
    st.stop()

# ✅ 닉네임 변경 (사이드바)
with st.sidebar:
    st.write(f"👋 안녕하세요, **{st.session_state.nickname}** 님!")
    if st.button("🔁 닉네임 변경하기"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ✅ 문제 셔플
# if st.session_state.questions is None:
#     all_questions = basic_deriv + applied_deriv
#     random.shuffle(all_questions)
#     st.session_state.questions = all_questions
# ✅ 문제 셔플 (10문제 중 무작위 5개 추출)
if st.session_state.questions is None:
    df_questions = load_questions_from_sheet()

    if df_questions.empty:
        st.error("❌ 불러온 문제가 없습니다.")
        st.stop()

    # 문제유형별 분류
    basic_qs = df_questions[df_questions["문제유형"] == "기본공식"].to_dict("records")
    applied_qs = df_questions[df_questions["문제유형"] == "적용문제"].to_dict("records")

    # 랜덤 추출 (각 5개, 부족하면 있는 만큼만)
    selected_basic = random.sample(basic_qs, min(5, len(basic_qs)))
    selected_applied = random.sample(applied_qs, min(5, len(applied_qs)))

    # 합치고 셔플
    combined = selected_basic + selected_applied
    random.shuffle(combined)

    # 기존 튜플 형식으로 변환 (문제, 정답, 선지, 힌트)
    st.session_state.questions = [
        (q["문제"], q["정답"], q["선지"], q["힌트"]) for q in combined
    ]
questions = st.session_state.questions

# ✅ 문제 풀이
if st.session_state.current_q < len(questions):
    q_num = st.session_state.current_q
    q = questions[q_num]  # (문제, 정답, 선지, 힌트)

    st.markdown(f"### 문제 {q_num + 1} / {len(questions)}")
    st.progress(q_num / len(questions))
    st.latex(q[0])

    if st.session_state.question_start_time is None:
        st.session_state.question_start_time = time.time()

    # 👉 선지 섞기 (정답 포함) — 최초 1회만 섞이게
    if f"shuffled_choices_{q_num}" not in st.session_state:
        choices = q[2][:]
        random.shuffle(choices)
        st.session_state[f"shuffled_choices_{q_num}"] = choices
    else:
        choices = st.session_state[f"shuffled_choices_{q_num}"]

    # 👉 LaTeX 라벨과 실제 값 분리
    choice_labels = [f"${c}$" for c in choices]  # 수식 표현
    choice_mapping = {f"${c}$": c for c in choices}  # 라벨 → 값 매핑

    selected_label = st.radio(
        "정답을 고르세요:",
        choice_labels,
        index=None,
        key=f"q_{q_num}",
        disabled=st.session_state.answered
    )

    # 채점 처리
    if selected_label is not None and not st.session_state.answered:
        st.session_state.answered = True
        elapsed = time.time() - st.session_state.question_start_time
        st.session_state.times.append(elapsed)

        selected = choice_mapping[selected_label]  # 선택한 실제 값

        if selected == q[1]:
            st.session_state.score += 1
            st.success("✅ 정답입니다!")
        else:
            st.error(f"❌ 틀렸습니다. 정답은: **${q[1]}**")

    if st.session_state.answered:
        if st.button("➡️ 다음 문제로"):
            st.session_state.current_q += 1
            st.session_state.answered = False
            st.session_state.question_start_time = None
            st.rerun()
# ✅ 게임 종료
else:
    total_elapsed = sum(st.session_state.times)
    st.subheader(f"{st.session_state.nickname}님의 풀이 결과")
    st.success(f"🎉 게임 완료! 총 점수: {st.session_state.score} / {len(questions)}")
    st.info(f"🕒 총 소요 시간: {total_elapsed:.2f}초 (풀이 시간만 측정)")

    # ✅ 중복 기록 방지
    if 'score_saved' not in st.session_state:
        st.session_state.score_saved = False

    if not st.session_state.score_saved:
        now = datetime.datetime.now(timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([
            st.session_state.nickname,
            st.session_state.score,
            round(total_elapsed, 2),
            now
        ])
        st.session_state.score_saved = True  # 기록 완료 표시
        st.balloons()

    # ✅ 랭킹 등 이후 처리 동일
    df = pd.DataFrame(sheet.get_all_records())
    df['걸린시간'] = pd.to_numeric(df['걸린시간'], errors='coerce')
    if "기록시간" in df.columns:
        df['기록일'] = df['기록시간']
    else:
        df['기록일'] = ""

    df_best = df.sort_values(by=['점수', '걸린시간'], ascending=[False, True])
    df_best = df_best.groupby('닉네임', as_index=False).first()
    ranking = df_best.sort_values(by=['점수', '걸린시간'], ascending=[False, True]).head(10)

    rank_emojis = ["🥇", "🥈", "🥉"] + [f"{i+1}위" for i in range(3, 10)]
    styled_ranking = []
    for i, row in ranking.reset_index(drop=True).iterrows():
        styled_ranking.append({
            "순위": rank_emojis[i],
            "닉네임": f"**{row['닉네임']}**",
            "점수": f"{row['점수']}/10",
            "풀이시간": f"⏱ {row['걸린시간']}초",
            "기록일": row["기록일"]
        })

    st.markdown("## 🏆 랭킹 Top 10")
    st.markdown("**상위 랭커들을 소개합니다!**")
    st.table(pd.DataFrame(styled_ranking))
    st.success(f"현재까지 {df['닉네임'].nunique()}명이 총 {len(df['닉네임'])}회 도전했어요. 평균 시도 횟수: {np.round(len(df['닉네임'])/df['닉네임'].nunique(),2)}")

    if st.button("🔄 다시 시작하기"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()



# ✅ 제작자 정보 하단 고정
st.markdown("""
<style>
.footer {
    position: fixed;
    bottom: 10px;
    left: 0;
    width: 100%;
    padding: 10px 0;
    background-color: #f9f9f9;
    color: #444;
    text-align: center;
    font-size: 14px;
    border-top: 1px solid #e0e0e0;
    z-index: 999;
}
.footer a {
    text-decoration: none;
    color: #007acc;
    font-weight: bold;
}
</style>

<div class="footer">
    📌 Made by <strong>반포고 황수빈T</strong> | 문의: <a href="mailto:sbhath17@gmail.com">sbhath17@gmail.com</a>
</div>
""", unsafe_allow_html=True)
