import os
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import glob

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ChromaDB 클라이언트 초기화 (로컬 저장)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# 컬렉션 생성 또는 가져오기
collection = chroma_client.get_or_create_collection(
    name="md_documents",
    metadata={"description": "MD 파일 임베딩 컬렉션"}
)

def get_openai_embedding(text):
    """OpenAI API를 사용하여 텍스트 임베딩 생성"""
    response = client.embeddings.create(
        model="text-embedding-3-small",  # 또는 "text-embedding-3-large"
        input=text
    )
    return response.data[0].embedding

def process_md_files(directory_path):
    """MD 파일들을 읽어서 임베딩 생성 및 ChromaDB에 저장"""
    
    md_files = glob.glob(f"{directory_path}/**/*.md", recursive=True)
    
    print(f"총 {len(md_files)}개의 MD 파일을 찾았습니다.")
    
    for idx, file_path in enumerate(md_files):
        print(f"처리 중: {file_path} ({idx+1}/{len(md_files)})")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 파일이 이미 chunking 되어 있다면 그대로 사용
            # 아니면 여기서 chunking 수행
            chunks = split_into_chunks(content)
            
            for chunk_idx, chunk in enumerate(chunks):
                # 임베딩 생성
                embedding = get_openai_embedding(chunk)
                
                # ChromaDB에 저장
                collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "source": file_path,
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks)
                    }],
                    ids=[f"{file_path}_{chunk_idx}"]
                )
            
            print(f"  ✓ {len(chunks)}개 청크 처리 완료")
            
        except Exception as e:
            print(f"  ✗ 오류 발생: {str(e)}")

def split_into_chunks(text, chunk_size=1000, overlap=200):
    """텍스트를 chunk로 분할 (이미 chunking 되어 있다면 생략 가능)"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks

def query_rag(query_text, n_results=3):
    """RAG 검색 수행"""
    # 쿼리 임베딩 생성
    query_embedding = get_openai_embedding(query_text)
    
    # 유사한 문서 검색
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results

# 사용 예시
if __name__ == "__main__":
    # 1. MD 파일들을 처리하여 ChromaDB에 저장
    print("=== 임베딩 생성 및 저장 시작 ===")
    process_md_files("./output_folder")  # MD 파일이 있는 디렉토리 경로
    
    print("\n=== 저장 완료 ===")
    print(f"총 {collection.count()}개의 문서가 저장되었습니다.")
    
    # 2. 테스트 쿼리
    print("\n=== 테스트 쿼리 ===")
    test_query = "여기에 테스트 질문을 입력하세요"
    results = query_rag(test_query, n_results=3)
    
    print(f"\n쿼리: {test_query}")
    print("\n검색 결과:")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n[결과 {i+1}]")
        print(f"출처: {metadata['source']}")
        print(f"내용: {doc[:200]}...")  # 처음 200자만 출력