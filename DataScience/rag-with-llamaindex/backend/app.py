from flask import Flask, jsonify, request, send_from_directory
import os
from llama_index.vector_stores.postgres import PGVectorStore
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
    database=os.getenv("DB_NAME"),  # app.config["DB_NAME"],
    host=os.getenv("DB_HOST"),  # app.config["DB_HOST"],
    password=os.getenv("DB_PASSWORD"),  # app.config["DB_PASSWORD"],
    port=os.getenv("DB_PORT"),  # app.config["DB_PORT"],
    user=os.getenv("DB_USER"),  # app.config["DB_USER"],
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
    # set to at least 1 to use GPU
    model_kwargs={"n_gpu_layers": 1},
    verbose=True,
)

embed_model = HuggingFaceEmbedding(
    model_name=app.config["HUGGING_FACE_EMBEDDING_MODEL"]
)


@app.route("/upload", methods=["POST"])
def upload_file():

    if "files" not in request.files:
        return jsonify({"error": "No files part in the request"}), 400
    files = request.files.getlist("files")
    filenames = []
    for file in files:
        if file:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            filenames.append(file.filename)

    return (
        jsonify({"message": "File uploaded successfully", "filename": filenames}),
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

    # Configure global settings
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = app.config["INDEX_CHUNK_SIZE"]
    Settings.chunk_overlap = app.config["INDEX_CHUNK_OVERLAP"]

    documents = SimpleDirectoryReader(input_dir=app.config["UPLOAD_FOLDER"]).load_data()

    # Clean up documents by removing null characters
    for doc in documents:
        doc.text = doc.text.replace("\x00", "")

    _ = VectorStoreIndex.from_documents(
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

    # Configure global settings
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = app.config["INDEX_CHUNK_SIZE"]
    Settings.chunk_overlap = app.config["INDEX_CHUNK_OVERLAP"]

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model,
    )
    query_engine = index.as_query_engine(
        similarity_top_k=app.config["SIMILARITY_TOP_K"]
    )

    results = query_engine.query(question_text)

    if results:
        filename = results.source_nodes[0].metadata.get("file_name", "N/A")
        return (
            jsonify(
                {
                    "message": str(results),
                    "filename": str(filename),
                }
            ),
            200,
        )
    else:
        return jsonify({"message": "No relevant answer found"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
