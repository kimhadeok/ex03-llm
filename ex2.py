import streamlit as st
import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 환경 설정 및 API 키 로드
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(page_title="초보자용 파이썬 디버거", layout="wide")

# 세션 상태(Session State) 초기화
if "debug_data" not in st.session_state:
    st.session_state.debug_data = None
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "code_review" not in st.session_state:
    st.session_state.code_review = None

st.title("👨‍🏫 비전공자를 위한 AI 파이썬 디버거")
st.caption("코드를 작성하면 AI 튜터가 전체 리뷰와 단계별 디버깅(변수 추적)을 도와줍니다.")
st.write("---")

# ==========================================
# [상단 영역] 코드 입력 및 전체 리뷰 창 (50:50 분할)
# ==========================================
col_input, col_review = st.columns(2, gap="large")

with col_input:
    st.subheader("💻 코드 입력 및 편집")
    
    # 파일 업로드
    uploaded_file = st.file_uploader("파이썬 파일(.py) 업로드 (드래그 앤 드롭 가능)", type=["py", "txt"])
    
    default_code = ""
    if uploaded_file is not None:
        default_code = uploaded_file.getvalue().decode("utf-8")
        
    # 코드 입력 창
    code_input = st.text_area("여기에 코드를 입력하거나 수정하세요:", value=default_code, height=250)
    
    # 통합 분석 버튼
    analyze_clicked = st.button("🚀 AI 분석 및 디버깅 실행", type="primary", use_container_width=True)

with col_review:
    st.subheader("📝 종합 코드 리뷰")
    
    # 분석 버튼이 클릭되었을 때 두 가지(리뷰, 디버깅) 작업을 순차적으로 실행
    if analyze_clicked:
        if code_input.strip():
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            
            # 1. 종합 코드 리뷰 생성
            with st.spinner("🔍 코드를 전체적으로 분석하며 리뷰를 작성 중입니다... (1/2)"):
                review_prompt = """
                너는 친절하고 긍정적인 파이썬 튜터야.
                비전공자 초보자가 코드를 완벽하게 이해할 수 있도록, 입력된 코드를 다음 4가지 항목으로 나누어 상세하고 풍성하게 리뷰해줘.
                어려운 전문 용어는 피하고 쉬운 비유를 사용해.
                
                ### 🎯 코드의 목적
                (이 코드가 전체적으로 어떤 작업을 수행하는지 설명)
                
                ### ✨ 칭찬할 점
                (초보자 입장에서 잘 적용한 파이썬 문법이나 흐름을 칭찬)
                
                ### 💡 개선 팁 및 주의사항
                (더 좋은 코드를 위한 조언이나, 에러가 발생할 수 있는 주의점 설명)
                
                ### 📚 사용된 핵심 개념
                (이 코드에 사용된 파이썬 핵심 문법 1~2가지 간단 설명)
                """
                review_response = llm.invoke([
                    SystemMessage(content=review_prompt),
                    HumanMessage(content=code_input)
                ])
                st.session_state.code_review = review_response.content
                
            # 2. 단계별 디버깅 데이터 생성
            with st.spinner("🐞 단계별 변수 추적 데이터를 생성 중입니다... (2/2)"):
                system_prompt = """
                너는 비전공자에게 파이썬 코드를 친절하게 설명하는 디버거야.
                사용자가 입력한 코드를 라인별로 분석해서 반드시 아래 JSON 배열 형식으로만 응답해.
                [
                    {
                        "line": "실제 코드 한 줄",
                        "explanation": "이 라인이 무엇을 하는지 초보자 눈높이의 쉬운 설명",
                        "variables": {"변수명": "현재 값"},
                        "error": "이 라인에서 문법 또는 실행 오류가 발생할 것으로 예상되면 초보자가 이해하기 쉬운 말로 원인을 작성해. (오류가 없으면 null 또는 빈 문자열)"
                    }
                ]
                * 변수 상태는 해당 라인이 실행되었을 때 메모리에 등록된 상태를 추적해서 작성해.
                * 오류가 예상되는 라인 이후에도 분석을 계속하되, 변수 값 추적이 어렵다면 비워두어도 좋아.
                * 마크다운 백틱(\`\`\`json)을 포함하지 말고 순수 JSON 문자열만 반환해.
                """
                debug_response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=code_input)
                ])
                
                try:
                    raw_content = debug_response.content.strip()
                    if raw_content.startswith("```json"):
                        raw_content = raw_content[7:-3].strip()
                    elif raw_content.startswith("```"):
                        raw_content = raw_content[3:-3].strip()
                        
                    st.session_state.debug_data = json.loads(raw_content)
                    st.session_state.current_step = 0
                except Exception as e:
                    st.error(f"디버깅 분석 중 오류가 발생했습니다: {e}")
                    st.session_state.debug_data = None
                    
        else:
            st.warning("왼쪽 창에 코드를 먼저 입력해 주세요.")
            
    # 리뷰 결과 출력 영역
    if st.session_state.code_review:
        with st.container(height=350, border=True):
            st.markdown(st.session_state.code_review)
    else:
        with st.container(height=350, border=True):
            st.info("👈 코드를 입력하고 **'AI 분석 및 디버깅 실행'** 버튼을 누르면,\n이곳에 상세한 종합 리뷰가 표시됩니다.")

st.divider()

# ==========================================
# [하단 영역] 코드 리뷰 및 디버깅 창
# ==========================================
st.subheader("🐞 단계별 디버깅 창")
st.caption("버튼을 눌러 코드가 한 줄씩 실행될 때마다 변수 값이 어떻게 변하는지 확인해 보세요.")

if st.session_state.debug_data:
    data = st.session_state.debug_data
    step = st.session_state.current_step
    
    debug_col1, debug_col2 = st.columns([1.5, 1])
    
    # [왼쪽] 코드 실행 흐름 (하이라이트 뷰어)
    with debug_col1:
        st.markdown("##### 💻 실시간 코드 흐름")
        
        # HTML/CSS를 사용하여 코드 에디터 스타일 구현
        code_html = "<div style='background-color: #282c34; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 15px; line-height: 1.6; color: #abb2bf;'>"
        
        for i, item in enumerate(data):
            safe_line = item['line'].replace('<', '&lt;').replace('>', '&gt;')
            
            if i == step:
                # 현재 단계 노란색 하이라이트 (오류가 있을 경우 빨간색 하이라이트)
                if item.get("error"):
                    code_html += f"<div style='background-color: #FFCDD2; color: #B71C1C; padding: 2px 8px; border-radius: 4px; font-weight: bold;'>{safe_line}</div>"
                else:
                    code_html += f"<div style='background-color: #FFEB3B; color: #000000; padding: 2px 8px; border-radius: 4px; font-weight: bold;'>{safe_line}</div>"
            else:
                code_html += f"<div style='padding: 2px 8px;'>{safe_line}</div>"
                
        code_html += "</div>"
        st.markdown(code_html, unsafe_allow_html=True)
        
        st.write("") # 여백
        
        # 단계 이동 버튼
        if st.button("⏭️ 다음 라인으로 (단계별 진행)", type="primary"):
            if st.session_state.current_step < len(data) - 1:
                st.session_state.current_step += 1
                st.rerun()
            else:
                st.success("🎉 코드의 마지막 줄까지 실행을 완료했습니다!")

    # [오른쪽] 변수 값 표시 및 AI 설명
    with debug_col2:
        st.markdown("##### 📊 현재 상태 및 설명")
        current_info = data[step]
        
        # AI 튜터 설명 또는 오류 경고창 표시
        error_msg = current_info.get('error')
        if error_msg:
            st.error(f"**🚨 앗, 이 코드에서 오류가 예상돼요!**\n\n{error_msg}")
        else:
            st.info(f"**💡 AI 튜터:**\n\n{current_info.get('explanation', '설명 없음')}")
        
        # 변수 상태 표시
        st.markdown("**📦 사용 중인 변수 값:**")
        variables = current_info.get('variables', {})
        
        if variables:
            for var_name, var_value in variables.items():
                st.success(f"**{var_name}** : `{var_value}`")
        else:
            st.write("해당 라인에서 변경된 변수가 없습니다.")
            
        # 진행률 바
        st.progress((step + 1) / len(data))
        st.caption(f"전체 {len(data)} 라인 중 {step + 1} 번째 라인 실행 중")
else:
    st.write("분석을 실행하면 여기에 단계별 디버깅 화면이 나타납니다.")