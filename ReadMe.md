# Credit Card Fraud Detection Dashboard

A Streamlit dashboard for exploring credit card transaction activity and labeled fraud patterns. It cleans the supplied CSV data, applies interactive filters, and displays transaction metrics and charts.

> This project analyzes existing transactions labeled as fraudulent or legitimate; it does not train a fraud-prediction model or score live transactions.

## Dashboard features

- Filter transactions by date, merchant category, merchant country, and fraud status.
- View transaction count, fraud rate, total transaction volume, and average transaction amount.
- Explore transaction amount distributions, daily fraud rates, country-level activity, and fraud rates by credit-score band.
- View the filtered transaction records.

## Project workflow

1. **Load the data:** The app reads `credit_card_fraud_detection_2026.csv`.
2. **Validate and clean:** The data-processing module checks for required columns, parses dates and numeric values, removes invalid or duplicate transactions, and fills missing merchant categories and countries with `Unknown`.
3. **Filter transactions:** Dashboard controls select the date range, merchant categories, merchant countries, and transaction type.
4. **Calculate and visualize:** The app summarizes the filtered data and displays metrics and charts.
5. **Test and deploy:** Pytest verifies data-processing behavior; Docker and Kubernetes manifests support deployment.

## Project files

- `app.py` — Streamlit dashboard and interactive visualizations.
- `data_processing.py` — CSV loading, cleaning, and aggregation functions.
- `credit_card_fraud_detection_2026.csv` — supplied transaction dataset.
- `tests/` — data-processing tests.
- `requirements.txt` — Python dependencies.
- `Dockerfile`, `Docker.md` — container build and run instructions.
- `k8s/`, `kubernates.md` — Kubernetes deployment and autoscaling manifests and instructions.
- `.github/workflows/main.yml` — CI/CD workflow for tests, image publishing, and deployment.

## Requirements

- Python 3.12
- Internet access to install Python dependencies
- Optional for container deployment: Docker
- Optional for Kubernetes deployment: a running Kubernetes cluster and `kubectl`

## Run locally on Windows

From PowerShell, change to the project directory:

```powershell
cd "C:\Users\Aadar\OneDrive\Attachments\Credit_Card_Fraud SDP"
```

Create and activate a virtual environment, then install dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the dashboard:

```powershell
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually <http://localhost:8501>. Keep the CSV file in the project root, alongside `app.py`.

## Run tests

With the virtual environment activated:

```powershell
python -m pytest
```

The tests cover transaction cleaning, required-column validation, duplicate and invalid row handling, missing merchant values, and daily and geographic aggregations.

## Run with Docker

Build the image from the project root:

```powershell
docker build -t credit-card-fraud-dashboard .
```

Start the container:

```powershell
docker run --rm -p 8501:8501 credit-card-fraud-dashboard
```

Open <http://localhost:8501>. The Docker image includes the CSV dataset and runs the app as an unprivileged user. See `Docker.md` for the project's Docker instructions.

## Deploy to Kubernetes

1. Build the image:

   ```powershell
   docker build -t credit-card-fraud-dashboard:latest .
   ```

2. Start a Kubernetes cluster and confirm `kubectl` is configured for it. The provided deployment instructions target Docker Desktop Kubernetes.

3. Ensure the `ghcr-pull` image-pull secret referenced by `k8s/deployment.yaml` exists in the deployment namespace. For a local-only image, configure the manifest and image-pull settings appropriately for your cluster.

4. Apply the manifests:

   ```powershell
   kubectl apply -f k8s/
   ```

5. Check deployment, service, and autoscaler status:

   ```powershell
   kubectl get deployments,services,hpa
   ```

6. Open <http://localhost:30080> when the service is available.

The manifests configure two initial replicas, health probes, resource requests and limits, a NodePort service, and CPU-based scaling from two to five replicas. The HPA requires a working Metrics Server. See `kubernates.md` for the project's Kubernetes instructions.

## GitHub Actions CI/CD

The workflow in `.github/workflows/main.yml` runs tests on GitHub-hosted Ubuntu when changes are pushed to `main` or the workflow is manually dispatched. It then builds and publishes a GHCR image and deploys it to Docker Desktop Kubernetes using a Windows self-hosted runner.

Deployment prerequisites:

- Docker Desktop Kubernetes enabled on the machine running the self-hosted runner.
- A configured, online Windows self-hosted GitHub Actions runner with Docker and `kubectl` available.
- Repository secrets `GHCR_USERNAME` and `GHCR_READ_TOKEN`; the token needs permission to read the published package.
- The runner's Kubernetes context configured for Docker Desktop.

GitHub-hosted runners cannot access a Kubernetes cluster running locally on your machine. The repository includes `start-runner.ps1` to start its configured runner. Refer to `kubernates.md` for the workflow setup details.

## Data requirements

The CSV must include these columns for dashboard processing:

- `transaction_id`
- `transaction_datetime`
- `transaction_amount`
- `is_fraud`
- `merchant_country`
- `merchant_category`

The dashboard also uses `credit_score` when that column is present. The `is_fraud` values must be `0` (legitimate) or `1` (fraudulent); invalid rows are excluded during cleaning.
