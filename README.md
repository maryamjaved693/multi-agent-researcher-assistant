# 🧠 Multi-Agent Research Assistant (Streamlit + CrewAI)

This is a Streamlit-based research assistant app built using the **CrewAI framework**. It automates the process of researching any company or product by combining multiple AI agents—one for web research and another for website scraping. It uses **TinyLlama (via Ollama)** for fast, local LLM responses.

---

## 🚀 Features

- 🔍 **Web Research Agent**: Uses SerperDev to find relevant news and information about the company/product.
- 🕸 **Data Extractor Agent**: Scrapes and summarizes content from official websites using Firecrawl.
- 🤖 **Local LLM**: Uses TinyLlama via Ollama instead of cloud LLMs for fast, cost-free inference.
- 🧾 **Structured Output**: Displays a clean and organized research report in Streamlit.

---

## 📦 Tech Stack

- [CrewAI](https://docs.crewai.com/)
- [Streamlit](https://streamlit.io/)
- [Serper.dev](https://serper.dev/) (Web search)
- [Firecrawl](https://firecrawl.dev/) (Web scraping)
- [Ollama + TinyLlama](https://ollama.com/) (Local language model)

---

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
pip install crewai[tools] streamlit requests
