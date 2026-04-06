논문 & 학술 문서 요약기

논문이나 학술 자료를 PDF 업로드 또는 텍스트 붙여넣기로 입력하면 AI가 핵심만 정리해주는 웹 서비스

사용 기술
- Python, Flask
- OpenAI API (gpt-4o-mini)
- PyMuPDF (PDF 파싱)
- HTML/CSS

주요 기능
- PDF 파일 직접 업로드
- 텍스트 직접 입력
- 핵심 내용 3줄 요약
- 주요 키워드 자동 추출
- 인용할 만한 문장 추출
- 한 줄 결론 생성

실행 방법
1. 필요한 라이브러리 설치
pip install flask openai pymupdf

2. OpenAI API 키 환경변수 설정
export OPENAI_API_KEY="your-api-key"

3. 실행
python3 app.py

4. 브라우저에서 접속
http://127.0.0.1:5000

타깃
- 논문 읽어야 하는 대학생
- 학술 자료 정리가 필요한 연구자
- 긴 문서 빠르게 파악해야 하는 직장인