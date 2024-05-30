from flask import Flask, jsonify, request, send_from_directory
import os
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.indices.service_context import ServiceContext
from llama_index.core import (
    StorageContext,
    VectorStoreIndex,
    Settings,
    SimpleDirectoryReader,
)
from llama_index.llms.llama_cpp import LlamaCPP
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load configuration from a file
app.config.from_pyfile("./config/dev_environment.cfg")

# Ensure the upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize the vector store
vector_store = PGVectorStore.from_params(
    database=app.config["DB_NAME"],
    host=app.config["DB_HOST"],
    password=app.config["DB_PASSWORD"],
    port=app.config["DB_PORT"],
    user=app.config["DB_USER"],
    table_name=app.config["VECTOR_STORE_DB_TABLE"],
    embed_dim=app.config["EMBED_DIMS"],
)

# Initialize storage context
storage_context = StorageContext.from_defaults(
    vector_store=vector_store,
)

# Initialize the LLM and embedding model
llm = LlamaCPP(
    model_url=app.config["HUGGING_FACE_LLM_URL"],
    model_path=None,
    temperature=0.2,
    max_new_tokens=256,
    context_window=3900,
    generate_kwargs={},
    model_kwargs={"n_gpu_layers": 1},
    verbose=True,
)

embed_model = HuggingFaceEmbedding(
    model_name=app.config["HUGGING_FACE_EMBEDDING_MODEL"]
)

# Configure global settings
Settings.llm = llm
Settings.embed_model = embed_model
Settings.chunk_size = app.config["INDEX_CHUNK_SIZE"]
Settings.chunk_overlap = app.config["INDEX_CHUNK_OVERLAP"]


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if f:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], f.filename)
        f.save(filepath)
        return (
            jsonify({"message": "File uploaded successfully", "filename": f.filename}),
            200,
        )


@app.route("/files", methods=["GET"])
def list_files():
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return jsonify(files)


@app.route("/files/<filename>", methods=["GET"])
def get_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/sync_vector_store", methods=["POST"])
def sync_vector_store():
    documents = SimpleDirectoryReader(app.config["UPLOAD_FOLDER"]).load_data()

    # Clean up documents by removing null characters
    for doc in documents:
        doc.text = doc.text.replace("\x00", "")

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )

    return (
        jsonify(
            {"message": "Vector store generated and stored in PostgreSQL successfully"}
        ),
        200,
    )


@app.route("/query", methods=["POST"])
def query_document():
    question_text = request.json.get("question", None)
    if question_text is None:
        return "No text found, please include a question in the JSON body", 400

    service_context = ServiceContext.from_defaults(
        llm=llm,
        embed_model=embed_model,
    )
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model,
        service_context=service_context,
    )
    query_engine = index.as_query_engine(similarity_top_k=2)
    results = query_engine.query(question_text)

    if results:
        filename = results.source_nodes[0].metadata.get("file_name", "N/A")
        page_label = results.source_nodes[0].metadata.get("page_label", "N/A")
        return (
            jsonify(
                {
                    "message": str(results),
                    "context": f"-- Source: {filename} page {page_label}",
                }
            ),
            200,
        )
    else:
        return jsonify({"message": "No relevant answer found"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
