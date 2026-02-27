# registration-api

A containerized REST API with automated documentation and test coverage.

---

## 🚀 Getting Started

### 1 — Clone the repository

```bash
git clone https://github.com/dradenvandewind/registration-api.git
cd registration-api
```

### 2 — Generate a secret key

```bash
./GenerateSecretKey.sh
```

### 3 — Build & Run

**First time (build the image):**
```bash
docker compose up -d --build
```

**Subsequent starts:**
```bash
docker compose up -d
```

---

## 📖 API Documentation

Once the stack is running, open your browser at:

```
http://localhost:8000/docs
```

---

## 🧪 Run Tests

```bash
docker compose exec api pytest -v --cov=app
```

---

## 📋 Logs

```bash
docker compose logs -f api
```

---

## 🛑 Stop & Clean Up

```bash
docker compose down -v
```

> ⚠️ The `-v` flag removes all volumes — any persisted data will be lost.
