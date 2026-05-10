from http.server import BaseHTTPRequestHandler
import json
from kiwipiepy import Kiwi

kiwi = Kiwi()

STOPWORDS = {
    '그리고', '하지만', '그런데', '그래서', '또는', '또한', '즉', '다만',
    '조금', '많이', '좀', '너무', '정말', '진짜', '아직', '계속', '자꾸',
    '바로', '다시', '같이', '함께', '가장', '제일', '더욱', '훨씬', '매우',
    '오늘', '내일', '어제', '이번', '다음', '처음', '마지막', '나중',
    '수업', '시간', '동작', '연습', '선생님', '느낌', '부분', '방향',
}

KEEP_POS = {'NNG', 'NNP', 'SL', 'SH'}


def extract_keywords(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    seen = set()
    out = []
    for tk in kiwi.tokenize(text):
        if tk.tag not in KEEP_POS:
            continue
        word = tk.form
        if len(word) < 2:
            continue
        if word in STOPWORDS:
            continue
        if word in seen:
            continue
        seen.add(word)
        out.append(word)
    return out


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length else b''
            data = json.loads(body) if body else {}
            comments = data.get('comments', [])
            result = [extract_keywords(c) for c in comments]
            payload = json.dumps({'keywords_per_comment': result}).encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as e:
            err = json.dumps({'error': str(e)}).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(err)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
