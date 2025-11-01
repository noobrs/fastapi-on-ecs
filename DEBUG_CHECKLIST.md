# Debug Checklist for fastapi-on-ecs

## ✅ Fixed Issues

### 1. Requirements.txt Updated
- Added all missing dependencies:
  - `python-dotenv` - for loading .env files
  - `supabase` - Supabase client
  - `pydantic-settings` - for Settings management
  - `httpx` - async HTTP client
  - `Pillow` - image processing
  - `spacy` - NLP processing
  - `spacy-layout` - PDF layout analysis
  - `gliner` - entity recognition
  - `PyMuPDF` - PDF processing
  - `opencv-python` - face detection
  - `numpy` - numerical operations

### 2. README.md Typo Fixed
- Changed `.gitiginore` to `.gitignore`

### 3. Dockerfile Enhanced
- Added system dependencies for OpenCV and PyMuPDF
- Improved layer caching by copying requirements.txt first
- Added comments for spaCy model download if needed

---

## ⚠️ Issues That Need Manual Review

### 1. Resume Processing Logic Commented Out
**File:** `app/services/resume_pipeline.py` (lines 91-108)

**Problem:** The actual resume parsing and redaction is commented out, replaced with placeholder data:
```python
# parsed_resume = await asyncio.to_thread(self._parse_resume, pdf_bytes)
# redacted_bytes = await asyncio.to_thread(self._redactor.redact, pdf_bytes)

result = ResumeProcessingResult(
    resume_id=payload.resume_id,
    job_seeker_id=payload.job_seeker_id,
    redacted_file_path=redacted_path,
    skills=list("skills"),  # ❌ Creates ['s', 'k', 'i', 'l', 'l', 's']
    education=list("education"),  # ❌ Creates ['e', 'd', 'u', 'c', 'a', 't', 'i', 'o', 'n']
    experience=list("experience"),  # ❌ Creates individual letters
    feedback=str("feedback"),  # ❌ Just the string "feedback"
)
```

**Action Required:** Uncomment the actual processing logic when ready to use it.

---

### 2. Environment Variables Configuration

**Files that need `.env.local`:**
- `app/config.py` - needs:
  - `RESUME_PIPELINE_HMAC_SECRET`
  - `RESUME_PIPELINE_WEBHOOK_URL`
- `app/supabase_client.py` - needs:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`

**Root `.env` file needed for Makefile:**
- `AWS_ACCOUNT_ID`
- `AWS_REGION`

**Action Required:** Create these environment files before running the application.

---

### 3. Spacy Language Model
**File:** `app/pdf/nlp.py`

**Potential Issue:** The GLiNER model will be downloaded on first run. Consider pre-downloading in Dockerfile or during container build.

**File:** `app/pdf/layout.py`

**Note:** Uses `spacy.blank("en")` which doesn't require a pre-trained model, but if you need NER later, you'll need to download a model like `en_core_web_sm`.

---

### 4. Import Path Consistency

**Current Structure:**
```
app/
├── main.py (imports from root: supabase_client, config, services.resume_pipeline)
├── config.py
├── supabase_client.py
├── services/
│   └── resume_pipeline.py (also imports from root: config, supabase_client)
├── app/
│   ├── schemas.py
│   └── security.py
└── pdf/
    ├── layout.py
    ├── nlp.py
    └── redactor.py
```

**Problem:** Mixing root-level imports with package imports can cause issues.

**Recommendation:** Consider reorganizing to have a clearer package structure or ensure PYTHONPATH is set correctly.

---

### 5. Supabase Storage Bucket
**File:** `app/services/resume_pipeline.py`

**Line 140-149:** Uploads to bucket `resumes-redacted`

**Action Required:** 
- Ensure this bucket exists in your Supabase project
- Verify proper permissions are set for the service role key

---

### 6. Face Detection Performance
**File:** `app/pdf/redactor.py`

**Line 72-78:** Currently removes ALL images on a page if ANY face is detected.

**Comment in code:**
```python
# Use full-page heuristic: if any face exists, remove all images (safer bias-wise)
```

**Consideration:** This is aggressive. If you have logos or charts, they'll be removed too. Consider if this is the desired behavior.

---

## 🧪 Testing Recommendations

### Local Testing Steps:

1. **Install Dependencies Locally:**
   ```bash
   cd app
   pip install -r requirements.txt
   ```

2. **Create `.env.local` in app/ directory:**
   ```env
   RESUME_PIPELINE_HMAC_SECRET=your-secret-key
   RESUME_PIPELINE_WEBHOOK_URL=http://localhost:3000/api/webhooks/resume
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   ```

3. **Run the application:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Test endpoints:**
   - `http://localhost:8000/` - Basic health check
   - `http://localhost:8000/api/py/health` - Health endpoint
   - `http://localhost:8000/api/py/test-supabase` - Test Supabase connection
   - `http://localhost:8000/api/py/docs` - API documentation

### Docker Testing:

1. **Build locally first:**
   ```bash
   cd app
   docker build -t fastapi-test .
   ```

2. **Run with environment variables:**
   ```bash
   docker run -p 8000:80 --env-file .env.local fastapi-test
   ```

---

## 📝 Additional Notes

### Current Import Errors in IDE:
These are expected if you haven't installed dependencies locally:
- ✅ Will be resolved after running `pip install -r requirements.txt`

### AWS Deployment:
- Ensure `.env` file exists in root for Makefile variables
- Backend TF files should be created as per README instructions
- Remember to `make destroy-service` to avoid costs

### Performance Considerations:
- GLiNER and OpenCV models load in memory - consider container memory sizing
- PDF processing is CPU-intensive - ECS task size should be appropriate
- Consider adding health check timeouts for model loading

---

## 🔧 Quick Fix Commands

```bash
# Install dependencies in virtual environment
cd app
pip install -r requirements.txt

# Check for Python syntax errors
python -m py_compile main.py

# Run local server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test Docker build
docker build -t test-fastapi .

# Run with Docker
docker run -p 8000:80 --env-file .env.local test-fastapi
```

---

## ✨ Summary

**Status:** Repository structure is sound, but needs configuration and testing.

**Priority Actions:**
1. ✅ Dependencies updated in requirements.txt
2. ⚠️ Create `.env.local` file with required variables
3. ⚠️ Uncomment resume processing logic when ready
4. ⚠️ Test locally before deploying to AWS
5. ⚠️ Ensure Supabase bucket exists

**Ready for:** Local testing after environment configuration
**Not ready for:** Production deployment without testing
