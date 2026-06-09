import streamlit as st
from langchain_community.llms import CTransformers
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

@st.cache_resource
def get_llm():
    """Initializes and returns the CTransformers LLM."""
    return CTransformers(
        model="llama-2-7b-chat.ggmlv3.q2_K.bin",
        model_type="llama"
    )

st.title('인공지능 시인')

content = st.text_input('시의 주제를 제시해주세요.')

if st.button('시 작성 요청하기'):
    if not content:
        st.warning('시의 주제를 제시해주세요.')
    else:
        with st.spinner('시 작성 중...'):
            llm = get_llm()
            prompt = ChatPromptTemplate.from_template("write a poem about {topic}")
            chain = prompt | llm | StrOutputParser()
            result = chain.invoke({"topic": content})
            st.write(result)