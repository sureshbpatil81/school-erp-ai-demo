# Database package
# Import main functions for easy access

from .connection import get_connection, execute_query, execute_many
from .schema import create_tables
from .demo_data import generate_all_demo_data
