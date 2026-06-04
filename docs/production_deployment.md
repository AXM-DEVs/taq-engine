# TaQ Engine Production Deployment Guide

This document provides guidance for deploying TaQ Engine in a production environment with enterprise-grade security, scalability, and monitoring.

## Table of Contents
1. [Environment Configuration](#environment-configuration)
2. [Reverse Proxy Setup (NGINX)](#reverse-proxy-setup-nginx)
3. [Container Orchestration](#container-orchestration)
4. [Secret Management](#secret-management)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
7. [Scaling Considerations](#scaling-considerations)
8. [Security Best Practices](#security-best-practices)
9. [Operational Procedures](#operational-procedures)

---

## Environment Configuration

TaQ Engine uses environment variables for configuration. Below are the key environment variables for production:

### Required Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `TAQ_SECRET_KEY` | Secret key for JWT token generation (must be strong and unique) | `openssl rand -hex 32` | Yes |
| `TAQ_DB_ENGINE` | Database engine (`sqlite` or `postgresql`) | `postgresql` | Yes |
| `TAQ_DB_HOST` | Database host | `db.taq.internal` | Yes (if not sqlite) |
| `TAQ_DB_PORT` | Database port | `5432` | Yes (if not sqlite) |
| `TAQ_DB_USER` | Database username | `taq` | Yes (if not sqlite) |
| `TAQ_DB_PASSWORD` | Database password | `secure_password` | Yes (if not sqlite) |
| `TAQ_DB_NAME` | Database name | `taq_prod` | Yes |
| `TAQ_LLM_PROVIDER` | LLM provider (`ollama` or `openai`) | `ollama` | No |
| `TAQ_LLM_MODEL` | LLM model name | `mistral:7b` | No |
| `TAQ_LLM_BASE_URL` | LLM service URL | `http://ollama:11434` | No |
| `TAQ_LLM_API_KEY` | API key for LLM provider (if required) | `sk-...` | No |
| `TAQ_LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` | No |
| `TAQ_CACHE_ENABLED` | Enable caching (`true` or `false`) | `true` | No |
| `TAQ_CACHE_TTL` | Default cache TTL in seconds | `300` | No |
| `TAQ_DEBUG` | Enable debug mode (`true` or `false`) | `false` | No |

### Environment File Example (`.env.production`)

```env
TAQ_SECRET_KEY=your-strong-secret-key-here-change-in-production
TAQ_DB_ENGINE=postgresql
TAQ_DB_HOST=postgres.taq.internal
TAQ_DB_PORT=5432
TAQ_DB_USER=taq
TAQ_DB_PASSWORD=secure_postgres_password
TAQ_DB_NAME=taq_production
TAQ_LLM_PROVIDER=ollama
TAQ_LLM_MODEL=mistral:7b
TAQ_LLM_BASE_URL=http://ollama:11434
TAQ_LOG_LEVEL=INFO
TAQ_CACHE_ENABLED=true
TAQ_CACHE_TTL=300
TAQ_DEBUG=false
```

---

## Reverse Proxy Setup (NGINX)

For production deployments, it's recommended to use a reverse proxy like NGINX to handle SSL/TLS termination, load balancing, and static file serving.

### NGINX Configuration Example

```nginx
# /etc/nginx/sites-available/taq-engine
server {
    listen 80;
    server_name taq.example.com;
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name taq.example.com;

    # SSL/TLS Configuration (obtain certificates from Let's Encrypt or your CA)
    ssl_certificate /etc/letsencrypt/live/taq.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/taq.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Static files (served directly by NGINX for performance)
    location /static/ {
        alias /app/taq/static/;
        expires 30d;
        access_log off;
    }

    # API and application
    location / {
        proxy_pass http://taq-engine:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed for future features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (accessible without authentication)
    location /health/ {
        proxy_pass http://taq-engine:8000/health/;
        access_log off;
    }

    # Increase client body size for file uploads (if needed)
    client_max_body_size 10M;
}
```

### Docker Compose with NGINX

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  taq-engine:
    build: .
    env_file:
      - .env.production
    volumes:
      - taq-data:/app/data
      - taq-playbooks:/app/playbooks/user
    restart: unless-stopped
    depends_on:
      - postgres
      - ollama

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: taq_production
      POSTGRES_USER: taq
      POSTGRES_PASSWORD: secure_postgres_password
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/letsencrypt:ro
    depends_on:
      - taq-engine
    restart: unless-stopped

volumes:
  taq-data:
  taq-playbooks:
  pgdata:
  ollama-data:
```

---

## Container Orchestration (Kubernetes)

### Kubernetes Manifests Example

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: taq-production
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: taq-config
  namespace: taq-production
data:
  TAQ_LOG_LEVEL: "INFO"
  TAQ_CACHE_ENABLED: "true"
  TAQ_CACHE_TTL: "300"
  TAQ_DEBUG: "false"
---
# k8s/secrets.yaml (encrypt with SOPS or similar)
apiVersion: v1
kind: Secret
metadata:
  name: taq-secrets
  namespace: taq-production
type: Opaque
data:
  # These should be base64-encoded
  TAQ_SECRET_KEY: <base64-encoded-secret>
  TAQ_DB_PASSWORD: <base64-encoded-password>
  TAQ_LLM_API_KEY: <base64-encoded-api-key>
---
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: taq-postgres
  namespace: taq-production
spec:
  serviceName: "taq-postgres"
  replicas: 1
  selector:
    matchLabels:
      app: taq-postgres
  template:
    metadata:
      labels:
        app: taq-postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: taq_production
        - name: POSTGRES_USER
          value: taq
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: taq-secrets
              key: TAQ_DB_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
---
# k8s/taq-engine.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: taq-engine
  namespace: taq-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: taq-engine
  template:
    metadata:
      labels:
        app: taq-engine
    spec:
      containers:
      - name: taq-engine
        image: taq-engine:latest
        envFrom:
        - configMapRef:
            name: taq-config
        - secretRef:
            name: taq-secrets
        ports:
        - containerPort: 8000
        readinessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: taq-data
          mountPath: /app/data
        - name: taq-playbooks
          mountPath: /app/playbooks/user
      volumes:
      - name: taq-data
        persistentVolumeClaim:
          claimName: taq-data-pvc
      - name: taq-playbooks
        persistentVolumeClaim:
          claimName: taq-playbooks-pvc
---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: taq-engine
  namespace: taq-production
spec:
  selector:
    app: taq-engine
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: taq-ingress
  namespace: taq-production
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - taq.example.com
    secretName: taq-tls
  rules:
  - host: taq.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: taq-engine
            port:
              number: 80
```

---

## Secret Management

For production environments, never hardcode secrets in container images or configuration files. Use dedicated secret management solutions:

### Recommended Approaches:
1. **HashiCorp Vault** - Dynamic secrets, encryption as a service
2. **AWS Secrets Manager** - For AWS deployments
3. **Azure Key Vault** - For Azure deployments
4. **Kubernetes Secrets** (with encryption at rest) - For simple deployments
5. **SOPS** - For encrypting files in Git

### Example: Using Docker Secrets with Docker Swarm
```bash
# Create secrets
echo "your-strong-secret-key" | docker secret create TAQ_SECRET_KEY -
echo "secure_postgres_password" | docker secret create TAQ_DB_PASSWORD -

# Deploy stack with secrets
docker stack deploy -c docker-compose.production.yml taq
```

### Example: Using Kubernetes External Secrets Operator
```yaml
# ExternalSecret example for AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: taq-secrets
  namespace: taq-production
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: taq-secrets
    creationPolicy: Owner
  data:
  - secretKey: TAQ_SECRET_KEY
    remoteRef:
      key: prod/taq/secret-key
  - secretKey: TAQ_DB_PASSWORD
    remoteRef:
      key: prod/taq/db-password
```

---

## Monitoring and Logging

### Structured Logging
TaQ Engine already outputs structured logs in JSON-friendly format. For production, configure log aggregation.

### Recommended Monitoring Stack:
1. **Prometheus** + **Grafana** - For metrics collection and visualization
2. **ELK Stack** (Elasticsearch, Logstash, Kibana) or **EFK** (with Fluentd) - For log aggregation
3. **Jaeger** or **Zipkin** - For distributed tracing (if implementing microservices)
4. **Alertmanager** - For alerting on critical metrics

### Key Metrics to Monitor:
- Request latency and throughput (by endpoint)
- Error rates (HTTP 5xx, 4xx)
- Database connection pool usage
- Authentication success/failure rates
- Rate limiting events (HTTP 429)
- Investigation creation and execution times
- Playbook execution metrics
- Resource usage (CPU, memory, disk, network)

### Example Prometheus Configuration Snippet
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'taq-engine'
    static_configs:
      - targets: ['taq-engine:8000']
    metrics_path: '/metrics'  # Would need to implement metrics endpoint
    scrape_interval: 15s
```

### Health Check Endpoints
TaQ Engine provides:
- `GET /health/` - Basic liveness check
- `GET /docs` - API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

Consider adding a readiness probe that checks database connectivity.

---

## Backup and Disaster Recovery

### Database Backups
For PostgreSQL:
```bash
# Daily logical backup
pg_dump -U taq -h postgres.taq.internal taq_production > /backups/taq-db-$(date +%Y%m%d).sql

# Weekly base backup + WAL archiving for PITR
# Configure wal_level = replica, archive_mode = on in postgresql.conf
```

For SQLite (not recommended for production multi-instance):
```bash
# Copy the database file when no connections are active (or use VACUUM INTO)
cp taq.db /backups/taq-db-$(date +%Y%m%d).sqlite
```

### Configuration and Data Backups
- Back up `.env.production` and any custom configuration files
- Back up user-generated playbooks (stored in `/app/playbooks/user/` or persistent volume)
- Back up uploaded files or cached data if applicable

### Disaster Recovery Plan
1. **Backup Frequency**: Daily database backups, hourly WAL archiving (PostgreSQL)
2. **Retention**: Keep daily backups for 30 days, weekly for 3 months, monthly for 2 years
3. **Recovery Time Objective (RTO)**: < 4 hours
4. **Recovery Point Objective (RPO)**: < 1 hour
5. **Testing**: Perform restore drills quarterly

### Example Recovery Procedure
1. Provision new infrastructure
2. Restore database from latest backup
3. Apply WAL logs (if using PITR) to reach desired point in time
4. Deploy application with restored configuration
5. Validate data integrity and application functionality
6. Update DNS/load balancer to point to recovered system

---

## Scaling Considerations

### Horizontal Scaling
TaQ Engine can be scaled horizontally behind a load balancer. Considerations:
1. **Statelessness**: The application is designed to be stateless (state stored in database)
2. **Database Connections**: Ensure connection pool settings accommodate increased connections
3. **Cache**: If using a local cache (like Redis not currently implemented), use a distributed cache
4. **File Storage**: User playbooks are stored in a shared volume or object storage

### Vertical Scaling
Increase resources (CPU, memory) for individual instances based on workload.

### Database Scaling
- **Read Replicas**: For scaling read queries
- **Connection Pooling**: Use PgBouncer to manage database connections
- **Partitioning**: For large investigations tables, consider partitioning by date

### Caching Layer (Future Enhancement)
Consider adding Redis for:
- Rate limiting storage (to replace current in-memory limiter)
- Session storage
- Query result caching
- Playbook definition caching

---

## Security Best Practices

### Network Security
1. **Zero Trust**: Assume breach, verify every request
2. **Network Segmentation**: Separate frontend, backend, database, and monitoring networks
3. **Firewall Rules**: Only allow necessary ports (e.g., DB only accessible from app servers)
4. **Service Mesh**: Consider Istio or Linkerd for service-to-service security

### Application Security
1. **Input Validation**: TaQ Engine uses Pydantic for validation - keep dependencies updated
2. **Authentication**: 
   - Requires strong passwords (min 8 chars)
   - Uses bcrypt for password hashing
   - Implements rate limiting on auth endpoints
   - Uses JWT tokens with configurable expiration
3. **Authorization**: 
   - Role-based access control (Free/Premium tiers)
   - Resource ownership enforcement (users can only access their own investigations/playbooks)
   - Premium feature gating (e.g., abuse reporting)
4. **Secure Headers**: Already implemented via NGINX and middleware
5. **Dependency Scanning**: Regularly update dependencies and scan for vulnerabilities
6. **Security Headers**: Ensure X-Frame-Options, X-Content-Type-Options, etc. are set

### Data Protection
1. **Encryption at Rest**: Enable filesystem encryption or use encrypted volumes
2. **Encryption in Transit**: Enforce TLS 1.2+ everywhere
3. **Secrets Management**: Use dedicated secret management tools (see above)
4. **Data Minimization**: Only store necessary data; purge old investigations per retention policy

### Monitoring and Alerting
1. **Security Events**: Alert on multiple failed login attempts, rate limiting events
2. **Anomalous Behavior**: Alert on unusual spikes in investigation creation
3. **Vulnerability Scanning**: Regularly scan containers and host OS
4. **Audit Logs**: Maintain logs of administrative actions and sensitive data access

---

## Operational Procedures

### Deployment Process
1. **Code Changes**: 
   - Commit to feature branch
   - Open pull request
   - Required approvals and automated tests pass
   - Merge to main branch
2. **Build**: 
   - CI pipeline builds Docker image
   - Image pushed to registry with version tag
3. **Deploy**: 
   - Staging environment deployment and smoke tests
   - Production deployment (blue/green or rolling update)
   - Post-deployment validation

### Rollback Procedure
1. Identify problematic deployment
2. Rollback to previous known-good Docker image version
3. Verify service health
4. Investigate issue in isolated environment

### Routine Maintenance
1. **Daily**: 
   - Check backup success
   - Review security alerts
   - Monitor disk usage
2. **Weekly**:
   - Apply OS security patches (if managing hosts)
   - Check for application updates
   - Review performance metrics
3. **Monthly**:
   - Test backup restoration
   - Review access logs for anomalies
   - Update dependencies
4. **Quarterly**:
   - Perform disaster recovery drill
   - Review and update security policies
   - Capacity planning

### Incident Response
1. **Detection**: Via monitoring alerts or user reports
2. **Containment**: Isolate affected systems
3. **Eradication**: Remove threat, patch vulnerabilities
4. **Recovery**: Restore from backups if needed
5. **Post-Incident**: Conduct root cause analysis, update procedures

---

## Appendix: Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `TAQ_DEBUG` | `false` | Enable debug mode |
| `TAQ_SECRET_KEY` | `change-me` | Secret key for JWT (must be changed in production) |
| `TAQ_DATA_DIR` | `./data` | Directory for data storage |
| `TAQ_DB_ENGINE` | `sqlite` | Database engine (sqlite or postgresql) |
| `TAQ_DB_HOST` | `localhost` | Database host |
| `TAQ_DB_PORT` | `5432` | Database port |
| `TAQ_DB_USER` | `taq` | Database username |
| `TAQ_DB_PASSWORD` | `` | Database password |
| `TAQ_DB_NAME` | `taq` | Database name |
| `TAQ_LLM_PROVIDER` | `ollama` | LLM provider (ollama or openai) |
| `TAQ_LLM_MODEL` | `mistral:7b` | LLM model name |
| `TAQ_LLM_BASE_URL` | `http://localhost:11434` | LLM service URL |
| `TAQ_LLM_API_KEY` | `` | API key for LLM provider |
| `TAQ_LOG_LEVEL` | `INFO` | Logging level |
| `TAQ_CACHE_ENABLED` | `true` | Enable caching |
| `TAQ_CACHE_TTL` | `300` | Default cache TTL in seconds |

---

## License and Support

TaQ Engine is released under the MIT License. For enterprise support, contact the maintainers.

**Last Updated**: 2026-06-04