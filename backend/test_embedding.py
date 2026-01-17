from api.services.embedding_service import get_embedding

print("Testing Local Embedding Service...")
text = "What is recursion?"
vec = get_embedding(text)

if vec and len(vec) > 0:
    print(f"Success! Generated embedding of length: {len(vec)}")
    print(f"Sample: {vec[:5]}...")
else:
    print("Failed to generate embedding.")
