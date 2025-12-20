# 🚀 BirdSense Deployment Guide

## Quick Deploy Options

### Option 1: HuggingFace Spaces (FREE - Recommended)

**URL after deploy:** `https://huggingface.co/spaces/YOUR_USERNAME/birdsense`

1. **Create HuggingFace account** at https://huggingface.co/join

2. **Create new Space:**
   ```bash
   # Install HuggingFace CLI
   pip install huggingface_hub
   
   # Login
   huggingface-cli login
   
   # Create and push
   cd birdsense
   huggingface-cli repo create birdsense --type space --space_sdk gradio
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/birdsense
   git push hf main
   ```

3. **Or use web interface:**
   - Go to https://huggingface.co/new-space
   - Name: `birdsense`
   - SDK: `Gradio`
   - Hardware: `CPU Basic` (free) or `T4 GPU` (faster)
   - Upload files manually

**Files needed:**
- `huggingface_app.py` → rename to `app.py`
- `requirements_hf.txt` → rename to `requirements.txt`
- `audio/` folder
- `models/` folder
- `data/` folder
- `checkpoints/` (if trained model available)

---

### Option 2: Render.com (FREE tier available)

**URL after deploy:** `https://birdsense.onrender.com`

1. **Connect GitHub repo** to Render

2. **Create new Web Service:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.server:app --host 0.0.0.0 --port $PORT`

3. **Environment variables:**
   ```
   PORT=8000
   ```

**render.yaml:**
```yaml
services:
  - type: web
    name: birdsense
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.server:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/v1/health
```

---

### Option 3: Railway.app (FREE tier: $5/month credits)

**URL after deploy:** `https://birdsense.up.railway.app`

1. **Connect GitHub** to Railway

2. **Deploy with one click:**
   - Railway auto-detects Python
   - Uses Dockerfile if present

3. **Add environment:**
   ```
   PORT=8000
   ```

---

### Option 4: Fly.io (FREE tier: 3 shared VMs)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login and launch
fly auth login
fly launch --name birdsense
fly deploy
```

**fly.toml:**
```toml
app = "birdsense"
primary_region = "sin"  # Singapore for India users

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[services.ports]]
  port = 80
  handlers = ["http"]

[[services.ports]]
  port = 443
  handlers = ["tls", "http"]
```

---

### Option 5: Google Colab (FREE - for demos)

Create a notebook:
```python
# Install dependencies
!pip install -q torch torchaudio librosa soundfile gradio

# Clone repository
!git clone https://github.com/YOUR_USERNAME/birdsense.git
%cd birdsense

# Run Gradio app
!python huggingface_app.py
```

---

## Deployment Comparison

| Platform | Cost | GPU | Custom Domain | Ease |
|----------|------|-----|---------------|------|
| **HuggingFace Spaces** | FREE | Optional ($) | No | ⭐⭐⭐⭐⭐ |
| Render | FREE/Paid | No | Yes ($) | ⭐⭐⭐⭐ |
| Railway | $5 credit | No | Yes | ⭐⭐⭐⭐ |
| Fly.io | FREE tier | No | Yes | ⭐⭐⭐ |
| Colab | FREE | Yes | No | ⭐⭐⭐⭐ |

---

## Recommended: HuggingFace Spaces

**Pros:**
- Completely free
- Built-in Gradio support
- ML community visibility
- Easy sharing
- Auto-scaling

**Steps:**
1. Fork/clone this repo
2. Rename `huggingface_app.py` to `app.py`
3. Rename `requirements_hf.txt` to `requirements.txt`
4. Push to HuggingFace Space
5. Share URL: `https://huggingface.co/spaces/YOUR_USERNAME/birdsense`

---

## Local Docker Deployment

```bash
# Build and run
docker-compose up -d

# Access
open http://localhost:8000/app
```

---

## Share with Team

After deployment, share:

1. **Web App URL:** `https://huggingface.co/spaces/YOUR_USERNAME/birdsense`
2. **API Docs:** `https://YOUR_URL/docs`
3. **Health Check:** `https://YOUR_URL/api/v1/health`

**For field researchers:**
- Open the URL on mobile browser
- Grant microphone permission
- Record bird sounds
- Get instant identification!

