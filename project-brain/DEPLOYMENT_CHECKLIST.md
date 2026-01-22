# Project Brain - Deployment Checklist

## ? Pre-Deployment

### Code & Documentation
- [x] All backend code complete (43 endpoints, 5000+ LOC)
- [x] All frontend code complete (8 pages, responsive UI)
- [x] Database schema complete (17 tables, optimized indexes)
- [x] API documentation complete (OpenAPI/Swagger)
- [x] README.md with quick start and troubleshooting
- [x] ARCHITECTURE.md with technical details
- [x] Inline code comments on complex logic
- [x] .gitignore configured

### Testing
- [ ] Local docker-compose tests
  ```bash
  ./quick-start.sh
  curl http://localhost:8000/health
  # Upload test document at http://localhost:3000
  # Test search at http://localhost:3000/search
  ```

- [ ] API endpoint tests (at least smoke tests)
  ```bash
  curl http://localhost:8000/health
  curl http://localhost:8000/documents
  curl -X POST http://localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "limit": 5}'
  ```

- [ ] Database migration tests
  ```bash
  docker-compose exec backend python -m alembic downgrade -1
  docker-compose exec backend python -m alembic upgrade head
  ```

- [ ] Celery task tests (watch logs)
  ```bash
  # Upload document via UI
  docker-compose logs worker -f  # Should show parse task starting
  ```

## ?? Security Checklist

- [ ] Change default credentials:
  - [ ] PostgreSQL `brain_user` password in `.env`
  - [ ] MinIO `admin/admin` credentials in `.env`
  - [ ] Neo4j `neo4j/neo4j_password` in `.env`
  - [ ] Qdrant API key in `.env`
  - [ ] FastAPI `SECRET_KEY` in `config.py`

- [ ] Update `.env` file:
  ```env
  # CHANGE THESE:
  POSTGRES_PASSWORD=<random-strong-password>
  MINIO_ACCESS_KEY=<random-key>
  MINIO_SECRET_KEY=<random-secret>
  NEO4J_PASSWORD=<random-password>
  QDRANT_API_KEY=<random-key>
  SECRET_KEY=<random-secret-key>
  
  # CONFIGURE FOR YOUR ENVIRONMENT:
  DATABASE_URL=postgresql://...
  MINIO_URL=http://...  # Change if using AWS S3 instead
  LM_STUDIO_URL=...     # Point to your LM Studio instance
  ```

- [ ] Enable HTTPS/SSL:
  - [ ] Use reverse proxy (nginx/traefik)
  - [ ] Configure SSL certificates
  - [ ] Update CORS settings in `main.py`

- [ ] Database security:
  - [ ] Enable PostgreSQL password authentication
  - [ ] Restrict network access to private networks
  - [ ] Set up automated backups
  - [ ] Enable query logging for audit

- [ ] API security:
  - [ ] Add authentication (JWT/OAuth2) - see `main.py` TODO
  - [ ] Implement rate limiting
  - [ ] Add request validation
  - [ ] Log all API calls

## ?? Deployment Steps

### Local Development (Docker)
1. [ ] Clone repository
   ```bash
   git clone <repo-url>
   cd project-brain
   ```

2. [ ] Configure environment
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. [ ] Start services
   ```bash
   # Option A: Automatic
   ./quick-start.sh
   
   # Option B: Manual
   docker-compose up -d
   sleep 15
   docker-compose exec backend python -m alembic upgrade head
   docker-compose exec backend python seed_data.py
   ```

4. [ ] Verify services
   ```bash
   docker-compose ps  # All should be "Up"
   curl http://localhost:8000/health
   ```

5. [ ] Access UI
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - MinIO: http://localhost:9001

### Production Deployment (Cloud)

#### AWS EC2
1. [ ] Launch EC2 instance:
   - AMI: Ubuntu 22.04 LTS
   - Type: t3.large (or larger)
   - Storage: 100GB+ EBS
   - Security: Allow ports 80, 443, 3000, 8000

2. [ ] Install Docker
   ```bash
   sudo apt-get update
   sudo apt-get install docker.io docker-compose
   sudo usermod -aG docker $USER
   ```

3. [ ] Clone and configure
   ```bash
   git clone <repo-url>
   cd project-brain
   cp .env.example .env
   # Edit .env for production
   ```

4. [ ] Use managed services (if possible):
   - [ ] RDS for PostgreSQL (instead of Docker)
   - [ ] ElastiCache for Redis (instead of Docker)
   - [ ] S3 for MinIO (instead of local)
   - [ ] Increase security, backups, monitoring

5. [ ] Set up reverse proxy (nginx)
   ```bash
   # Install nginx
   sudo apt-get install nginx
   # Configure at /etc/nginx/sites-available/default
   # Point to backend (8000), frontend (3000)
   sudo systemctl restart nginx
   ```

6. [ ] Set up SSL (Let's Encrypt)
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot certonly --nginx -d yourdomain.com
   ```

7. [ ] Start services
   ```bash
   docker-compose up -d
   docker-compose exec backend python -m alembic upgrade head
   docker-compose exec backend python seed_data.py
   ```

#### Kubernetes (Recommended for Scale)
1. [ ] Create Kubernetes manifests (not included, follow standard patterns)
   - Deployment for backend
   - Deployment for worker
   - Deployment for frontend
   - StatefulSet for PostgreSQL (or use managed RDS)
   - Ingress for traffic routing

2. [ ] Deploy
   ```bash
   kubectl apply -f k8s/
   ```

### Docker Compose (Staging/Testing)
```bash
# On your server
git clone <repo-url>
cd project-brain

# Edit .env for staging
cp .env.example .env
nano .env

# Start
docker-compose up -d

# Initialize
docker-compose exec backend python -m alembic upgrade head
docker-compose exec backend python seed_data.py

# Monitor
docker-compose logs -f
```

## ?? Post-Deployment

### Health Checks
- [ ] API responds to health check
  ```bash
  curl https://yourdomain.com/api/health
  ```

- [ ] Frontend loads
  ```bash
  curl https://yourdomain.com
  ```

- [ ] Database is running
  ```bash
  # From application
  GET /documents  # Should return documents list
  ```

- [ ] Vector DB is responsive
  ```bash
  # Via application search
  POST /search {"query": "test"}
  ```

- [ ] MinIO is accessible
  ```bash
  # Check in admin UI or via API
  ```

### Monitoring
- [ ] Set up logging aggregation
  - [ ] CloudWatch (AWS)
  - [ ] Stackdriver (GCP)
  - [ ] ELK Stack (self-hosted)

- [ ] Set up application monitoring
  - [ ] Application Performance Monitoring (APM)
  - [ ] Error tracking (Sentry)
  - [ ] Uptime monitoring

- [ ] Set up alerts
  - [ ] CPU/Memory > 80%
  - [ ] Disk space < 20%
  - [ ] Database connection pool exhausted
  - [ ] Task queue backlog > threshold
  - [ ] API errors > threshold

### Backups
- [ ] Daily PostgreSQL backups
  ```bash
  # AWS: Use RDS automated backups
  # Self-hosted: Use pg_dump
  pg_dump -U brain_user project_brain | gzip > backup-$(date +%Y%m%d).sql.gz
  ```

- [ ] Store backups offline
  - [ ] S3 with cross-region replication
  - [ ] Google Cloud Storage
  - [ ] Azure Blob Storage

- [ ] Test backup restoration
  ```bash
  # Monthly: Restore from backup to test instance
  ```

### Capacity Planning
- [ ] Monitor disk usage
  - [ ] PostgreSQL data size
  - [ ] MinIO storage
  - [ ] Qdrant vector storage

- [ ] Monitor database performance
  - [ ] Query execution times
  - [ ] Connection pool usage
  - [ ] Slow query log

- [ ] Monitor task queue
  - [ ] Queue depth
  - [ ] Task processing time
  - [ ] Worker utilization

- [ ] Monitor embeddings
  - [ ] Vector DB size
  - [ ] Search latency
  - [ ] Reranking latency

## ?? Updates & Maintenance

### Regular Tasks
- [ ] Weekly: Check logs for errors
- [ ] Weekly: Monitor disk space
- [ ] Monthly: Review security logs
- [ ] Monthly: Test backup restoration
- [ ] Quarterly: Update dependencies
- [ ] Quarterly: Review performance metrics

### Dependency Updates
```bash
# Backend
pip list --outdated
pip install --upgrade <package>

# Frontend
npm outdated
npm update

# Docker images
docker pull postgres:15
docker pull redis:7
# Restart services
docker-compose down
docker-compose up -d
```

### Schema Changes
```bash
# Create migration
docker-compose exec backend python -m alembic revision --autogenerate -m "Description"

# Review migration in alembic/versions/

# Apply (test first!)
docker-compose exec backend python -m alembic upgrade head
```

## ?? Scaling Considerations

### Horizontal Scaling
- [ ] Load balancer for multiple backend instances
- [ ] Multiple Celery workers
- [ ] PostgreSQL read replicas
- [ ] Redis cluster

### Vertical Scaling
- [ ] Increase server resources (CPU, RAM)
- [ ] Optimize database queries (add indexes)
- [ ] Optimize embedding models (quantization)

### Performance Optimization
- [ ] Cache frequently accessed data
- [ ] Batch process embeddings
- [ ] Use connection pooling
- [ ] Enable query result caching

## ?? Documentation for Production

- [ ] Create runbooks for common tasks
  - How to restart services
  - How to restore from backup
  - How to scale up/down
  - How to handle common errors

- [ ] Document your setup
  - Network architecture diagram
  - Service dependencies
  - Backup strategy
  - Disaster recovery plan

- [ ] Create on-call guide
  - Common alerts and responses
  - Escalation procedures
  - Emergency contacts

## ? Final Checklist Before Going Live

- [ ] All security checks completed
- [ ] All health checks passing
- [ ] Monitoring and alerts configured
- [ ] Backup strategy tested
- [ ] Documentation completed
- [ ] Team trained on deployment
- [ ] Runbooks prepared
- [ ] Disaster recovery plan tested
- [ ] Load testing completed (for anticipated traffic)
- [ ] SSL/HTTPS configured
- [ ] Domain DNS configured
- [ ] SSL certificate renewed annually (if applicable)
- [ ] Maintenance window scheduled for updates

## ?? Launch!

Once all items are checked:

1. Set DNS to point to your deployment
2. Monitor logs closely for first 24 hours
3. Be ready to roll back if issues arise
4. Communicate with users about the new system
5. Train users on how to use Project Brain

---

**Version**: 1.0  
**Last Updated**: 2024-01-15  
**Status**: Ready to Deploy ?
