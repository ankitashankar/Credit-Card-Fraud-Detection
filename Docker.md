# Docker

Build the image from the project root:

```powershell
docker build -t credit-card-fraud-dashboard .
```

Start the dashboard and open <http://localhost:8501>:

```powershell
docker run --rm -p 8501:8501 credit-card-fraud-dashboard
```

The image includes the transaction CSV used by the dashboard and runs Streamlit
as an unprivileged user.