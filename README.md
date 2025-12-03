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

## 문의

저자: ehdnshine-AI (dnshine_doc-file-parser)

즐겁게 사용하세요! ✨
