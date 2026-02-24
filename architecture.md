# Architecture Overview

```mermaid
graph TB
    Client[Client Application]
    API[FastAPI Application]
    DB[(PostgreSQL)]
    Redis[(Redis)]
    Email[Email Service API]
    
    subgraph "Docker Containers"
        API
        DB
        Redis
        Email
    end
    
    Client -->|HTTP Requests| API
    
    subgraph "API Layer"
        direction TB
        Router[API Router]
        Auth[Auth Dependency]
        Registration[Registration Endpoint]
        Activation[Activation Endpoint]
    end
    
    subgraph "Service Layer"
        direction TB
        UserService[User Service]
        ActivationService[Activation Service]
        EmailService[Email Service]
    end
    
    subgraph "Data Layer"
        direction TB
        UserRepo[User Repository]
        ActivationRepo[Activation Repository]
    end
    
    Router --> Registration
    Router --> Activation
    Activation --> Auth
    
    Registration --> UserService
    Registration --> ActivationService
    Registration --> EmailService
    
    Activation --> ActivationService
    ActivationService --> UserService
    
    UserService --> UserRepo
    ActivationService --> ActivationRepo
    
    UserRepo --> DB
    ActivationRepo --> DB
    
    EmailService -->|HTTP| Email
    
    style API fill:#f9f,stroke:#333,stroke-width:2px
    style DB fill:#dfd,stroke:#333,stroke-width:2px
    style Redis fill:#ffd,stroke:#333,stroke-width:2px
