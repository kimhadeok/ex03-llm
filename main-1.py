from dotenv import load_dotenv
from langchain_openai import OpenAI, ChatOpenAI

load_dotenv()

# 1. 모델 불러오기
llm = OpenAI()
# 2. 모델 사용하기
llm_response = llm.invoke("오늘 점심 추천해줘")
print(llm_response)

# 1. 모델 불러오기
chat_model = ChatOpenAI()
# 2. 모델 사용하기
chat_response = chat_model.invoke("오늘 서울 날씨 어때?")
print(chat_response.content)
