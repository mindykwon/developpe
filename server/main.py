from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mecab import MeCab
from pathlib import Path

app = FastAPI()
mecab = MeCab()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# 발레 용어 보호 목록 — MeCab 사전에 없는 외래어
BALLET_TERMS = {
    '데리에', '드방', '알라세공드', '앙나방', '앙들당', '앙레르', '앙바',
    '앙오',  '쥬떼', '파드부레', '파드샤', '글리사드', '아라베스크',
    '아티튜드', '피루엣', '그랑바트망', '탕뒤', '데가제', '롱드장브',
    '퐁뒤', '프라페', '아다지오', '알레그로', '포르드브라',
}

STOPWORDS = {
    '그리고', '하지만', '그런데', '그래서', '또는', '또한', '즉', '다만',
    '조금', '많이', '좀', '너무', '정말', '진짜', '아직', '계속', '자꾸',
    '바로', '다시', '같이', '함께', '가장', '제일', '더욱', '훨씬', '매우',
    '오늘', '내일', '어제', '이번', '다음', '처음', '마지막', '나중',
    '수업', '시간', '동작', '연습', '선생님', '느낌', '부분', '방향',
}

KEEP_POS = {'NNG', 'NNP', 'SL', 'SH'}  # 일반명사, 고유명사, 외국어, 한자


def extract_keywords(text: str) -> list[str]:
    if not text.strip():
        return []

    results = set()

    # 1) 발레 용어 먼저 직접 매칭 (MeCab보다 우선)
    for term in BALLET_TERMS:
        if term in text:
            results.add(term)

    # 2) MeCab 형태소 분석으로 명사 추출
    for word, pos in mecab.pos(text):
        base_pos = pos.split('+')[0]
        if base_pos not in KEEP_POS:
            continue
        if len(word) < 2:
            continue
        if word in STOPWORDS:
            continue
        # 이미 발레 용어로 처리된 부분 단어 제거
        if any(word in term for term in results):
            continue
        results.add(word)

    return list(results)


class KeywordsRequest(BaseModel):
    comments: list[str]


class KeywordsResponse(BaseModel):
    keywords_per_comment: list[list[str]]


@app.post("/api/keywords", response_model=KeywordsResponse)
def get_keywords(req: KeywordsRequest):
    return KeywordsResponse(
        keywords_per_comment=[extract_keywords(c) for c in req.comments]
    )


# index.html 서빙 (API 라우트보다 아래에 위치해야 함)
index_html = Path(__file__).parent.parent / "index.html"

@app.get("/{full_path:path}")
async def serve_html(full_path: str):
    return FileResponse(str(index_html))
