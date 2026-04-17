#!/usr/bin/env python3
"""
AI Agent Runner for CRM Integration
Sets up environment variables and runs the AI agent
"""

import os
import sys

# Set CRM database environment variables
os.environ['CRM_DB_HOST'] = 'localhost'
os.environ['CRM_DB_USER'] = 'root'
os.environ['CRM_DB_PASSWORD'] = 'Dayachand@7037'
os.environ['CRM_DB_NAME'] = 'crm_db'

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from main import main

if __name__ == "__main__":
    main()
