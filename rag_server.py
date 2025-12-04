from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from openai import OpenAI
import os
from typing import List, Optional
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 초기화
app = FastAPI(
    title="RAG API Server",
    description="ChromaDB와 OpenAI를 사용한 RAG 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ChromaDB 클라이언트 초기화
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="md_documents")

# 요청/응답 모델
class QueryRequest(BaseModel):
    question: str
    n_results: Optional[int] = 3
    model: Optional[str] = "gpt-4o-mini"

class SearchResult(BaseModel):
    content: str
    source: str
    filename: str
    chunk_index: int

class QueryResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    model_used: str

class HealthResponse(BaseModel):
    status: str
    documents_count: int

def get_openai_embedding(text: str):
    """OpenAI 임베딩 생성"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def search_similar_documents(query: str, n_results: int = 3):
    """유사 문서 검색"""
    query_embedding = get_openai_embedding(query)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results

def generate_answer(question: str, context_docs: list, model: str = "gpt-4o-mini"):
    """LLM을 사용하여 답변 생성"""
    
    # 컨텍스트 구성
    context = "\n\n".join([
        f"[문서 {i+1}]\n{doc}" 
        for i, doc in enumerate(context_docs)
    ])
    
    # 프롬프트 구성
    prompt = f"""다음 문서들을 참고하여 질문에 답변해주세요.
답변은 한국어로 작성하고, 제공된 문서의 내용을 기반으로 해주세요.
문서에 없는 내용이라면 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 답변해주세요.

참고 문서:
{context}

질문: {question}

답변:"""
    
    # OpenAI API 호출
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "당신은 문서 기반 질의응답을 수행하는 도움이 되는 AI 어시스턴트입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    
    return response.choices[0].message.content

@app.get("/", response_model=dict)
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "RAG API 서버에 오신 것을 환영합니다",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health - 서버 상태 확인",
            "query": "POST /query - RAG 질의응답",
            "search": "POST /search - 문서 검색만",
            "docs": "GET /docs - API 문서 (Swagger UI)"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 상태 확인"""
    try:
        doc_count = collection.count()
        return HealthResponse(
            status="healthy",
            documents_count=doc_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """RAG 질의응답"""
    try:
        # 1. 유사 문서 검색
        search_results = search_similar_documents(
            request.question, 
            request.n_results
        )
        
        if not search_results['documents'][0]:
            raise HTTPException(
                status_code=404, 
                detail="관련 문서를 찾을 수 없습니다"
            )
        
        # 2. LLM으로 답변 생성
        answer = generate_answer(
            request.question,
            search_results['documents'][0],
            request.model
        )
        
        # 3. 응답 구성
        sources = [
            SearchResult(
                content=doc[:200] + "..." if len(doc) > 200 else doc,
                source=meta.get('source', 'unknown'),
                filename=meta.get('filename', 'unknown'),
                chunk_index=meta.get('chunk_index', 0)
            )
            for doc, meta in zip(
                search_results['documents'][0],
                search_results['metadatas'][0]
            )
        ]
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            model_used=request.model
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류: {str(e)}")

@app.post("/search")
async def search_documents(request: QueryRequest):
    """문서 검색만 수행 (LLM 답변 없이)"""
    try:
        search_results = search_similar_documents(
            request.question,
            request.n_results
        )
        
        if not search_results['documents'][0]:
            return {"results": [], "message": "관련 문서를 찾을 수 없습니다"}
        
        results = [
            {
                "content": doc,
                "source": meta.get('source', 'unknown'),
                "filename": meta.get('filename', 'unknown'),
                "chunk_index": meta.get('chunk_index', 0),
                "similarity_score": 1 - dist  # distance를 similarity로 변환
            }
            for doc, meta, dist in zip(
                search_results['documents'][0],
                search_results['metadatas'][0],
                search_results['distances'][0]
            )
        ]
        
        return {
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 RAG API 서버를 시작합니다...")
    print("📖 API 문서: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)