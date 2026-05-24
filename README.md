# Remindee Backend

A **FastAPI** backend service that powers the Remindee app. It accepts a user headshot and a text prompt, then generates stylized AI images (realistic, anime, pixel art, cartoon) using **OpenAI** and stores them via **ImageKit**.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🖼️ AI Image Generation | Generates up to **4 styled images** per job using OpenAI's image API |
| 🎨 Art Styles | Realistic · Anime · Pixel Art · Cartoon |
| ☁️ Cloud Storage | Images uploaded and served via **ImageKit CDN** |
| 🗄️ Persistent Jobs | All jobs & images tracked in a **SQLite** database (swappable) |
| ⚡ Async Processing | Image generation runs as a background fire-and-forget task |
| 📖 Auto Docs | Interactive Swagger UI at `/docs` |

---

## 🏗️ Project Structure

```
remindee-backend/
├── main.py                  # FastAPI app entry point
├── config.py                # Environment variable loader
├── database.py              # SQLModel engine & session helpers
├── models.py                # Job & Image database models
├── routes/
│   └── routes.py            # All API endpoints
├── services/
│   ├── generator.py         # Orchestrates AI image generation
│   ├── openai_service.py    # OpenAI API wrapper
│   └── imagekit_service.py  # ImageKit upload wrapper
├── Dockerfile               # Multi-stage Docker build
├── pyproject.toml           # Project metadata & dependencies
└── requirement.txt          # Pip-compatible dependency list
```

---

## 🚀 Quick Start

### Prerequisites

- Python **3.9+** (or Docker)
- An **OpenAI API key** with image generation access
- An **ImageKit** account (free tier works)

---

### Option 1 – Run with Docker (Recommended)

**1. Clone the repository**

```bash
git clone https://github.com/your-username/remindee-backend.git
cd remindee-backend
```

**2. Create your environment file**

```bash
cp .env.example .env
```

Then open `.env` and fill in your keys:

```env
OPENAI_API_KEY=sk-...
IMAGEKIT_PRIVATE_KEY=private_...
IMAGEKIT_PUBLIC_KEY=public_...
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_id
```

**3. Build the Docker image**

```bash
docker build -t remindee-backend .
```

**4. Run the container**

```bash
docker run -d \
  --name remindee-backend \
  --env-file .env \
  -p 8000:8000 \
  remindee-backend
```

**5. Open the API docs**

Visit [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2 – Run Locally (without Docker)

**1. Clone & enter the project**

```bash
git clone https://github.com/your-username/remindee-backend.git
cd remindee-backend
```

**2. Create a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

**3. Install dependencies**

```bash
pip install -r requirement.txt
```

**4. Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

**5. Start the server**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**6. Open the API docs**

Visit [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔑 Environment Variables

Create a `.env` file in the project root with the following keys:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key |
| `IMAGEKIT_PRIVATE_KEY` | ✅ | ImageKit private key |
| `IMAGEKIT_PUBLIC_KEY` | ✅ | ImageKit public key |
| `IMAGEKIT_URL_ENDPOINT` | ✅ | Your ImageKit URL endpoint |

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload-headshot` | Upload a headshot image, returns a CDN URL |
| `POST` | `/api/jobs` | Create a new image generation job |
| `GET` | `/api/jobs/{job_id}` | Poll job status and retrieve generated image URLs |
| `GET` | `/docs` | Interactive Swagger UI |

### Example: Create a Job

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A confident entrepreneur in a modern city",
    "nums_images": 2,
    "headshot": "https://ik.imagekit.io/your_id/headshots/photo.png"
  }'
```

Response:
```json
{ "job_id": "3f7a2b1c-..." }
```

---

## 🎨 Supported Art Styles

| Style | Description |
|---|---|
| `realistic` | Photo-realistic, DSLR quality, natural lighting |
| `anime` | Studio Ghibli-inspired, vibrant cel-shading |
| `pixel_art` | 16-bit retro, classic arcade aesthetic |
| `cartoon` | Bold outlines, flat vivid colors, western animation |

---

## 🛠️ Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** – Modern async Python web framework
- **[SQLModel](https://sqlmodel.tiangolo.com/)** – SQL database ORM built on SQLAlchemy + Pydantic
- **[OpenAI Python SDK](https://github.com/openai/openai-python)** – AI image generation
- **[ImageKit](https://imagekit.io/)** – Image storage and CDN delivery
- **[Uvicorn](https://www.uvicorn.org/)** – ASGI server
- **SQLite** – Zero-config embedded database (easily swappable via `DATABASE_URL`)

---

## 🐳 Docker Details

The `Dockerfile` uses a **multi-stage build** to keep the final image small and secure:

1. **Builder stage** – installs all Python dependencies using `uv`
2. **Runtime stage** – copies only the venv and app code, runs as a **non-root user**

```bash
# Rebuild after dependency changes
docker build --no-cache -t remindee-backend .

# View container logs
docker logs -f remindee-backend

# Stop & remove the container
docker stop remindee-backend && docker rm remindee-backend
```

---

## 📄 License

MIT © Remindee
