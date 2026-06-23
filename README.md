# 한우 시장 AI 포털 (Hanwoo Market AI Portal)

트랜스포머 기반 한우 시장 예측과 LLM 진단을 **WebChat + REST API**로 제공하는 **멀티모달 포털** 프로토타입.
「한우시장 트랜스포머·LLM 방법론 제안서」를 구현한 Mock-Up이며, 시장분석·예측 업무를 지원하는 LLM을 중심으로 한다.

🔗 **데모(정적, 카카오 공유용)**: `https://sdkparkforbi.github.io/hanwoo-ai-portal/`
🖥 **실서비스(서버)**: `http://106.247.236.2:8000/` ← FastAPI가 프론트+API를 같은 출처로 서빙

---

## 기능

| 기능 | 설명 |
|---|---|
| 📺 소개 영상 | 시스템 소개 영상 자리(`assets/intro.mp4` 또는 유튜브 임베드) |
| 💬 대화형 AI | 한우 시장분석 챗봇 + P10·P50·P90 예측 차트 |
| 📰 뉴스 포털 | 한우 시장 기사 목록·상세 |
| 🤖 기사 해설봇 | 기사를 핵심 3가지로 친절히 해설 |
| 🧒 초등학생용 쉬운 기사 | 어려운 기사를 비유·쉬운 말로 재작성 |
| 🎬 영상기사 생성 | 음성+텍스트+그림 → 영상기사 스크립트/스토리보드 (TTS·이미지·합성 파이프라인) |
| ⚖️ LLM Jury | 자동 생성 기사 품질을 다기준 채점 → 게재 가부(PASS/REVISE/REJECT) |
| 🔌 API | 모든 기능을 REST로 제공 (`/docs` Swagger) |

## 구조

```
hanwoo_ai_portal/
├── backend/
│   ├── main.py          # FastAPI (chat·explain·kidify·video·jury·news·forecast)
│   └── requirements.txt
├── frontend/
│   ├── index.html       # 단일 포털 (Tailwind + Chart.js, 데모 폴백 내장)
│   └── assets/og-image.png  # 카카오/OG 썸네일 (1200×630)
└── README.md
```

## 실행 (서버 106.247.236.2)

```bash
pip install -r requirements.txt
# 키는 환경변수 또는 프로젝트 상위 폴더의 *_KEY.txt 에서 자동 로드 (저장소엔 커밋되지 않음)
export OPENAI_API_KEY="sk-..."     # 또는 OPENAI_API_KEY.txt 배치
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
# http://106.247.236.2:8000  → 프론트+API 동일 출처 (혼합콘텐츠 없음)
```

키가 없으면 모든 LLM 기능은 **데모 폴백 응답**으로 동작한다(서버 미기동 시 정적 사이트도 동일).

## 보안

- `*_KEY.txt`, `*PASSWORD*.txt`, `.env` 는 `.gitignore` 로 **커밋 제외**. 키는 서버에만 둔다.
- GitHub Pages(HTTPS 정적)에서 HTTP 백엔드 직접 호출은 혼합콘텐츠로 차단되므로,
  **실서비스는 서버에서 프론트+API를 같은 출처로 서빙**하고, GitHub Pages는 데모(정적)로 운영한다.

## 한계 / 다음 단계

- 예측은 `mock_forecast()` (학습된 트랜스포머 자리), 뉴스는 샘플 데이터 → 실데이터/모델 연동 필요
- 영상기사: 현재 스크립트 생성까지. TTS·이미지 생성·영상 합성 워커로 확장
- RAG·Tool-use Agent, 인증/RBAC 미구현
