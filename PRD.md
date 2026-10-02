# PRD: 다국어 번역기 (영어 / 일본어 / 러시아어)

| 항목 | 내용 |
|---|---|
| 문서 버전 | v1.0 |
| 작성일 | 2026-10-02 |
| 플랫폼 | Streamlit (Python) 웹 앱 |
| 번역 엔진 | OpenAI API — `gpt-6-astra` 모델 |

---

## 1. 개요

### 1.1 배경
사용자가 입력한 글을 영어, 일본어, 러시아어 세 언어로 한 번에 번역해 주는 간단한 웹 프로그램이 필요하다. 번역은 OpenAI의 `gpt-6-astra` 모델로 하고, API 키 같은 민감한 설정은 `.env` 파일로 관리한다.

### 1.2 목표
- 텍스트를 한 번 입력하면 **영어 / 일본어 / 러시아어** 번역 결과를 동시에 보여준다.
- **Streamlit**으로 구현해 별도 프론트엔드 개발 없이 웹 UI를 제공한다.
- 로컬 실행과 클라우드 배포(Streamlit Community Cloud 등)를 모두 지원하는 프로젝트 구조를 갖춘다.

### 1.3 범위 밖 (Non-Goals)
- 회원가입 / 로그인 기능
- 번역 기록의 서버 저장(DB)
- 파일(PDF, DOCX) 업로드 번역
- 음성 입력 / 출력

---

## 2. 대상 사용자

| 사용자 | 니즈 |
|---|---|
| 일반 사용자 | 짧은 문장이나 문단을 여러 언어로 빠르게 번역 |
| 콘텐츠 작성자 | 같은 글을 다국어로 동시에 준비 (SNS, 공지 등) |
| 학습자 | 한 문장이 언어별로 어떻게 표현되는지 비교 |

---

## 3. 사용자 시나리오

1. 사용자가 웹 앱에 접속한다.
2. 텍스트 입력창에 번역할 글을 입력한다. (원문 언어는 자동 감지)
3. 번역할 언어를 고른다. (기본값: 영어, 일본어, 러시아어 모두 선택)
4. **[번역하기]** 버튼을 누른다.
5. 로딩 표시가 나온 뒤 언어별 결과가 탭 또는 카드로 표시된다.
6. 각 결과의 **복사** 기능으로 번역문을 복사한다.

---

## 4. 기능 요구사항

### 4.1 필수 기능 (P0)

| ID | 기능 | 설명 |
|---|---|---|
| F-01 | 텍스트 입력 | 여러 줄 입력이 가능한 `st.text_area` 제공. 최대 5,000자 |
| F-02 | 대상 언어 선택 | `st.multiselect`로 영어/일본어/러시아어 선택. 기본값은 3개 모두 |
| F-03 | 번역 실행 | 버튼 클릭 시 선택된 언어로 번역 요청 |
| F-04 | 결과 표시 | 언어별로 나눈 결과 영역(`st.tabs` 또는 `st.columns`) |
| F-05 | 결과 복사 | `st.code` 블록의 복사 버튼으로 결과 복사 |
| F-06 | 입력 검증 | 빈 입력, 글자 수 초과, 언어 미선택 시 경고 메시지 |
| F-07 | 오류 처리 | API 키 누락, 네트워크 오류, 사용량 제한(Rate Limit) 시 알기 쉬운 오류 메시지 |
| F-08 | 로딩 표시 | 번역 중 `st.spinner` 표시 |

### 4.2 선택 기능 (P1)

| ID | 기능 | 설명 |
|---|---|---|
| F-09 | 원문 언어 표시 | 감지된 원문 언어를 결과 위에 표시 |
| F-10 | 세션 내 번역 기록 | `st.session_state`로 현재 세션의 최근 번역 10건 표시 |
| F-11 | 결과 다운로드 | 전체 번역 결과를 `.txt` 파일로 다운로드 (`st.download_button`) |
| F-12 | 번역 톤 선택 | 기본 / 격식체 / 캐주얼 중 선택 |

---

## 5. 기술 요구사항

### 5.1 기술 스택

| 구분 | 기술 |
|---|---|
| 언어 | Python 3.10 이상 |
| UI 프레임워크 | Streamlit |
| LLM API | OpenAI Python SDK (`openai`) |
| 모델 | `gpt-6-astra` (`.env`의 `OPENAI_MODEL`로 변경 가능) |
| 환경 변수 | `python-dotenv` |

### 5.2 환경 변수 (`.env`)

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-6-astra
```

- `.env`는 **절대 Git에 커밋하지 않는다.** (`.gitignore`에 포함)
- 저장소에는 키 값이 비어 있는 `.env.example`만 올린다.
- 배포 환경에서는 `.env` 대신 **Streamlit Secrets**(`st.secrets`)를 쓸 수 있도록, 설정을 다음 순서로 읽는다:
  1. `st.secrets` (배포 환경)
  2. `.env` / 시스템 환경 변수 (로컬 환경)

### 5.3 번역 처리 방식

- 선택된 언어들을 **한 번의 API 호출**로 처리하고, 결과는 JSON으로 받는다. (호출 횟수와 비용 절감)
- 시스템 프롬프트 예시:

```text
You are a professional translator.
Detect the source language of the user's text and translate it into the requested target languages.
Preserve the original meaning, tone, line breaks, and formatting.
Do not add explanations.
Respond ONLY in JSON:
{"source_language": "...", "translations": {"en": "...", "ja": "...", "ru": "..."}}
```

- 언어 코드: `en` (영어), `ja` (일본어), `ru` (러시아어)
- JSON 파싱에 실패하면 1회 재시도하고, 그래도 실패하면 오류 메시지를 표시한다.

### 5.4 프로젝트 구조

```
번역기/
├── app.py                  # Streamlit 메인 앱 (UI)
├── translator.py           # OpenAI 번역 로직
├── requirements.txt        # 의존성 목록
├── .env                    # 실제 API 키 (Git 제외)
├── .env.example            # 환경 변수 템플릿
├── .gitignore              # .env, __pycache__, .streamlit/secrets.toml 등 제외
├── .streamlit/
│   └── config.toml         # 테마 및 서버 설정
├── PRD.md                  # 본 문서
└── README.md               # 설치 / 실행 / 배포 가이드
```

### 5.5 `requirements.txt`

```text
streamlit>=1.38
openai>=1.50
python-dotenv>=1.0
```

---

## 6. UI / UX 요구사항

### 6.1 화면 구성

```
┌──────────────────────────────────────────────┐
│  🌐 다국어 번역기                              │
│  입력한 글을 영어 · 일본어 · 러시아어로 번역합니다  │
├──────────────────────────────────────────────┤
│  [ 번역할 텍스트 입력 ...                    ] │
│  [                                          ] │
│                                  1,234/5,000 │
│  대상 언어: [영어 ✕] [일본어 ✕] [러시아어 ✕]    │
│                              [ 번역하기 ]     │
├──────────────────────────────────────────────┤
│  감지된 원문 언어: 한국어                      │
│  ┌ 🇺🇸 영어 ┬ 🇯🇵 일본어 ┬ 🇷🇺 러시아어 ┐       │
│  │ Translated text ...           [복사] │       │
│  └──────────────────────────────────────┘       │
│                       [ 결과 다운로드 (.txt) ] │
└──────────────────────────────────────────────┘
```

- 사이드바: 모델명 표시, 번역 톤 선택(P1), 세션 기록(P1)
- 반응형: Streamlit 기본 레이아웃(`layout="centered"`)을 쓰고 모바일에서도 사용 가능해야 한다.

### 6.2 메시지 정의

| 상황 | 메시지 |
|---|---|
| 빈 입력 | ⚠️ 번역할 텍스트를 입력해 주세요. |
| 글자 수 초과 | ⚠️ 최대 5,000자까지 입력할 수 있습니다. |
| 언어 미선택 | ⚠️ 번역할 언어를 하나 이상 선택해 주세요. |
| API 키 없음 | ❌ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일 또는 Secrets를 확인하세요. |
| API 오류 | ❌ 번역 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요. |
| 사용량 제한 | ⏳ 요청이 많습니다. 잠시 후 다시 시도해 주세요. |

---

## 7. 비기능 요구사항

| 항목 | 요구사항 |
|---|---|
| 성능 | 1,000자 기준 번역 응답 10초 이내 (API 응답 시간에 따라 다름) |
| 보안 | API 키를 코드에 하드코딩하지 않음. 화면이나 로그에 키를 출력하지 않음 |
| 안정성 | API 호출 타임아웃 60초, 실패 시 사용자에게 안내 |
| 비용 | 다국어 번역을 한 번의 호출로 처리. `st.cache_data`로 같은 입력의 중복 호출 방지 |
| 유지보수 | UI(`app.py`)와 번역 로직(`translator.py`) 분리 |

---

## 8. 배포 계획

### 8.1 로컬 실행

```bash
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
copy .env.example .env           # 이후 .env에 API 키 입력
streamlit run app.py
```

### 8.2 Streamlit Community Cloud 배포 (권장)

1. 프로젝트를 GitHub 저장소에 푸시한다. (`.env`는 제외되었는지 확인)
2. [share.streamlit.io](https://share.streamlit.io)에서 저장소를 연결한다.
3. Main file path에 `app.py`를 지정한다.
4. **Advanced settings → Secrets**에 다음을 입력한다:
   ```toml
   OPENAI_API_KEY = "sk-xxxxxxxx"
   OPENAI_MODEL = "gpt-6-astra"
   ```
5. Deploy를 누르면 공개 URL이 발급된다.

### 8.3 대안 배포 방식
- **Docker**: `Dockerfile` 추가 후 Render, Railway, Google Cloud Run 등에 배포 (환경 변수는 각 플랫폼 설정으로 주입)

---

## 9. 성공 지표

| 지표 | 목표 |
|---|---|
| 번역 성공률 | 정상 입력 기준 99% 이상 |
| 평균 응답 시간 | 10초 이내 |
| 배포 | 공개 URL로 접속해 3개 언어 번역이 정상 동작 |

---

## 10. 개발 일정 (예시)

| 단계 | 작업 | 기간 |
|---|---|---|
| 1 | 프로젝트 구조, `.env` 설정, `translator.py` 구현 | 0.5일 |
| 2 | `app.py` UI 구현 (P0 기능) | 0.5일 |
| 3 | 오류 처리, 입력 검증, 테스트 | 0.5일 |
| 4 | P1 기능 (기록, 다운로드, 톤 선택) | 0.5일 |
| 5 | README 작성, Streamlit Cloud 배포 | 0.5일 |

---

## 11. 리스크 및 대응

| 리스크 | 대응 |
|---|---|
| 모델명(`gpt-6-astra`)이 계정에서 사용할 수 없음 | `.env`의 `OPENAI_MODEL` 값만 바꿔 다른 모델로 교체 가능하게 설계 |
| API 키 유출 | `.gitignore`로 `.env` 제외, 배포 시 Secrets 사용 |
| 모델이 JSON 형식을 지키지 않음 | JSON 응답 모드 사용, 파싱 실패 시 재시도 |
| API 비용 증가 | 입력 글자 수 제한, 캐싱 적용 |
