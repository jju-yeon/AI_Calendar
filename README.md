# AI Calendar

이미지 또는 텍스트에서 일정 정보를 추출하여 Google Calendar에 자동 등록하는 AI 기반 캘린더 웹 애플리케이션입니다.

본 프로젝트는 사용자가 일정 안내문, 공지 이미지, 자연어 문장을 입력하면 AI 모델이 일정 제목, 설명, 장소, 시작 시간, 종료 시간을 JSON 형식으로 추출하고, 사용자가 내용을 확인한 뒤 Google Calendar에 일정을 등록하는 구조로 동작합니다.

## 주요 기능

- Google Calendar 연동
- 월간 캘린더 화면 제공
- 이미지 드래그 앤 드롭 기반 일정 분석
- 자연어 텍스트 기반 일정 분석
- AI 모델을 이용한 일정 정보 JSON 추출
- 추출 결과 수정 후 Google Calendar 일정 등록
- Gemini API 대신 직접 연결한 로컬 AI 모델 서버 사용

## 프로젝트 구조

```text
AI_Calendar/
├─ ai_model/
│  ├─ app.py
│  ├─ predict_from_image.py
│  ├─ calendar_schema.py
│  └─ calendar_json_model/
│
├─ g_calendar-api/
│  ├─ router/
│  │  └─ analyzer.js
│  └─ services/
│     └─ localModel.js
│
└─ g_calendar-client/
   ├─ public/
   └─ src/
      ├─ App.js
      ├─ LoginPage.js
      ├─ CalendarPage.js
      └─ index.js


사용자 입력
  ├─ 이미지 업로드
  └─ 텍스트 입력
        ↓
React 프론트엔드
        ↓
Express 백엔드
        ↓
FastAPI AI 모델 서버
        ↓
EasyOCR + 직접 학습한 일정 추출 모델
        ↓
일정 JSON 반환
        ↓
사용자 확인 및 수정
        ↓
Google Calendar API로 일정 등록
