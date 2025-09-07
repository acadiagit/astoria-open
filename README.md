---
title: Astoria Open G
emoji: ⛵
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Astoria Open Query Console

An advanced, multi-LLM application that allows users to query a maritime history database using natural language.

## ✨ Features

- **Natural Language to SQL:** Ask complex questions in plain English and get answers directly from a PostgreSQL database.
- **Intelligent Routing:** Automatically uses a fast, direct chain for simple queries and a powerful Gemini-powered agent for complex, analytical questions.
- **RAG Pipeline:** Enriches SQL data with contextual information from a vector database to provide comprehensive, narrative summaries.
- **Multi-LLM Architecture:** Leverages Google's Gemini for high-accuracy SQL generation and Groq for high-speed narrative synthesis.

## 🚀 How to Use

1.  Check the **External Service Status** panel to ensure all systems are operational.
2.  Type a question about the maritime database into the text box (e.g., "List 10 vessels built after 1900").
3.  Click **Submit** to see the generated SQL, the raw data results, and a synthesized narrative summary.

## 🛠️ Tech Stack

- **Backend:** FastAPI, Uvicorn, LangChain
- **Frontend:** React, Vite
- **LLMs:** Google Gemini, Groq
- **Database:** PostgreSQL with pgvector (via Supabase)
