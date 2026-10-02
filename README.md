# 🌐 다국어 번역기

입력한 글을 영어 · 일본어 · 러시아어로 한 번에 번역하는 Streamlit 앱입니다. 번역은 OpenAI API(기본 모델 `gpt-6-astra`)를 사용합니다.

## 기능
- 원문 언어 자동 감지, 영어/일본어/러시아어 중 원하는 언어 선택
- 번역 톤 선택 (기본 / 격식체 / 캐주얼)
- 결과 복사, `.txt` 다운로드, 세션 내 최근 번역 기록 10건
- 최대 5,000자 입력

## 로컬 실행

```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env
```

`.env`에 API 키를 넣고 실행합니다.

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-6-astra
```

```bash
streamlit run app.py
```

## Streamlit Community Cloud 배포

1. 이 저장소를 GitHub에 올립니다. (`.env`는 `.gitignore`로 제외됩니다)
2. [share.streamlit.io](https://share.streamlit.io)에서 **Create app** → 저장소, 브랜치 `main`, Main file path `app.py`를 지정합니다.
3. **Advanced settings → Secrets**에 다음을 입력합니다.
   ```toml
   OPENAI_API_KEY = "sk-..."
   OPENAI_MODEL = "gpt-6-astra"
   ```
4. **Deploy**를 누르면 공개 URL이 발급됩니다.

앱은 설정을 Streamlit Secrets → `.env` / 환경 변수 순서로 읽습니다.
