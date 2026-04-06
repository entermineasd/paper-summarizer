from flask import Flask, request, render_template_string, jsonify
from openai import OpenAI
import os
import json
import fitz
import arxiv

app = Flask(__name__)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

STYLE = """
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f4ff; color: #333; }
    .navbar { background: #1e3a8a; padding: 15px 30px; }
    .navbar h1 { color: white; font-size: 18px; }
    .navbar p { color: #93c5fd; font-size: 12px; margin-top: 3px; }
    .container { max-width: 800px; margin: 40px auto; padding: 0 20px; }
    .card { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
    .card h2 { font-size: 16px; margin-bottom: 15px; color: #1e3a8a; }
    textarea { width: 100%; height: 200px; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 13px; resize: vertical; outline: none; line-height: 1.6; }
    textarea:focus { border-color: #1e3a8a; }
    .upload-area { border: 2px dashed #bcd; border-radius: 8px; padding: 30px; text-align: center; cursor: pointer; margin-bottom: 15px; color: #6b7280; transition: all 0.2s; }
    .upload-area:hover { border-color: #1e3a8a; color: #1e3a8a; background: #eff6ff; }
    .upload-area input { display: none; }
    .tab { display: inline-block; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; margin-right: 8px; border: 1px solid #ddd; color: #666; }
    .tab.active { background: #1e3a8a; color: white; border-color: #1e3a8a; }
    .tab-content { display: none; margin-top: 15px; }
    .tab-content.active { display: block; }
    .btn { display: inline-block; padding: 11px 28px; background: #1e3a8a; color: white; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; margin-top: 12px; margin-right: 8px; }
    .btn:hover { background: #1e40af; }
    .btn-sm { padding: 7px 16px; font-size: 13px; margin-top: 0; }
    .section { margin-bottom: 20px; }
    .section-title { font-size: 12px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
    .summary-box { background: #eff6ff; border-left: 4px solid #1e3a8a; padding: 15px 18px; border-radius: 6px; font-size: 14px; line-height: 1.8; }
    .quote-box { background: #f9fafb; border-left: 4px solid #6b7280; padding: 12px 18px; border-radius: 6px; font-size: 13px; line-height: 1.7; margin-bottom: 8px; color: #374151; font-style: italic; }
    .tag { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; background: #dbeafe; color: #1e3a8a; margin: 4px 3px; }
    .conclusion-box { background: #ecfdf5; border-left: 4px solid #10b981; padding: 15px 18px; border-radius: 6px; font-size: 14px; line-height: 1.8; }
    .loading { color: #888; font-size: 14px; margin-top: 15px; }
    .file-name { font-size: 13px; color: #1e3a8a; margin-top: 8px; font-weight: 600; }
    .paper-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s; }
    .paper-item:hover { border-color: #1e3a8a; background: #eff6ff; }
    .paper-title { font-size: 14px; font-weight: 600; color: #1e3a8a; margin-bottom: 5px; }
    .paper-authors { font-size: 12px; color: #6b7280; margin-bottom: 5px; }
    .paper-abstract { font-size: 12px; color: #374151; line-height: 1.6; }
    input[type=text] { width: 100%; padding: 11px 14px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; outline: none; margin-bottom: 10px; }
    input[type=text]:focus { border-color: #1e3a8a; }
</style>
"""

@app.route('/')
def index():
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>논문 요약기</title>{STYLE}</head>
    <body>
    <div class='navbar'>
        <h1>📚 논문 & 학술 문서 요약기</h1>
        <p>PDF 업로드, 텍스트 입력, 또는 논문 자동 검색으로 분석해요</p>
    </div>
    <div class='container'>
        <div class='card'>
            <h2>📄 문서 입력</h2>
            <span class='tab active' onclick='switchTab("search", this)'>🔎 논문 검색</span>
            <span class='tab' onclick='switchTab("pdf", this)'>📎 PDF 업로드</span>
            <span class='tab' onclick='switchTab("text", this)'>📝 텍스트 입력</span>

            <div id='tab-search' class='tab-content active'>
                <input type='text' id='searchInput' placeholder='검색어를 입력해요 (예: machine learning, sleep deprivation)'>
                <button class='btn' onclick='searchPapers()'>🔍 논문 검색</button>
                <div id='searchResult'></div>
            </div>

            <div id='tab-pdf' class='tab-content'>
                <div class='upload-area' onclick='document.getElementById("fileInput").click()'>
                    <input type='file' id='fileInput' accept='.pdf' onchange='handleFile(this)'>
                    <div style='font-size:32px;margin-bottom:8px;'>📎</div>
                    <div>PDF 파일을 클릭해서 업로드해요</div>
                    <div style='font-size:12px;margin-top:5px;'>최대 10MB</div>
                </div>
                <div id='fileName' class='file-name'></div>
                <button class='btn' onclick='analyzePdf()'>🔍 분석하기</button>
            </div>

            <div id='tab-text' class='tab-content'>
                <textarea id='textInput' placeholder='논문이나 학술 자료 텍스트를 붙여넣어요...'></textarea>
                <button class='btn' onclick='analyzeText()'>🔍 분석하기</button>
            </div>

            <div id='result'></div>
        </div>
    </div>
    <script>
        let currentTab = 'search';
        let pdfFile = null;

        function switchTab(tab, el) {{
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            el.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
        }}

        function handleFile(input) {{
            pdfFile = input.files[0];
            document.getElementById('fileName').textContent = '✅ ' + pdfFile.name;
        }}

        async function searchPapers() {{
            const query = document.getElementById('searchInput').value;
            if (!query.trim()) return;
            document.getElementById('searchResult').innerHTML = '<p class="loading">검색 중...</p>';
            const res = await fetch('/search', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{query: query}})
            }});
            const papers = await res.json();
            let html = '<div style="margin-top:15px;">';
            papers.forEach((p, i) => {{
                html += `<div class='paper-item' onclick='analyzePaperUrl("${{p.pdf_url}}")'>
                    <div class='paper-title'>${{p.title}}</div>
                    <div class='paper-authors'>${{p.authors}}</div>
                    <div class='paper-abstract'>${{p.abstract}}</div>
                    <div style='margin-top:8px;'><span class='tag'>클릭해서 분석하기</span></div>
                </div>`;
            }});
            html += '</div>';
            document.getElementById('searchResult').innerHTML = html;
        }}

        async function analyzePaperUrl(url) {{
            document.getElementById('result').innerHTML = '<p class="loading">논문 분석 중... (잠시 기다려요)</p>';
            const res = await fetch('/analyze-url', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{url: url}})
            }});
            const data = await res.json();
            showResult(data);
        }}

        async function analyzePdf() {{
            if (!pdfFile) return;
            document.getElementById('result').innerHTML = '<p class="loading">분석 중...</p>';
            const formData = new FormData();
            formData.append('file', pdfFile);
            const res = await fetch('/analyze-pdf', {{ method: 'POST', body: formData }});
            const data = await res.json();
            showResult(data);
        }}

        async function analyzeText() {{
            const text = document.getElementById('textInput').value;
            if (!text.trim()) return;
            document.getElementById('result').innerHTML = '<p class="loading">분석 중...</p>';
            const res = await fetch('/analyze-text', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{text: text}})
            }});
            const data = await res.json();
            showResult(data);
        }}

        function showResult(data) {{
            if (data.error) {{ document.getElementById('result').innerHTML = '<p style="color:red;">오류: ' + data.error + '</p>'; return; }}
            let html = '<br>';
            html += '<div class="section"><div class="section-title">📌 핵심 요약</div>';
            html += `<div class="summary-box">${{data.summary}}</div></div>`;
            html += '<div class="section"><div class="section-title">🏷 주요 키워드</div><div>';
            data.keywords.forEach(k => {{ html += `<span class="tag">${{k}}</span>`; }});
            html += '</div></div>';
            html += '<div class="section"><div class="section-title">💬 인용할 만한 문장</div>';
            data.quotes.forEach(q => {{ html += `<div class="quote-box">"${{q}}"</div>`; }});
            html += '</div>';
            html += '<div class="section"><div class="section-title">✅ 한 줄 결론</div>';
            html += `<div class="conclusion-box">${{data.conclusion}}</div></div>`;
            document.getElementById('result').innerHTML = html;
        }}
    </script>
    </body></html>
    """)

def ai_analyze(text):
    text = text[:8000]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": '''너는 학술 논문 분석 전문가야. 반드시 JSON만 출력해. 다른 텍스트 절대 금지.
형식: {
    "summary": "핵심 내용 3줄 요약 (줄바꿈은 <br>으로)",
    "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
    "quotes": ["인용할 만한 문장1", "인용할 만한 문장2", "인용할 만한 문장3"],
    "conclusion": "논문의 한 줄 결론"
}'''},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

@app.route('/search', methods=['POST'])
def search():
    try:
        query = request.json['query']
        search_client = arxiv.Client()
        results = search_client.results(arxiv.Search(query=query, max_results=5))
        papers = []
        for r in results:
            papers.append({
                "title": r.title,
                "authors": ", ".join([a.name for a in r.authors[:3]]),
                "abstract": r.summary[:200] + "...",
                "pdf_url": r.pdf_url
            })
        return jsonify(papers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-url', methods=['POST'])
def analyze_url():
    try:
        import requests
        url = request.json['url']
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        pdf = fitz.open(stream=response.content, filetype="pdf")
        text = ""
        for page in pdf:
            text += page.get_text()
        pdf.close()
        return jsonify(ai_analyze(text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-pdf', methods=['POST'])
def analyze_pdf():
    try:
        file = request.files['file']
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in pdf:
            text += page.get_text()
        pdf.close()
        return jsonify(ai_analyze(text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-text', methods=['POST'])
def analyze_text():
    try:
        text = request.json['text']
        return jsonify(ai_analyze(text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)