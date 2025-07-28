
-----

# 🚀 Adobe India Hackathon 2025 (Challenge 1B) - Team Syn3rgy

## 🎯 Overview

This repository contains the complete, Dockerized solution for **Challenge 1B** of the Adobe India Hackathon 2025. The project is an intelligent content analysis system that processes collections of PDF documents to provide persona-specific, context-aware insights.

Given a set of PDFs, a `persona` (e.g., "Travel Planner"), and a `job_to_be_done` (e.g., "Plan a trip for college friends"), the system identifies the 5 most relevant sections from the entire document library and generates a concise summary for each. The solution is designed to be robust, scalable, and truly generic, capable of handling any user-defined scenario without modification.

-----

## 🧠 Approach: Context-Aware Page Analysis

This solution abandons brittle, rule-based visual parsing in favor of a more robust, content-first strategy that mimics human research patterns.

1.  **Universal Content Ingestion**: The script first processes all PDFs by chunking them page by page. This is the most reliable way to ingest content without making flawed assumptions about a document's visual layout. For each page, it identifies the most prominent line of text (based on font size) to serve as a candidate title.

2.  **Dynamic Constraint Filtering**: Before ranking, the system intelligently analyzes the `job_to_be_done` for keywords that imply hard constraints. For example, if the query includes "vegetarian," the system **dynamically filters out any page** containing non-vegetarian terms (e.g., 'beef', 'pork', 'chicken'). This ensures the results are logically sound and adhere to strict user requirements.

3.  **Persona-Driven Ranking**: The core of the solution is a powerful weighted scoring system. It ranks each page based on the combined semantic similarity of its **title** and **content** to a rich, persona-driven query (e.g., "Travel Planner: Plan a trip..."). This ensures the results are not just textually similar but are contextually relevant to the user's role and goal.

4.  **Intelligent Summarization**: For the top 5 ranked pages, the system generates a high-quality summary (`refined_text`) by identifying and combining the 2-3 most relevant sentences from the page content, ensuring the output is both concise and informative.

This content-first approach, powered by a state-of-the-art sentence-transformer model, allows the system to deliver highly accurate and relevant results across diverse document sets and user scenarios.

-----

## 📦 Core Technologies

| Library/Tool              | Purpose                                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------------------- |
| `PyMuPDF`                 | Fast and reliable PDF text extraction.                                                             |
| `sentence-transformers`   | Powers the semantic search and relevance ranking using the efficient `all-MiniLM-L6-v2` model (\<1GB). |
| `numpy`                   | Numerical operations for efficient ranking and analysis.                                           |
| `Docker`                  | Ensures a consistent, reproducible, and easy-to-deploy environment for the entire solution.         |
| `re`, `json`, `pathlib`   | Standard libraries for text processing, data handling, and file system operations.                 |

-----

## 🛠️ How to Build & Run

### 1\. Project Structure

Ensure your project is structured as follows before building:

```
ADOBE_CHALLENGE_1B/
├── Dockerfile
├── main.py                  # Main processing script
├── Collection 1/
│   ├── PDFs/                # Input PDFs for the first use case
│   └── challenge1b_input.json
├── Collection 2/
│   ├── PDFs/
│   └── challenge1b_input.json
└── ...
```

### 2\. Build the Docker Image

Execute the following command from the root of the project directory.

```bash
docker build -t round-1b .
```

### 3\. Run the Container

This command will run the analysis on all `Collection *` directories found in the project folder.

```bash
docker run --rm \
  -v "$(pwd):/app" \
  -v "sentence_transformer_cache:/root/.cache/huggingface" \
  round-1b
```

  - **`-v "$(pwd):/app"`**: Mounts your project directory into the container. This allows the script to access your `Collection` folders and write the `output.json` files back to your host machine.
  - **`-v "sentence_transformer_cache:/root/.cache/huggingface"`**: Creates a persistent cache for the language model. The model will only be downloaded on the first run, making all subsequent runs significantly faster.

-----

## 📤 Output Format

For each `Collection` directory, the script generates a `challenge1b_output.json` file with the following structure:

```json
{
  "metadata": {
    "input_documents": [
      "list_of_input_docs.pdf"
    ],
    "persona": "User's Persona",
    "job_to_be_done": "User's Task",
    "processing_timestamp": "ISO 8601 Timestamp"
  },
  "extracted_sections": [
    {
      "document": "source.pdf",
      "section_title": "Identified Section Title",
      "importance_rank": 1,
      "page_number": 1
    },
    
  ],
  "subsection_analysis": [
    {
      "document": "source.pdf",
      "refined_text": "A concise, relevant summary of the section's content.",
      "page_number": 1
    },
    
  ]
}
```

## 👨‍💻 Developed By

### **Team Syn3rgy**

### **Submission for Adobe India Hackathon 2025**