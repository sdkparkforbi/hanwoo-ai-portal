"""
한우 시장 AI 포털 — 백엔드 (Hanwoo Market AI Portal)
=====================================================
한우시장_트랜스포머_LLM_방법론 제안서를 구현한 멀티모달 Mock-Up.
"시장분석·예측 업무를 지원하는 LLM" 을 WebChat + REST API 로 제공한다.

기능(엔드포인트)
  GET  /                      정적 프론트엔드(포털)
  GET  /api/news              한우 시장 기사 목록(뉴스 포털)
  GET  /api/news/{id}         기사 상세
  POST /api/chat              대화형 시장분석 AI (LLM)
  POST /api/article/explain   기사 해설봇 (친절한 설명)
  POST /api/article/kidify    초딩도 이해하는 쉬운 이야기 기사
  POST /api/article/video     음성+텍스트+그림 → 영상기사 스크립트/스토리보드
  POST /api/jury              LLM Jury — 자동기사 품질 보장(다심사위원 채점)
  GET  /api/forecast          시장 예측 (mock 트랜스포머)
  GET  /api/health            상태 점검

보안
  API 키는 절대 코드/저장소에 두지 않는다. 환경변수 또는 서버의 *_KEY.txt 에서만 로드.
  (이 저장소의 .gitignore 가 *.txt 키 파일을 제외한다.)

배포(서버 106.247.236.2)
  pip install -r requirements.txt
  # 키: 환경변수 또는 프로젝트 상위 폴더의 OPENAI_API_KEY.txt 등 자동 탐색
  uvicorn main:app --host 0.0.0.0 --port 8000
  # 같은 출처(http)로 프론트+API를 서빙하므로 혼합콘텐츠 문제 없음
"""
import os
import json
import math
import random
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from openai import OpenAI
    _OPENAI_OK = True
except ImportError:
    _OPENAI_OK = False

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT.parent / "frontend"
# 키 탐색 경로: 환경변수 우선, 없으면 상위 폴더들의 *.txt
KEY_SEARCH_DIRS = [ROOT, ROOT.parent, ROOT.parent.parent]

random.seed(42)


def load_key(env_name: str, file_name: str) -> str:
    """환경변수 → 파일 순으로 키를 찾는다. 키 값은 로그/응답에 절대 노출하지 않는다."""
    v = os.environ.get(env_name, "").strip()
    if v:
        return v
    for d in KEY_SEARCH_DIRS:
        p = d / file_name
        if p.exists():
            try:
                return p.read_text(encoding="utf-8").strip()
            except Exception:
                pass
    return ""


OPENAI_KEY = load_key("OPENAI_API_KEY", "OPENAI_API_KEY.txt")
OPENAI_MODEL = os.environ.get("PORTAL_LLM_MODEL", "gpt-4o-mini")


def llm(messages: List[dict], temperature: float = 0.4, max_tokens: int = 700) -> Optional[str]:
    """OpenAI 호환 LLM 호출. 키 없으면 None 반환(프론트는 데모 응답으로 폴백)."""
    if not (OPENAI_KEY and _OPENAI_OK):
        return None
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"[LLM 오류] {e}"


app = FastAPI(title="Hanwoo Market AI Portal", version="1.0.0",
              description="멀티모달 한우 시장분석·예측 LLM 포털")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# =====================================================
# 샘플 한우 시장 기사 (실서비스에서는 DB/크롤링으로 대체)
# =====================================================
NEWS = [
    {
        "id": "n1",
        "category": "가격동향",
        "title": "송아지 경매가 1년 새 11~21% 급등… 한우 사이클 반등 신호",
        "summary": "암소 사육 감소가 누적되며 송아지 생산이 줄어 경매가가 급등했다. 30개월 시차를 고려하면 도매가 상승 전환의 선행지표로 해석된다.",
        "date": "2026-06-10",
        "difficulty": "중",
        "body": ("최근 송아지 경매가격이 전년 대비 11~21% 급등했다. 2022~2023년 사육마릿수가 "
                 "역대 최대를 기록하며 도매가격이 약 11% 하락했으나, 이후 누적된 암소 감축이 "
                 "송아지 출생 감소로 이어졌다. 한우는 입식부터 출하까지 약 30개월이 걸려 가격 "
                 "신호가 공급에 반영되기까지 시차가 크다. 따라서 현재의 송아지가격 급등은 약 "
                 "2~3년 뒤 도매가 흐름을 예고하는 선행지표로 읽힌다."),
    },
    {
        "id": "n2",
        "category": "사료·원가",
        "title": "사료가격지수 고공행진… 곡물가·환율 동반 상승에 농가 원가 부담",
        "summary": "우크라이나 사태 이후 국제 곡물가와 환율이 함께 오르며 사료가격지수가 높은 수준을 유지, 사육 농가의 수익성을 압박하고 있다.",
        "date": "2026-05-28",
        "difficulty": "중",
        "body": ("사료가격지수가 2020년 100 기준 대비 높은 수준을 이어가고 있다. 국제 곡물가 "
                 "상승과 원/달러 환율 상승이 겹치며 배합사료 단가가 올랐다. 사료비는 한우 생산비의 "
                 "큰 비중을 차지해 농가 수익성에 직접적인 영향을 준다."),
    },
    {
        "id": "n3",
        "category": "정책",
        "title": "농식품부, 한우 수급조절 정책 발표 — 저능력 암소 도태 지원",
        "summary": "공급 과잉 완화를 위해 저능력 암소 도태를 지원한다. 단기적으로 도축이 늘어 가격이 눌리지만, 12~24개월 뒤에는 공급 감소로 반등 요인이 된다.",
        "date": "2026-05-12",
        "difficulty": "상",
        "body": ("정부가 한우 수급조절을 위해 저능력 암소 도태 지원 정책을 발표했다. 도태는 단기적으로 "
                 "도축마릿수를 늘려 가격을 일시적으로 낮추지만, 12~24개월 후에는 송아지 생산 감소로 "
                 "출하가 줄어 가격 반등 요인으로 작용한다. 정책 효과는 시차를 두고 나타난다."),
    },
    {
        "id": "n4",
        "category": "방역",
        "title": "럼피스킨 산발 발생… 도축·이동 일시 제한에 단기 수급 교란",
        "summary": "가축전염병 발생으로 일부 지역의 도축·이동이 제한되며 단기 출하 차질이 우려된다. 비정형 충격은 예측 모형의 난도를 높인다.",
        "date": "2026-04-30",
        "difficulty": "상",
        "body": ("럼피스킨이 산발적으로 발생하며 일부 지역에서 도축·이동이 일시 제한됐다. 이러한 "
                 "가축전염병은 예고 없이 발생해 단기 수급을 교란하고, 선형·정상성 가정을 둔 전통 "
                 "통계모형으로는 포착이 어렵다. 트랜스포머 기반 모형은 이벤트 임베딩으로 이런 "
                 "비정형 충격을 학습에 반영한다."),
    },
]
NEWS_BY_ID = {n["id"]: n for n in NEWS}


# =====================================================
# Mock 예측 (hanwoo_proto 와 동일 개념)
# =====================================================
def mock_forecast(target: str = "wholesale_price", horizon: int = 12) -> List[dict]:
    base = {"wholesale_price": 19000, "calf_price": 380, "slaughter_count": 7.0}.get(target, 19000)
    amp = {"wholesale_price": 1500, "calf_price": 30, "slaughter_count": 0.6}.get(target, 1000)
    noise = {"wholesale_price": 350, "calf_price": 12, "slaughter_count": 0.18}.get(target, 100)
    out = []
    for h in range(1, horizon + 1):
        p50 = base + 80 * h + amp * math.sin(2 * math.pi * h / 30)
        widen = 1 + h / 12
        out.append({"month": h,
                    "p10": round(p50 - 1.28 * noise * widen, 1),
                    "p50": round(p50, 1),
                    "p90": round(p50 + 1.28 * noise * widen, 1)})
    return out


# =====================================================
# 프롬프트
# =====================================================
SYS_ANALYST = (
    "당신은 한우 시장 분석을 돕는 전문 AI 비서입니다. 가격·수급·사료비·정책·전염병 등 "
    "한우 시장 요인을 쉽게 설명하고, 30개월 생산 시차와 사이클 변동을 고려해 분석합니다. "
    "한국어 존댓말로, 근거를 갖춰 3~6문장으로 간결하게 답하세요. 모르면 모른다고 하세요."
)


# =====================================================
# 스키마
# =====================================================
class ChatReq(BaseModel):
    message: str
    history: List[dict] = []


class ArticleReq(BaseModel):
    article_id: Optional[str] = None
    text: Optional[str] = None


class VideoReq(BaseModel):
    article_id: Optional[str] = None
    text: Optional[str] = None
    voice: str = "ko-female-1"


class JuryReq(BaseModel):
    text: str
    title: Optional[str] = ""


def _article_text(article_id, text):
    if text:
        return text
    if article_id and article_id in NEWS_BY_ID:
        a = NEWS_BY_ID[article_id]
        return f"{a['title']}\n\n{a['body']}"
    raise HTTPException(400, "article_id 또는 text 가 필요합니다.")


# =====================================================
# 엔드포인트
# =====================================================
@app.get("/api/health")
def health():
    return {"status": "ok", "llm_configured": bool(OPENAI_KEY and _OPENAI_OK),
            "model": OPENAI_MODEL if OPENAI_KEY else "demo-fallback"}


@app.get("/api/news")
def news():
    return {"items": [{k: v for k, v in n.items() if k != "body"} for n in NEWS]}


@app.get("/api/news/{nid}")
def news_detail(nid: str):
    if nid not in NEWS_BY_ID:
        raise HTTPException(404, "기사를 찾을 수 없습니다.")
    return NEWS_BY_ID[nid]


@app.get("/api/forecast")
def forecast(target: str = "wholesale_price", horizon: int = 12):
    return {"target": target, "horizon": horizon, "forecast": mock_forecast(target, horizon)}


@app.post("/api/chat")
def chat(req: ChatReq):
    msgs = [{"role": "system", "content": SYS_ANALYST}]
    msgs += req.history[-6:]
    msgs.append({"role": "user", "content": req.message})
    reply = llm(msgs)
    if reply is None:
        reply = ("(데모) 한우 가격은 30개월 생산 시차 때문에 사이클을 그립니다. "
                 "송아지가격 급등은 보통 2~3년 뒤 도매가 상승의 선행지표입니다. "
                 "서버에 OPENAI_API_KEY 를 설정하면 실시간 분석이 제공됩니다.")
    return {"reply": reply, "live": bool(OPENAI_KEY and _OPENAI_OK)}


@app.post("/api/article/explain")
def explain(req: ArticleReq):
    text = _article_text(req.article_id, req.text)
    out = llm([
        {"role": "system", "content": SYS_ANALYST + " 아래 기사를 일반 독자가 이해하기 쉽게 핵심 3가지로 친절히 해설하세요."},
        {"role": "user", "content": text},
    ])
    if out is None:
        out = ("(데모 해설) ① 핵심: 송아지가격 급등은 공급 감소 신호입니다. "
               "② 이유: 한우는 출하까지 30개월이 걸려 가격 반영에 시차가 큽니다. "
               "③ 전망: 시차를 고려하면 향후 도매가 상승 압력으로 이어질 수 있습니다.")
    return {"explanation": out}


@app.post("/api/article/kidify")
def kidify(req: ArticleReq):
    text = _article_text(req.article_id, req.text)
    out = llm([
        {"role": "system", "content": "당신은 초등학생도 이해할 수 있게 설명하는 이야기 작가입니다. 어려운 경제·축산 기사를 비유와 쉬운 말로, 짧은 이야기처럼 바꿔 쓰세요. 3~5문장."},
        {"role": "user", "content": text},
    ], temperature=0.7)
    if out is None:
        out = ("(데모) 소를 키우는 건 라면이 아니라 '사골 가마솥'이에요. 송아지를 들여도 어른 소가 "
               "되려면 2년 반이 걸리거든요. 그래서 지금 아기 소 값이 비싸졌다는 건, 2~3년 뒤에 "
               "소고기가 귀해질 수 있다는 미리 알려주는 신호랍니다!")
    return {"story": out}


@app.post("/api/article/video")
def video(req: VideoReq):
    """음성+텍스트+그림 → 영상기사. 여기서는 스크립트/스토리보드를 생성한다.
    실제 렌더링은 TTS(음성)+이미지 생성+영상합성 파이프라인(서버 워커)으로 확장."""
    text = _article_text(req.article_id, req.text)
    out = llm([
        {"role": "system", "content": "당신은 뉴스 영상 작가입니다. 기사로 30초 영상기사 스크립트를 만드세요. 장면(scene)별로 [나레이션] / [화면: 이미지 설명] / [자막] 을 3~4컷으로 제시하세요."},
        {"role": "user", "content": text},
    ], temperature=0.6)
    if out is None:
        out = ("[컷1] 나레이션: 송아지 값이 1년 새 최대 21% 뛰었습니다.\n화면: 경매장 송아지\n자막: 송아지가 21%↑\n\n"
               "[컷2] 나레이션: 한우는 출하까지 30개월, 가격 반영에 시차가 큽니다.\n화면: 달력 30개월 그래픽\n자막: 30개월의 시차\n\n"
               "[컷3] 나레이션: 지금의 급등은 2~3년 뒤 도매가 상승의 신호입니다.\n화면: 상승 화살표 차트\n자막: 선행지표")
    return {
        "script": out,
        "voice": req.voice,
        "pipeline": ["LLM 스크립트 생성", "TTS 음성합성", "장면별 이미지 생성", "자막·합성 렌더링"],
        "status": "script_ready",
        "note": "영상 렌더링은 서버 워커(TTS+이미지+합성)에서 비동기 처리하도록 확장 예정",
    }


JURY_CRITERIA = ["사실정확성", "논리성", "출처·근거", "편향성(낮을수록 좋음)", "가독성"]


@app.post("/api/jury")
def jury(req: JuryReq):
    """LLM Jury — 자동 생성 기사의 품질을 여러 심사 기준으로 채점해 게재 가부를 판단."""
    out = llm([
        {"role": "system", "content":
            "당신은 기사 품질 심사위원단(LLM Jury)입니다. 아래 기사를 "
            + ", ".join(JURY_CRITERIA) +
            " 기준으로 각 0~100점 채점하고, 평균과 게재 가부(PASS/REVISE/REJECT), 한 줄 총평을 "
            "반드시 JSON 으로만 출력하세요. 형식: "
            '{"scores":{"사실정확성":int,...},"average":int,"verdict":"PASS|REVISE|REJECT","comment":"..."}'},
        {"role": "user", "content": f"제목: {req.title}\n\n{req.text}"},
    ], temperature=0.0)
    if out is None:
        demo = {"scores": {c: random.randint(72, 94) for c in JURY_CRITERIA}}
        demo["average"] = round(sum(demo["scores"].values()) / len(JURY_CRITERIA))
        demo["verdict"] = "PASS" if demo["average"] >= 80 else "REVISE"
        demo["comment"] = "(데모) 근거가 비교적 충실하나 출처 표기를 보강하면 좋습니다."
        return {"jury": demo, "live": False}
    try:
        parsed = json.loads(out[out.find("{"): out.rfind("}") + 1])
    except Exception:
        parsed = {"raw": out}
    return {"jury": parsed, "live": True, "criteria": JURY_CRITERIA}


# =====================================================
# 정적 프론트엔드 (같은 출처로 서빙 → 혼합콘텐츠 없음)
# =====================================================
@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


if FRONTEND.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print(f"[Portal] LLM: {'OK' if OPENAI_KEY else 'MISSING (데모 폴백)'} / model={OPENAI_MODEL}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
