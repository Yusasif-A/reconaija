import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

JSON_FOLDER_PATH = "new_processed"
AGENCY_CONTACT_FILE = "agencies_data.json"
MINISTRIES_FILE = "ministries.json" 
CHROMA_PATH = "chroma_store"
COLLECTION_NAME = "Meta_public_service"
BATCH_SIZE = 100  # Increased from 50
MAX_RETRIES = 3
RETRY_DELAY = 5
MAX_WORKERS = 4  # Parallel processing

load_dotenv()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=10
)

print("🔌 Initializing OpenAI embeddings...")
embedding = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=os.getenv("OPENAI_API_KEY"),
    chunk_size=2048,  # Process more embeddings per API call
    max_retries=3
)

print(f"📞 Loading agency contact info from {AGENCY_CONTACT_FILE}...")
agency_contact_map = {}
with open(AGENCY_CONTACT_FILE, "r", encoding="utf-8") as f:
    contacts = json.load(f)
    for contact in contacts:
        acronym = contact.get("agency_acronym", "").upper()
        if acronym:
            agency_contact_map[acronym] = contact
print(f"✅ Loaded {len(agency_contact_map)} agencies")

print(f"📋 Loading ministries info from {MINISTRIES_FILE}...")
ministry_map = {}
with open(MINISTRIES_FILE, "r", encoding="utf-8") as f:
    ministries = json.load(f)
    for item in ministries:
        ministry_name = item.get("ministry", "").upper()  
        minister = item.get("minister", "N/A")
        if ministry_name:
            ministry_map[ministry_name] = minister
print(f"✅ Loaded {len(ministry_map)} ministries")

def build_contact_info(acronym: str) -> str:
    contact = agency_contact_map.get(acronym.upper())
    if not contact:
        return ""
    return f"""Agency: {contact.get('agency', 'N/A')}
Acronym: {acronym.upper()}
Current Head: {contact.get('current head', 'N/A')}
Designation: {contact.get('designation', 'N/A')}
Official Website: {contact.get('official_website', 'N/A')}
Official Email: {contact.get('official_email', 'N/A')}
Official Phone: {contact.get('official_phone_number', 'N/A')}
Official Address: {contact.get('official_address', 'N/A')}
"""

def process_file(file_name):
    """Process a single JSON file and return documents"""
    if not file_name.endswith(".json"):
        return []
    
    file_path = os.path.join(JSON_FOLDER_PATH, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    agency_name = data.get("agency", "")
    acronym = (data.get("acronym") or "").upper()
    ministry = data.get("ministry", "").upper()  
    original_text = data.get("text", "")
    
    minister = ministry_map.get(ministry, "N/A")
    ministry_name_lower = ministry.replace("FEDERAL MINISTRY OF ", "").lower()
    minister_formatted = f"Minister of {ministry_name_lower}: {minister}"
    
    contact_info = build_contact_info(acronym)
    
    base_doc = Document(
        page_content=original_text,
        metadata={
            "ministry": ministry, 
            "minister": minister_formatted,  
            "agency": agency_name,
            "acronym": acronym,
        }
    )
    
    chunks = text_splitter.split_documents([base_doc])
    
    # Prepend contact info to EACH chunk
    processed_chunks = []
    for idx, chunk in enumerate(chunks):
        if contact_info:
            chunk.page_content = f"""=== {agency_name} INFORMATION ===
{contact_info}
=== {agency_name} DETAILS ===
{chunk.page_content}
"""
        chunk.metadata['chunk_id'] = f"{acronym or 'UNKNOWN'}-{idx}"
        processed_chunks.append(chunk)
    
    return processed_chunks

# ================= PARALLEL FILE PROCESSING =================
print(f"📂 Reading JSON files from {JSON_FOLDER_PATH}...")
files = [f for f in os.listdir(JSON_FOLDER_PATH) if f.endswith(".json")]

documents = []
print(f"⚡ Processing {len(files)} files in parallel with {MAX_WORKERS} workers...")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_file = {executor.submit(process_file, f): f for f in files}
    
    completed = 0
    for future in as_completed(future_to_file):
        file_name = future_to_file[future]
        try:
            chunks = future.result()
            documents.extend(chunks)
            completed += 1
            if completed % 10 == 0:
                print(f"  Processed {completed}/{len(files)} files...")
        except Exception as e:
            print(f"❌ Error processing {file_name}: {e}")

print(f"✅ Prepared {len(documents)} chunks for embedding")

# ================= SAVE TO CHROMA =================
if not documents:
    print("⚠️ No documents found. Exiting.")
    exit()

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedding,
    persist_directory=CHROMA_PATH
)

print(f"📦 Adding documents to Chroma in batches of {BATCH_SIZE}...")
total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE

start_time = time.time()

for i in range(0, len(documents), BATCH_SIZE):
    batch_num = i // BATCH_SIZE + 1
    batch_docs = documents[i:i+BATCH_SIZE]
    batch_texts = [d.page_content for d in batch_docs]
    batch_metas = [d.metadata for d in batch_docs]
    batch_ids = [d.metadata['chunk_id'] for d in batch_docs]
    
    retries = 0
    while retries < MAX_RETRIES:
        try:
            vectorstore.add_texts(
                texts=batch_texts,
                metadatas=batch_metas,
                ids=batch_ids
            )
            
            elapsed = time.time() - start_time
            rate = (i + len(batch_docs)) / elapsed if elapsed > 0 else 0
            eta = (len(documents) - (i + len(batch_docs))) / rate if rate > 0 else 0
            
            print(f"✅ Batch {batch_num}/{total_batches} ({i+len(batch_docs)}/{len(documents)} docs) | Rate: {rate:.1f} docs/sec | ETA: {eta:.0f}s")
            break
        except Exception as e:
            retries += 1
            wait = RETRY_DELAY * (2 ** (retries - 1))
            print(f"❌ Batch {batch_num} failed ({retries}/{MAX_RETRIES}): {e}")
            if retries < MAX_RETRIES:
                print(f"   Retrying in {wait}s...")
                time.sleep(wait)

total_time = time.time() - start_time
print(f"\n🎉 Vector store ready at '{CHROMA_PATH}'")
print(f"⏱️  Total time: {total_time:.1f}s | Average: {len(documents)/total_time:.1f} docs/sec")
