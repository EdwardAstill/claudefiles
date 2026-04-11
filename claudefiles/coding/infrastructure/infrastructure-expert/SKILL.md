---
name: infrastructure-expert
description: >
  Use when writing Dockerfiles, docker-compose configs, Kubernetes manifests,
  Terraform or Pulumi IaC, cloud configuration (AWS/GCP), or Nginx and reverse
  proxy setups. Covers containerization, orchestration, infrastructure-as-code,
  and deployment configuration. Medium-priority — invoke for any infra work.
---

# Infrastructure Expert

Infrastructure-as-code, containerization, orchestration, and deployment
configuration. Produces reproducible, secure, minimal infrastructure.

**Core principle:** Infrastructure must be reproducible from code alone.
If it can't be recreated by running a script, it doesn't exist.

## When to Use

- Writing or reviewing Dockerfiles and docker-compose configurations
- Creating or modifying Kubernetes manifests (Deployments, Services, Ingress)
- Writing Terraform or Pulumi infrastructure-as-code
- Configuring cloud services (AWS, GCP, Azure)
- Setting up Nginx, Caddy, or other reverse proxies
- Configuring CI/CD deployment pipelines
- Debugging container build or runtime issues

## When NOT to Use

- **CI/CD workflow files** (GitHub Actions YAML) — use `github-actions-expert`
- **Application security review** — use `security-review`
- **Database configuration and tuning** — use `database-expert`
- **Application code performance** — use `performance-profiling`

## The Iron Law

```
EVERY INFRASTRUCTURE CHANGE MUST BE IN VERSION-CONTROLLED CODE
```

No manual console clicks. No SSH-and-edit. No "I'll document it later."

## Docker Best Practices

### Dockerfile Patterns

```dockerfile
# GOOD: Multi-stage build, minimal final image
FROM rust:1.77 AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main(){}" > src/main.rs && cargo build --release
COPY src/ src/
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/myapp /usr/local/bin/
USER nobody
ENTRYPOINT ["myapp"]
```

**Dockerfile rules:**
1. Use multi-stage builds — build dependencies don't belong in production images
2. Order layers by change frequency — `COPY requirements.txt` before `COPY . .`
3. Pin base image versions — `python:3.12-slim`, never `python:latest`
4. Run as non-root — `USER nobody` or create a dedicated user
5. Use `.dockerignore` — exclude `.git`, `node_modules`, `target/`, `.env`
6. Minimize layers — combine RUN commands with `&&`
7. Clean up in the same layer — `apt-get install && rm -rf /var/lib/apt/lists/*`

### docker-compose

```yaml
services:
  app:
    build: .
    ports: ["8080:8080"]
    environment:
      DATABASE_URL: postgres://db:5432/app
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]

volumes:
  pgdata:
```

## Kubernetes Patterns

**Deployment checklist:**
- Resource requests AND limits on every container
- Liveness and readiness probes
- Pod disruption budgets for HA
- ConfigMaps for non-sensitive config, Secrets for sensitive
- Never use `latest` tag — pin image versions

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    spec:
      containers:
        - name: myapp
          image: myapp:1.2.3
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
```

## Terraform / IaC

**Principles:**
1. **State is sacred** — use remote backend (S3, GCS), enable state locking
2. **Modules for reuse** — don't copy-paste resource blocks
3. **Variables for environment differences** — same code, different tfvars
4. **Plan before apply** — always `terraform plan` and review
5. **Import existing resources** — don't recreate what already exists

```hcl
# Remote state backend
terraform {
  backend "s3" {
    bucket         = "my-tf-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf-lock"
    encrypt        = true
  }
}
```

## Nginx / Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    location / {
        proxy_pass http://app:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Anti-patterns

| Anti-pattern | Why It's Bad | Instead |
|-------------|-------------|---------|
| `latest` tag in production | Non-reproducible deployments | Pin exact version tags |
| Running as root in containers | Container escape = host compromise | `USER nobody` or dedicated user |
| Secrets in environment variables | Visible in `docker inspect`, process list | Secret managers, mounted files |
| No health checks | Orchestrator can't detect failures | Add liveness and readiness probes |
| Manual infrastructure changes | Undocumented, unreproducible state drift | Infrastructure-as-code only |
| Single replica with no PDB | Any disruption = downtime | Multiple replicas + PDB |
| No resource limits | One pod can starve the node | Always set requests and limits |
| Storing state in containers | Lost on restart | External volumes or databases |

## Tools

| Tool | Purpose | Command |
|------|---------|---------|
| `docker` | Container runtime | `docker build`, `docker compose up` |
| `kubectl` | Kubernetes CLI | `kubectl apply -f`, `kubectl get pods` |
| `terraform` | Infrastructure-as-code | `terraform plan`, `terraform apply` |
| `pulumi` | IaC with real languages | `pulumi up` |
| `trivy` | Container image scanning | `trivy image myapp:latest` |
| `hadolint` | Dockerfile linter | `hadolint Dockerfile` |
| `kubeval` | Kubernetes manifest validation | `kubeval deployment.yaml` |
| `dive` | Docker image layer analysis | `dive myapp:latest` |

## Outputs

- Dockerfiles with multi-stage builds and security hardening
- docker-compose configs with health checks and proper networking
- Kubernetes manifests with resource limits and probes
- Terraform/Pulumi modules with remote state configuration
- Chain into `verification-before-completion` to confirm deployment works
