# Kubernetes

## Manual deployment

```powershell
docker build -t credit-card-fraud-dashboard:latest .
```

Enable the Kubernetes cluster in Docker Desktop and ensure the Metrics Server
is available; the HPA needs it to read CPU utilization. Apply the manifests:

```powershell
kubectl apply -f k8s/
```

Open the dashboard at <http://localhost:30080>. Check rollout and autoscaling
status with:

```powershell
kubectl get deployments,services,hpa
```

## GitHub Actions deployment

The workflow in `.github/workflows/main.yml` runs tests and publishes the image
to GHCR on pushes to `main`. Its deploy job targets a Windows self-hosted GitHub
Actions runner on the machine running Docker Desktop, because GitHub-hosted
runners cannot access a local Kubernetes cluster.

To enable that job:

1. Enable Docker Desktop Kubernetes and confirm
   `kubectl config current-context` returns `docker-desktop`.
2. Add a Windows self-hosted runner to the GitHub repository on this machine.
   Keep the runner online and ensure it can run `kubectl`.
3. Create repository secrets `GHCR_USERNAME` and `GHCR_READ_TOKEN`. The token
   must be a GitHub classic personal access token with `read:packages` access
   to the published image.
4. Push to `main`. The workflow tests the project, builds and pushes the
   commit-tagged image, then updates the local Kubernetes deployment.