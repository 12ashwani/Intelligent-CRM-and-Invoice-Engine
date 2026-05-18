# Intelligent CRM and Invoice Engine

An integrated business automation platform that combines:

- Customer Relationship Management (CRM)
- AI-powered business assistant
- Invoice and billing management
- Payment tracking
- PDF invoice generation
- Business workflow automation

This project is designed to help businesses manage leads, customers, invoices, payments, and business operations from a unified system powered by Flask, MySQL, and AI-assisted workflows.

---

# Project Overview

The system contains three major modules:

| Module | Description |
|---|---|
| CRM System | Manage leads, customers, follow-ups, and payments |
| Invoice Engine | Generate GST invoices, proforma invoices, and payment records |
| AI Assistant | Query CRM and invoice data using natural language |

---

# Features

## CRM Features

- Lead management
- Customer management
- Follow-up tracking
- Payment tracking
- Lead status monitoring
- Dashboard analytics
- Search and filter leads
- CRM-integrated invoice generation

---

## Invoice Engine Features

- Tax Invoice generation
- Proforma Invoice generation
- GST calculations
- CGST / SGST / IGST support
- Company profile setup
- Company logo upload
- Bank details configuration
- PDF invoice export
- Invoice payment tracking
- Invoice history management

---

## AI Assistant Features

The AI assistant supports natural language queries such as:

- Show today's leads
- List pending payments
- Search company details
- Payment history lookup
- Lead status reports
- GST registration document requirements
- CRM business insights

The AI module currently supports:

- Rule-based intent routing
- CRM database querying
- Voice-ready architecture
- Ollama integration
- Whisper speech processing
- pyttsx3 text-to-speech

---

# Tech Stack

## Backend

- Python
- Flask
- MySQL
- SQLAlchemy
- flask-mysqldb
- mysql-connector-python

---

## AI & Automation

- Ollama
- Whisper
- pyttsx3

---

## PDF & Reporting

- WeasyPrint
- HTML/CSS invoice templates

---

# Project Structure

```text
Intelligent-CRM-and-Invoice-Engine/
│
├── ai_agent/
│   ├── agent/
│   ├── config/
│   ├── db/
│   ├── input/
│   ├── llm/
│   ├── tools/
│   ├── voice/
│   ├── main.py
│   ├── run_agent.py
│   └── test_db.py
│
├── crm/
│   ├── app.py
│   ├── routes/
│   ├── templates/
│   ├── static/
│   ├── models/
│   ├── controllers/
│   ├── services/
│   └── utils/
│
├── comman_db/
│
├── invoice_system/
│   ├── app/
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── templates/
│   │   └── utils/
│   │
│   ├── migrate.py
│   ├── run.py
│   └── requirements.txt
│
├── shared_sso/
├── requirements.txt
├── run.py
├── LICENSE
└── README.md
```

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/12ashwani/Intelligent-CRM-and-Invoice-Engine.git
cd Intelligent-CRM-and-Invoice-Engine
```

Repository:
https://github.com/12ashwani/Intelligent-CRM-and-Invoice-Engine

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv crmenv
crmenv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv crmenv
source crmenv/bin/activate
```

---

## 3. Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

Optional invoice-system-specific dependencies:

```bash
pip install -r invoice_system/requirements.txt
```

---

# Environment Variables

Create a `.env` file in the root directory.

## CRM Database

```env
CRM_DB_HOST=localhost
CRM_DB_USER=root
CRM_DB_PASSWORD=your_password
CRM_DB_NAME=crm_db
```

---

## Invoice System

```env
SECRET_KEY=change-me

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=crm_db

APP_HOST=127.0.0.1
APP_PORT=5001

CRM_URL=http://localhost:5000

INVOICE_ACCESS_SECRET=change-this-secret
INVOICE_ACCESS_TTL_SECONDS=3600
INVOICE_DEV_MODE=true
```

---

# Database Setup

You need MySQL databases for:

## CRM Database

Tables such as:

- leads
- customers
- follow_ups
- payments

---

## Invoice Database

Tables such as:

- invoices
- invoice_items
- customers
- company_settings
- invoice_payments

---

## Run Database Migration

```bash
cd invoice_system
python migrate.py
```

---

# Running the Project

## Run CRM Application

```bash
python crm/app.py
```

Default:

```text
http://127.0.0.1:5000
```

---

## Run Invoice System

```bash
python invoice_system/run.py
```

Default:

```text
http://127.0.0.1:5001
```

---

## Run AI Assistant

```bash
python ai_agent/main.py
```

Or:

```bash
python ai_agent/run_agent.py
```

---

## Run Complete System

```bash
python run.py
```

This launches the integrated CRM + Invoice + AI workflow system.

---

# Example AI Queries

```text
show today's leads

list pending payments

lead details for ABC company

status report

payment history for XYZ Pvt Ltd

documents required for gst registration
```

---

# Main Entry Points

| File | Purpose |
|---|---|
| run.py | Main integrated launcher |
| crm/app.py | CRM application |
| invoice_system/run.py | Invoice module |
| ai_agent/main.py | AI assistant |

---

# Security Notes

Before production deployment:

- Remove hard-coded credentials
- Use environment variables
- Configure HTTPS
- Secure database access
- Add authentication & authorization
- Store secrets securely

---

# Future Enhancements

- Role-based authentication
- Multi-user CRM
- Email automation
- WhatsApp integration
- AI analytics dashboard
- OCR invoice scanning
- API integrations
- Cloud deployment support
- Docker support
- Kubernetes deployment

---

# Deployment Options

You can deploy the project using:

- Render
- Railway
- VPS (Ubuntu)
- AWS EC2
- Azure
- DigitalOcean

---

# License

This project is licensed under the MIT License.

See the LICENSE file for details.

---

# Author

Ashwani Kumar

- Machine Learning Engineer
- Data Science & AI Developer
- CRM and Business Automation Developer

GitHub:
https://github.com/12ashwani