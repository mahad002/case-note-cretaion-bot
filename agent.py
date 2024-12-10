import json


class AgentState:
    def __init__(self):
        # Core components of legal judgments as defined earlier
        self.citations = []      # List of citations (references to case law, legal texts, etc.)
        self.facts = []          # List of facts (as individual strings or paragraphs)
        self.statutes = {        # Dictionary for laws and associated sections or articles
            "acts": [],
            "sections": [],
            "articles": []
        }
        self.precedents = []     # List of precedent cases
        self.ratio = []          # List of legal reasoning paragraphs
        self.rulings = []        # List of rulings (to handle multiple judgments over appeals)
        
        # Optional metadata for tracking progress or chunk handling
        self.current_chunk_index = 0  # Tracks the current chunk being processed
        # self.chunk_history = []       # Stores processed chunks for reference
        self.is_complete = False      # Boolean flag to mark if the entire judgment has been processed

    # Method to update citations
    def add_citation(self, citation):
        if citation and citation not in self.citations:
            self.citations.append(citation)
        
    # Method to update facts
    def add_facts(self, facts_text):
        if facts_text:
            self.facts.append(facts_text)  # Store each fact entry as a separate item

    # Method to add statutes (acts, sections, articles)
    def add_statute(self, statute_type, statute_value):
        if statute_type in self.statutes and statute_value not in self.statutes[statute_type]:
            self.statutes[statute_type].append(statute_value)

    # Method to update precedents
    def add_precedent(self, precedent):
        if precedent and precedent not in self.precedents:
            self.precedents.append(precedent)

    # Method to update the ratio of the decision
    def add_ratio(self, ratio_text):
        if ratio_text:
            self.ratio.append(ratio_text)  # Store each ratio reasoning as a separate item

    # Method to update and append multiple rulings
    def add_ruling(self, ruling_text):
        if ruling_text:
            self.rulings.append(ruling_text)  # Append each ruling to the list

    # Method to mark a chunk as processed and store it in history
    # def track_chunk(self, chunk):
    #     self.chunk_history.append(chunk)
    #     self.current_chunk_index += 1

    # Method to finalize the state as complete
    def finalize(self):
        self.is_complete = True

    # Debug method to print the current state (useful during development)
    def print_state(self):
        print(f"Citations: {self.citations}")
        print(f"Facts: {self.facts}")
        print(f"Statutes: {self.statutes}")
        print(f"Precedents: {self.precedents}")
        print(f"Ratio: {self.ratio}")
        print(f"Rulings: {self.rulings}")
        # print(f"Processed Chunks: {self.chunk_history}")
        print(f"Is Complete: {self.is_complete}")

    
    def to_json(self):
        # Convert the AgentState instance to a JSON-formatted string
        return json.dumps({
            'citations': self.citations,
            'facts': self.facts,
            'statutes': self.statutes,
            'precedents': self.precedents,
            'ratio': self.ratio,
            'rulings': self.rulings
        }, indent=4)