# Deployment Guide

## Option 1: Hugging Face Spaces (Recommended - Free)

Hugging Face Spaces provides free hosting for Gradio apps.

### Quick Deploy

1. **Create a HuggingFace Account**
   - Go to https://huggingface.co/join
   - Verify your email

2. **Create a New Space**
   - Go to https://huggingface.co/new-space
   - Choose a name: `prompt-creator`
   - Select SDK: **Gradio**
   - Choose visibility: Public (free) or Private (Pro)

3. **Upload Files**
   
   Upload these files/folders to your Space:
   ```
   prompt_creator/     # The entire package directory
   app.py              # Entry point
   requirements.txt    # Dependencies
   README.md           # Copy from README_HF.md
   ```

4. **Add Secrets (Required for LLM)**
   - Go to Space Settings → Repository secrets
   - Add:
     ```
     AZURE_OPENAI_API_KEY = your-api-key
     AZURE_OPENAI_ENDPOINT = https://zycus-ptu.azure-api.net/ptu-intakemanagement
     AZURE_OPENAI_DEPLOYMENT = gpt4o-130524
     AZURE_OPENAI_API_VERSION = 2024-02-15-preview
     AZURE_OPENAI_VERIFY_SSL = false
     ```

5. **Done!** Your app will be live at:
   ```
   https://huggingface.co/spaces/YOUR_USERNAME/prompt-creator
   ```

### Using the Deploy Script

```bash
chmod +x deploy_to_hf.sh
./deploy_to_hf.sh
```

---

## Option 2: Docker (Self-Hosted)

### Build the Image

```bash
docker build -t prompt-creator .
```

### Run Locally

```bash
docker run -p 7860:7860 \
  -e AZURE_OPENAI_API_KEY="your-key" \
  -e AZURE_OPENAI_ENDPOINT="https://zycus-ptu.azure-api.net/ptu-intakemanagement" \
  -e AZURE_OPENAI_DEPLOYMENT="gpt4o-130524" \
  -e AZURE_OPENAI_VERIFY_SSL="false" \
  prompt-creator
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  prompt-creator:
    build: .
    ports:
      - "7860:7860"
    environment:
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=https://zycus-ptu.azure-api.net/ptu-intakemanagement
      - AZURE_OPENAI_DEPLOYMENT=gpt4o-130524
      - AZURE_OPENAI_API_VERSION=2024-02-15-preview
      - AZURE_OPENAI_VERIFY_SSL=false
    restart: unless-stopped
```

Run with:
```bash
export AZURE_OPENAI_API_KEY="your-key"
docker-compose up -d
```

---

## Option 3: Railway.app (Free Tier Available)

1. Connect your GitHub repo to Railway
2. Railway will auto-detect the Dockerfile
3. Add environment variables in Railway dashboard
4. Deploy!

---

## Option 4: Render.com (Free Tier Available)

1. Create a new Web Service on Render
2. Connect your GitHub repo
3. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
4. Add environment variables
5. Deploy!

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_API_KEY` | Yes | Your Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Yes | Deployment name (e.g., gpt4o-130524) |
| `AZURE_OPENAI_API_VERSION` | No | API version (default: 2024-02-15-preview) |
| `AZURE_OPENAI_VERIFY_SSL` | No | Set to "false" for corporate APIM |
| `GRADIO_SERVER_PORT` | No | Port to run on (default: 7860) |

---

## Demo Mode

If no API key is provided, the app runs in **demo mode** with mock LLM responses.
This is useful for testing the UI without incurring API costs.

