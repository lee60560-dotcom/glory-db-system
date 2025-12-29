import streamlit as st
import pandas as pd
import os
from datetime import datetime

# [설정] 화면 전체를 넓게 사용
st.set_page_config(layout="wide", page_title="글로리지점 DB분배 시스템")

# 1. 사용자 정보 및 권한 설정
USERS = {
    "김주용": {"pw": "1129", "role": "admin"},
    "이지호": {"pw": "0830", "role": "admin"},
    "배재민": {"pw": "0116", "role": "user"},
    "김호람": {"pw": "0403", "role": "user"},
    "김동성": {"pw": "0917", "role": "user"},
    "홍기웅": {"pw": "0212", "role": "user"},
}

REQUIRED_COLUMNS = ["담당자", "이름", "휴대전화", "성별", "문의내용"]

# 2. 로그인 세션 관리
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- [로그인 화면] ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1, 1, 1])
    with center_col:
        for _ in range(5): st.write("")
        st.markdown("<h1 style='text-align: center; color: #FF8C00;'>🛡️ 글로리지점 DB분배</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>연도별/월별 통합 관리 시스템</p>", unsafe_allow_html=True)
        st.write("---")
        user_id = st.text_input("아이디 (성함)")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인", use_container_width=True, type="primary"):
            if user_id in USERS and USERS[user_id]["pw"] == password:
                st.session_state.update({'logged_in': True, 'user_id': user_id, 'role': USERS[user_id]["role"]})
                st.rerun()
            else:
                st.error("입력하신 정보가 일치하지 않습니다.")

# --- [메인 화면] ---
else:
    # 사이드바 설정
    st.sidebar.title(f"👤 {st.session_state['user_id']}님")
    st.sidebar.info(f"권한: {'관리자' if st.session_state['role'] == 'admin' else '설계사'}")
    
    # [추가] 연도 및 월 선택 필터 (사이드바)
    st.sidebar.write("---")
    st.sidebar.subheader("📅 조회 기간 선택")
    current_year = datetime.now().year
    selected_year = st.sidebar.selectbox("연도 선택", [2024, 2025, 2026, 2027], index=1) # 2025년 기본 선택
    selected_month = st.sidebar.selectbox("월 선택", [f"{i}월" for i in range(1, 13)], index=datetime.now().month - 1)
    
    # 파일명 규약: db_2025_1월.csv
    DB_FILE = f"db_{selected_year}_{selected_month}.csv"

    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.title(f"📋 {selected_year}년 {selected_month} 고객 DB 현황")

    # [관리자 전용]: 데이터 업로드
    if st.session_state['role'] == "admin":
        with st.expander(f"📤 {selected_year}년 {selected_month} 신규 DB 업로드", expanded=False):
            st.write(f"현재 **{selected_year}년 {selected_month}** 폴더에 저장됩니다. 기간을 확인해 주세요.")
            uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요.", type=["xlsx", "xls"])
            if uploaded_file:
                try:
                    df_raw = pd.read_excel(uploaded_file)
                    if "휴대전화" not in df_raw.columns and "전화번호" in df_raw.columns:
                        df_raw = df_raw.rename(columns={"전화번호": "휴대전화"})

                    missing = [c for c in REQUIRED_COLUMNS if c not in df_raw.columns]
                    if missing:
                        st.error(f"⚠️ 엑셀에 다음 항목이 없습니다: {', '.join(missing)}")
                    else:
                        df_final = df_raw[REQUIRED_COLUMNS]
                        df_final.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
                        st.success(f"✅ {selected_year}년 {selected_month} DB가 저장되었습니다!")
                        st.rerun()
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    # [데이터 표시 영역]
    st.divider()
    if os.path.exists(DB_FILE):
        try:
            df_master = pd.read_csv(DB_FILE)
            
            if st.session_state['role'] == "admin":
                st.subheader(f"🔍 {selected_year}년 {selected_month} 전체 리스트")
                display_df = df_master
            else:
                st.subheader(f"📂 {st.session_state['user_id']}님 배정 DB ({selected_year}년 {selected_month})")
                display_df = df_master[df_master["담당자"] == st.session_state['user_id']]

            if not display_df.empty:
                st.dataframe(display_df, use_container_width=True, height=500)
                st.caption(f"총 {len(display_df)}건의 데이터가 조회되었습니다.")
                
                # [관리자용 추가 기능] 현재 조회 중인 월별 데이터 다운로드
                if st.session_state['role'] == "admin":
                    csv = display_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(label="📥 현재 시트 엑셀 다운로드", data=csv, file_name=f"Glory_{DB_FILE}", mime='text/csv')
            else:
                st.info(f"{selected_year}년 {selected_month}에 배정된 데이터가 없습니다.")
        except Exception as e:
            st.error(f"데이터 로드 오류: {e}")
    else:
        st.warning(f"⚠️ {selected_year}년 {selected_month}에 등록된 데이터 파일이 없습니다.")