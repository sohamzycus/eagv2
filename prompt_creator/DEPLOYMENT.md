# Deployment Guide

Deploy the Procurement Workflow Agent Creator to various free-tier platforms.

## 🥇 Option 1: Hugging Face Spaces (Recommended)

**Best for:** Gradio apps, completely free, no credit card required.

### Quick Deploy

1. Create a Hugging Face account at https://huggingface.co/join

2. Create a new Space:
   - Go to https://huggingface.co/new-space
   - Name: `workflow-agent-creator`
   - SDK: `Gradio`
   - Visibility: Public (free) or Private (Pro)

3. Upload files:
   ```bash
   # Install git-lfs if needed
   git lfs install
   
   # Clone your space
   git clone https://huggingface.co/spaces/YOUR_USERNAME/workflow-agent-creator
   cd workflow-agent-creator
   
   # Copy files
   cp -r /path/to/prompt_creator/* .
   
   # Rename README
   mv README_HF.md README.md
   
   # Push to HF
   git add .
   git commit -m "Initial deployment"
   git push
   ```

4. (Optional) Add secrets for LLM support:
   - Go to Space Settings > Repository secrets
   - Add: `AZURE_OPENAI_API_KEY`

### Using the Deploy Script

```bash
chmod +x deploy_to_hf.sh
./deploy_to_hf.sh YOUR_USERNAME workflow-agent-creator
```

---

## 🥈 Option 2: Railway.app

**Best for:** Docker deployments, $5 free credit/month.

1. Sign up at https://railway.app

2. Create new project from GitHub:
   - Connect your repo
   - Railway auto-detects Dockerfile

3. Add environment variables:
   ```
   AZURE_OPENAI_API_KEY=your_key
   GRADIO_SERVER_PORT=7860
   ```

4. Deploy!

---

## 🥉 Option 3: Render.com

**Best for:** Simple deployments, free tier with sleep after inactivity.

1. Sign up at https://render.com

2. Create new Web Service:
   - Connect GitHub repo
   - Environment: Docker
   - Instance Type: Free

3. Add environment variables in dashboard

4. Deploy triggers automatically on push

---

## 🎯 Option 4: Fly.io

**Best for:** Low-latency global deployment, free tier available.

1. Install flyctl:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Login and deploy:
   ```bash
   fly auth login
   fly launch --name workflow-creator
   fly secrets set AZURE_OPENAI_API_KEY=your_key
   fly deploy
   ```

---

## 🐳 Local Docker Deployment

### Build and Run

```bash
# Build
docker build -t workflow-creator .

# Run (demo mode - no API key)
docker run -p 7860:7860 workflow-creator

# Run with LLM support
docker run -p 7860:7860 \
  -e AZURE_OPENAI_API_KEY="your_key" \
  -e AZURE_OPENAI_VERIFY_SSL="false" \
  workflow-creator
```

### Using Docker Compose

```bash
# Create .env file with your keys
echo "AZURE_OPENAI_API_KEY=your_key" > .env

# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | No | - | API key for LLM refinement |
| `AZURE_OPENAI_ENDPOINT` | No | Zycus PTU | Azure endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | No | gpt4o-130524 | Deployment name |
| `AZURE_OPENAI_API_VERSION` | No | 2024-02-15-preview | API version |
| `AZURE_OPENAI_VERIFY_SSL` | No | false | SSL verification |
| `GRADIO_SERVER_PORT` | No | 7860 | Server port |

**Note:** The app works without any API keys - it just won't have LLM-powered refinement.

---

## Troubleshooting

### Port already in use
```bash
lsof -i:7860 | awk 'NR>1 {print $2}' | xargs kill -9
```

### Docker build fails
```bash
# Clean Docker cache
docker system prune -a
docker build --no-cache -t workflow-creator .
```

### Hugging Face Space not loading
- Check Space logs in Settings > Logs
- Ensure `app.py` is in root directory
- Verify requirements.txt has all dependencies
