Component Description

API Layer (FastAPI)

* Router: Handles request routing and versioning

* Endpoints: Registration and activation endpoints

* Dependencies: Authentication, validation

* Middleware: Logging, error handling

Service Layer

* User Service: Business logic for user management

* Activation Service: Code generation and validation

* Email Service: Third-party email API integration

Data Layer

* Repositories: Pure SQL queries with connection pooling

* Models: Pydantic models for validation

* Migrations: SQL schema management

Database

* PostgreSQL: Primary data store

* Redis: Optional for rate limiting/caching

External Services

* Email Service: Third-party SMTP API (MailHog for dev)

Key Features

1 - Async/Await: Full async stack with asyncpg connection pooling

2 - Dependency Injection: FastAPI Depends for auth and services

3 - Pydantic Validation: Request/response model validation

4 - Lifespan Events: Proper startup/shutdown handling

5 - Exception Handling: Custom exceptions with HTTP mapping

6 - Background Tasks: Email sending without blocking

7 - Security: Password hashing with bcrypt

8 - Testing: Async tests with pytest

Data Flow

1 - Registration:

* Client POST /v1/registration with email/password

* Validate input with Pydantic

* Check for existing user

* Hash password and store user

* Generate 6-digit code (expires in 600s)

* Send code via email service (background)

* Return user data

2 - Activation:

* Client POST /v1/activation with Basic Auth

* Authenticate user with credentials

* Validate code (4 digits, not expired, not used)

* Mark code as used

* Activate user account

* Return success response


Testing Strategy

* Unit Tests: Service layer logic

*Integration Tests: API endpoints with test database

* Mock External Services: Email service

* Coverage: Minimum 99% coverage

Production Considerations

1 - Security: HTTPS, rate limiting, input validation

2 - Monitoring: Health checks, metrics, structured logging

3 - Resilience: Retry logic for email service, dead letter queues

4 - Scalability: Connection pooling, stateless design

5 - CI/CD: GitHub Actions for automated testing