from flask import Flask, request, render_template_string, jsonify
from openai import OpenAI
import os
import json
import fitz
import arxiv
import requests

app = Flask(__name__)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

STYLE = """
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f4ff; color: #333; }
    .navbar { background: #1e3a8a; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
    .navbar h1 { color: white; font-size: 18px; }
    .navbar p { color: #93c5fd; font-size: 12px; margin-top: 3px; }
    .lang-toggle { display: flex; background: #ffffff22; border-radius: 6px; overflow: hidden; }
    .lang-btn { padding: 6px 14px; color: white; cursor: pointer; font-size: 13px; border: none; background: transparent; }
    .lang-btn.active { background: #4f46e5; }
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
    .btn-outline { background: transparent; border: 1px solid #1e3a8a; color: #1e3a8a; }
    .btn-outline:hover { background: #eff6ff; }
    .section { margin-bottom: 20px; }
    .section-title { font-size: 12px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
    .summary-box { background: #eff6ff; border-left: 4px solid #1e3a8a; padding: 15px 18px; border-radius: 6px; font-size: 14px; line-height: 1.8; }
    .tag { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; background: #dbeafe; color: #1e3a8a; margin: 4px 3px; }
    .loading { color: #888; font-size: 14px; margin-top: 15px; }
    .file-name { font-size: 13px; color: #1e3a8a; margin-top: 8px; font-weight: 600; }
    .paper-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s; }
    .paper-item:hover { border-color: #1e3a8a; background: #eff6ff; }
    .paper-title { font-size: 14px; font-weight: 600; color: #1e3a8a; margin-bottom: 5px; }
    .paper-authors { font-size: 12px; color: #6b7280; margin-bottom: 3px; }
    .paper-year { font-size: 11px; color: #9ca3af; margin-bottom: 5px; }
    .paper-abstract { font-size: 12px; color: #374151; line-height: 1.6; }
    .paper-link { font-size: 12px; color: #4f46e5; margin-top: 6px; display: inline-block; }
    input[type=text] { width: 100%; padding: 11px 14px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; outline: none; margin-bottom: 10px; }
    input[type=text]:focus { border-color: #1e3a8a; }
    .sort-bar { display: flex; gap: 8px; margin-bottom: 12px; align-items: center; font-size: 13px; color: #6b7280; 
 .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #dbeafe; border-top: 3px solid #1e3a8a; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 8px; vertical-align: middle; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
"""

TEXTS = {
    "ko": {
        "title": "📚 논문 & 학술 문서 요약기",
        "subtitle": "PDF 업로드, 텍스트 입력, 또는 논문 자동 검색으로 분석해요",
        "tab_search": "🔎 논문 검색",
        "tab_pdf": "📎 PDF 업로드",
        "tab_text": "📝 텍스트 입력",
        "search_placeholder": "검색어를 입력해요 (예: machine learning, sleep deprivation)",
        "search_btn": "🔍 논문 검색",
        "analyze_btn": "🔍 분석하기",
        "pdf_label": "PDF 파일을 클릭해서 업로드해요",
        "pdf_size": "최대 10MB",
        "text_placeholder": "논문이나 학술 자료 텍스트를 붙여넣어요...",
        "loading": "분석 중...",
        "searching": "검색 중...",
        "sort_label": "정렬:",
        "sort_default": "기본순",
        "sort_alpha": "알파벳순",
        "click_analyze": "클릭해서 분석하기",
        "summary_title": "📌 핵심 요약",
        "keywords_title": "🏷 주요 키워드",
        "source_title": "📎 출처",
        "lang": "언어",
    },
    "en": {
        "title": "📚 Paper & Academic Document Summarizer",
        "subtitle": "Upload PDF, paste text, or search papers automatically",
        "tab_search": "🔎 Search Papers",
        "tab_pdf": "📎 Upload PDF",
        "tab_text": "📝 Enter Text",
        "search_placeholder": "Enter search term (e.g. machine learning, sleep deprivation)",
        "search_btn": "🔍 Search",
        "analyze_btn": "🔍 Analyze",
        "pdf_label": "Click to upload a PDF file",
        "pdf_size": "Max 10MB",
        "text_placeholder": "Paste your paper or academic text here...",
        "loading": "Analyzing...",
        "searching": "Searching...",
        "sort_label": "Sort:",
        "sort_default": "Default",
        "sort_alpha": "Alphabetical",
        "click_analyze": "Click to analyze",
        "summary_title": "📌 Summary",
        "keywords_title": "🏷 Keywords",
        "source_title": "📎 Source",
        "lang": "Language",
    }
}

@app.route('/')
def index():
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>논문 요약기</title>{STYLE}</head>
    <body>
    <div class='navbar'>
        <div>
            <h1 id='nav-title'>📚 논문 & 학술 문서 요약기</h1>
            <p id='nav-subtitle'>PDF 업로드, 텍스트 입력, 또는 논문 자동 검색으로 분석해요</p>
        </div>
        <div class='lang-toggle'>
            <button class='lang-btn active' onclick='setLang("ko")'>한국어</button>
            <button class='lang-btn' onclick='setLang("en")'>English</button>
        </div>
    </div>
    <div class='container'>
        <div class='card'>
            <h2 id='card-title'>📄 문서 입력</h2>
            <span class='tab active' id='tab-btn-search' onclick='switchTab("search", this)'>🔎 논문 검색</span>
            <span class='tab' id='tab-btn-pdf' onclick='switchTab("pdf", this)'>📎 PDF 업로드</span>
            <span class='tab' id='tab-btn-text' onclick='switchTab("text", this)'>📝 텍스트 입력</span>

            <div id='tab-search' class='tab-content active'>
                <input type='text' id='searchInput' placeholder='검색어를 입력해요 (예: machine learning)'>
                <button class='btn' id='search-btn' onclick='searchPapers()'>🔍 논문 검색</button>
                <button class='btn btn-outline' id='sort-alpha-btn' onclick='sortAlpha()' style='display:none;'>알파벳순 정렬</button>
                <div id='searchResult'></div>
            </div>

            <div id='tab-pdf' class='tab-content'>
                <div class='upload-area' onclick='document.getElementById("fileInput").click()'>
                    <input type='file' id='fileInput' accept='.pdf' onchange='handleFile(this)'>
                    <div style='font-size:32px;margin-bottom:8px;'>📎</div>
                    <div id='pdf-label'>PDF 파일을 클릭해서 업로드해요</div>
                    <div id='pdf-size' style='font-size:12px;margin-top:5px;'>최대 10MB</div>
                </div>
                <div id='fileName' class='file-name'></div>
                <button class='btn' id='pdf-analyze-btn' onclick='analyzePdf()'>🔍 분석하기</button>
            </div>

            <div id='tab-text' class='tab-content'>
                <textarea id='textInput' placeholder='논문이나 학술 자료 텍스트를 붙여넣어요...'></textarea>
                <button class='btn' id='text-analyze-btn' onclick='analyzeText()'>🔍 분석하기</button>
            </div>

            <div id='result'></div>
        </div>
    </div>
    <script>
        let currentLang = 'ko';
        let currentTab = 'search';
        let pdfFile = null;
        let allPapers = [];

        const texts = {json.dumps(TEXTS)};

        function setLang(lang) {{
            currentLang = lang;
            document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            const t = texts[lang];
            document.getElementById('nav-title').textContent = t.title;
            document.getElementById('nav-subtitle').textContent = t.subtitle;
            document.getElementById('tab-btn-search').textContent = t.tab_search;
            document.getElementById('tab-btn-pdf').textContent = t.tab_pdf;
            document.getElementById('tab-btn-text').textContent = t.tab_text;
            document.getElementById('searchInput').placeholder = t.search_placeholder;
            document.getElementById('search-btn').textContent = t.search_btn;
            document.getElementById('pdf-label').textContent = t.pdf_label;
            document.getElementById('pdf-size').textContent = t.pdf_size;
            document.getElementById('textInput').placeholder = t.text_placeholder;
            document.getElementById('pdf-analyze-btn').textContent = t.analyze_btn;
            document.getElementById('text-analyze-btn').textContent = t.analyze_btn;
            if (document.getElementById('sort-alpha-btn').style.display !== 'none') {{
                document.getElementById('sort-alpha-btn').textContent = t.sort_alpha;
            }}
        }}

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

        function renderPapers(papers) {{
            const t = texts[currentLang];
            let html = '<div style="margin-top:15px;">';
            papers.forEach(p => {{
                html += `<div class='paper-item' onclick='analyzePaperUrl("${{p.pdf_url}}")'>
                    <div class='paper-title'>${{p.title}}</div>
                    <div class='paper-authors'>${{p.authors}}</div>
                    <div class='paper-year'>${{p.year}}</div>
                    <div class='paper-abstract'>${{p.abstract}}</div>
                    <a class='paper-link' href='${{p.pdf_url}}' target='_blank' onclick='event.stopPropagation()'>📎 ${{p.pdf_url}}</a>
                    <div style='margin-top:8px;'><span class='tag'>${{t.click_analyze}}</span></div>
                </div>`;
            }});
            html += '</div>';
            return html;
        }}

        async function searchPapers() {{
            const query = document.getElementById('searchInput').value;
            if (!query.trim()) return;
            const t = texts[currentLang];
            document.getElementById('searchResult').innerHTML = `<p class="loading"><span class="spinner"></span>${{t.searching}}</p>`;
            document.getElementById('sort-alpha-btn').style.display = 'none';
            const res = await fetch('/search', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{query: query}})
            }});
            allPapers = await res.json();
            document.getElementById('searchResult').innerHTML = renderPapers(allPapers);
            document.getElementById('sort-alpha-btn').style.display = 'inline-block';
            document.getElementById('sort-alpha-btn').textContent = t.sort_alpha;
        }}

        function sortAlpha() {{
            const sorted = [...allPapers].sort((a, b) => a.title.localeCompare(b.title));
            document.getElementById('searchResult').innerHTML = renderPapers(sorted);
        }}

        async function analyzePaperUrl(url) {{
            const t = texts[currentLang];
            document.getElementById('result').innerHTML = `<p class="loading">${{t.loading}}</p>`;
            const res = await fetch('/analyze-url', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{url: url, lang: currentLang}})
            }});
            const data = await res.json();
            showResult(data, url);
        }}

        async function analyzePdf() {{
            if (!pdfFile) return;
            const t = texts[currentLang];
            document.getElementById('result').innerHTML = `<p class="loading">${{t.loading}}</p>`;
            const formData = new FormData();
            formData.append('file', pdfFile);
            formData.append('lang', currentLang);
            const res = await fetch('/analyze-pdf', {{ method: 'POST', body: formData }});
            const data = await res.json();
            showResult(data, null);
        }}

        async function analyzeText() {{
            const text = document.getElementById('textInput').value;
            if (!text.trim()) return;
            const t = texts[currentLang];
            document.getElementById('result').innerHTML = `<p class="loading">${{t.loading}}</p>`;
            const res = await fetch('/analyze-text', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{text: text, lang: currentLang}})
            }});
            const data = await res.json();
            showResult(data, null);
        }}

        function showResult(data, sourceUrl) {{
            const t = texts[currentLang];
            if (data.error) {{ document.getElementById('result').innerHTML = '<p style="color:red;">Error: ' + data.error + '</p>'; return; }}
            let html = '<br>';
            html += `<div class="section"><div class="section-title">${{t.summary_title}}</div>`;
            html += `<div class="summary-box">${{data.summary}}</div></div>`;
            html += `<div class="section"><div class="section-title">${{t.keywords_title}}</div><div>`;
            data.keywords.forEach(k => {{ html += `<span class="tag">${{k}}</span>`; }});
            html += '</div></div>';
            if (sourceUrl) {{
                html += `<div class="section"><div class="section-title">${{t.source_title}}</div>`;
                html += `<a href="${{sourceUrl}}" target="_blank" class="paper-link">${{sourceUrl}}</a></div>`;
            }}
            document.getElementById('result').innerHTML = html;
	    document.getElementById('result').scrollIntoView({{behavior: 'smooth'}});
        }}
    </script>
    </body></html>
    """)

def ai_analyze(text, lang='ko'):
    text = text[:8000]
    lang_instruction = "한국어로 답해줘" if lang == 'ko' else "Answer in English"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f'''너는 학술 논문 분석 전문가야. 반드시 JSON만 출력해. 다른 텍스트 절대 금지. {lang_instruction}.
형식: {{
    "summary": "핵심 내용 5~7줄 요약 (줄바꿈은 <br>으로)",
    "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
}}'''},
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
        results = list(search_client.results(arxiv.Search(query=query, max_results=10)))
        papers = []
        for r in results:
            papers.append({
                "title": r.title,
                "authors": ", ".join([a.name for a in r.authors[:3]]),
                "year": r.published.strftime("%Y"),
                "abstract": r.summary[:200] + "...",
                "pdf_url": r.pdf_url
            })
        return jsonify(papers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-url', methods=['POST'])
def analyze_url():
    try:
        url = request.json['url']
        lang = request.json.get('lang', 'ko')
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        pdf = fitz.open(stream=response.content, filetype="pdf")
        text = ""
        for page in pdf:
            text += page.get_text()
        pdf.close()
        return jsonify(ai_analyze(text, lang))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-pdf', methods=['POST'])
def analyze_pdf():
    try:
        file = request.files['file']
        lang = request.form.get('lang', 'ko')
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in pdf:
            text += page.get_text()
        pdf.close()
        return jsonify(ai_analyze(text, lang))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-text', methods=['POST'])
def analyze_text():
    try:
        text = request.json['text']
        lang = request.json.get('lang', 'ko')
        return jsonify(ai_analyze(text, lang))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)