# dnshine_doc-file-parser

간단한 문서 변환 및 분할 도구 모음

이 저장소는 `.docx` 파일을 Markdown으로 변환하는 스크립트와, Markdown 파일을 헤딩 기준으로 잘라 페이지(청크)로 만드는 도구를 포함합니다.

주요 스크립트

- `docs-parser.py` – `.docx` 문서를 Markdown으로 변환하며 문단, 제목, 표, 이미지(추출) 및 하이퍼링크를 처리합니다.
- `md_chunker.py` – Markdown 파일을 지정한 헤딩 레벨(#) 기준으로 분할하고, 길이가 너무 긴 섹션은 문단 단위로 더 작은 청크로 나눕니다. 결과는 디스크에 여러 `.md` 파일과 `index.json`로 저장됩니다.

⚙️ 요구사항

- Python 3.8+ (권장)
- 설치 필요 패키지:
  - python-docx (docs-parser.py에서 사용)

간단 설치 (venv 권장)

```powershell
# 윈도우즈 PowerShell 예시
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install python-docx
```

---

사용법 — docs-parser.py

`docs-parser.py`는 현재 파일 하단의 실행 예시를 통해 바로 실행할 수 있습니다. 예시 부분의 경로를 실제 파일 경로로 바꾼 뒤 실행하세요.

```powershell
# docs-parser.py 파일 안의 예시 경로를 사용자 환경에 맞게 수정한 뒤
python docs-parser.py
```

스크립트는 다음을 수행합니다:
- 문서의 문단을 Markdown로 변환
- 스타일이 Heading이면 적절한 Markdown 제목(#)으로 변환
- 표는 Markdown 테이블 형태로 출력
- 삽입된 이미지는 지정된 폴더로 추출하고 Markdown에 링크 추가
- 하이퍼링크는 [텍스트](URL) 형태로 변환

※ 참고: `docs-parser.py`는 라이브러리 함수 `docx_to_markdown_full`를 노출하므로, 필요하다면 직접 임포트해 재사용하거나 실행부를 수정하여 CLI 인자 파싱 기능을 추가할 수 있습니다.

---

사용법 — md_chunker.py

`md_chunker.py`는 Command-line 인터페이스를 제공합니다. 예:

```powershell
python md_chunker.py C:\path\to\output.md --out-dir C:\path\to\output_chunks --level 1 --max-chars 20000 --min-chars 500 --prefix page
```

주요 옵션:
- `infile` : 분할할 Markdown 파일 경로
- `--out-dir` : 청크를 쓸 출력 폴더 (기본: `./md_chunks`)
- `--level` : 헤딩 레벨(1 ~ 6) — 이 레벨의 헤딩을 기준으로 분할합니다
- `--max-chars` : 청크 최대 문자 수 (기본: 10000), 넘칠 경우 문단 단위로 분할 시도
- `--min-chars` : 작은 청크 병합을 고려하는 기준 길이(기본: 200)
- `--prefix` : 생성 파일 이름 접두사

출력:
- 여러 개의 `NNN_prefix_{heading}.md` 파일
- `index.json` : 생성된 파일 목록 및 메타(파일명, 헤딩, 문자 수)

---

개발자 가이드 / 확장 아이디어

- `docs-parser.py`에 CLI 인자 파싱을 추가하여 입력/출력 경로와 이미지 폴더를 인자로 받도록 개선
- 마크다운 변환 품질 향상 (인라인 스타일, 리스트, 인용, 코드 블록 등 추가 파싱)
- 병렬 이미지 추출 및 파일명 충돌 보호
- 더 나은 파일명 정규화/충돌 해결 로직

---

기여 및 라이선스

- 개선 사항이나 버그 리포트는 Pull Request 또는 Issue로 환영합니다.
- 현재 저장소에 LICENSE 파일이 없습니다. 사용/배포 시 라이선스를 명시하려면 `LICENSE` 파일을 추가하세요.

---

문의

저자: ehdnshine-AI (저장소: dnshine_doc-file-parser)

즐겁게 사용하세요! ✨
