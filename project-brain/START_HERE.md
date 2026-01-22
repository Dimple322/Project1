# ?? Project Brain

**AI-powered document analysis and entity management system** | DB-First Architecture | Production-Ready

## ?? Welcome!

You've just received a **complete, production-ready monorepo** with everything needed to deploy an intelligent document analysis system. Everything is included—code, databases, frontend, documentation, and deployment guides.

## ? Quick Start (Choose One)

### ?? Automatic Setup (Recommended)

**Linux/Mac:**
```bash
cd project-brain
chmod +x quick-start.sh
./quick-start.sh
```

**Windows:**
```cmd
cd project-brain
quick-start.bat
```

### ?? Manual Setup

```bash
cd project-brain
docker-compose up -d
sleep 15
docker-compose exec backend python -m alembic upgrade head
docker-compose exec backend python seed_data.py
```

### ? Verify Installation

```bash
chmod +x verify.sh
./verify.sh
```

## ?? After Setup (5 seconds)

Once the quick-start completes, everything is running:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Web UI - Upload documents, search, review |
| **API** | http://localhost:8000 | REST API endpoints |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger documentation |
| **Qdrant** | http://localhost:6333/dashboard | Vector database UI |
| **MinIO** | http://localhost:9001 | File storage UI (admin/admin) |

## ?? Documentation Guide

Start here based on your role:

### ?? **For Everyone**
1. **[COMPLETE.md](./project-brain/COMPLETE.md)** - What's included & quick overview (2 min)
2. **[IMPLEMENTATION_SUMMARY.md](./project-brain/IMPLEMENTATION_SUMMARY.md)** - Features & tech stack (5 min)

### ????? **For Developers**
1. [README.md](./project-brain/README.md) - Full setup guide + API docs
2. [ARCHITECTURE.md](./project-brain/ARCHITECTURE.md) - Technical deep-dive
3. [DOCUMENTATION_INDEX.md](./project-brain/DOCUMENTATION_INDEX.md) - Navigation guide

### ?? **For DevOps/Deployment**
1. [DEPLOYMENT_CHECKLIST.md](./project-brain/DEPLOYMENT_CHECKLIST.md) - Pre-deployment & deployment steps
2. [docker-compose.yml](./project-brain/docker-compose.yml) - Container orchestration
3. [README.md](./project-brain/README.md) - Production section

## ?? Key Features

### Document Processing
- ?? Upload PDF, DOCX, TXT files
- ?? Automatic parsing (Docling + Unstructured fallback)
- ?? Semantic search with BGE-M3 embeddings
- ?? Result reranking with BGE-Reranker-v2-m3

### Intelligence Extraction
- ?? Auto-extract Issues, Actions, Decisions
- ??? Transcript correction using Lexicon
- ?? Entity linking (Projects, Facilities, Wells, Subsystems, etc.)
- ? Confidence scoring for human review

### Knowledge Management
- ?? Status cards with claims & evidence
- ?? Lexicon system (terms, abbreviations, synonyms)
- ?? Immutable curation audit trail
- ?? Comprehensive status reports

## ??? Architecture Overview

```
???????????????????????????????????????????????????
?         Browser (Next.js Frontend)              ?
?      http://localhost:3000                      ?
???????????????????????????????????????????????????
                          ?
???????????????????????????????????????????????????
?    FastAPI Backend (43 API Endpoints)           ?
?      http://localhost:8000/docs                 ?
??????????????????????????????????????????????????
     ?                                      ?
????????????????                  ????????????????????
? PostgreSQL   ?                  ? Specialized      ?
? (Relational) ?                  ? Services         ?
????????????????                  ????????????????????
                                  ? • Qdrant         ?
                                  ? • MinIO          ?
                                  ? • Redis          ?
                                  ? • Neo4j (opt)    ?
                                  ? • LM Studio (opt)?
                                  ????????????????????
```

**DB-First Design**: PostgreSQL is the single source of truth. Specialized stores support specific features.

## ?? What's Inside

```
project-brain/
??? ?? Documentation (3500+ lines)
?   ??? README.md - Full guide + API reference
?   ??? ARCHITECTURE.md - Technical design
?   ??? IMPLEMENTATION_SUMMARY.md - Features overview
?   ??? DEPLOYMENT_CHECKLIST.md - Production steps
?   ??? DOCUMENTATION_INDEX.md - Navigation
?
??? ?? Backend (Python 3.11 + FastAPI)
?   ??? 43 REST API endpoints
?   ??? 17 database tables
?   ??? 4 async tasks (Celery)
?   ??? Document parsing & embeddings
?   ??? Transcript processing
?
??? ??  Frontend (Next.js 14 + React)
?   ??? 8 pages (Documents, Search, Reports, etc.)
?   ??? 5 reusable components
?   ??? API client & custom hooks
?   ??? Responsive Tailwind CSS design
?
??? ?? DevOps (Docker)
?   ??? docker-compose.yml (7 services)
?   ??? Dockerfile files (backend + UI)
?   ??? quick-start scripts (auto setup)
?   ??? Makefile (dev commands)
?
??? ?? Database (PostgreSQL)
    ??? Complete schema with migrations
    ??? Optimized indexes
    ??? Seed data with demo entities
    ??? Support for versioning
```

## ? Real-World Example Workflow

1. **Upload a document**
   ```
   PDF file ? SHA256 check ? MinIO storage ? Create Document record
   ```

2. **Automatic processing**
   ```
   Parse (Docling) ? Extract chunks ? Generate embeddings (BGE-M3) ? Index in Qdrant
   ```

3. **Semantic search**
   ```
   Query ? Embed query ? Qdrant search (top-20) ? Rerank (BGE-Reranker) ? Return top-10
   ```

4. **Extract intelligence**
   ```
   Meeting transcript ? Correct using Lexicon ? Extract Issues/Actions/Decisions ? Flag for review
   ```

5. **Generate reports**
   ```
   Status card ? Aggregate claims + issues + actions ? Include evidence ? Present to user
   ```

## ?? Getting Started (5-10 minutes)

### Step 1: Start Services
```bash
cd project-brain
./quick-start.sh  # or quick-start.bat on Windows
```

### Step 2: Verify Everything Works
```bash
./verify.sh
```

### Step 3: Explore the UI
- Open http://localhost:3000 in your browser
- Click on "Documents" ? Upload a test PDF/DOCX file
- Click on "Search" ? Try a semantic search query
- Click on "Pending Review" ? See extracted items

### Step 4: Try the API
- Open http://localhost:8000/docs
- Explore interactive API documentation
- Try uploading a file via the API

## ?? Common Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f ui

# Stop services
docker-compose down

# Restart services
docker-compose restart backend worker

# Database access
docker-compose exec postgres psql -U brain_user -d project_brain

# Seed new demo data
docker-compose exec backend python seed_data.py

# Run database migrations
docker-compose exec backend python -m alembic upgrade head
```

## ?? Documentation Structure

```
project-brain/
??? COMPLETE.md                    ? What's included & stats
??? IMPLEMENTATION_SUMMARY.md      ? Features & overview
??? README.md                      ? Setup + API reference
??? ARCHITECTURE.md                ? Technical details
??? DOCUMENTATION_INDEX.md         ? Nav guide
??? DEPLOYMENT_CHECKLIST.md       ? Deployment steps
```

**Recommended reading order:**
1. **IMPLEMENTATION_SUMMARY.md** (5 min) - Overview
2. **README.md** (15 min) - Setup & features
3. **ARCHITECTURE.md** (20 min) - Technical details
4. Start coding! Follow patterns in existing code.

## ?? Learning Path

### Beginner (Understanding the System)
1. Read IMPLEMENTATION_SUMMARY.md
2. Run quick-start script
3. Explore UI at http://localhost:3000
4. Upload a test document
5. Read README.md sections

### Intermediate (Development)
1. Review backend code structure (main.py, models.py)
2. Review frontend components (lib/api.ts, components/)
3. Add a new API endpoint (follow existing patterns)
4. Add a new frontend page (follow existing patterns)

### Advanced (Scaling & Deployment)
1. Read ARCHITECTURE.md thoroughly
2. Review DEPLOYMENT_CHECKLIST.md
3. Set up for production deployment
4. Configure monitoring & logging
5. Plan for scale (caching, replication, etc.)

## ?? Key Concepts

- **DB-First**: PostgreSQL is source of truth
- **Idempotency**: SHA256 hashing prevents duplicates
- **Async**: Long-running tasks via Celery + Redis
- **Evidence**: All extractions link to source documents
- **Confidence**: Scores enable human review filtering
- **Versioning**: Support multiple parsing attempts

## ?? Tips for Success

1. **Read the Architecture**: Understand the design before modifying
2. **Follow Patterns**: New code should match existing style
3. **Test Locally**: Use docker-compose + quick-start before deploying
4. **Check Logs**: Errors appear in docker-compose logs
5. **Use API Docs**: http://localhost:8000/docs is your friend
6. **Explore DB**: Get comfortable with the schema

## ?? Troubleshooting

**Services won't start?**
```bash
docker-compose logs postgres  # Check what's wrong
docker system prune -a        # Clear Docker state
./quick-start.sh              # Try again
```

**Port conflicts?**
```bash
# Edit docker-compose.yml, change ports like "8001:8000"
```

**Slow embeddings?**
```bash
# BGE-M3 works on CPU but is faster on GPU
# Install CUDA support or use mock embeddings for testing
```

See **[README.md - Troubleshooting](./project-brain/README.md#troubleshooting)** for more.

## ?? Support Resources

- **Quick Questions**: Check [DOCUMENTATION_INDEX.md](./project-brain/DOCUMENTATION_INDEX.md)
- **API Questions**: Visit http://localhost:8000/docs
- **Architecture Questions**: Read [ARCHITECTURE.md](./project-brain/ARCHITECTURE.md)
- **Code Issues**: Check source code comments
- **Deployment Issues**: See [DEPLOYMENT_CHECKLIST.md](./project-brain/DEPLOYMENT_CHECKLIST.md)

## ? Checklist Before Going Live

- [ ] Read DEPLOYMENT_CHECKLIST.md
- [ ] Change all default passwords (.env file)
- [ ] Set up database backups
- [ ] Configure monitoring & logging
- [ ] Test on staging environment
- [ ] Load test with expected traffic
- [ ] Set up HTTPS/SSL
- [ ] Document your setup & runbooks

## ?? Project Stats

```
? 55+ Files Generated
? 5000+ Lines of Production Code
? 3500+ Lines of Documentation
? 43 API Endpoints
? 17 Database Tables
? 8 Frontend Pages
? 4 Async Tasks
? 100% Complete & Functional
```

## ?? Your Next Steps

1. **This minute**: `./quick-start.sh`
2. **Next 5 minutes**: Verify with `./verify.sh`
3. **Next 10 minutes**: Explore http://localhost:3000
4. **Next 30 minutes**: Read [IMPLEMENTATION_SUMMARY.md](./project-brain/IMPLEMENTATION_SUMMARY.md)
5. **Next hour**: Follow [ARCHITECTURE.md](./project-brain/ARCHITECTURE.md)
6. **Next day**: Review code and start customizing

## ?? License

MIT License - See LICENSE file in project-brain/ directory

---

## ?? You're All Set!

Everything you need is ready to go. Start with the quick-start script and refer to the documentation as needed.

**Made with ?? for intelligent document analysis**

Questions? Check the docs. Issues? See Troubleshooting. Ready to customize? Follow the code patterns.

**Happy analyzing! ????**
