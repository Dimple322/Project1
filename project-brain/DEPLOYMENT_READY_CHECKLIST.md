# ?? PRE-DEPLOYMENT CHECKLIST

## Database & Migrations

- [ ] PostgreSQL running (verify connection in .env)
- [ ] `alembic upgrade head` completes without errors
- [ ] `registry_entities` table exists with correct schema
- [ ] `registry_relations` table exists
- [ ] `curation_rules` table exists
- [ ] `object_state` table exists
- [ ] `state_conflicts` table exists
- [ ] `doc_page_blocks` table exists
- [ ] `page_anchors` table exists
- [ ] `table_attachments` table exists
- [ ] All indexes created successfully
- [ ] Foreign key constraints active

## Backend Services

- [ ] FastAPI starts: `docker exec project-brain-backend python -c "from main import app; print('OK')"`
- [ ] Redis running and accessible
- [ ] Qdrant running and accessible
- [ ] Neo4j running (for future features)
- [ ] MinIO running and accessible

## API Testing

### Registry Endpoints
- [ ] `GET /registry/entities` returns data
- [ ] `POST /registry/entities` creates entity
- [ ] `GET /registry/entities/{id}` returns entity
- [ ] `PUT /registry/entities/{id}` updates entity
- [ ] `DELETE /registry/entities/{id}` archives entity
- [ ] `POST /registry/relations` creates relation
- [ ] `GET /registry/relations` returns relations
- [ ] `GET /registry/tree` returns hierarchy
- [ ] `POST /registry/merge` merges entities
- [ ] `POST /registry/link-mention` returns scores

### Page Anchoring Endpoints
- [ ] `POST /page-anchors/detect` detects anchors
- [ ] `GET /page-anchors/page/{doc}/{page}` returns anchors
- [ ] `POST /page-anchors/table-attachments/auto-attach` attaches tables
- [ ] `GET /page-anchors/table-attachments/{doc}` returns attachments
- [ ] `PUT /page-anchors/table-attachments/{id}/reassign` reassigns table

### State & Rules Endpoints
- [ ] `POST /state/compute` computes state
- [ ] `GET /state/entity/{id}` returns state
- [ ] `GET /state/conflicts/{id}` returns conflicts
- [ ] `POST /state/conflicts/{id}/resolve` resolves conflict
- [ ] `POST /state/report/{id}` generates report
- [ ] `POST /rules/create-from-event` creates rule
- [ ] `GET /rules/` lists rules
- [ ] `GET /rules/{id}` returns rule details
- [ ] `PUT /rules/{id}` updates rule
- [ ] `POST /rules/{id}/test` tests rule
- [ ] `DELETE /rules/{id}` deletes rule

## Data Seeding

- [ ] `python seed_data.py` completes without errors
- [ ] Registry has 6 phases
- [ ] Registry has 2 facilities
- [ ] Registry has 4 subsystems
- [ ] Registry has 6 wells
- [ ] Registry has 2 contractors
- [ ] Registry has 5 people
- [ ] Lexicon has 13 terms
- [ ] Relations created for entities

## Frontend

- [ ] Next.js starts: `docker exec project-brain-ui npm run dev`
- [ ] UI loads at http://localhost:3000
- [ ] RegistryManager component loads
- [ ] RulesManager component loads
- [ ] StatusDashboard component loads
- [ ] API calls work (check network tab)
- [ ] No console errors

## Documentation

- [ ] ARCHITECTURE_ENHANCED.md exists and readable
- [ ] OPERATIONS_GUIDE.md exists and readable
- [ ] README_ENTERPRISE.md exists and readable
- [ ] ENTERPRISE_IMPLEMENTATION_COMPLETE.md exists
- [ ] All code files have docstrings
- [ ] README contains quick start

## Configuration

- [ ] `.env` file exists with all required variables
- [ ] `DATABASE_URL` is correct
- [ ] `REDIS_URL` is correct
- [ ] `QDRANT_HOST` is correct
- [ ] `AUTO_LINK_THRESHOLD` is set (recommend 0.75)
- [ ] `PENDING_REVIEW_THRESHOLD` is set (recommend 0.6)
- [ ] `CORRECTION_APPLY_THRESHOLD` is set (recommend 0.8)

## Security

- [ ] Passwords changed from defaults (.env)
- [ ] Database access restricted (if applicable)
- [ ] API not exposed to internet initially
- [ ] MinIO credentials changed from defaults
- [ ] Neo4j credentials set
- [ ] CORS configured for your domain
- [ ] Logging level appropriate (not DEBUG in production)

## Performance

- [ ] Database indexes verified: `\d registry_entities` shows indexes
- [ ] Query plan acceptable: `EXPLAIN SELECT * FROM registry_entities LIMIT 1`
- [ ] Connection pooling configured (if applicable)
- [ ] Qdrant storage configured appropriately
- [ ] No N+1 query issues (check logs)

## Monitoring Setup

- [ ] Logging configuration in place
- [ ] Correlation ID tracking ready to enable
- [ ] Error alerting configured
- [ ] Database backup strategy defined
- [ ] Backup tested and works
- [ ] Log aggregation set up (if applicable)

## Scaling Readiness

- [ ] Horizontal pod autoscaling configured (if K8s)
- [ ] Database connection pool size appropriate
- [ ] Worker scaling configured
- [ ] Cache strategy defined
- [ ] Read replicas planned (if applicable)
- [ ] Sharding plan documented (if applicable)

## Operational

- [ ] Team trained on OPERATIONS_GUIDE.md
- [ ] Runbooks created for common operations
- [ ] Incident response plan defined
- [ ] Rollback procedure tested
- [ ] Team access to systems verified
- [ ] On-call rotation established
- [ ] Communication channels set up

## Testing

- [ ] `pytest tests/test_linking.py` runs (even if placeholders)
- [ ] No SQL injection vulnerabilities (check query builders)
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak sensitive info
- [ ] Rate limiting considered
- [ ] Load test planned

## Final Verification

- [ ] System startup time acceptable
- [ ] Memory usage acceptable
- [ ] Disk usage acceptable
- [ ] Network latency acceptable
- [ ] All features work end-to-end
- [ ] Documentation is accurate
- [ ] Team can operate system
- [ ] Rollback tested and documented

---

## Pre-Launch Checklist (48 hours before)

- [ ] Full integration test passed
- [ ] Load test passed (if applicable)
- [ ] Backup verified
- [ ] Team briefed
- [ ] Monitoring alerts tested
- [ ] Incident response plan reviewed
- [ ] Communication channels tested
- [ ] Documentation finalized
- [ ] Release notes prepared
- [ ] Rollback procedure practiced

---

## Go-Live Checklist

**Day Before:**
- [ ] All pre-launch items complete
- [ ] Team available (no vacation)
- [ ] Monitoring active
- [ ] Backup recent and verified

**Day Of:**
- [ ] Start with monitoring dashboard open
- [ ] Have rollback plan accessible
- [ ] Team in war room (virtual or physical)
- [ ] Communication channels open
- [ ] Status page updated

**During Deployment:**
- [ ] Each step verified before next
- [ ] Monitoring checked after each step
- [ ] Team communication active
- [ ] No parallel changes to other systems

**Post-Deployment (First 4 hours):**
- [ ] All endpoints responding
- [ ] No error spikes in logs
- [ ] Database queries performing
- [ ] User workflows tested
- [ ] Team notified of go-live
- [ ] Documentation accessible

**Day 1 (First 24 hours):**
- [ ] Monitor continuously
- [ ] No critical issues reported
- [ ] Performance metrics acceptable
- [ ] User adoption proceeding
- [ ] Team ready for escalation

**Week 1:**
- [ ] Collect user feedback
- [ ] Monitor performance trends
- [ ] Document any issues
- [ ] Plan improvements
- [ ] Celebrate successful launch ??

---

## Rollback Procedure

**If serious issues found during launch:**

```bash
# 1. Stop application
docker-compose down

# 2. Restore database from backup
psql -U brain_user project_brain < backup_$(date +%Y%m%d).sql

# 3. Switch to previous code version
git checkout <previous_tag>

# 4. Rebuild and restart
docker-compose up -d

# 5. Verify endpoints respond
curl http://localhost:8000/docs

# 6. Verify data integrity
curl http://localhost:8000/registry/entities

# 7. Notify team
# Post to war room channel
```

**Decision points for rollback:**
- [ ] Multiple API errors (>10% failure rate)
- [ ] Database connection failures
- [ ] Data corruption detected
- [ ] Critical security issue found
- [ ] Performance degradation >50%
- [ ] User data loss
- [ ] Cannot access UI/API

---

## Success Criteria

? All tests passing  
? All endpoints responding  
? Database queries fast (<100ms for reads)  
? No critical errors in logs  
? User workflows complete successfully  
? Documentation accurate  
? Team comfortable with operations  
? Monitoring active and alerting  
? Backups automated  

**Status**: Ready for production ?

---

**Last Updated**: January 2024  
**Version**: 1.0  
**Next Review**: After first week of production  
