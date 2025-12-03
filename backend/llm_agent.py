"""
LLM Agent Module using Google Gemini.

This module provides an intelligent agent that can understand natural language
queries about SportsRadar NCAAFB data and generate SQL queries to retrieve
information from the database.
"""

import os
import sys
import re
import json
from typing import Optional, Dict, List, Any, Tuple
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import google.generativeai as genai
except ImportError:
    print("⚠️  WARNING: google-generativeai not installed!")
    print("   Please run: pip install google-generativeai")
    genai = None

try:
    from backend.db_connection import DatabaseConnection
except ImportError:
    from db_connection import DatabaseConnection

# Load environment variables
load_dotenv()


class LLMAgent:
    """LLM Agent for querying SportsRadar NCAAFB database using Google Gemini."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the LLM agent.
        
        Args:
            api_key: Google Gemini API key. If None, reads from environment.
            model_name: Gemini model to use (default: gemini-2.5-flash, will auto-select if not available)
        """
        if genai is None:
            raise ImportError("google-generativeai package is required. Install with: pip install google-generativeai")
        
        # Load from .env file in backend directory
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please set it in your .env file or pass it as a parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Get available models and find one that supports generateContent
        available_models = self._get_available_models()
        
        # Try to use the requested model first
        if model_name in available_models:
            try:
                self.model = genai.GenerativeModel(model_name)
                self.model_name = model_name
            except Exception as e:
                print(f"Warning: Could not initialize {model_name}, trying alternatives...")
                model_name = None
        
        # If requested model failed or not available, try alternatives
        if model_name is None or model_name not in available_models:
            # Try models in order of preference (lighter models first for better quota)
            model_attempts = [
                "gemini-2.5-flash",           # Newest, fast, good quota
                "gemini-2.0-flash",           # Fast, good quota
                "gemini-flash-latest",        # Latest flash version
                "gemini-2.5-flash-lite",      # Even lighter
                "gemini-2.0-flash-lite",      # Light version
                "gemini-1.5-flash",           # Older but reliable
                "gemini-pro-latest",          # Latest pro version
                "gemini-1.5-pro",             # Older pro
                "gemini-pro",                 # Original pro
                "models/gemini-2.5-flash",    # With models/ prefix
                "models/gemini-2.0-flash",
                "models/gemini-flash-latest",
                "models/gemini-pro-latest"
            ]
            
            # Also try any available model
            if available_models:
                model_attempts.extend(available_models)
            
            model_initialized = False
            for attempt_model in model_attempts:
                try:
                    self.model = genai.GenerativeModel(attempt_model)
                    self.model_name = attempt_model
                    print(f"✅ Using model: {attempt_model}")
                    model_initialized = True
                    break
                except Exception as e:
                    # Try next model
                    continue
            
            if not model_initialized:
                error_msg = f"Could not initialize any Gemini model. "
                if available_models:
                    error_msg += f"Available models: {', '.join(available_models[:5])}"
                else:
                    error_msg += "No models found. Please check your API key."
                raise ValueError(error_msg)
        
        # Initialize database connection
        self.db = DatabaseConnection()
        self.db.connect()
        
        # Get schema information
        self.schema_info = self.db.get_schema_info()
        
        # Build schema context for LLM
        self.schema_context = self._build_schema_context()
    
    def _get_available_models(self) -> List[str]:
        """
        Get list of available Gemini models that support generateContent.
        
        Returns:
            List of available model names
        """
        try:
            models = genai.list_models()
            available = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    # Extract model name (remove 'models/' prefix if present)
                    model_name = model.name
                    if model_name.startswith('models/'):
                        short_name = model_name[7:]  # Remove 'models/' prefix
                        available.append(short_name)
                    available.append(model_name)  # Also add the full name
            return list(set(available))  # Remove duplicates
        except Exception as e:
            print(f"Warning: Could not list models: {e}")
            return []
    
    def _build_schema_context(self) -> str:
        """
        Build a human-readable schema description for the LLM.
        
        Returns:
            String containing schema description
        """
        context = """# NCAAFB Database Schema

This database contains SportsRadar NCAA Football data with the following tables:

"""
        for table_name, table_info in self.schema_info.get('tables', {}).items():
            context += f"## {table_name.upper()}\n"
            context += "Columns:\n"
            for col in table_info['columns']:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                context += f"  - {col['name']} ({col['type']}) {nullable}{default}\n"
            
            if table_info['foreign_keys']:
                context += "Foreign Keys:\n"
                for fk in table_info['foreign_keys']:
                    context += f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}\n"
            context += "\n"
        
        # Add example queries
        context += """## Example Query Patterns

- Team information: "What teams are in the SEC conference?"
- Player statistics: "Show me the top 10 players by rushing yards"
- Rankings: "What are the current top 5 ranked teams?"
- Conference data: "List all conferences and their divisions"
- Player details: "Find players from Alabama"

## Important Notes

- All IDs are UUIDs (not integers)
- Use JOINs to connect related tables
- Use proper SQL syntax for PostgreSQL
- Always use parameterized queries when possible
- Return only SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)

"""
        return context
    
    def _validate_sql_safety(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that SQL query is safe (read-only).
        
        Args:
            sql_query: SQL query string to validate
            
        Returns:
            Tuple of (is_safe: bool, error_message: Optional[str])
        """
        sql_upper = sql_query.upper().strip()
        
        # Remove comments to avoid false positives
        # Remove single line comments (-- ...)
        sql_no_comments = re.sub(r'--.*$', '', sql_upper, flags=re.MULTILINE)
        # Remove multi-line comments (/* ... */)
        sql_no_comments = re.sub(r'/\*.*?\*/', '', sql_no_comments, flags=re.DOTALL)
        
        # Block dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 
            'INSERT', 'UPDATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
        
        for keyword in dangerous_keywords:
            # Check for the keyword as a whole word, not as part of another word
            if re.search(rf'\b{keyword}\b', sql_no_comments):
                return False, f"Query contains forbidden keyword: {keyword}"
        
        # Only allow SELECT or WITH statements
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
            return False, "Only SELECT or WITH queries are allowed"
        
        # Block semicolon injection attempts
        if sql_query.count(';') > 1:
            return False, "Multiple statements not allowed"
        
        return True, None
    
    def _extract_sql_from_response(self, response_text: str) -> Optional[str]:
        """
        Extract SQL query from LLM response.
        
        Args:
            response_text: LLM response text
            
        Returns:
            SQL query string or None if not found
        """
        # Try to find SQL in code blocks
        sql_pattern = r'```(?:sql)?\s*((?:WITH|SELECT).*?)\s*```'
        match = re.search(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            # Validate and fix incomplete query
            return self._validate_and_fix_sql(query)
        
        # Try to find SQL without code blocks
        sql_pattern = r'((?:WITH|SELECT).*?)(?:;|$)'
        match = re.search(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            # Validate and fix incomplete query
            return self._validate_and_fix_sql(query)
        
        # Look for SQL after keywords
        lines = response_text.split('\n')
        in_sql = False
        sql_lines = []
        
        for line in lines:
            if re.match(r'^\s*(WITH|SELECT)\s+', line, re.IGNORECASE):
                in_sql = True
                sql_lines.append(line)
            elif in_sql:
                if line.strip().endswith(';') or not line.strip():
                    sql_lines.append(line)
                    break
                elif re.match(r'^\s*(FROM|WHERE|JOIN|GROUP|ORDER|HAVING|LIMIT|UNION|INTERSECT|EXCEPT)', line, re.IGNORECASE):
                    sql_lines.append(line)
                else:
                    sql_lines.append(line)
        
        if sql_lines:
            query = '\n'.join(sql_lines).strip().rstrip(';')
            # Validate and fix incomplete query
            return self._validate_and_fix_sql(query)
        
        return None
    
    def _validate_and_fix_sql(self, sql_query: str) -> Optional[str]:
        """
        Validate and fix common SQL syntax issues.
        
        Args:
            sql_query: SQL query string
            
        Returns:
            Fixed SQL query string or None if invalid
        """
        if not sql_query:
            return None
        
        # Remove trailing whitespace
        sql_query = sql_query.strip()
        
        # Early validation - reject obviously malformed queries
        # Check if query contains explanatory text that suggests it's not actual SQL
        if ('to generate a query' in sql_query.lower() or 
            'specific question' in sql_query.lower() or 
            'please provide' in sql_query.lower() or
            'related to the database' in sql_query.lower() or
            'understand the question' in sql_query.lower()):
            return None
        
        # Check if query has basic SQL structure
        sql_upper = sql_query.upper()
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
            return None
        
        # Check if query contains valid SQL keywords
        valid_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP', 'ORDER', 'LIMIT', 'WITH', 'AS', 'ON', 'AND', 'OR', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN']
        has_valid_structure = any(keyword in sql_upper for keyword in valid_keywords)
        if not has_valid_structure:
            return None
        
        # Additional validation - check if query looks like natural language text
        # Count words vs SQL-like tokens
        words = sql_query.split()
        if len(words) < 3:  # Too short to be a valid SQL query
            return None
        
        # Check for too many consecutive lowercase words (indicative of natural language)
        consecutive_lowercase = 0
        max_consecutive = 0
        for word in words:
            if word.isalpha() and word.islower() and not word.upper() in valid_keywords:
                consecutive_lowercase += 1
                max_consecutive = max(max_consecutive, consecutive_lowercase)
            else:
                consecutive_lowercase = 0
        
        # If we have too many consecutive lowercase words, it's likely natural language
        if max_consecutive > 4:
            return None
        
        # Fix common CTE issues - ensure proper structure
        if 'WITH' in sql_query.upper():
            # Check if this looks like a malformed CTE
            lines = sql_query.split('\n')
            fixed_lines = []
            in_cte_definition = False
            
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                
                # Check if we're starting a CTE definition
                if stripped_line.upper().startswith('WITH'):
                    in_cte_definition = True
                    fixed_lines.append(line)
                elif in_cte_definition and stripped_line.upper().startswith('SELECT'):
                    # This should be part of a CTE definition
                    # Check if the previous line has proper CTE syntax
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        # If previous line doesn't end with 'AS (' or ',' then we might need to fix it
                        if not (prev_line.endswith('AS (') or prev_line.endswith(',')):
                            # Add proper CTE syntax if missing
                            pass
                    fixed_lines.append(line)
                elif stripped_line.upper() == 'AS (':
                    # Proper CTE syntax
                    in_cte_definition = False
                    fixed_lines.append(line)
                elif stripped_line.endswith(')') and in_cte_definition:
                    # End of CTE definition
                    in_cte_definition = False
                    fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            
            sql_query = '\n'.join(fixed_lines)
        
        # Check if query is incomplete (missing closing parentheses)
        open_parens = sql_query.count('(')
        close_parens = sql_query.count(')')
        
        # Add missing closing parentheses
        if open_parens > close_parens:
            sql_query += ')' * (open_parens - close_parens)
        
        # Ensure query ends with semicolon
        if not sql_query.endswith(';'):
            sql_query += ';'
        
        return sql_query
    
    def query(self, user_question: str, max_results: int = 100) -> Dict[str, Any]:
        """
        Process a natural language query and return results.
        
        Args:
            user_question: Natural language question about the data
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing:
                - answer: Natural language response
                - sql: SQL query that was executed
                - results: Query results (list of dicts)
                - error: Error message if any
        """
        # Build prompt for Gemini
        prompt = f"""Hello! I'm your NCAAFB Database Professor, here to help you explore college football data with expertise and precision.

As a seasoned SQL professor with deep knowledge of the NCAAFB database, I'll help you understand complex queries and provide insightful answers to your questions about teams, players, rankings, and more.

Your Question: {user_question}

My Approach:
1. I'll carefully analyze your question to understand exactly what you're looking for
2. I'll craft an optimized SQL query to extract the relevant data
3. I'll explain my methodology and the insights I discover
4. I'll present the findings in a clear, professional format

Database Schema Context:
{self.schema_context}

Please generate a SQL SELECT query to answer this question. Follow these rules:
1. Use proper PostgreSQL syntax
2. Use JOINs to connect related tables when needed
3. Use appropriate WHERE clauses to filter data
4. Use LIMIT to restrict results (max {max_results} rows)
5. Return only the SQL query, optionally wrapped in ```sql code blocks

SQL Query:"""

        try:
            # Generate SQL query using Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract SQL from response
            sql_query = self._extract_sql_from_response(response_text)
            
            if not sql_query:
                return {
                    "answer": "Hello there! I'm your NCAAFB Database Professor. I couldn't generate a valid SQL query for your question. This information is not available in the database.",
                    "sql": None,
                    "results": None,
                    "error": "No SQL query found in LLM response"
                }
            
            # Validate SQL safety
            is_safe, safety_error = self._validate_sql_safety(sql_query)
            if not is_safe:
                return {
                    "answer": "I cannot process that request for security reasons.",
                    "sql": None,
                    "results": None,
                    "error": safety_error
                }
            
            # Execute SQL
            success, query_results, error = self.db.execute_query(sql_query)
            
            if not success:
                return {
                    "answer": "Hello there! I'm your NCAAFB Database Professor. I've encountered an issue while executing the query. This information is not available in the database.",
                    "sql": sql_query,
                    "results": None,
                    "error": error
                }
            
            # Generate structured response from results following the required format without markdown
            if not query_results:
                answer = f"""Hello there! I'm your NCAAFB Database Professor, and I've analyzed your question: '{user_question}'

🧠 QUERY ANALYSIS:
I've carefully crafted an SQL query to find the information you're looking for:
{sql_query}

📊 QUERY RESULTS:
Unfortunately, my search of the database didn't return any matching records.

🔍 ANALYSIS & INSIGHTS:
This could mean one of several things:
• The specific data you're looking for isn't in our current database
• The parameters of your query might be too restrictive
• The data might not exist in the database at this time

🎯 FINAL ANSWER:
I'm afraid this information is not currently available in the database. If you'd like to rephrase your question or try a different approach, I'd be happy to help!"""
            else:
                # Format results in a more user-friendly way
                results_summary = "\n"
                if query_results:
                    # Create a more descriptive summary
                    if len(query_results) == 1:
                        results_summary += "I found the following result:\n"
                    elif len(query_results) <= 10:
                        results_summary += f"I found {len(query_results)} results:\n"
                    else:
                        results_summary += f"I found {len(query_results)} results (showing first 10):\n"
                    
                    # Format rows in a more readable way
                    for i, row in enumerate(query_results[:10]):
                        if len(row) == 1:
                            # If only one column, show it directly
                            key, value = list(row.items())[0]
                            results_summary += f"  • {value}\n"
                        elif len(row) == 2 and 'team_name' in row and 'rank' in row:
                            # Special formatting for team rankings
                            results_summary += f"  {row['rank']}. {row['team_name']}\n"
                        elif len(row) == 2 and 'name' in row and 'total_players' in row:
                            # Special formatting for team player counts
                            results_summary += f"  • {row['name']}: {row['total_players']} players\n"
                        else:
                            # Generic formatting for other cases
                            results_summary += f"  Result {i+1}:\n"
                            for key, value in row.items():
                                results_summary += f"    {key}: {value}\n"
                        results_summary += "\n"
                
                # Create a more engaging final answer
                if len(query_results) == 1:
                    final_answer = "Here's the information you requested:"
                elif len(query_results) <= 5:
                    final_answer = "Here are the results I found for your query:"
                else:
                    final_answer = "I've found the information you requested. Here are the top results:"
                
                # Add specific insights based on the data
                insights = "\n"
                if all('team_name' in row and 'rank' in row for row in query_results[:3]):
                    # Ranking data
                    insights += "These are the current top-ranked teams in the database.\n"
                elif all('name' in row and 'total_players' in row for row in query_results[:3]):
                    # Team player count data
                    insights += "These teams and their respective player counts are shown above.\n"
                else:
                    insights += f"The query successfully returned {len(query_results)} results from the database.\n"
                
                answer = f"""Hello there! I'm your NCAAFB Database Professor, and I've analyzed your question: '{user_question}'

🧠 QUERY ANALYSIS:
I've carefully crafted an SQL query to find the information you're looking for:
{sql_query}

📊 QUERY RESULTS:{results_summary}

🔍 ANALYSIS & INSIGHTS:{insights}
🎯 FINAL ANSWER:
{final_answer}"""

            return {
                "answer": answer,
                "sql": sql_query,
                "results": query_results,
                "error": None
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error in LLM query: {error_msg}")
            
            # Check for quota errors
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return {
                    "answer": "I've reached the API rate limit. Please wait a minute and try again, or consider upgrading your Gemini API plan.",
                    "sql": None,
                    "results": None,
                    "error": "API quota/rate limit exceeded. Please wait and retry."
                }
            
            return {
                "answer": "Hello there! I'm your NCAAFB Database Professor. I've encountered an issue while processing your request. This information is not available in the database.",
                "sql": None,
                "results": None,
                "error": error_msg
            }
    
    def close(self) -> None:
        """Close database connection."""
        if self.db:
            self.db.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """CLI interface for testing the LLM agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM Agent for NCAAFB Database Queries')
    parser.add_argument('--question', '-q', type=str, required=True,
                       help='Natural language question about the data')
    parser.add_argument('--model', '-m', type=str, default='gemini-2.5-flash',
                       help='Gemini model to use (default: gemini-2.5-flash, will auto-select if not available)')
    parser.add_argument('--show-sql', action='store_true',
                       help='Show the generated SQL query')
    parser.add_argument('--show-results', action='store_true',
                       help='Show raw query results')
    
    args = parser.parse_args()
    
    try:
        agent = LLMAgent(model_name=args.model)
        
        print("\n" + "=" * 60)
        print("LLM Agent - NCAAFB Database Query")
        print("=" * 60)
        print(f"\nQuestion: {args.question}\n")
        
        result = agent.query(args.question)
        
        print("\n" + "-" * 60)
        print("Answer:")
        print("-" * 60)
        print(result['answer'])
        
        if args.show_sql and result['sql']:
            print("\n" + "-" * 60)
            print("Generated SQL:")
            print("-" * 60)
            print(result['sql'])
        
        if args.show_results and result['results']:
            print("\n" + "-" * 60)
            print(f"Query Results ({len(result['results'])} rows):")
            print("-" * 60)
            for i, row in enumerate(result['results'][:10], 1):
                print(f"\nRow {i}:")
                for key, value in row.items():
                    print(f"  {key}: {value}")
            if len(result['results']) > 10:
                print(f"\n... and {len(result['results']) - 10} more rows")
        
        if result['error']:
            print("\n" + "-" * 60)
            print("Error:")
            print("-" * 60)
            print(result['error'])
        
        agent.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

