## Example kubernetes files

- Use with kubectl to apply to a working kubernetes cluster
- Modify `ingress.yaml` with your desired hostname and TLS settings
- Modify `configmap-and-secrets.yaml` with your email settings
- If needed, modify `deployments.yaml` with a higher `--concurrency` argument for the Celery worker
