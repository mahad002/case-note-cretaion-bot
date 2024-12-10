from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_core.messages import SystemMessage
import logging
import os
from prompt import SYSTEM_PROMPT
from agent import AgentState
from chunking import chunk_text
import json

# Set up logging for detailed debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the model and parsers
logging.info("Initializing the Ollama model and parsers...")
preprocessor = OllamaLLM(model="llama3", temperature=0)
json_parser = JsonOutputParser()

prompt = PromptTemplate(
    template="{SYSTEM_PROMPT}.\n{format_instructions}\n{text}\n",
    input_variables=["text"],
    partial_variables={"format_instructions": json_parser.get_format_instructions(), "SYSTEM_PROMPT": SYSTEM_PROMPT},
)

def process_chunk(chunk, agent_state):
    logging.info(f"Processing a new chunk with {len(chunk.split())} words.")
    
    # Format the prompt with the current chunk
    formatted_prompt = prompt.format_prompt(text=chunk)
    prompt_text = formatted_prompt.to_string()
    logging.debug(f"Formatted prompt: {prompt_text}")

    # Create the input messages as plain text
    messages = [
        {"role": "system", "content": prompt_text}  # Convert to JSON-serializable format
    ]
    print(f"Sending the following message to the model:\n{messages}")

    try:
        # Get the model's response
        response = preprocessor.invoke(messages)

        # Handle response depending on type
        if isinstance(response, str):
            response_content = response.strip()
        elif hasattr(response, 'content'):
            response_content = response.content.strip()
        else:
            raise ValueError("Unexpected response type from preprocessor.invoke()")

        logging.info(f"Received response: {response_content}")

        # Parse the JSON response
        extracted_info = json_parser.parse(response_content)
        print(f"Extracted JSON: {extracted_info}")

        # Update AgentState based on extracted information
        for citation in extracted_info.get('citations', []):
            agent_state.add_citation(citation)
            logging.debug(f"Added citation: {citation}")

        for fact in extracted_info.get('facts', []):
            agent_state.add_facts(fact)
            logging.debug(f"Added fact: {fact}")

        for statute_type, statutes in extracted_info.get('statutes', {}).items():
            for statute in statutes:
                agent_state.add_statute(statute_type, statute)
                logging.debug(f"Added statute: {statute_type} - {statute}")

        for precedent in extracted_info.get('precedents', []):
            agent_state.add_precedent(precedent)
            logging.debug(f"Added precedent: {precedent}")

        for ratio in extracted_info.get('ratio', []):
            agent_state.add_ratio(ratio)
            logging.debug(f"Added ratio: {ratio}")

        for ruling in extracted_info.get('rulings', []):
            agent_state.add_ruling(ruling)
            logging.debug(f"Added ruling: {ruling}")

    except json.JSONDecodeError:
        logging.error(f"Error: Unable to parse agent response as JSON: {response_content}")
        print(f"Error while parsing JSON: {response_content}")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")

def process_legal_judgment(judgment_text):
    logging.info("Starting processing of the legal judgment.")
    agent_state = AgentState()
    chunks = chunk_text(judgment_text)
    logging.info(f"Split the judgment into {len(chunks)} chunks.")

    for idx, chunk in enumerate(chunks):
        logging.info(f"Processing chunk {idx+1}/{len(chunks)}.")
        process_chunk(chunk, agent_state)

    logging.info("Finalizing agent state.")
    agent_state.finalize()
    return agent_state

# Directories for input and output
input_directory = "./Preprocessed Judgements"
output_directory = "./Case Notes"

# Create output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

MAX_FILES = 2  # To limit the number of processed files for testing
processed_count = 0

logging.info("Starting batch processing of judgments.")
for filename in os.listdir(input_directory):
    if filename.endswith(".txt"):
        logging.info(f"Processing file: {filename}")
        judgment_filepath = os.path.join(input_directory, filename)

        with open(judgment_filepath, 'r', encoding='utf-8') as file:
            judgment_text = file.read()
            print(f"Loaded text from {filename}. Length: {len(judgment_text.split())} words.")

        final_state = process_legal_judgment(judgment_text)
        output_filepath = os.path.join(output_directory, filename)

        with open(output_filepath, 'w', encoding='utf-8') as output_file:
            output_data = final_state.to_json()
            output_file.write(output_data)
            print(f"Saved processed data to {output_filepath}.")

        processed_count += 1
        logging.info(f"Processed {processed_count} files so far.")
        if processed_count >= MAX_FILES:
            logging.info(f"Reached maximum file limit ({MAX_FILES}). Stopping.")
            break
