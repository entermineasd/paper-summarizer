from flask import Flask, request, render_template_string, jsonify
from openai import OpenAI
import os
import json
import fitz  # pymupdf

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
    .btn { display: inline-block; padding: 11px 28px; background: #1e3a8a; color: white; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; margin-top: 12px; }
    .btn:hover { background: #1e40af; }
    .section { margin-bottom: 20px; }
    .section-title { font-size: 12px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
    .summary-box { background: #eff6ff; border-left: 4px solid #1e3a8a; padding: 15px 18px; border-radius: 6px; font-size: 14px; line-height: 1.8; }
    .quote-box { background: #f9fafb; border-left: 4px solid #6b7280; padding: 12px 18px; border-radius: 6px; font-size: 13px; line-height: 1.7; margin-bottom: 8px; color: #374151; font-style: italic; }
    .tag { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; background: #dbeafe; color: #1e3a8a; margin: 4px 3px; }
    .conclusion-box { background: #ecfdf5; border-left: 4px solid #10b981; padding: 15px 18px; border-radius: 6px; font-size: 14px; line-height: 1.8; }
    .loading { color: #888; font-size: 14px; margin-top: 15px; }
    .file-name { font-size: 13px; color: #1e3a8a; margin-top: 8px; font-weight: 600; }
</style>
"""

@app.route('/')
def index():
    return render_template_string(f"""
    <!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>논문 요약기</title>{STYLE}</head>
    <body>
    <div class='navbar'>
        <h1>📚 논문 & 학술 문서 요약기</h1>
        <p>PDF 업로드 또는 텍스트 붙여넣기로 논문을 분석해요</p>
    </div>
    <div class='container'>
        <div class='card'>
            <h2>📄 문서 입력</h2>
            <span class='tab active' onclick='switchTab("pdf")'>📎 PDF 업로드</span>
            <span class='tab' onclick='switchTab("text")'>📝 텍스트 입력</span>

            <div id='tab-pdf' class='tab-content active'>
                <div class='upload-area' onclick='document.getElementById("fileInput").click()'>
                    <input type='file' id='fileInput' accept='.pdf' onchange='handleFile(this)'>
                    <div style='font-size:32px;margin-bottom:8px;'>📎</div>
                    <div>PDF 파일을 클릭해서 업로드해요</div>
                    <div style='font-size:12px;margin-top:5px;'>최대 10MB</div>
                </div>
                <div id='fileName' class='file-name'></div>
            </div>

            <div id='tab-text' class='tab-content'>
                <textarea id='textInput' placeholder='논문이나 학술 자료 텍스트를 붙여넣어요...'></textarea>
            </div>

            <button class='btn' onclick='analyze()'>🔍 분석하기</button>
            <div id='result'></div>
        </div>
    </div>
    <script>
        let currentTab = 'pdf';
        let pdfFile = null;

        function switchTab(tab) {{
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
        }}

        function handleFile(input) {{
            pdfFile = input.files[0];
            document.getElementById('fileName').textContent = '✅ ' + pdfFile.name;
        }}

        async function analyze() {{
            document.getElementById('result').innerHTML = '<p class="loading">분석 중... (PDF는 시간이 조금 걸려요)</p>';

            let res;
            if (currentTab === 'pdf' && pdfFile) {{
                const formData = new FormData();
                formData.append('file', pdfFile);
                res = await fetch('/analyze-pdf', {{ method: 'POST', body: formData }});
            }} else {{
                const text = document.getElementById('textInput').value;
                if (!text.trim()) {{ document.getElementById('result').innerHTML = ''; return; }}
                res = await fetch('/analyze-text', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{text: text}})
                }});
            }}

            const data = await res.json();
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

@app.route('/analyze-text', methods=['POST'])
def analyze_text():
    try:
        text = request.json['text']
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

if __name__ == '__main__':
    app.run(debug=True)