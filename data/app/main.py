from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

# -------------------------
# Simple chat memory
# -------------------------
chat_history = []
MAX_HISTORY = 5  # keep last 5 interactions

# -------------------------
# Load data safely
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
knowledge_file = r"C:\Users\jammi\OneDrive\Desktop\AI-customer-support\data\cricket_teams.txt"

with open(knowledge_file, "r", encoding="utf-8") as f:
    cricket_text = f.read()

print("Cricket knowledge loaded")

# -------------------------
# Split text into chunks
# -------------------------
chunks = [chunk.strip() for chunk in cricket_text.split("\n\n") if chunk.strip()]

print(f"Total chunks created: {len(chunks)}")

# -------------------------
# Create embeddings
# -------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(chunks)

print("Embeddings created")

# -------------------------
# Store embeddings in FAISS
# -------------------------
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

print("Embeddings stored in FAISS")

def format_team_answer(chunk: str, query: str) -> str:
    lines = [line.strip() for line in chunk.split("\n") if line.strip()]

    team_name = lines[0].replace(":", "")
    players = lines[1:]

    # Check if question is about a player
    for player in players:
        if player.lower() in query.lower():
            response = f"{player} belongs to {team_name}.\n\n"
            response += f"{team_name} Players:\n"
            for p in players:
                response += f"• {p}\n"
            return response

    # Otherwise return team players
    response = f"{team_name} Players:\n"
    for p in players:
        response += f"• {p}\n"

    return response

def build_context(history):
    context = ""
    for h in history:
        context += f"User: {h['question']}\n"
        context += f"AI: {h['answer']}\n"
    return context

# -------------------------
# Ask user questions safely
# -------------------------
THRESHOLD = 1.2

while True:
    query = input("\nAsk a question (or type exit): ")
    if query.lower() == "exit":
        break

    # Build context (for future LLM use)
    context = build_context(chat_history)

    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, k=1)

    best_distance = distances[0][0]
    best_chunk = chunks[indices[0][0]]

    if best_distance > THRESHOLD:
        answer = "Sorry, I don't have information related to your question."
    else:
        answer = format_team_answer(best_chunk, query)

    print("\nAnswer:\n", answer)

    # Save to history
    chat_history.append({
        "question": query,
        "answer": answer
    })

    # Keep memory short
    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)
