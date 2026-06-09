import streamlit as st
import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 1. 환경 설정 및 API 키 로드
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(page_title="초보자용 파이썬 디버거", layout="wide")

# 세션 상태(Session State) 초기화
# 디버깅 데이터와 현재 실행 중인 라인(단계)을 기억하기 위해 사용합니다.
if "debug_data" not in st.session_state:
    st.session_state.debug_data = None
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "code_review" not in st.session_state:
    st.session_state.code_review = None

st.title("👨‍🏫 비전공자를 위한 AI 파이썬 디버거")

# ==========================================
# [상단 영역] 코드 입력 및 전체 리뷰 창 (50:50 분할)
# ==========================================
top_col1, top_col2 = st.columns(2)

with top_col1:
    st.subheader("1. 코드 입력")

    # 파일 드래그 앤 드롭 및 업로드 지원
    uploaded_file = st.file_uploader("파이썬 파일(.py)을 업로드하거나 드래그 앤 드롭하세요.", type=["py", "txt"])

    default_code = ""
    if uploaded_file is not None:
        # 업로드된 파일의 내용을 읽어서 텍스트로 변환
        default_code = uploaded_file.getvalue().decode("utf-8")

    # 코드 입력 창 (업로드된 파일 내용이 자동으로 채워짐)
    code_input = st.text_area("여기에 코드를 입력하거나 수정하세요:", value=default_code, height=200)

with top_col2:
    st.subheader("📝 전체 코드 간단 리뷰")
    
    # 리뷰 버튼
    if st.button("💡 전체 코드 리뷰하기"):
        if code_input.strip():
            with st.spinner("코드를 전체적으로 훑어보는 중입니다..."):
                llm = ChatOpenAI(model="gpt-4o", temperature=0)
                review_prompt = """
                너는 친절한 파이썬 튜터야. 
                비전공자 초보자가 이해할 수 있도록, 입력된 파이썬 코드가 전체적으로 어떤 역할을 하는지,
                잘 짠 부분이나 개선 및 주의할 점은 없는지 3~4문장으로 아주 쉽고 간단하게 요약해서 리뷰해줘.
                """
                response = llm.invoke([
                    SystemMessage(content=review_prompt),
                    HumanMessage(content=code_input)
                ])
                st.session_state.code_review = response.content
        else:
            st.warning("먼저 왼쪽 창에 코드를 입력해 주세요.")
    
    # 리뷰 결과 출력 영역
    if st.session_state.code_review:
        st.info(st.session_state.code_review)
    else:
        st.write("버튼을 눌러 전체 코드에 대한 간단한 리뷰를 확인하세요.")

# ==========================================
# [중간 영역] 분석 실행 버튼
# ==========================================
if st.button("🚀 분석 및 디버깅 시작", type="primary"):
    if code_input.strip():
        with st.spinner("AI가 코드를 라인별로 분석하고 있습니다... 잠시만 기다려주세요."):
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            
            # LLM에게 JSON 형식으로 응답하도록 프롬프트 작성
            system_prompt = """
            너는 비전공자에게 파이썬 코드를 친절하게 설명하는 디버거야.
            사용자가 입력한 코드를 라인별로 분석해서 반드시 아래 JSON 배열 형식으로만 응답해.
            [
                {
                    "line": "실제 코드 한 줄",
                    "explanation": "이 라인이 무엇을 하는지 초보자 눈높이의 쉬운 설명",
                    "variables": {"변수명": "현재 값"} 
                }
            ]
            * 변수 상태는 해당 라인이 실행되었을 때 메모리에 등록된 상태를 추적해서 작성해줘.
            * 마크다운 백틱(```json)을 포함하지 말고 순수 JSON 문자열만 반환해.
            """
            
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=code_input)
            ])
            
            try:
                # LLM 응답에서 마크다운 포맷(```json 등) 제거 후 JSON 파싱
                raw_content = response.content.strip()
                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:-3].strip()
                elif raw_content.startswith("```"):
                    raw_content = raw_content[3:-3].strip()
                    
                st.session_state.debug_data = json.loads(raw_content)
                st.session_state.current_step = 0 # 디버깅 단계를 0(첫 번째 줄)으로 초기화
            except Exception as e:
                st.error(f"코드 분석 중 오류가 발생했습니다. (오류: {e})\n코드를 조금 더 명확하게 작성해 주세요.")
    else:
        st.warning("코드를 입력해 주세요.")

st.divider()

# ==========================================
# [하단 영역] 코드 리뷰 및 디버깅 창
# ==========================================
st.subheader("2. 코드 리뷰 및 디버깅 창")

# 분석된 데이터가 있을 경우에만 하단 UI 표시
if st.session_state.debug_data:
    data = st.session_state.debug_data
    step = st.session_state.current_step
    
    col1, col2 = st.columns([1.5, 1]) # 왼쪽 코드창을 조금 더 넓게 배치
    
    # [왼쪽] 코드 뷰어 (현재 라인 하이라이트)
    with col1:
        st.markdown("#### 💻 코드 실행 흐름")
        
        # HTML/CSS를 사용하여 코드 에디터 스타일(어두운 배경) 구현
        code_html = "<div style='background-color: #282c34; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 15px; line-height: 1.6; color: #abb2bf;'>"
        
        for i, item in enumerate(data):
            # HTML 태그가 깨지지 않도록 <, > 괄호 치환
            safe_line = item['line'].replace('<', '&lt;').replace('>', '&gt;')
            
            if i == step:
                # 현재 단계(Step)와 일치하는 라인에 노란색 백그라운드 적용
                code_html += f"<div style='background-color: #FFEB3B; color: #000000; padding: 2px 8px; border-radius: 4px; font-weight: bold;'>{safe_line}</div>"
            else:
                # 일반 코드 라인
                code_html += f"<div style='padding: 2px 8px;'>{safe_line}</div>"
                
        code_html += "</div>"
        
        # HTML 렌더링
        st.markdown(code_html, unsafe_allow_html=True)
        
        st.write("") # 여백
        
        # 단계별 디버깅 이동 버튼
        if st.button("⏭️ 다음 라인으로 (단계별 디버깅)", type="primary"):
            if st.session_state.current_step < len(data) - 1:
                st.session_state.current_step += 1
                st.rerun() # 화면 즉시 새로고침
            else:
                st.success("🎉 코드의 마지막 줄까지 실행을 완료했습니다!")

    # [오른쪽] 변수 값 표시 창 및 AI 설명
    with col2:
        st.markdown("#### 📊 현재 변수 상태 및 설명")
        current_info = data[step]
        
        # 1. 튜터의 설명
        st.info(f"**💡 AI 튜터:**\n\n{current_info.get('explanation', '설명 없음')}")
        
        # 2. 변수 값 표시 영역
        st.markdown("**📦 사용 중인 변수 값:**")
        variables = current_info.get('variables', {})
        
        if variables:
            # 변수가 존재할 경우 "변수명 : 값" (예: abc : 123) 형태로 표시
            for var_name, var_value in variables.items():
                st.success(f"**{var_name}** : `{var_value}`")
        else:
            st.write("해당 라인에서 새롭게 등록되거나 변경된 변수가 없습니다.")
            
        # 진행률 바 표시
        st.progress((step + 1) / len(data))
        st.caption(f"전체 {len(data)} 라인 중 {step + 1} 번째 라인 실행 중")