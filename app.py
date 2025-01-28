from flask import Flask, request, jsonify, render_template
import openai
import json
from pymongo import MongoClient
import os

app = Flask(__name__)

# Load knowledge base
with open("knowledge_base/faq.json", "r") as f:
    knowledge_base = json.load(f)

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure MongoDB for logging
client = MongoClient("mongodb://localhost:27017/")
db = client["faq_logs"]
logs_collection = db["interactions"]

# Homepage with query input
@app.route("/")
def home():
    return render_template("index.html")

# API endpoint to handle queries
@app.route("/ask", methods=["POST"])
def ask():
    user_query = request.json.get("query")
    
    # Generate context from knowledge base
    context = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in knowledge_base])
    
    # Use OpenAI to generate a response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful FAQ assistant."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"}
            ]
        )
        answer = response.choices[0].message["content"]
    except Exception as e:
        answer = "Sorry, I couldn't process your request. Please try again later."

    # Log the interaction
    logs_collection.insert_one({"query": user_query, "response": answer})

    return jsonify({"response": answer})

# Admin endpoint to update knowledge base
@app.route("/admin/update_kb", methods=["POST"])
def update_kb():
    new_kb = request.json.get("knowledge_base")
    with open("knowledge_base/faq.json", "w") as f:
        json.dump(new_kb, f)
    return jsonify({"status": "success", "message": "Knowledge base updated."})

# Admin endpoint to view logs
@app.route("/admin/logs", methods=["GET"])
def view_logs():
    logs = list(logs_collection.find({}, {"_id": 0}))
    return jsonify(logs)

if __name__ == "__main__":
    app.run(debug=True)