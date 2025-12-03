"""
BRD Agent - API Module
FastAPI services for BRD processing
"""

from .pdf_parser import app as pdf_parser_app

__all__ = ["pdf_parser_app"]
