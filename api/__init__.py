"""
BRD Agent - API Module
FastAPI services for BRD processing
"""

from .main import app
from .pdf_parser import app as pdf_parser_app

__all__ = ["app", "pdf_parser_app"]
