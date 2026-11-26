"""Prompts. FROZEN before the test set is run; change only on the development questions."""

SYSTEM = (
    "You are an expert PostgreSQL data analyst. Answer the user's business question with exactly one "
    "PostgreSQL SELECT query. Return only the SQL, with no explanation and no markdown."
)


def baseline_prompt(question: str, raw_schema: str) -> str:
    """Configuration A: question + raw table and column names only."""
    return f"Database tables and columns:\n{raw_schema}\n\nQuestion: {question}\n\nSQL:"


def schema_prompt(question: str, context: str) -> str:
    """Configurations B and C: question + selected tables with descriptions and foreign keys."""
    return f"Relevant database schema:\n{context}\n\nQuestion: {question}\n\nSQL:"


def retry_prompt(original: str, previous_sql: str, error: str) -> str:
    return (f"{original}\n\nYour previous query was:\n{previous_sql}\n\n"
            f"It failed with this error:\n{error}\n\nReturn a corrected single SELECT query.\n\nSQL:")
