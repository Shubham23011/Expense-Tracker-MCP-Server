from fastmcp import FastMCP
import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    with sqlite3.connect(DB_PATH) as c:

        # Expenses
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

        # Money/credits added to account
        c.execute("""
            CREATE TABLE IF NOT EXISTS credits(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                source TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)


init_db()


# ============================================================
# CATEGORY HELPERS
# ============================================================

def load_categories():
    """Load categories and subcategories from categories.json."""

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_category(category, subcategory=""):
    """
    Validate category and subcategory against categories.json.

    Returns None if valid, otherwise returns an error message.
    """

    categories = load_categories()

    if category not in categories:
        return (
            f"Invalid category '{category}'. "
            f"Available categories: {', '.join(categories.keys())}"
        )

    if subcategory:
        if subcategory not in categories[category]:
            return (
                f"Invalid subcategory '{subcategory}' for category "
                f"'{category}'. Available subcategories: "
                f"{', '.join(categories[category])}"
            )

    return None


# ============================================================
# ADD EXPENSE
# ============================================================

@mcp.tool()
def add_expense(
    date,
    amount,
    category,
    subcategory="",
    note=""
):
    """
    Add a new expense.

    category and subcategory must match categories.json.
    """

    # Validate category/subcategory
    error = validate_category(category, subcategory)

    if error:
        return {
            "status": "error",
            "message": error
        }

    # Validate amount
    if amount <= 0:
        return {
            "status": "error",
            "message": "Expense amount must be greater than 0"
        }

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            INSERT INTO expenses(
                date,
                amount,
                category,
                subcategory,
                note
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                date,
                amount,
                category,
                subcategory,
                note
            )
        )

        return {
            "status": "ok",
            "id": cur.lastrowid,
            "message": "Expense added successfully"
        }


# ============================================================
# EDIT EXPENSE
# ============================================================

@mcp.tool()
def edit_expense(
    expense_id,
    date=None,
    amount=None,
    category=None,
    subcategory=None,
    note=None
):
    """
    Edit an existing expense.

    Only supplied fields are changed.
    """

    with sqlite3.connect(DB_PATH) as c:

        # Find existing expense
        cur = c.execute(
            """
            SELECT
                date,
                amount,
                category,
                subcategory,
                note
            FROM expenses
            WHERE id = ?
            """,
            (expense_id,)
        )

        existing = cur.fetchone()

        if existing is None:
            return {
                "status": "error",
                "message": f"Expense with ID {expense_id} not found"
            }

        (
            old_date,
            old_amount,
            old_category,
            old_subcategory,
            old_note
        ) = existing

        # Use existing values when fields aren't supplied
        date = old_date if date is None else date
        amount = old_amount if amount is None else amount
        category = old_category if category is None else category
        subcategory = (
            old_subcategory
            if subcategory is None
            else subcategory
        )
        note = old_note if note is None else note

        # Validate amount
        if amount <= 0:
            return {
                "status": "error",
                "message": "Expense amount must be greater than 0"
            }

        # Validate category/subcategory
        error = validate_category(
            category,
            subcategory
        )

        if error:
            return {
                "status": "error",
                "message": error
            }

        # Update
        c.execute(
            """
            UPDATE expenses
            SET
                date = ?,
                amount = ?,
                category = ?,
                subcategory = ?,
                note = ?
            WHERE id = ?
            """,
            (
                date,
                amount,
                category,
                subcategory,
                note,
                expense_id
            )
        )

        return {
            "status": "ok",
            "id": expense_id,
            "message": "Expense updated successfully"
        }


# ============================================================
# DELETE EXPENSE
# ============================================================

@mcp.tool()
def delete_expense(expense_id):
    """Delete an expense by ID."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            "SELECT id FROM expenses WHERE id = ?",
            (expense_id,)
        )

        if cur.fetchone() is None:
            return {
                "status": "error",
                "message": f"Expense with ID {expense_id} not found"
            }

        c.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )

        return {
            "status": "ok",
            "id": expense_id,
            "message": "Expense deleted successfully"
        }


# ============================================================
# LIST EXPENSES
# ============================================================

@mcp.tool()
def list_expenses(start_date, end_date):
    """List expenses within an inclusive date range."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            SELECT
                id,
                date,
                amount,
                category,
                subcategory,
                note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
            """,
            (
                start_date,
                end_date
            )
        )

        cols = [d[0] for d in cur.description]

        return [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]


# ============================================================
# SUMMARIZE EXPENSES
# ============================================================

@mcp.tool()
def summarize(
    start_date,
    end_date,
    category=None
):
    """Summarize expenses by category."""

    with sqlite3.connect(DB_PATH) as c:

        query = """
            SELECT
                category,
                SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """

        params = [
            start_date,
            end_date
        ]

        if category:

            # Validate category
            categories = load_categories()

            if category not in categories:
                return {
                    "status": "error",
                    "message": (
                        f"Invalid category '{category}'. "
                        f"Available categories: "
                        f"{', '.join(categories.keys())}"
                    )
                }

            query += " AND category = ?"
            params.append(category)

        query += """
            GROUP BY category
            ORDER BY category ASC
        """

        cur = c.execute(
            query,
            params
        )

        cols = [
            d[0]
            for d in cur.description
        ]

        return [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]


# ============================================================
# ADD CREDIT
# ============================================================

@mcp.tool()
def add_credit(
    date,
    amount,
    source="",
    note=""
):
    """
    Add money/credit to the account.

    Examples:
    - Salary
    - Freelance income
    - Refund
    - Cash deposit
    - Bank transfer
    - Interest
    """

    if amount <= 0:
        return {
            "status": "error",
            "message": "Credit amount must be greater than 0"
        }

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            INSERT INTO credits(
                date,
                amount,
                source,
                note
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                date,
                amount,
                source,
                note
            )
        )

        return {
            "status": "ok",
            "id": cur.lastrowid,
            "message": "Credit added successfully"
        }


# ============================================================
# LIST CREDITS
# ============================================================

@mcp.tool()
def list_credits(start_date, end_date):
    """List credits within an inclusive date range."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            SELECT
                id,
                date,
                amount,
                source,
                note
            FROM credits
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
            """,
            (
                start_date,
                end_date
            )
        )

        cols = [
            d[0]
            for d in cur.description
        ]

        return [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]


# ============================================================
# DELETE CREDIT
# ============================================================

@mcp.tool()
def delete_credit(credit_id):
    """Delete a credit by ID."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            "SELECT id FROM credits WHERE id = ?",
            (credit_id,)
        )

        if cur.fetchone() is None:
            return {
                "status": "error",
                "message": f"Credit with ID {credit_id} not found"
            }

        c.execute(
            "DELETE FROM credits WHERE id = ?",
            (credit_id,)
        )

        return {
            "status": "ok",
            "id": credit_id,
            "message": "Credit deleted successfully"
        }


# ============================================================
# ACCOUNT SUMMARY
# ============================================================

@mcp.tool()
def account_summary(
    start_date,
    end_date
):
    """
    Show total credits, total expenses and
    net balance for a date range.
    """

    with sqlite3.connect(DB_PATH) as c:

        # Credits
        cur = c.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM credits
            WHERE date BETWEEN ? AND ?
            """,
            (
                start_date,
                end_date
            )
        )

        total_credits = cur.fetchone()[0]

        # Expenses
        cur = c.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """,
            (
                start_date,
                end_date
            )
        )

        total_expenses = cur.fetchone()[0]

        net_balance = (
            total_credits -
            total_expenses
        )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_credits": total_credits,
            "total_expenses": total_expenses,
            "net_balance": net_balance
        }


# ============================================================
# CATEGORIES RESOURCE
# ============================================================

@mcp.resource(
    "expense://categories",
    mime_type="application/json"
)
def categories():
    """
    Return the current categories.json contents.

    The file is read fresh on every request,
    so category changes don't require a server restart.
    """

    with open(
        CATEGORIES_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


# ============================================================
# RUN MCP SERVER
# ============================================================

if __name__ == "__main__":
    mcp.run()