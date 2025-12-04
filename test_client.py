import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """서버 상태 확인"""
    print("\n=== 서버 상태 확인 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_search(question, n_results=3):
    """문서 검색 테스트"""
    print(f"\n=== 문서 검색 테스트 ===")
    print(f"질문: {question}")
    
    response = requests.post(
        f"{BASE_URL}/search",
        json={
            "question": question,
            "n_results": n_results
        }
    )
    
    print(f"상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n검색 결과 ({data['total']}개):")
        for i, result in enumerate(data['results']):
            print(f"\n[결과 {i+1}]")
            print(f"파일명: {result['filename']}")
            print(f"청크: {result['chunk_index']}")
            print(f"유사도: {result['similarity_score']:.4f}")
            print(f"내용: {result['content'][:150]}...")
    else:
        print(f"오류: {response.text}")

def test_query(question, model="gpt-4o-mini"):
    """RAG 질의응답 테스트"""
    print(f"\n=== RAG 질의응답 테스트 ===")
    print(f"질문: {question}")
    print(f"모델: {model}")
    
    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "question": question,
            "n_results": 3,
            "model": model
        }
    )
    
    print(f"\n상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📝 답변:")
        print(data['answer'])
        print(f"\n📚 참고 문서:")
        for i, source in enumerate(data['sources']):
            print(f"\n  [{i+1}] {source['filename']} (청크 {source['chunk_index']})")
            print(f"      {source['content'][:100]}...")
    else:
        print(f"오류: {response.text}")

if __name__ == "__main__":
    print("="*60)
    print("RAG API 테스트 클라이언트")
    print("="*60)
    
    # 1. 서버 상태 확인
    test_health()
    
    # 2. 문서 검색 테스트
    test_search("여기에 검색할 내용을 입력하세요")
    
    # 3. RAG 질의응답 테스트
    test_query("여기에 질문을 입력하세요")
    
    print("\n" + "="*60)
    print("테스트 완료!")
    print("="*60)