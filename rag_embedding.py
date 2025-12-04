import os
import chromadb
from openai import OpenAI
import glob
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

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

def split_into_chunks(text, chunk_size=1000, overlap=200):
    """텍스트를 chunk로 분할"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # 빈 청크는 건너뛰기
        if chunk.strip():
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks

def process_md_files(directory_path):
    """MD 파일들을 읽어서 임베딩 생성 및 ChromaDB에 저장"""
    
    md_files = glob.glob(f"{directory_path}/**/*.md", recursive=True)
    
    if not md_files:
        print(f"{directory_path}에서 MD 파일을 찾을 수 없습니다.")
        return
    
    print(f"총 {len(md_files)}개의 MD 파일을 찾았습니다.")
    
    total_chunks = 0
    
    for idx, file_path in enumerate(md_files):
        print(f"\n처리 중: {file_path} ({idx+1}/{len(md_files)})")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 텍스트를 청크로 분할
            chunks = split_into_chunks(content)
            
            if not chunks:
                print(f"파일이 비어있거나 처리할 수 없습니다.")
                continue
            
            for chunk_idx, chunk in enumerate(chunks):
                # 임베딩 생성
                embedding = get_openai_embedding(chunk)
                
                # ChromaDB에 저장
                doc_id = f"{os.path.basename(file_path)}_{chunk_idx}"
                
                collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "source": file_path,
                        "filename": os.path.basename(file_path),
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks)
                    }],
                    ids=[doc_id]
                )
            
            total_chunks += len(chunks)
            print(f"{len(chunks)}개 청크 처리 완료")
            
        except Exception as e:
            print(f"오류 발생: {str(e)}")
    
    return total_chunks

def query_test(query_text, n_results=3):
    """RAG 검색 테스트"""
    # 쿼리 임베딩 생성
    query_embedding = get_openai_embedding(query_text)
    
    # 유사한 문서 검색
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results

def reset_database():
    """데이터베이스 초기화 (모든 데이터 삭제)"""
    try:
        chroma_client.delete_collection(name="md_documents")
        print("데이터베이스가 초기화되었습니다.")
    except:
        print("초기화할 데이터가 없습니다.")

# 메인 실행
if __name__ == "__main__":
    print("="*60)
    print("RAG 시스템 - 임베딩 생성 및 저장")
    print("="*60)
    
    # 사용자 선택
    print("\n선택하세요:")
    print("1. MD 파일 임베딩 생성 및 저장")
    print("2. 테스트 검색")
    print("3. 데이터베이스 초기화")
    print("4. 종료")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice == "1":
        directory = input("MD 파일 디렉토리 경로 (기본값: ./md_files): ").strip()
        if not directory:
            directory = "./output_folder"
        
        print(f"\n📁 디렉토리: {directory}")
        total = process_md_files(directory)
        
        print("\n" + "="*60)
        print(f"✅ 저장 완료!")
        print(f"📊 총 {collection.count()}개의 청크가 저장되었습니다.")
        print("="*60)
    
    elif choice == "2":
        query = input("\n검색할 질문을 입력하세요: ").strip()
        if query:
            print("\n🔍 검색 중...\n")
            results = query_test(query, n_results=3)
            
            print(f"질문: {query}\n")
            print("검색 결과:")
            print("-"*60)
            
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"\n[결과 {i+1}]")
                print(f"📄 출처: {metadata['filename']}")
                print(f"📍 청크: {metadata['chunk_index'] + 1}/{metadata['total_chunks']}")
                print(f"📝 내용: {doc[:300]}...")
                print("-"*60)
    
    elif choice == "3":
        confirm = input("정말 데이터베이스를 초기화하시겠습니까? (yes/no): ").strip().lower()
        if confirm == "yes":
            reset_database()
    
    elif choice == "4":
        print("종료합니다.")
    
    else:
        print("잘못된 선택입니다.")