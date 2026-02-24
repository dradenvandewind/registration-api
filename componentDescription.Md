Component Description
API Layer (FastAPI)
Router: Handles request routing and versioning

Endpoints: Registration and activation endpoints

Dependencies: Authentication, validation

Middleware: Logging, error handling

Service Layer
User Service: Business logic for user management

Activation Service: Code generation and validation

Email Service: Third-party email API integration

Data Layer
Repositories: Pure SQL queries with connection pooling

Models: Pydantic models for validation

Migrations: SQL schema management

Database
PostgreSQL: Primary data store

Redis: Optional for rate limiting/caching

External Services
Email Service: Third-party SMTP API (MailHog for dev)

Key Features
Async/Await: Full async stack with asyncpg connection pooling

Dependency Injection: FastAPI Depends for auth and services

Pydantic Validation: Request/response model validation

Lifespan Events: Proper startup/shutdown handling

Exception Handling: Custom exceptions with HTTP mapping

Background Tasks: Email sending without blocking

Security: Password hashing with bcrypt

Testing: Async tests with pytest

Data Flow
Registration:

Client POST /v1/registration with email/password

Validate input with Pydantic

Check for existing user

Hash password and store user

Generate 4-digit code (expires in 60s)

Send code via email service (background)

Return user data

Activation:

Client POST /v1/activation with Basic Auth

Authenticate user with credentials

Validate code (4 digits, not expired, not used)

Mark code as used

Activate user account

Return success response
