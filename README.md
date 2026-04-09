# AI Assistant - Student Tutoring & Assessment System

A robust, human-in-the-loop AI tutoring system that leverages RAG (Retrieval-Augmented Generation) to guide students through learning and provide automated evaluations with human oversight.

---

## 🚀 Key Features
- **Intelligent Tutoring**: AI-driven guidance tailored to student questions using contextual knowledge.
- **Automated Evaluation**: Instant scoring and feedback on student answers.
- **Human-In-The-Loop (HITL)**: Mandatory manual review for assessment finalization.
- **Stateful Workflows**: Built with LangGraph for complex, multi-step agent interactions.
- **Data Isolation**: Multi-tenant support via Pinecone namespaces.

---

## 🏗 System Architecture & Flow

### Application Flow
The application follows a structured lifecycle for each tutoring session:

1. **Ask (`/workflow/ask`)**: Student submits a question. The system rephrases it for better retrieval, fetches context from the vector database, and generates a reference answer.
2. **Answer (`/workflow/answer`)**: Student provides their response. The Evaluator Agent compares it against the reference answer and provides an initial AI score and feedback.
3. **Review (`/workflow/review`)**: A Reviewer-role user assesses the AI's evaluation, providing a final score and human comments.
4. **Finalization**: Once approved, the question record is updated with final scores and the identity of the reviewer.

#### Agent Roles:
- **Supervisor Agent**: Orchestrates the workflow and determines the next step (Tutor vs. Evaluator).
- **Tutor Agent**: Focuses on helping the student understand the concepts.
- **Evaluator Agent**: Objectively assesses the student's answer against the context.

---

## 🛠 Tech Stack & Dependencies

### Core Backend
- **FastAPI**: High-performance web framework for building APIs with Python 3.14+.
- **SQLAlchemy (Async)**: Modern SQL toolkit and Object Relational Mapper for PostgreSQL.
- **PostgreSQL**: Primary relational database for user management and session persistence.

### AI & Agents
- **LangChain / LangGraph**: Frameworks for building stateful, multi-agent AI applications.
- **LangGraph Checkpoint (Postgres)**: Ensures workflow sessions are durable across restarts.
- **OpenAI / Google Gemini**: LLM providers for agent reasoning.
- **Pinecone**: Vector database for high-performance semantic search (RAG).

### Utilities & Processing
- **Docling**: Advanced document parsing (PDF, DOCX) to markdown for better AI ingestion.
- **Pydantic**: Data validation and settings management using Python type annotations.
- **Bcrypt**: Secure password hashing.
- **PyJWT**: JSON Web Token implementation for secure authentication.

---

## 🚦 Getting Started

### Prerequisites
- Python 3.14+
- [uv](https://github.com/astral-sh/uv) (Recommended) or `pip`
- Docker & Docker Compose (for database and indexing services)
- OpenAI / Google Gemini API Keys
- Pinecone API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-assisment
   ```

2. **Environment Setup**:
   Copy `.env.example` to `.env` and fill in your credentials.
   ```bash
   cp .env.example .env
   ```

3. **Install Dependencies**:
   ```bash
   # Using uv (fastest)
   uv sync

   # Using pip
   pip install -r requirements.txt
   ```

4. **Running Locally**:
   ```bash
   PYTHONPATH=src uv run uvicorn src.main:app --reload
   ```

### Running with Docker
```bash
# Build and start services (PostgreSQL, Adminer)
docker compose up -d

# Run application
PYTHONPATH=src uv run uvicorn src.main:app --reload
```

---

## 🧪 Code Quality

We maintain high standards for code quality using the following tools:

- **Pylint**: For static code analysis and enforcing coding standards.
  ```bash
  pylint src/
  ```
- **Black**: For consistent code formatting.
  ```bash
  black src/
  ```

---

## 📖 API Documentation

The full API documentation is available at `{BASE_URL}/docs` via Swagger UI.

### Key Endpoints

#### Authentication (`/auth`)
- `POST /auth/sign-up`: Register a new user (Student/Reviewer).
- `POST /auth/sign-in`: Authenticate and receive access/refresh tokens.
- `POST /auth/refresh-token`: Get a new access token.

#### Tutoring Workflow (`/workflow`)
- `POST /workflow/ask`: Initialize a session with a question.
- `POST /workflow/answer`: Submit a student answer for evaluation.
- `GET /workflow/pending`: (Reviewer Only) List questions awaiting approval.
- `POST /workflow/review`: (Reviewer Only) Approve/Reject AI evaluation.
- `GET /workflow/state/{question_id}`: Retrieve current session status.

#### Knowledge Management (`/vector-db`)
- `POST /vector-db/upload`: Parse and index documents (PDF/DOCX) into specific namespaces.

---

## 🤝 Contributing
Please ensure all code changes pass pylint and are formatted with black before submitting a pull request.

---

## 👥 User Roles & Permissions

The system implements Role-Based Access Control (RBAC) to ensure secure interaction with the tutoring workflow.

| Role | Description |
|---|---|
| **STUDENT** | Can ask questions, receive tutoring, and submit answers for evaluation. |
| **REVIEWER** | Can list pending evaluations and provide final human approval/scoring. |

### API Permission Mapping

| Category | Endpoint | Permission |
|---|---|---|
| **Auth** | `/auth/sign-up`, `/auth/sign-in`, `/auth/forgot-password`, `/auth/reset-password` | **Public** |
| | `/auth/refresh-token` | **Public** |
| **Workflow** | `POST /workflow/ask` | **STUDENT** |
| | `POST /workflow/answer` | **STUDENT** |
| | `GET /workflow/pending` | **REVIEWER** |
| | `POST /workflow/review` | **REVIEWER** |
| | `GET /workflow/state/{question_id}` | **Authenticated** |
| **User** | `PUT /users/{user_id}`, `DELETE /users/{user_id}` | **Authenticated (Self)** |
| **Vector DB** | `POST /vector-db/upload` | **Authenticated** |