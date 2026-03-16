from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
import re
import json
import requests
import numpy as np
from datetime import datetime
import traceback
import sys

import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from langchain_community.document_loaders import PyPDFLoader, TextLoader

from database import init_db, save_application, application_id_exists, generate_application_id

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()

# ── Initialize FastAPI ────────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Groq client ───────────────────────────────────────────────────────────────
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
print(f">>> GROQ_API_KEY loaded: {'YES' if os.getenv('GROQ_API_KEY') else 'NO - THIS IS THE PROBLEM'}")

# ── Model config ──────────────────────────────────────────────────────────────
FAST_MODEL = "llama-3.1-8b-instant"   # for intent, reranking, query rewrite, context generation
CHAT_MODEL = "llama-3.3-70b-versatile" # for final user-facing responses only

# ── Embedding model ───────────────────────────────────────────────────────────
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ── ChromaDB — documents ──────────────────────────────────────────────────────
doc_chroma_client = chromadb.PersistentClient(path="./mudra_rag_db")
collection = doc_chroma_client.get_or_create_collection(
    name="mudra_scheme_docs",
    metadata={"heuristic": "cosine"}
)

# ── ChromaDB — conversation history ──────────────────────────────────────────
history_chroma_client = chromadb.PersistentClient(path="./mudra_history_db")
history_collection = history_chroma_client.get_or_create_collection(
    name="conversation_history",
    metadata={"heuristic": "cosine"}
)

# ── Initialize database ───────────────────────────────────────────────────────
init_db()

# ── Application state ─────────────────────────────────────────────────────────
current_intent = "form_filling"

application_data = {
    "full_name": None,
    "aadhaar_number": None,
    "pan_number": None,
    "date_of_birth": None,
    "gender": None,
    "category": None,
    "mobile_number": None,
    "email": None,
    "residential_address": None,
    "business_name": None,
    "business_type": None,
    "business_description": None,
    "business_address": None,
    "business_status": None,
    "years_in_operation": None,
    "number_of_employees": None,
    "loan_category": None,
    "loan_amount": None,
    "loan_purpose": None,
    "preferred_bank": None,
    "documents_provided": []
}

# ── Conversation history state ────────────────────────────────────────────────
history_chunks = []
history_bm25 = None
history_message_counter = 0
recent_messages_window = []
CONTEXT_WINDOW_SIZE = 3

# ── BM25 index for documents ──────────────────────────────────────────────────
all_chunks = []
bm25_index = None


# =============================================================================
# PROMPTS
# =============================================================================

form_filling_prompt = """
ROLE
You are a Government Digital Assistant helping citizens apply for a PM Mudra Yojana loan.
Your job is to collect information step-by-step and complete a structured application form.

IMPORTANT PRINCIPLE
This is a structured form collection task, not a general conversation.
You must only ask for missing information and validate user input.

The current application state will be provided separately as:
APPLICATION_DATA (fields already collected and fields still missing)

Your task is to determine the next field needed and ask the user for it.


APPLICATION FORM STRUCTURE

SECTION 1 — PERSONAL DETAILS
1. full_name
2. aadhaar_number (12 digits)
3. pan_number (ABCDE1234F format)
4. date_of_birth (DD/MM/YYYY)
5. gender (Male/Female/Other)
6. category (General/SC/ST/OBC/Minority)
7. mobile_number (10 digits)
8. email
9. residential_address

SECTION 2 — BUSINESS DETAILS
10. business_name
11. business_type (Manufacturing/Trading/Services)
12. business_description
13. business_address
14. business_status (Existing/New)
15. years_in_operation (ONLY if Existing)
16. employee_count

SECTION 3 — LOAN DETAILS
17. loan_category (Shishu/Kishore/Tarun)
18. loan_amount
19. loan_purpose (equipment / working capital / expansion)
20. preferred_bank

SECTION 4 — DOCUMENT CONFIRMATION
21. confirm_documents_ready

DOCUMENTS REQUIRED

Mandatory:
- Aadhaar card
- PAN card
- Passport size photo
- Address proof of business
- Bank statement (last 6 months)

Conditional:
- Business proof (if business is existing)
- Caste certificate (if category is SC/ST/OBC/Minority)


STRICT VALIDATION RULES

AADHAAR: Must be exactly 12 digits. No spaces, letters, or symbols.
PAN: Format: 5 uppercase letters + 4 digits + 1 uppercase letter. Example: ABCDE1234F
MOBILE: Must be exactly 10 digits. Must start with 6, 7, 8, or 9.

NEVER guess missing numbers, correct the user's value, or reject valid values.


CONVERSATION RULES

1. Ask ONE question at a time.
2. Always ask for the next missing field in the form.
3. If the user provides multiple answers in one message, extract all valid ones.
4. If business_status = New, skip years_in_operation.
5. If category = General, caste certificate not required.
6. If business address = residential address, reuse it.

Always acknowledge the user's answer briefly before asking the next question.
Use clear and simple language.
Detect the language the user is writing in and always respond in that same language.


APPLICATION COMPLETION

When all fields are collected:
1. Show a structured summary of the application.
2. Ask the user to review the details.
3. Ask: "Do you want to SUBMIT the application or change anything?"

Only when the user explicitly says "Submit", output:
FORM_COMPLETE
<JSON application object>

Do NOT output FORM_COMPLETE unless the user explicitly confirms submission.
"""

scheme_info_prompt = """
ROLE
You are a knowledgeable Government Assistant specializing in the PM Mudra Yojana scheme.
Answer the user's questions clearly and accurately about the scheme.

TOPICS YOU CAN COVER
- What is PM Mudra Yojana
- Eligibility criteria
- Loan categories: Shishu (up to ₹50,000), Kishore (₹50,001–₹5 lakh), Tarun (₹5 lakh–₹10 lakh)
- Purpose of the loan
- Required documents
- How to apply
- Interest rates and repayment
- Which banks and NBFCs offer Mudra loans
- Government subsidies or benefits

RULES
- Only answer questions related to PM Mudra Yojana and its application process.
- Be concise, friendly, and easy to understand.
- If the user asks something outside this scope, politely redirect them.
- Detect the language the user is writing in and respond in the same language.
- At the end of your answer, add a gentle nudge:
  "Would you like to continue with your application or do you have more questions?"
"""

status_prompt = """
ROLE
You are a Government Assistant helping users check the status of their PM Mudra Yojana application.

RULES
- The current application data will be provided to you.
- Summarize what fields have been filled and what fields are still pending.
- If the application is complete, confirm it and show the Application ID if available.
- Be concise and friendly.
- Detect the language the user is writing in and respond in the same language.
- At the end, ask: "Would you like to continue filling the form or do you have any questions?"
"""

offtopic_prompt = """
ROLE
You are a focused Government Assistant for PM Mudra Yojana loan applications.

RULES
- The user has asked something unrelated to PM Mudra Yojana or their application.
- Politely let them know you can only help with:
  1. Filling the Mudra loan application form
  2. Answering questions about the PM Mudra Yojana scheme
  3. Checking their current application status
- Do NOT answer the off-topic question.
- Keep the response short, friendly, and redirect them.
- Detect the language the user is writing in and respond in the same language.
"""


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_aadhaar(value):
    value = value.strip().replace(" ", "")
    if not value.isdigit():
        return False, "Aadhaar must contain only numbers"
    if len(value) != 12:
        return False, f"Aadhaar must be exactly 12 digits, you entered {len(value)}"
    return True, "Valid"

def validate_pan(value):
    value = value.strip().upper()
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    if not re.match(pattern, value):
        return False, "PAN must be in format ABCDE1234F (5 letters, 4 numbers, 1 letter)"
    return True, "Valid"

def validate_mobile(value):
    value = value.strip().replace(" ", "")
    if not value.isdigit():
        return False, "Mobile number must contain only digits"
    if len(value) != 10:
        return False, "Mobile number must be exactly 10 digits"
    if value[0] not in ['6', '7', '8', '9']:
        return False, "Mobile number must start with 6, 7, 8, or 9"
    return True, "Valid"

def validate_email(value):
    value = value.strip()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        return False, "Please enter a valid email address like example@gmail.com"
    return True, "Valid"

def validate_dob(value):
    value = value.strip()
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %m %Y"]
    for fmt in formats:
        try:
            dob = datetime.strptime(value, fmt)
            age = (datetime.now() - dob).days // 365
            if age < 18:
                return False, f"You must be at least 18 years old. Your age appears to be {age}"
            if age > 100:
                return False, "Please enter a valid date of birth"
            return True, "Valid"
        except ValueError:
            continue
    return False, "Please enter date in DD/MM/YYYY format"


# =============================================================================
# GROQ FAST MODEL HELPER
# =============================================================================

def call_fast_model(prompt, max_tokens=512):
    """Call the fast 8b model for all utility tasks — intent, reranking, query rewrite, context generation."""
    try:
        response = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Fast model call failed: {e}")
        return None


# =============================================================================
# DOCUMENT RAG — INGESTION
# =============================================================================

def load_file(file_path):
    file_path = file_path.strip()
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        return [page.page_content for page in pages if page.page_content.strip()]
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
        return [doc.page_content for doc in docs if doc.page_content.strip()]
    else:
        print(f"⚠️ Unsupported file type: {file_path}. Skipping.")
        return []


def chunk_by_paragraph(text, min_chunk_words=30, max_chunk_words=200):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    raw_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    if len(raw_paragraphs) <= 2:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        raw_paragraphs = []
        current = []
        for line in lines:
            word_count = len(line.split())
            if word_count < 15:
                current.append(line)
            else:
                if current:
                    raw_paragraphs.append(' '.join(current))
                    current = []
                current.append(line)
        if current:
            raw_paragraphs.append(' '.join(current))

    noise_patterns = [
        "comprehensive reference document",
        "source: official",
        "version 1.0",
        "page ",
        "rbi guidelines"
    ]
    filtered = []
    for p in raw_paragraphs:
        if any(noise.lower() in p.lower() for noise in noise_patterns):
            continue
        if len(p.split()) < 5:
            continue
        filtered.append(p)

    merged = []
    buffer = ""
    for para in filtered:
        word_count = len((buffer + " " + para).split())
        if len(buffer.split()) < min_chunk_words:
            buffer = (buffer + " " + para).strip()
        elif word_count <= max_chunk_words:
            buffer = (buffer + " " + para).strip()
        else:
            if buffer:
                merged.append(buffer)
            buffer = para
    if buffer:
        merged.append(buffer)

    final_chunks = []
    for chunk in merged:
        if len(chunk.split()) <= max_chunk_words:
            final_chunks.append(chunk)
        else:
            sentences = re.split(r'(?<=[.!?])\s+', chunk)
            current = ""
            for sentence in sentences:
                if len((current + " " + sentence).split()) <= max_chunk_words:
                    current = (current + " " + sentence).strip()
                else:
                    if current:
                        final_chunks.append(current)
                    current = sentence
            if current:
                final_chunks.append(current)

    return final_chunks


def generate_chunk_context(whole_document, chunk):
    prompt = f"""<document>
{whole_document}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{chunk}
</chunk>

Please give a short succinct context to situate this chunk within the
overall document for the purposes of improving search retrieval of the
chunk. Answer only with the succinct context and nothing else."""
    context = call_fast_model(prompt, max_tokens=128)
    return context.strip() if context else ""


def augment_chunk(context, chunk):
    return f"{context}\n\n{chunk}" if context else chunk


def ingest_documents(file_paths):
    global all_chunks, bm25_index
    all_documents = []
    for fp in file_paths:
        all_documents.extend(load_file(fp))

    if not all_documents:
        print("⚠️ No documents loaded.")
        return []

    all_augmented_chunks = []
    all_raw_chunks = []

    for document in all_documents:
        chunks = chunk_by_paragraph(document)
        for chunk in chunks:
            context = generate_chunk_context(document, chunk)
            augmented = augment_chunk(context, chunk)
            all_augmented_chunks.append(augmented)
            all_raw_chunks.append(chunk)

    existing_ids = collection.get()["ids"]
    if existing_ids:
        print(f"⚠️ Replacing {len(existing_ids)} existing chunks with fresh ingestion.")
        collection.delete(ids=existing_ids)

    embeddings = embedding_model.encode(all_augmented_chunks).tolist()
    collection.add(
        documents=all_augmented_chunks,
        embeddings=embeddings,
        ids=[f"chunk_{i}" for i in range(len(all_augmented_chunks))],
        metadatas=[{"raw_chunk": all_raw_chunks[i]} for i in range(len(all_raw_chunks))]
    )

    all_chunks = all_raw_chunks
    tokenized = [chunk.lower().split() for chunk in all_chunks]
    bm25_index = BM25Okapi(tokenized)
    print(f"✅ Ingested {len(all_augmented_chunks)} chunks.")
    return all_raw_chunks


# =============================================================================
# DOCUMENT RAG — RETRIEVAL
# =============================================================================

def rewrite_query(user_query):
    prompt = f"""You are a search query rewriter for a PM Mudra Yojana information retrieval system.

Given the user's question, generate exactly 3 different search queries that together cover
different angles of the question. These will be used to retrieve relevant document chunks.

Rules:
- Each query should be distinct and capture a different aspect
- Keep queries concise (under 15 words each)
- Output ONLY a JSON array of 3 strings, nothing else
- No explanation, no preamble, no markdown

Example output: ["query one", "query two", "query three"]

Original question: {user_query}"""

    raw = call_fast_model(prompt, max_tokens=128)
    if raw:
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            queries = json.loads(clean)
            if isinstance(queries, list) and len(queries) == 3:
                return queries
        except Exception:
            pass
    return [user_query, user_query, user_query]


def vector_search(query, top_k=5):
    query_embedding = embedding_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)
    return results["documents"][0]


def bm25_search(query, top_k=5):
    if not bm25_index:
        return []
    tokenized_query = query.lower().split()
    scores = bm25_index.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [all_chunks[i] for i in top_indices]


def dual_retrieval(queries, top_k=5):
    seen = set()
    merged = []
    for query in queries:
        for chunk in vector_search(query, top_k) + bm25_search(query, top_k):
            if chunk not in seen:
                seen.add(chunk)
                merged.append(chunk)
    return merged


def rerank_chunks(user_query, chunks, top_n=5):
    if not chunks:
        return []
    numbered_chunks = "\n\n".join([f"[{i}] {chunk}" for i, chunk in enumerate(chunks)])
    prompt = f"""You are a document relevance ranker for a PM Mudra Yojana assistant.

Given the user's question and a list of document chunks, return the indices of the
{top_n} most relevant chunks in order from most to least relevant.

Rules:
- Output ONLY a JSON array of {top_n} integers (indices)
- No explanation, no preamble, no markdown backticks
- Example output: [2, 0, 4, 1, 3]

User Question: {user_query}

Document Chunks:
{numbered_chunks}"""

    raw = call_fast_model(prompt, max_tokens=64)
    if raw:
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            indices = json.loads(clean)
            valid_indices = [i for i in indices if 0 <= i < len(chunks)][:top_n]
            if valid_indices:
                return [chunks[i] for i in valid_indices]
        except Exception:
            pass
    return chunks[:top_n]


def retrieve_context(user_query, top_n=5):
    queries = rewrite_query(user_query)
    candidate_chunks = dual_retrieval(queries, top_k=5)
    top_chunks = rerank_chunks(user_query, candidate_chunks, top_n=top_n)
    return "\n\n---\n\n".join(top_chunks)


# =============================================================================
# CONVERSATION HISTORY RAG
# =============================================================================

def generate_message_context(recent_messages, current_message):
    if not recent_messages:
        return ""
    conversation_window = "\n".join(recent_messages)
    prompt = f"""<document>
{conversation_window}
</document>

Here is the message we want to situate within the conversation:
<chunk>
{current_message}
</chunk>

Please give a short succinct context to situate this message within the
overall conversation for the purposes of improving search retrieval of
the message. Answer only with the succinct context and nothing else."""
    context = call_fast_model(prompt, max_tokens=128)
    return context.strip() if context else ""


def store_message(role, content):
    global history_chunks, history_bm25, history_message_counter, recent_messages_window

    print(f">>> store_message called: role={role}, counter={history_message_counter}")
    raw_message = f"[{role.upper()}]: {content}"
    context = generate_message_context(recent_messages_window, raw_message)
    augmented_message = f"{context}\n\n{raw_message}" if context else raw_message

    msg_id = f"msg_{history_message_counter}"
    print(f">>> adding to history_collection with id={msg_id}")

    embedding = embedding_model.encode([augmented_message]).tolist()
    history_collection.add(
        documents=[augmented_message],
        embeddings=embedding,
        ids=[msg_id],
        metadatas=[{
            "role": role,
            "index": history_message_counter,
            "raw_message": raw_message
        }]
    )

    history_chunks.append(augmented_message)
    tokenized = [chunk.lower().split() for chunk in history_chunks]
    history_bm25 = BM25Okapi(tokenized)

    recent_messages_window.append(raw_message)
    if len(recent_messages_window) > CONTEXT_WINDOW_SIZE:
        recent_messages_window.pop(0)

    history_message_counter += 1
    print(f">>> store_message done, counter now={history_message_counter}")


def retrieve_relevant_history(current_query, top_n=3):
    if len(history_chunks) <= 1:
        return None

    query_embedding = embedding_model.encode([current_query]).tolist()
    n_results = min(top_n, len(history_chunks) - 1)
    vector_results = history_collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    vector_chunks = [
        r["raw_message"]
        for r in vector_results["metadatas"][0]
        if "raw_message" in r
    ]

    bm25_chunks = []
    if history_bm25 and len(history_chunks) > 1:
        tokenized_query = current_query.lower().split()
        scores = history_bm25.get_scores(tokenized_query)
        scores[-1] = -1
        top_indices = np.argsort(scores)[::-1][:top_n]
        all_metadata = history_collection.get()["metadatas"]
        bm25_chunks = [
            all_metadata[i]["raw_message"]
            for i in top_indices
            if scores[i] > 0 and i < len(all_metadata)
        ]

    seen = set()
    merged = []
    for chunk in vector_chunks + bm25_chunks:
        if chunk not in seen:
            seen.add(chunk)
            merged.append(chunk)

    return "\n".join(merged[:top_n]) if merged else None


def reset_history():
    global history_chunks, history_bm25, history_message_counter, recent_messages_window
    all_ids = history_collection.get()["ids"]
    if all_ids:
        history_collection.delete(ids=all_ids)
    history_chunks = []
    history_bm25 = None
    history_message_counter = 0
    recent_messages_window = []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_fields_needed():
    needed = [k for k, v in application_data.items() if v is None]
    if (application_data.get("business_status") or "").lower() == "new":
        if "years_in_operation" in needed:
            needed.remove("years_in_operation")
    return needed


def build_dynamic_prompt():
    collected = {k: v for k, v in application_data.items() if v is not None}
    needed = get_fields_needed()
    return f"""
CURRENT APPLICATION STATE:
Fields collected so far: {json.dumps(collected, indent=2)}
Fields still needed: {json.dumps(needed, indent=2)}
"""


def detect_intent(user_message):
    prompt = f"""You are an intent classifier for a PM Mudra Yojana loan application chatbot.

Classify the user's message into EXACTLY one of these intents:
- form_filling   : User is filling the application form, providing personal/business/loan details, or wants to apply
- scheme_info    : User is asking about what the scheme is, eligibility, loan types, documents, interest rates, banks, benefits
- status         : User is asking about the status of their current application or what they have filled so far
- off_topic      : User is asking something completely unrelated to Mudra Yojana or their application

Reply with ONLY one word — the intent label. No explanation, no punctuation.

User message: {user_message}"""

    raw = call_fast_model(prompt, max_tokens=16)
    if raw:
        intent = raw.strip().lower().split()[0]
        if intent in ["form_filling", "scheme_info", "status", "off_topic"]:
            return intent
    return "form_filling"


def get_prompt_for_intent(intent, rag_context=None):
    if intent == "scheme_info":
        context_block = f"""
RELEVANT DOCUMENT CONTEXT (use this to answer the user's question):
---
{rag_context if rag_context else "No context retrieved."}
---
"""
        return scheme_info_prompt + context_block

    mapping = {
        "form_filling": form_filling_prompt,
        "status": status_prompt,
        "off_topic": offtopic_prompt,
    }
    return mapping.get(intent, form_filling_prompt)


def extract_form_data(response_text):
    if "FORM_COMPLETE" not in response_text:
        return None
    try:
        json_start = response_text.find("{", response_text.find("FORM_COMPLETE"))
        json_end = response_text.rfind("}") + 1
        return json.loads(response_text[json_start:json_end])
    except Exception as e:
        print(f"Could not parse form data: {e}")
        return None


def update_application_data(extracted_data):
    if not extracted_data:
        return
    for key in application_data:
        if key in extracted_data and extracted_data[key]:
            application_data[key] = extracted_data[key]


# =============================================================================
# CORE CHAT FUNCTION
# =============================================================================

def chat_core(user_message):
    global current_intent

    print(f"\n>>> chat_core called with: {user_message[:60]}")

    print(">>> detecting intent...")
    current_intent = detect_intent(user_message)
    print(f">>> intent: {current_intent}")

    print(">>> retrieving relevant history...")
    relevant_history = retrieve_relevant_history(user_message, top_n=3)
    print(f">>> history retrieved: {'yes' if relevant_history else 'none'}")

    print(">>> storing user message...")
    store_message("user", user_message)
    print(">>> user message stored")

    rag_context = None
    if current_intent == "scheme_info":
        print(">>> retrieving RAG context...")
        rag_context = retrieve_context(user_message)
        print(">>> RAG context retrieved")

    print(">>> building system prompt...")
    system_prompt = get_prompt_for_intent(current_intent, rag_context=rag_context)

    if current_intent in ["form_filling", "status"]:
        system_prompt += build_dynamic_prompt()

    messages = [{"role": "system", "content": system_prompt}]

    if relevant_history:
        messages.append({
            "role": "system",
            "content": f"""RELEVANT CONVERSATION HISTORY (for context only):
---
{relevant_history}
---"""
        })

    messages.append({"role": "user", "content": user_message})

    print(f">>> calling Groq 70b with {len(messages)} messages...")
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        max_tokens=1000
    )
    print(">>> Groq 70b response received")

    assistant_message = response.choices[0].message.content

    print(">>> storing assistant message...")
    store_message("assistant", assistant_message)
    print(">>> assistant message stored")

    if "FORM_COMPLETE" in assistant_message:
        extracted = extract_form_data(assistant_message)
        update_application_data(extracted)
        clean_response = assistant_message.split("FORM_COMPLETE")[0].strip()
        application_id = generate_application_id()
        try:
            save_application(application_data, application_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving application: {str(e)}")
        return clean_response, True, application_id

    print(">>> chat_core complete")
    return assistant_message, False, None


# =============================================================================
# FASTAPI ENDPOINTS
# =============================================================================

class ChatRequest(BaseModel):
    message: str

from typing import Optional

class ChatResponse(BaseModel):
    response: str
    form_complete: bool
    application_id: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    application_data: dict

class ResetResponse(BaseModel):
    message: str


@app.get("/status", response_model=StatusResponse)
async def get_status():
    return StatusResponse(status="ok", application_data=application_data)


@app.post("/reset", response_model=ResetResponse)
async def reset_conversation():
    global current_intent
    current_intent = "form_filling"

    for key in application_data:
        application_data[key] = None
    application_data["documents_provided"] = []

    reset_history()

    return ResetResponse(message="Conversation reset successfully")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response_text, form_complete, application_id = chat_core(request.message)
        return ChatResponse(
            response=response_text,
            form_complete=form_complete,
            application_id=application_id
        )
    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        full_tb = "".join(tb_lines)
        print("\n" + "=" * 60)
        print("FULL TRACEBACK:")
        print(full_tb)
        print("=" * 60 + "\n")
        raise HTTPException(status_code=500, detail=full_tb)


# =============================================================================
# STARTUP — ingest documents on boot
# =============================================================================

document_files = [
    r"D:\Downloads\PMMY_Reference_Document.pdf",
]

@app.on_event("startup")
async def startup_event():
    global all_chunks, bm25_index

    existing_ids = collection.get()["ids"]
    if existing_ids:
        print(f"✅ ChromaDB already has {len(existing_ids)} chunks — skipping ingestion.")
        all_chunks = [
            meta["raw_chunk"]
            for meta in collection.get()["metadatas"]
            if "raw_chunk" in meta
        ]
        if all_chunks:
            tokenized = [chunk.lower().split() for chunk in all_chunks]
            bm25_index = BM25Okapi(tokenized)
            print(f"✅ BM25 index rebuilt over {len(all_chunks)} chunks.")
    else:
        print("🚀 No existing data — ingesting documents...")
        all_chunks = ingest_documents(document_files)
        if all_chunks:
            tokenized = [chunk.lower().split() for chunk in all_chunks]
            bm25_index = BM25Okapi(tokenized)
            print(f"✅ BM25 index built over {len(all_chunks)} chunks.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)