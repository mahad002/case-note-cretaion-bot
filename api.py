from flask import Flask, request, jsonify
import requests
import logging
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM
from prompt import SYSTEM_PROMPT
from agent import AgentState
from chunking import chunk_text
import json
from flask_cors import CORS
import getpass
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):    
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

print(os.environ.get("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)  # Initialize CORS

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the model and parsers
# preprocessor = OllamaLLM(model="llama3", temperature=0)
preprocessor = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)

json_parser = JsonOutputParser()

prompt = PromptTemplate(
    template="{SYSTEM_PROMPT}.\n{format_instructions}\n{text}\n",
    input_variables=["text"],
    partial_variables={"format_instructions": json_parser.get_format_instructions(), "SYSTEM_PROMPT": SYSTEM_PROMPT},
)

# Process a chunk of text
def process_chunk(chunk, agent_state):
    formatted_prompt = prompt.format_prompt(text=chunk)
    prompt_text = formatted_prompt.to_string()

    messages = [
        {"role": "system", "content": prompt_text}
    ]

    try:
        response = preprocessor.invoke(messages)

        if isinstance(response, str):
            response_content = response.strip()
        elif hasattr(response, 'content'):
            response_content = response.content.strip()
        else:
            raise ValueError("Unexpected response type from preprocessor.invoke()")

        extracted_info = json_parser.parse(response_content)

        for citation in extracted_info.get('citations', []):
            agent_state.add_citation(citation)

        for fact in extracted_info.get('facts', []):
            agent_state.add_facts(fact)

        statutes = extracted_info.get('statutes', {})
        if isinstance(statutes, dict):
            for statute_type, statutes_list in statutes.items():
                for statute in statutes_list:
                    agent_state.add_statute(statute_type, statute)
        elif isinstance(statutes, list):
            for statute in statutes:
                agent_state.add_statute("unknown", statute)

        for precedent in extracted_info.get('precedents', []):
            agent_state.add_precedent(precedent)

        for ratio in extracted_info.get('ratio', []):
            agent_state.add_ratio(ratio)

        for ruling in extracted_info.get('rulings', []):
            agent_state.add_ruling(ruling)

    except json.JSONDecodeError:
        logging.error(f"Error: Unable to parse agent response as JSON: {response_content}")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

# Process the legal judgment text
def process_legal_judgment(judgment_text):
    agent_state = AgentState()
    chunks = chunk_text(judgment_text)

    for chunk in chunks:
        process_chunk(chunk, agent_state)

    agent_state.finalize()
    return agent_state.to_json()

# API Endpoint
@app.route('/process-judgment', methods=['POST'])
def process_judgment():
    try:
        data = request.json
        s3_link = data.get('s3_link')

        if not s3_link:
            return jsonify({"error": "S3 link is required"}), 400

        # Download file from S3 link
        response = requests.get(s3_link)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download file from S3 link"}), 400

        judgment_text = response.text

        # Process the legal judgment
        result = process_legal_judgment(judgment_text)

        return jsonify({"processed_data": json.loads(result)})

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Default to 5000 if PORT is not set
    app.run(host='0.0.0.0', port=port, debug=True)
