# Intelligent CRM with Invoice Engine

Intelligent CRM with Invoice Engine is a Python-based business workflow project that combines:

- a CRM data source for leads and payments
- an invoice management web app built with Flask
- a local AI assistant that can query CRM data in natural language

The goal of the project is to help teams manage customers, generate invoices, track payments, and access CRM insights through a simple AI-driven interface.

## Project Modules

### 1. Invoice System
The `invoice_system/` module is a Flask application for:

- company profile and logo setup
- customer management
- tax invoice and proforma invoice creation
- GST-based tax calculation
- payment recording
- invoice PDF generation

By default, it runs on `http://127.0.0.1:5001`.

### 2. AI Agent
The `ai_agent/` module is a local CLI assistant that can:

- show today's leads
- search leads by company
- show lead status reports
- list pending payments
- show payment history
- return document requirements for supported services

The AI agent currently works through rule-based intent routing plus CRM/MySQL queries.

### 3. CRM Integration
The project expects CRM data from a MySQL database such as:

- `leads`
- `payments`

The invoice system also reads CRM leads while creating invoices.

## Current Repository State

The root launcher `run.py` expects a CRM app at `crm-flask/app.py`, but the `crm-flask/` folder is empty in this repository snapshot. That means:

- the invoice system can still be documented and developed
- the AI agent code exists
- full end-to-end startup through `run.py` will not work until the CRM Flask app is added back

## Tech Stack

- Python
- Flask
- MySQL
- `flask-mysqldb`
- `mysql-connector-python`
- WeasyPrint / fallback PDF generation
- Whisper
- `pyttsx3`
- Ollama

## Folder Structure

```text
.
|-- ai_agent/
|   |-- agent/
|   |-- db/
|   |-- input/
|   |-- llm/
|   |-- tools/
|   |-- voice/
|   |-- main.py
|   `-- run_agent.py
|-- crm-flask/
|-- invoice_system/
|   |-- app/
|   |   |-- controllers/
|   |   |-- models/
|   |   |-- repositories/
|   |   |-- services/
|   |   |-- templates/
|   |   `-- utils/
|   |-- migrate.py
|   `-- run.py
|-- create_ai_agent.py
|-- requirements.txt
`-- run.py
```

## Features

- Create and manage customers
- Configure company details, bank details, and logo
- Generate proforma and tax invoices
- Calculate CGST, SGST, and IGST
- Download invoices as PDF
- Track invoice payments
- Pull CRM leads into invoice creation flow
- Ask the AI assistant for CRM summaries and service document requirements

## Installation

### 1. Clone the project

```bash
git clone <your-repository-url>
cd Intelligent-CRM-with-Invoice-Engine
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

Install the root dependencies:

```bash
pip install -r requirements.txt
```

Install the invoice-system-specific dependencies too:

```bash
pip install -r invoice_system/requirements.txt
```

## Environment Variables

Create a `.env` file for the invoice system if you want to override defaults:

```env
SECRET_KEY=change-me
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=invoice_db
APP_HOST=127.0.0.1
APP_PORT=5001
CRM_URL=http://localhost:5000
INVOICE_ACCESS_SECRET=change-this-secret
INVOICE_ACCESS_TTL_SECONDS=3600
INVOICE_DEV_MODE=true
```

For the AI agent, these environment variables are used for CRM database access:

```env
CRM_DB_HOST=localhost
CRM_DB_USER=root
CRM_DB_PASSWORD=your_password
CRM_DB_NAME=crm_db
```

Important: this repository currently contains hard-coded development credentials in some AI agent files. Replace them with environment variables before using the project outside local development.

## Database Notes

You will need MySQL databases/tables for:

- invoice system data such as customers, invoices, invoice items, company settings, and invoice payments
- CRM data such as leads and payments

The invoice module includes a migration helper:

```bash
cd invoice_system
python migrate.py
```

For additional migration details, see [invoice_system/MIGRATION_GUIDE.md](/e:/all%20projects/sample_py/Intelligent-CRM-with-Invoice-Engine/invoice_system/MIGRATION_GUIDE.md).

## Running the Project

### Run the invoice system

```bash
python invoice_system/run.py
```

Open:

```text
http://127.0.0.1:5001
```

### Run the AI agent

```bash
python ai_agent/main.py
```

Or:

```bash
python ai_agent/run_agent.py
```

### Run everything from the root launcher

```bash
python run.py
```

Note: this currently depends on `crm-flask/app.py`, which is missing from this repository snapshot.

## Example AI Queries

- `show today's leads`
- `list pending payments`
- `lead details for ABC company`
- `status report`
- `payment history for XYZ Pvt Ltd`
- `documents required for gst registration`

## Main Entry Points

- [run.py](/e:/all%20projects/sample_py/Intelligent-CRM-with-Invoice-Engine/run.py)
- [invoice_system/run.py](/e:/all%20projects/sample_py/Intelligent-CRM-with-Invoice-Engine/invoice_system/run.py)
- [ai_agent/main.py](/e:/all%20projects/sample_py/Intelligent-CRM-with-Invoice-Engine/ai_agent/main.py)

## Known Limitations

- `crm-flask/` is empty in the current repo snapshot
- root `requirements.txt` and `invoice_system/requirements.txt` overlap but are not unified
- some AI agent database credentials are hard-coded for development
- full setup instructions for database schema are only partially documented in the repo

## License

This project is licensed under the MIT License. See [LICENSE](/e:/all%20projects/sample_py/Intelligent-CRM-with-Invoice-Engine/LICENSE).
