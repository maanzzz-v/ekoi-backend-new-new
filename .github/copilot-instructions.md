### ABOUT
- This project is a resume parser and indexer that extracts key information from resumes and stores it in a vector database for easy retrieval and search based on user queries.
- The goal is to enable efficient and accurate resume screening and matching for recruitment purposes.

### General Instructions
- Follow best practices for code organization and documentation.
- Write clear and concise pydoc comments for all public functions and classes.
- Update documentation as needed to reflect changes in functionality.
- Use logger for all logging purposes.
- properly handle all exceptions and errors.

### Tech Stack
- FastAPI
- Pydantic
- Pinecone
- Langchain

### Project Structure
- `src/`: The main source code for the application.
- `controller/`: Contains the API route handlers.
- `model/`: Contains the data models and schemas.
- `service/`: Contains the business logic and service layer.
- `utils/`: Contains utility functions and helpers.
- `core/`: Contains the core application logic and configurations.


### Implementation Details
- Donot use absolute imports within the `src/` directory.
- Donot use relative imports that go up the directory tree (e.g., `from ...`).


### Error Handling
- Use appropriate HTTP status codes for different error scenarios (e.g., 404 for not found, 500 for server errors).
- `exceptions/`: Contains custom exception classes for handling specific errors.

