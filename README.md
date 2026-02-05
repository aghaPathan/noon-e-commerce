# Noon E-Commerce Intelligence Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Real-time price intelligence, competitor tracking, and alerting for **Noon.com** — Saudi Arabia's leading e-commerce marketplace.

## ✨ Features

- 📊 **Price Tracking** — Monitor SKU prices with historical trends
- 🏪 **Competitor Analysis** — Compare seller pricing across the marketplace
- 🔔 **Smart Alerts** — Get notified on price drops, stock changes, and anomalies
- 📈 **Analytics Dashboard** — Interactive charts and data visualization
- ⚡ **Daily Scraping** — Automated data collection via Airflow DAGs
- 🔌 **REST API** — Full-featured API with bearer token auth

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Airflow DAG   │────▶│  Noon Scraper   │────▶│   ClickHouse    │
│   (3 AM UTC)    │     │  (ScraperAPI)   │     │  (Price History)│
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
┌─────────────────┐     ┌─────────────────┐              │
│   PostgreSQL    │◀───▶│    FastAPI      │◀─────────────┘
│ (Users/Products)│     │   :8096/api     │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  React + Vite   │
                        │     :3001       │
                        └─────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| API Framework | FastAPI 0.109 |
| Primary DB | PostgreSQL 16 (users, products, auth) |
| Analytics DB | ClickHouse (price history, time-series) |
| Scraping | ScraperAPI + BeautifulSoup4 |
| Orchestration | Apache Airflow |
| Validation | Pydantic v2 |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| UI Components | Radix UI + shadcn/ui |
| Charts | Chart.js |
| State | Zustand + React Query |
| Testing | Vitest + Testing Library |

---

## 📁 Project Structure

```
noon-e-commerce/
├── api/                    # FastAPI backend
│   ├── main.py            # API endpoints
│   ├── models.py          # Pydantic schemas
│   └── database.py        # ClickHouse client
├── frontend-ts/           # React TypeScript frontend
│   ├── src/
│   │   ├── components/    # UI components (CompetitorTable, AlertFeed, etc.)
│   │   ├── hooks/         # Custom hooks (useAlertFeed, useProducts)
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript definitions
│   └── package.json
├── docker/                # Docker configurations
├── scripts/               # Utility scripts
├── noon_scraper.py        # Core scraping module
├── noon_dag.py            # Airflow DAG definition
├── postgres_schema.sql    # DB schema
└── docs/                  # Documentation
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- ClickHouse server
- [ScraperAPI](https://www.scraperapi.com/) account

### 1. Clone & Configure

```bash
git clone https://github.com/aghaPathan/noon-e-commerce.git
cd noon-e-commerce

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run API server
cd api && uvicorn main:app --host 0.0.0.0 --port 8096
```

### 3. Frontend Setup

```bash
cd frontend-ts
npm install
npm run dev   # Starts on http://localhost:3001
```

### 4. Airflow DAG (Optional)

```bash
# Copy DAG to Airflow
cp noon_dag.py ~/airflow/dags/

# DAG runs daily at 3 AM UTC (6 AM KSA)
```

---

## ⚙️ Configuration

| Variable | Description | Required |
|----------|-------------|:--------:|
| `SCRAPERAPI_KEY` | ScraperAPI authentication key | ✅ |
| `CLICKHOUSE_HOST` | ClickHouse server hostname | ✅ |
| `CLICKHOUSE_PORT` | ClickHouse native port (default: 9000) | ✅ |
| `CLICKHOUSE_USER` | Database username | ✅ |
| `CLICKHOUSE_PASSWORD` | Database password | ✅ |
| `CLICKHOUSE_DB` | Database name (default: `noon`) | ✅ |
| `API_TOKEN` | Bearer token for API auth | ✅ |
| `API_PORT` | API server port | ❌ |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/products` | List all tracked products |
| `GET` | `/api/products/{sku}` | Get product details |
| `GET` | `/api/prices/{sku}` | Get price history |
| `GET` | `/api/prices/{sku}/competitors` | Get competitor prices |
| `GET` | `/api/alerts` | Get active alerts |
| `POST` | `/api/alerts/acknowledge/{id}` | Acknowledge an alert |
| `GET` | `/api/health` | Health check |

All endpoints require `Authorization: Bearer <API_TOKEN>` header.

---

## 🧪 Testing

```bash
# Backend tests
pytest --cov=api

# Frontend tests
cd frontend-ts
npm run test
npm run test:ui   # Interactive UI
```

---

## 📊 Scraping Schedule

| Time (UTC) | Time (KSA) | Action |
|------------|------------|--------|
| 03:00 | 06:00 | Daily price scrape |

SKUs are configured in `skus.txt` (one per line).

---

## 📖 Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [API Design](API_DESIGN.md)
- [Scraping Guide](SCRAPING_GUIDE.md)
- [Dashboard Design](DASHBOARD_DESIGN.md)
- [DAG Strategy](DAG_STRATEGY.md)
- [Deployment Guide](DEPLOYMENT.md)

---

## 🔒 Security

- Credentials stored in `.env` (gitignored)
- API protected with bearer token authentication
- ClickHouse access restricted to localhost
- No PII collected — only public product data

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Agha Awais** — [@aghaPathan](https://github.com/aghaPathan)

---

<p align="center">
  <sub>Built for the KSA market 🇸🇦</sub>
</p>
