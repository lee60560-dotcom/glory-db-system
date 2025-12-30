import streamlit as st
import pandas as pd
import os
from datetime import datetime

# [설정] 화면 전체를 넓게 사용하며 타이틀 설정
st.set_page_config(layout="wide", page_title="글로리지점 DB분배 시스템")

# 파일 경로 및 상수 설정
USER_FILE = "users.csv"
REQUIRED_COLUMNS = ["담당자", "이름", "휴대전화", "성별", "문의내용"]
RECORD_COLUMNS = ["상태", "메모", "업데이트날짜"]

# 상태별 컬러 이모지 정의 (시각적 구분)
STATUS_OPTIONS = {
    "⚪ 미처리": "미처리",
    "🔴 거절": "거절",
    "🟡 부재": "부재",
    "🔵 상담진행": "상담진행",
    "🟢 완료": "완료"
}

# 1. 사용자 정보 로드 및 저장 함수
def load_users():
    initial_users = {
        "김주용": {"pw": "1129", "role": "admin"},
        "이지호": {"pw": "0830", "role": "admin"},
        "배재민": {"pw": "0116", "role": "user"},
        "김호람": {"pw": "0403", "role": "user"},
        "김동성": {"pw": "0917", "role": "user"},
        "홍기웅": {"pw": "0212", "role": "user"},
    }
    if os.path.exists(USER_FILE):
        try:
            df = pd.read_csv(USER_FILE, dtype={'pw': str})
            return df.set_index('id').to_dict('index')
        except:
            return initial_users
    else:
        df = pd.DataFrame.from_dict(initial_users, orient='index').reset_index().rename(columns={'index': 'id'})
        df.to_csv(USER_FILE, index=False, encoding='utf-8-sig')
        return initial_users

def save_users(users_dict):
    df = pd.DataFrame.from_dict(users_dict, orient='index').reset_index().rename(columns={'index': 'id'})
    df.to_csv(USER_FILE, index=False, encoding='utf-8-sig')

# 시스템 시작 시 데이터 로드
USERS = load_users()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'show_confirm' not in st.session_state:
    st.session_state['show_confirm'] = False

# --- [로그인 화면] ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1, 1, 1])
    with center_col:
        for _ in range(5): st.write("")
        st.markdown("<h1 style='text-align: center; color: #FF8C00;'>🛡️ 글로리지점 DB분배</h1>", unsafe_allow_html=True)
        st.write("---")
        user_id = st.text_input("아이디 (성함)")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인", use_container_width=True, type="primary"):
            if user_id in USERS and str(USERS[user_id]["pw"]).strip() == str(password).strip():
                st.session_state.update({'logged_in': True, 'user_id': user_id, 'role': USERS[user_id]["role"]})
                st.rerun()
            else:
                st.error("정보가 일치하지 않습니다.")

# --- [메인 화면] ---
else:
    st.sidebar.title(f"👤 {st.session_state['user_id']}님")
    
    # [비밀번호 변경]
    with st.sidebar.expander("🔑 비밀번호 변경"):
        old_pw = st.text_input("현재 비밀번호", type="password")
        new_pw = st.text_input("새 비밀번호", type="password")
        if st.button("변경 완료"):
            if str(USERS[st.session_state['user_id']]["pw"]).strip() == str(old_pw).strip():
                USERS[st.session_state['user_id']]["pw"] = str(new_pw).strip()
                save_users(USERS)
                st.success("변경되었습니다! 다시 로그인하세요.")
                st.session_state.clear()
                st.rerun()
            else:
                st.error("현재 비밀번호가 틀립니다.")

    # 연도/월 선택
    st.sidebar.write("---")
    selected_year = st.sidebar.selectbox("연도", [2024, 2025, 2026, 2027], index=1)
    selected_month = st.sidebar.selectbox("월", [f"{i}월" for i in range(1, 13)], index=datetime.now().month - 1)
    DB_FILE = f"db_{selected_year}_{selected_month}.csv"

    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.title(f"📋 {selected_year}년 {selected_month} DB 관리")

    # [관리자 전용 업로드/삭제]
    if st.session_state['role'] == "admin":
        col1, col2 = st.columns([4, 1])
        with col1:
            with st.expander("📤 엑셀 업로드"):
                uploaded_file = st.file_uploader("파일 선택", type=["xlsx", "xls"])
                if uploaded_file:
                    df_raw = pd.read_excel(uploaded_file)
                    df_final = df_raw[REQUIRED_COLUMNS].copy()
                    df_final["상태"] = "⚪ 미처리" # 초기 상태에 이모지 포함
                    df_final["메모"] = ""
                    df_final["업데이트날짜"] = ""
                    df_final.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
                    st.success("업로드 완료!")
                    st.rerun()
        with col2:
            if os.path.exists(DB_FILE):
                if not st.session_state['show_confirm']:
                    if st.button("🗑️ DB 삭제"): st.session_state['show_confirm'] = True; st.rerun()
                else:
                    if st.button("✅ 진짜 삭제", type="primary"): 
                        os.remove(DB_FILE); st.session_state['show_confirm'] = False; st.rerun()
                    if st.button("❌ 취소"): st.session_state['show_confirm'] = False; st.rerun()

    # [데이터 표시 및 필터링]
    st.divider()
    if os.path.exists(DB_FILE):
        df_master = pd.read_csv(DB_FILE).fillna("")
        
        # 권한 필터링
        if st.session_state['role'] == "admin":
            work_df = df_master
        else:
            work_df = df_master[df_master["담당자"] == st.session_state['user_id']]

        # [기능 추가] 상태별 필터링 (완료 고객 모아보기 등)
        st.subheader("🔍 상담 데이터 필터링")
        filter_col1, filter_col2 = st.columns([1, 3])
        with filter_col1:
            status_filter = st.selectbox("상태별 모아보기", ["전체보기", "⚪ 미처리", "🔴 거절", "🟡 부재", "🔵 상담진행", "🟢 완료"])
        
        display_df = work_df if status_filter == "전체보기" else work_df[work_df["상태"] == status_filter]

        if not display_df.empty:
            st.info(f"💡 총 {len(display_df)}건이 조회되었습니다. 상태와 메모를 수정한 후 반드시 아래 [저장하기]를 눌러주세요.")
            
            # [기능 추가] 데이터 에디터 (컬러 이모지 적용)
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                height=500,
                disabled=["담당자", "이름", "휴대전화", "성별", "문의내용", "업데이트날짜"],
                column_config={
                    "상태": st.column_config.SelectboxColumn(
                        "상태 (색상구분)",
                        options=list(STATUS_OPTIONS.keys()),
                        required=True,
                    ),
                    "메모": st.column_config.TextColumn("메모", width="large"),
                    "업데이트날짜": st.column_config.TextColumn("최종 수정 시간")
                },
                hide_index=True,
            )

            # [저장 로직]
            if st.button("💾 변경사항 및 날짜 저장하기", use_container_width=True, type="primary"):
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # 수정한 내용을 원본 마스터 DB에 반영
                for index, row in edited_df.iterrows():
                    # 마스터 DB에서 해당 고객(휴대전화 기준)을 찾아 업데이트
                    mask = (df_master["이름"] == row["이름"]) & (df_master["휴대전화"] == row["휴대전화"])
                    if (df_master.loc[mask, "상태"].values[0] != row["상태"]) or (df_master.loc[mask, "메모"].values[0] != row["메모"]):
                        df_master.loc[mask, "상태"] = row["상태"]
                        df_master.loc[mask, "메모"] = row["메모"]
                        df_master.loc[mask, "업데이트날짜"] = current_time
                
                df_master.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
                st.success(f"✅ 상담 기록이 저장되었습니다! ({current_time})")
                st.rerun()
        else:
            st.info("조건에 맞는 데이터가 없습니다.")
    else:
        st.warning("등록된 데이터가 없습니다.")
