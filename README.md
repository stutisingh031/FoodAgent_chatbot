# 🍔 FoodAgent AI – Agentic AI-Powered Food Delivery Support Chatbot

An intelligent, LLM-powered customer support chatbot designed for food delivery platforms. FoodAgent AI aims to go beyond traditional rule-based chatbots by using **Agentic AI, tool calling, conversation history, and database integration** to understand customer requests and perform relevant support operations.

The system is designed to help customers track orders, resolve food delivery issues, understand refund policies, get answers to frequently asked questions, and escalate complex problems to human support.

---

## 🚀 Project Overview

Traditional customer support chatbots mainly depend on predefined responses and fixed conversation flows.

**FoodAgent AI** is designed around an agent-based architecture where an AI model can understand user intent, decide which tool or operation is relevant, retrieve information, and generate contextual responses.

The project combines a Python backend, a relational database, and an LLM-powered agent to build an intelligent customer support system for food delivery applications.

### 🎯 Key Objectives

- Build an Agentic AI chatbot for food delivery customer support.
- Use an LLM to understand customer queries and generate contextual responses.
- Integrate tools that allow the agent to interact with backend services.
- Retrieve customer order information from a MySQL database.
- Maintain conversation history for contextual interactions.
- Support customer authentication and secure API access.
- Provide a foundation for human support escalation and ticket management.

---

## ✨ Key Features

### 1. AI-Powered Conversational Support
- Natural-language interaction with customers.
- LLM-powered response generation using Google Gemini.
- Context-aware conversations using stored conversation history.

### 2. Agentic AI Architecture
- Agent-based approach to handling customer queries.
- Tool-oriented architecture for interacting with backend functionality.
- Separation of agent instructions, agent logic, and individual tools.
- Designed to select relevant operations based on customer intent.

### 3. Order Management
- Retrieve order information.
- Check order status.
- Access order and order-item information.
- Support order-related customer queries.

### 4. Customer Authentication
- Customer registration and login services.
- Password hashing using `pwdlib`.
- JWT-based authentication support.
- Token generation and validation.

### 5. Conversation Management
- Generate unique conversation session IDs.
- Store customer and assistant messages.
- Retrieve previous conversation history.
- Provide conversation context to the AI agent.

### 6. Human Support and Ticket Management
- Support ticket database model.
- Ticket management service foundation.
- Architecture for escalating complex customer issues to human support.

### 7. Database Integration
- MySQL relational database.
- SQLAlchemy ORM for database operations.
- Models for customers, orders, conversations, and support tickets.

### 8. API Development
- REST APIs built using FastAPI.
- Request validation using Pydantic.
- Interactive API documentation through Swagger UI.

---

## 🧠 Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| AI / LLM | Google Gemini |
| Agent Framework | LangChain |
| Database | MySQL |
| ORM | SQLAlchemy |
| Authentication | JWT |
| Password Hashing | pwdlib |
| Data Validation | Pydantic |
| ASGI Server | Uvicorn |
| Configuration | Environment variables, Pydantic Settings |
| Logging | Python Logging |
| API Testing | Swagger UI |

**Frontend:** A frontend directory is part of the project structure. The frontend framework and implementation should be documented once the actual frontend setup is finalized.

---

## 🏗️ System Architecture

The application follows a modular architecture that separates API endpoints, business logic, AI agent functionality, and database operations.

```text
                    CUSTOMER
                        |
                        v
                 CHAT INTERFACE
                        |
                        v
                 FASTAPI BACKEND
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
      Auth APIs      Chat APIs     Order APIs
          |             |
          v             v
     Auth Service   Conversation Service
                        |
                        v
                 AGENTIC AI AGENT
                        |
                        v
                  GOOGLE GEMINI
                        |
                        v
                 AGENT TOOL LAYER
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
      Order
