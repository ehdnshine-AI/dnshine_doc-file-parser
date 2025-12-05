# dnshine_doc-file-parser

간단한 문서 변환 및 분할 도구 모음

이 저장소는 `.docx` 파일을 Markdown으로 변환하는 스크립트와, Markdown 파일을 헤딩 기준으로 잘라 페이지(청크)로 만드는 도구를 포함합니다.

주요 스크립트

- `docs_parser.py` – `.docx` 문서를 Markdown으로 변환하며 문단, 제목, 표, 이미지(추출) 및 하이퍼링크를 처리합니다.
- `md_chunker.py` – Markdown 파일을 지정한 헤딩 레벨(#) 기준으로 분할하고, 길이가 너무 긴 섹션은 문단 단위로 더 작은 청크로 나눕니다. 결과는 디스크에 여러 `.md` 파일과 `index.json`로 저장됩니다.

⚙️ 요구사항

# dnshine_doc-file-parser

간단한 문서 변환 및 분할 도구 모음

이 저장소는 다음 두 가지 주요 스크립트를 포함합니다:

- **`docs-parser.py`**  
  `.docx` 파일을 Markdown으로 변환합니다.  
  - 문단, 제목 스타일을 Markdown 헤딩으로 변환  
  - 표를 Markdown 표 형식으로 변환  
  - 삽입 이미지 추출 및 Markdown에 이미지 링크 삽입  
  - 하이퍼링크 처리  
  - 단일 파일 변환과 디렉토리 배치 변환 모드 지원  
  - CLI 인자: `--file` 또는 `--input-dir`, `--output-dir`, `--images-subdir`, `--recursive`, `--quiet`, `--verbose`

- **`excel-parser.py`**  
  Excel `.xlsx` 파일의 시트를 Markdown 표로 변환합니다.  
  - 특정 시트 또는 모든 시트 변환 가능  
  - MarkdownTableWriter를 사용하여 표 출력  
  - CLI 인자: `--file` (필수), `--output-dir`, `--sheet`, `--quiet`, `--verbose`  

---

## 요구사항 및 설치

- Python 3.8 이상 권장  
- 필수 패키지 설치 (최소):  
  ```
  python -m pip install python-docx pandas openpyxl pytablewriter
  ```
- (옵션) 테스트용: `pytest`, `Pillow`

---

## 사용법 예시

### docs-parser.py

- 디렉토리 배치 변환 (하위폴더 재귀 포함):  
  ```
  python docs-parser.py --input-dir path/to/docx_folder --output-dir path/to/output_folder --recursive --verbose
  ```

- 단일 파일 변환:  
  ```
  python docs-parser.py --file path/to/file.docx --output-dir path/to/output_folder
  ```

---

### excel-parser.py

- 전체 시트 Markdown 변환 (기본, 모든 시트):  
  ```
  python excel-parser.py --file path/to/file.xlsx --output-dir path/to/output_folder
  ```

- 특정 시트만 변환:  
  ```
  python excel-parser.py --file path/to/file.xlsx --sheet Sheet1 --output-dir path/to/output_folder
  ```

---

## 개발 및 확장 아이디어

- 변환 품질 향상: 리스트, 코드 블록, 인용 등 Markdown 요소 추가 파싱  
- 대규모 문서 병렬 처리 및 진행률 표시  
- 명명 충돌 방지를 위한 파일명 고도화  
- GUI 앱 또는 웹 인터페이스 개발  

---

## 기여 및 라이선스

- Fork 및 Pull Request 환영  
- 이 저장소에는 현재 LICENSE 파일이 없습니다. 필요 시 라이선스 추가 권장  

---


# RAG 구축 


## 구축 환경
<pre>
  PRETTY_NAME="Ubuntu 24.04.3 LTS"
  NAME="Ubuntu"
  VERSION_ID="24.04"
  VERSION="24.04.3 LTS (Noble Numbat)"
  VERSION_CODENAME=noble
  ID=ubuntu
  ID_LIKE=debian
  HOME_URL="https://www.ubuntu.com/"
  SUPPORT_URL="https://help.ubuntu.com/"
  BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
  PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
  UBUNTU_CODENAME=noble
  LOGO=ubuntu-logo
</pre>

## python install

```
  python3 --version
  pip3 --version

  # 설치되어 있지 않다면
  sudo apt update
  sudo apt install python3 python3-pip -y

  # venv 설치
  sudo apt install python3-venv -y

  # 가상환경 생성
  python3 -m venv ~/venv312

  # 가상환경 활성화
  source ~/venv312/bin/activate
```

## 필요한 패키지 설치

```
  python -m pip install --upgrade pip
  python -m pip install fastapi uvicorn chromadb openai pydantic
  python -m pip install python-docx pandas openpyxl pytablewriter

```
## 프로젝트 구조
<pre>

  rag_project/
  ├── .env                      # 환경 변수
  ├── requirements.txt          # Python 패키지 목록
  ├── rag_embedding.py          # 임베딩 생성 및 저장 스크립트
  ├── rag_server.py            # FastAPI 서버
  ├── test_client.py           # 테스트 클라이언트
  ├── md_files/                # MD 파일들이 저장될 디렉토리
  │   ├── doc1.md
  │   └── doc2.md
  └── chroma_db/               # ChromaDB 데이터 (자동 생성)

  </pre>

```
  cat > requirements.txt << EOF
  fastapi==0.109.0
  uvicorn[standard]==0.27.0
  chromadb==0.4.22
  openai==1.10.0
  pydantic==2.5.0
  python-dotenv==1.0.0
  EOF

```

```
python rag_embedding.py
```

## 3단계: 임베딩 생성 및 저장
<pre>
  ==================================================
  RAG 시스템 - 임베딩 생성 및 저장
  ==================================================

  선택하세요:
  1. MD 파일 임베딩 생성 및 저장
  2. 테스트 검색
  3. 데이터베이스 초기화
  4. 종료

  선택 (1-4): 1
  MD 파일 디렉토리 경로 (기본값: ./md_files): 

  📁 디렉토리: ./md_files
  📚 총 5개의 MD 파일을 찾았습니다.

  처리 중: ./md_files/doc1.md (1/5)
    ✅ 3개 청크 처리 완료

  ...

  ==================================================
  ✅ 저장 완료!
  📊 총 15개의 청크가 저장되었습니다.
  ==================================================
</pre>
## 4단계: FastAPI 서버 실행
### 서버 실행
```
python rag_server.py
```

### 또는 uvicorn으로 실행 (개발 모드)
```
uvicorn rag_server:app --reload --host 0.0.0.0 --port 8000

```

### 출력 예시
<pre>
  🚀 RAG API 서버를 시작합니다...
  📖 API 문서: http://localhost:8000/docs
  INFO:     Started server process
  INFO:     Uvicorn running on http://0.0.0.0:8000
</pre>

#### curl 상태 확인
```
curl http://localhost:8000/health
```

#### 문서 검색
```
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "RAG란 무엇인가요?",
    "n_results": 3
  }'
```

#### RAG 질의응답
```
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "RAG의 주요 구성요소는 무엇인가요?",
    "n_results": 3,
    "model": "gpt-4o-mini"
  }'
```

### python request 

```
import requests

# 질의응답
response = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "RAG 시스템의 장점은?",
        "n_results": 3,
        "model": "gpt-4o-mini"
    }
)

print(response.json()['answer'])

```

