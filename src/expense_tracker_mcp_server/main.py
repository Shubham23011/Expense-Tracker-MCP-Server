# # # from fastmcp import FastMCP
# # # import os
# # # import json
# # # import sqlite3
# # # import tempfile
# # # import aiosqlite


# # # # ============================================================
# # # # PATH CONFIGURATION
# # # # ============================================================

# # # # Use a writable temporary directory for the SQLite database.
# # # TEMP_DIR = tempfile.gettempdir()

# # # DB_PATH = os.path.join(
# # #     TEMP_DIR,
# # #     "expenses.db"
# # # )

# # # CATEGORIES_PATH = os.path.join(
# # #     os.path.dirname(__file__),
# # #     "categories.json"
# # # )

# # # print(f"Database path: {DB_PATH}")
# # # print(f"Categories path: {CATEGORIES_PATH}")


# # # # ============================================================
# # # # FASTMCP SERVER
# # # # ============================================================

# # # mcp = FastMCP("ExpenseTracker")


# # # # ============================================================
# # # # DATABASE INITIALIZATION
# # # # ============================================================

# # # def init_db():
# # #     """
# # #     Initialize the SQLite database synchronously.

# # #     This runs only when the server starts.
# # #     Runtime database operations use aiosqlite asynchronously.
# # #     """

# # #     try:
# # #         with sqlite3.connect(DB_PATH) as c:

# # #             # Enable WAL mode for better concurrent read/write behavior.
# # #             c.execute("PRAGMA journal_mode=WAL")

# # #             # Expenses table
# # #             c.execute("""
# # #                 CREATE TABLE IF NOT EXISTS expenses(
# # #                     id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #                     date TEXT NOT NULL,
# # #                     amount REAL NOT NULL,
# # #                     category TEXT NOT NULL,
# # #                     subcategory TEXT DEFAULT '',
# # #                     note TEXT DEFAULT ''
# # #                 )
# # #             """)

# # #             # Credits / money added to account
# # #             c.execute("""
# # #                 CREATE TABLE IF NOT EXISTS credits(
# # #                     id INTEGER PRIMARY KEY AUTOINCREMENT,
# # #                     date TEXT NOT NULL,
# # #                     amount REAL NOT NULL,
# # #                     source TEXT DEFAULT '',
# # #                     note TEXT DEFAULT ''
# # #                 )
# # #             """)

# # #             c.commit()

# # #         print("Database initialized successfully.")
# # #         print(f"Database location: {DB_PATH}")

# # #     except Exception as e:
# # #         print(f"Database initialization error: {e}")
# # #         raise


# # # # Initialize database when server starts
# # # init_db()


# # # # ============================================================
# # # # CATEGORY HELPERS
# # # # ============================================================

# # # def load_categories():
# # #     """
# # #     Load categories and subcategories from categories.json.
# # #     """

# # #     with open(
# # #         CATEGORIES_PATH,
# # #         "r",
# # #         encoding="utf-8"
# # #     ) as f:
# # #         return json.load(f)


# # # def validate_category(category, subcategory=""):
# # #     """
# # #     Validate category and subcategory against categories.json.

# # #     Returns:
# # #         None if valid
# # #         Error message string if invalid
# # #     """

# # #     try:
# # #         categories = load_categories()

# # #     except FileNotFoundError:
# # #         return "categories.json file was not found."

# # #     except json.JSONDecodeError:
# # #         return "categories.json contains invalid JSON."

# # #     except Exception as e:
# # #         return f"Could not load categories: {str(e)}"

# # #     # Validate category
# # #     if category not in categories:
# # #         return (
# # #             f"Invalid category '{category}'. "
# # #             f"Available categories: "
# # #             f"{', '.join(categories.keys())}"
# # #         )

# # #     # Validate subcategory if supplied
# # #     if subcategory:

# # #         if subcategory not in categories[category]:
# # #             return (
# # #                 f"Invalid subcategory '{subcategory}' "
# # #                 f"for category '{category}'. "
# # #                 f"Available subcategories: "
# # #                 f"{', '.join(categories[category])}"
# # #             )

# # #     return None


# # # # ============================================================
# # # # ADD EXPENSE
# # # # ============================================================

# # # @mcp.tool()
# # # async def add_expense(
# # #     date,
# # #     amount,
# # #     category,
# # #     subcategory="",
# # #     note=""
# # # ):
# # #     """
# # #     Add a new expense entry.

# # #     category and subcategory are validated
# # #     against categories.json.
# # #     """

# # #     try:

# # #         # Validate category/subcategory
# # #         error = validate_category(
# # #             category,
# # #             subcategory
# # #         )

# # #         if error:
# # #             return {
# # #                 "status": "error",
# # #                 "message": error
# # #             }

# # #         # Validate amount
# # #         if amount <= 0:
# # #             return {
# # #                 "status": "error",
# # #                 "message": "Expense amount must be greater than 0"
# # #             }

# # #         async with aiosqlite.connect(DB_PATH) as c:

# # #             cur = await c.execute(
# # #                 """
# # #                 INSERT INTO expenses(
# # #                     date,
# # #                     amount,
# # #                     category,
# # #                     subcategory,
# # #                     note
# # #                 )
# # #                 VALUES (?, ?, ?, ?, ?)
# # #                 """,
# # #                 (
# # #                     date,
# # #                     amount,
# # #                     category,
# # #                     subcategory,
# # #                     note
# # #                 )
# # #             )

# # #             expense_id = cur.lastrowid

# # #             await c.commit()

# # #             return {
# # #                 "status": "success",
# # #                 "id": expense_id,
# # #                 "message": "Expense added successfully"
# # #             }

# # #     except Exception as e:

# # #         if "readonly" in str(e).lower():

# # #             return {
# # #                 "status": "error",
# # #                 "message": (
# # #                     "Database is in read-only mode. "
# # #                     "Check file permissions."
# # #                 )
# # #             }

# # #         return {
# # #             "status": "error",
# # #             "message": f"Database error: {str(e)}"
# # #         }


# # # # ============================================================
# # # # EDIT EXPENSE
# # # # ============================================================

# # # @mcp.tool()
# # # async def edit_expense(
# # #     expense_id,
# # #     date=None,
# # #     amount=None,
# # #     category=None,
# # #     subcategory=None,
# # #     note=None
# # # ):
# # #     """
# # #     Edit an existing expense.

# # #     Only fields provided by the caller are changed.
# # #     """

# # #     try:

# # #         async with aiosqlite.connect(DB_PATH) as c:

# # #             # Find existing expense
# # #             cur = await c.execute(
# # #                 """
# # #                 SELECT
# # #                     date,
# # #                     amount,
# # #                     category,
# # #                     subcategory,
# # #                     note
# # #                 FROM expenses
# # #                 WHERE id = ?
# # #                 """,
# # #                 (expense_id,)
# # #             )

# # #             existing = await cur.fetchone()

# # #             if existing is None:

# # #                 return {
# # #                     "status": "error",
# # #                     "message": (
# # #                         f"Expense with ID "
# # #                         f"{expense_id} not found"
# # #                     )
# # #                 }

# # #             (
# # #                 old_date,
# # #                 old_amount,
# # #                 old_category,
# # #                 old_subcategory,
# # #                 old_note
# # #             ) = existing

# # #             # Keep existing values if not supplied
# # #             date = (
# # #                 old_date
# # #                 if date is None
# # #                 else date
# # #             )

# # #             amount = (
# # #                 old_amount
# # #                 if amount is None
# # #                 else amount
# # #             )

# # #             category = (
# # #                 old_category
# # #                 if category is None
# # #                 else category
# # #             )

# # #             subcategory = (
# # #                 old_subcategory
# # #                 if subcategory is None
# # #                 else subcategory
# # #             )

# # #             note = (
# # #                 old_note
# # #                 if note is None
# # #                 else note
# # #             )

# # #             # Validate amount
# # #             if amount <= 0:

# # #                 return {
# # #                     "status": "error",
# # #                     "message": (
# # #                         "Expense amount must "
# # #                         "be greater than 0"
# # #                     )
# # #                 }

# # #             # Validate category/subcategory
# # #             error = validate_category(
# # #                 category,
# # #                 subcategory
# # #             )

# # #             if error:

# # #                 return {
# # #                     "status": "error",
# # #                     "message": error
# # #                 }

# # #             # Update expense
# # #             await c.execute(
# # #                 """
# # #                 UPDATE expenses
# # #                 SET
# # #                     date = ?,
# # #                     amount = ?,
# # #                     category = ?,
# # #                     subcategory = ?,
# # #                     note = ?
# # #                 WHERE id = ?
# # #                 """,
# # #                 (
# # #                     date,
# # #                     amount,
# # #                     category,
# # #                     subcategory,
# # #                     note,
# # #                     expense_id
# # #                 )
# # #             )

# # #             await c.commit()

# # #             return {
# # #                 "status": "success",
# # #                 "id": expense_id,
# # #                 "message": "Expense updated successfully"
# # #             }

# # #     except Exception as e:

# # #         return {
# # #             "status": "error",
# # #             "message": (
# # #                 f"Error updating expense: {str(e)}"
# # #             )
# # #         }


# # # # ============================================================
# # # # DELETE EXPENSE
# # # # ============================================================

# # # @mcp.tool()
# # # async def delete_expense(expense_id):
# # #     """
# # #     Delete an expense by ID.
# # #     """

# # #     try:

# # #         async with aiosqlite.connect(DB_PATH) as c:

# # #             # Check whether expense exists
# # #             cur = await c.execute(
# # #                 """
# # #                 SELECT id
# # #                 FROM expenses
# # #                 WHERE id = ?
# # #                 """,
# # #                 (expense_id,)
# # #             )

# # #             existing = await cur.fetchone()

# # #             if existing is None:

# # #                 return {
# # #                     "status": "error",
# # #                     "message": (
# # #                         f"Expense with ID "
# # #                         f"{expense_id} not found"
# # #                     )
# # #                 }

# # #             # Delete
# # #             await c.execute(
# # #                 """
# # #                 DELETE FROM expenses
# # #                 WHERE id = ?
# # #                 """,
# # #                 (expense_id,)
# # #             )

# # #             await c.commit()

# # #             return {
# # #                 "status": "success",
# # #                 "id": expense_id,
# # #                 "message": "Expense deleted successfully"
# # #             }

# # #     except Exception as e:

# # #         return {
# # #             "status": "error",
# # #             "message": (
# # #                 f"Error deleting expense: {str(e)}"
# # #             )
# # #         }


# # # # ============================================================
# # # # LIST EXPENSES
# # # # ============================================================

# # # @mcp.tool()
# # # async def list_expenses(
# # #     start_date,
# # #     end_date
# # # ):
# # #     """
# # #     List expense entries within an inclusive date range.
# # #     """

# # #     try:

# # #         async with aiosqlite.connect(DB_PATH) as c:

# # #             cur = await c.execute(
# # #                 """
# # #                 SELECT
# # #                     id,
# # #                     date,
# # #                     amount,
# # #                     category,
# # #                     subcategory,
# # #                     note
# # #                 FROM expenses
# # #                 WHERE date BETWEEN ? AND ?
# # #                 ORDER BY date DESC, id DESC
# # #                 """,
# # #                 (
# # #                     start_date,
# # #                     end_date
# # #                 )
# # #             )

# # #             rows = await cur.fetchall()

# # #             cols = [
# # #                 description[0]
# # #                 for description in cur.description
# # #             ]

# # #             return [
# # #                 dict(zip(cols, row))
# # #                 for row in rows
# # #             ]

# # #     except Exception as e:

# # #         return {
# # #             "status": "error",
# # #             "message": (
# # #                 f"Error listing expenses: {str(e)}"
# # #             )
# # #         }


# # # # ============================================================
# # # # SUMMARIZE EXPENSES
# # # # ============================================================

# # # @mcp.tool()
# # # async def summarize(
# # #     start_date,
# # #     end_date,
# # #     category=None
# # # ):
# # #     """
# # #     Summarize expenses by category within
# # #     an inclusive date range.

# # #     Returns:
# # #     - category
# # #     - total_amount
# # #     - count
# # #     """

# # #     try:

# # #         # Validate category if supplied
# # #         if category:

# # #             categories = load_categories()

# # #             if category not in categories:

# # #                 return {
# # #                     "status": "error",
# # #                     "message": (
# # #                         f"Invalid category "
# # #                         f"'{category}'. "
# # #                         f"Available categories: "
# # #                         f"{', '.join(categories.keys())}"
# # #                     )
# # #                 }

# # #         async with aiosqlite.connect(DB_PATH) as c:

# # #             query = """
# # #                 SELECT
# # #                     category,
# # #                     SUM(amount) AS total_amount,
# # #                     COUNT(*) AS count
# # #                 FROM expenses
# # #                 WHERE date BETWEEN ? AND ?
# # #             """

# # #             params = [
# # #                 start_date,
# # #                 end_date
# # #             ]

# # #             if category:

# # #                 query += """
# # #                     AND category = ?
# # #                 """

# # #                 params.append(category)

# # #             query += """
# # #                 GROUP BY category
# # #                 ORDER BY total_amount DESC
# # #             """

# # #             cur = await c.execute(
# # #                 query,
# # #                 params
# # #             )

# # #             rows = await cur.fetchall()

# # #             cols = [
# # #                 description[0]
# # #                 for description in cur.description
# # #             ]

# # #             return [
# # #                 dict(zip(cols, row))
# # #                 for row in rows
# # #             ]

# # #     except Exception as e:

# # #         return {
# # #             "status": "error",
# # #             "message": (
# # #                 f"Error summarizing expenses: {str(e)}"
# # #             )
# # #         }


# # # # ============================================================
# # # # ADD CREDIT
# # # # ============================================================

# # # @mcp.tool()
# # # async def add_credit(
# # #     date,
# # #     amount,
# # #     source="",
# # #     note=""
# # # ):
# # #     """
# # #     Add money/credit to the account.

# # #     Examples:
# # #     - Salary
# # #     - Freelance income
# # #     - Refund
# # #     - Cash deposit
# # #     - Bank transfer
# # #     - Interest
# # #     """

# # #     try:

# # #         if amount <= 0:

# # #             return {
# # #                 "status": "error",
# # #                 "message": (
# # #                     "Credit amount must "
# # #                     "be greater than 0"
# # #                 )
# # #             }

# # #         async with aiosqlite.connect(DB_PATH) as c:

# # #             cur = await c.execute(
# # #                 """
# # #                 INSERT INTO credits(
# # #                     date,
# # #                     amount,
# # #                     source,
# # #                     note
# # #                 )
# # #                 VALUES (?, ?, ?, ?)
# # #                 """,
# # #                 (
# # #                     date,
# # #                     amount,
# # #                     source,
# # #                     note
# # #                 )
# # #             )

# # #             credit_id = cur.lastrowid

# # #             await c.commit()

# # #             return {
# # #                 "status": "success",
# # #                 "id": credit_id,
# # #                 "message": "Credit added successfully"
# # #             }

# # #     except Exception as e:

# # #         return {
# # #             "status": "error",
# # #             "message": (
# # #                 f"Database error: {str(e)}"
# # #             )
# # #         }


# # # # ============================================================
# # # # LIST CREDITS
# # # # ============================================================

# # # @mcp.tool()
# # # async def list_credits(
# # #     start_date,
# # #     end_date
# # # ):
# # #     """
# # #     List credits within an inclusive date range.
# # #     """

# # #     try:

# # #         async with aiosqlite.connect(DB_PATH) as c:

# # #             cur = await c.execute(
# # #                 """
# # #                 SELECT
# # #                     id,
# # #                     date,
# # #                     amount,
# # #                     source,
# # #                     note
# # #                 FROM credits
# # #                 WHERE date BETWEEN ? AND ?
# # #                 ORDER BY date DESC, id DESC
# # #                 """,
# # #                 (
# # #                     start_date,
# # #                     end_date
# # #                 )
# # #             )

# # #             rows = await cur.fetchall()

# # #             cols = [
# # #                 description[0]
# # #                 for description in cur.description
# # #             ]

# # #             return [
# # #                 dict(zip(cols, row))
# # #                 for row in rows
# # #             ]

# # #     except Exception as e:

# # #         return {
# # #             "status": "error",
# # #             "message": (
# # #                 f"Error listing credits: {str(e)}"
# # #             )
# # #         }


# # # # ============================================================
# # # # DELETE CREDIT
# # # # ============================================================

# # # @mcp.tool()
# # # async def delete_credit(credit_id):
# # #     """
# # #     Delete a credit by ID.
# # #     """

# # #     try:

# # #         async with aiosqlite.connect(DB_PATH) as c:

# # #             # Check whether credit exists
# # #             cur = await c.execute(
# # #                 """
# # #                 SELECT id
# # #                 FROM credits
# # #                 WHERE id = ?
# # #                 """,
# # #                 (credit_id,)
# # #             )

# # #             existing = await cur.fetchone()

# # #             if existing is None:

# # #                 return {
# # #                     "status": "error",
# # #                     "message": (
# # #                         f"Credit with ID "
# # #                         f"{credit_id} not found"
# # #                     )
# # #                 }

# # #             # Delete credit
# # #             await c.execute(
# # #                 """
# # #                 DELETE FROM credits
# # #                 WHERE id = ?
# # #                 """,
# # #                 (credit_id,)
# # #             )

# # #             await c.commit()

# # #             return {
# # #                 "status": "success",
# # #                 "id": credit_id,
# # #                 "message": "Credit deleted successfully"
# # #             }

# # #     except Exception as e:

# # #         return {
# # #             "status": "error",
# # #             "message": (
# # #                 f"Error deleting credit: {str(e)}"
# # #             )
# # #         }


# # # # ============================================================
# # # # ACCOUNT SUMMARY
# # # # ============================================================

# # # @mcp.tool()
# # # async def account_summary(
# # #     start_date,
# # #     end_date
# # # ):
# # #     """
# # #     Show total credits, total expenses
# # #     and net balance for a date range.

# # #     net_balance = total_credits - total_expenses
# # #     """

# # #     try:

# # #         async with aiosqlite.connect(DB_PATH) as c:

# # #             # --------------------------------------------
# # #             # Total credits
# # #             # --------------------------------------------

# # #             cur = await c.execute(
# # #                 """
# # #                 SELECT COALESCE(SUM(amount), 0)
# # #                 FROM credits
# # #                 WHERE date BETWEEN ? AND ?
# # #                 """,
# # #                 (
# # #                     start_date,
# # #                     end_date
# # #                 )
# # #             )

# # #             credit_result = await cur.fetchone()

# # #             total_credits = credit_result[0]


# # #             # --------------------------------------------
# # #             # Total expenses
# # #             # --------------------------------------------

# # #             cur = await c.execute(
# # #                 """
# # #                 SELECT COALESCE(SUM(amount), 0)
# # #                 FROM expenses
# # #                 WHERE date BETWEEN ? AND ?
# # #                 """,
# # #                 (
# # #                     start_date,
# # #                     end_date
# # #                 )
# # #             )

# # #             expense_result = await cur.fetchone()

# # #             total_expenses = expense_result[0]


# # #             # --------------------------------------------
# # #             # Calculate balance
# # #             # --------------------------------------------

# # #             net_balance = (
# # #                 total_credits -
# # #                 total_expenses
# # #             )


# # #             return {
# # #                 "status": "success",
# # #                 "start_date": start_date,
# # #                 "end_date": end_date,
# # #                 "total_credits": total_credits,
# # #                 "total_expenses": total_expenses,
# # #                 "net_balance": net_balance
# # #             }

# # #     except Exception as e:

# # #         return {
# # #             "status": "error",
# # #             "message": (
# # #                 f"Error generating account summary: "
# # #                 f"{str(e)}"
# # #             )
# # #         }


# # # # ============================================================
# # # # CATEGORIES RESOURCE
# # # # ============================================================

# # # @mcp.resource(
# # #     "expense:///categories",
# # #     mime_type="application/json"
# # # )
# # # def categories():
# # #     """
# # #     Return categories.json.

# # #     The file is read every time the resource
# # #     is requested, so category changes do not
# # #     require a server restart.
# # #     """

# # #     try:

# # #         with open(
# # #             CATEGORIES_PATH,
# # #             "r",
# # #             encoding="utf-8"
# # #         ) as f:

# # #             return f.read()

# # #     except FileNotFoundError:

# # #         return json.dumps(
# # #             {
# # #                 "error": (
# # #                     "categories.json "
# # #                     "file not found"
# # #                 )
# # #             },
# # #             indent=2
# # #         )

# # #     except json.JSONDecodeError:

# # #         return json.dumps(
# # #             {
# # #                 "error": (
# # #                     "categories.json "
# # #                     "contains invalid JSON"
# # #                 )
# # #             },
# # #             indent=2
# # #         )

# # #     except Exception as e:

# # #         return json.dumps(
# # #             {
# # #                 "error": (
# # #                     f"Could not load categories: "
# # #                     f"{str(e)}"
# # #                 )
# # #             },
# # #             indent=2
# # #         )


# # # # ============================================================
# # # # START SERVER
# # # # ============================================================

# # # if __name__ == "__main__":

# # #     print("Starting ExpenseTracker MCP server...")
# # #     print("Transport: HTTP")
# # #     print("Host: 0.0.0.0")
# # #     print("Port: 8080")

# # #     mcp.run(
# # #         transport="http",
# # #         host="0.0.0.0",
# # #         port=8080
# # #     )



# # from fastmcp import FastMCP
# # import os
# # import json
# # import sqlite3
# # import tempfile
# # import aiosqlite

# # # Turso / LibSQL client for persistent remote cloud storage
# # try:
# #     import libsql_client
# # except ImportError:
# #     libsql_client = None


# # # ============================================================
# # # PATH & DATABASE CONFIGURATION
# # # ============================================================

# # TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
# # TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
# # USE_TURSO = bool(TURSO_URL and TURSO_TOKEN and libsql_client)

# # # Fallback local SQLite path
# # TEMP_DIR = tempfile.gettempdir()
# # DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

# # CATEGORIES_PATH = os.path.join(
# #     os.path.dirname(__file__),
# #     "categories.json"
# # )

# # if USE_TURSO:
# #     print(f"Using remote Turso Database: {TURSO_URL}")
# # else:
# #     print(f"Using local SQLite database: {DB_PATH}")
# # print(f"Categories path: {CATEGORIES_PATH}")


# # # ============================================================
# # # DATABASE CLIENT & HELPERS
# # # ============================================================

# # def get_turso_client():
# #     # libsql_client expects an https:// URL scheme when communicating over HTTP
# #     url = TURSO_URL.replace("libsql://", "https://")
# #     return libsql_client.create_client(url=url, auth_token=TURSO_TOKEN)


# # # ============================================================
# # # FASTMCP SERVER
# # # ============================================================

# # mcp = FastMCP("ExpenseTracker")


# # # ============================================================
# # # DATABASE INITIALIZATION
# # # ============================================================

# # def init_db():
# #     """
# #     Initialize the database tables.
# #     Runs once on startup.
# #     """
# #     create_expenses_sql = """
# #         CREATE TABLE IF NOT EXISTS expenses(
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             date TEXT NOT NULL,
# #             amount REAL NOT NULL,
# #             category TEXT NOT NULL,
# #             subcategory TEXT DEFAULT '',
# #             note TEXT DEFAULT ''
# #         )
# #     """

# #     create_credits_sql = """
# #         CREATE TABLE IF NOT EXISTS credits(
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             date TEXT NOT NULL,
# #             amount REAL NOT NULL,
# #             source TEXT DEFAULT '',
# #             note TEXT DEFAULT ''
# #         )
# #     """

# #     try:
# #         if USE_TURSO:
# #             with get_turso_client() as client:
# #                 client.execute(create_expenses_sql)
# #                 client.execute(create_credits_sql)
# #             print("Remote Turso database schema verified successfully.")
# #         else:
# #             with sqlite3.connect(DB_PATH) as c:
# #                 c.execute("PRAGMA journal_mode=WAL")
# #                 c.execute(create_expenses_sql)
# #                 c.execute(create_credits_sql)
# #                 c.commit()
# #             print("Local SQLite database initialized successfully.")
# #     except Exception as e:
# #         print(f"Database initialization error: {e}")
# #         raise


# # init_db()


# # # ============================================================
# # # CATEGORY HELPERS
# # # ============================================================

# # def load_categories():
# #     with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
# #         return json.load(f)


# # def validate_category(category, subcategory=""):
# #     try:
# #         categories = load_categories()
# #     except FileNotFoundError:
# #         return "categories.json file was not found."
# #     except json.JSONDecodeError:
# #         return "categories.json contains invalid JSON."
# #     except Exception as e:
# #         return f"Could not load categories: {str(e)}"

# #     if category not in categories:
# #         return (
# #             f"Invalid category '{category}'. "
# #             f"Available categories: {', '.join(categories.keys())}"
# #         )

# #     if subcategory and subcategory not in categories[category]:
# #         return (
# #             f"Invalid subcategory '{subcategory}' for category '{category}'. "
# #             f"Available subcategories: {', '.join(categories[category])}"
# #         )

# #     return None


# # # ============================================================
# # # ADD EXPENSE
# # # ============================================================

# # @mcp.tool()
# # async def add_expense(
# #     date: str,
# #     amount: float,
# #     category: str,
# #     subcategory: str = "",
# #     note: str = ""
# # ):
# #     """
# #     Add a new expense entry.
# #     """
# #     try:
# #         error = validate_category(category, subcategory)
# #         if error:
# #             return {"status": "error", "message": error}

# #         if amount <= 0:
# #             return {"status": "error", "message": "Expense amount must be greater than 0"}

# #         if USE_TURSO:
# #             async with get_turso_client() as client:
# #                 rs = await client.execute(
# #                     "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
# #                     [date, amount, category, subcategory, note]
# #                 )
# #                 expense_id = rs.last_insert_rowid
# #         else:
# #             async with aiosqlite.connect(DB_PATH) as c:
# #                 cur = await c.execute(
# #                     "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
# #                     (date, amount, category, subcategory, note)
# #                 )
# #                 expense_id = cur.lastrowid
# #                 await c.commit()

# #         return {
# #             "status": "success",
# #             "id": expense_id,
# #             "message": "Expense added successfully"
# #         }

# #     except Exception as e:
# #         return {"status": "error", "message": f"Database error: {str(e)}"}


# # # ============================================================
# # # EDIT EXPENSE
# # # ============================================================

# # @mcp.tool()
# # async def edit_expense(
# #     expense_id: int,
# #     date: str = None,
# #     amount: float = None,
# #     category: str = None,
# #     subcategory: str = None,
# #     note: str = None
# # ):
# #     """
# #     Edit an existing expense. Only fields provided are updated.
# #     """
# #     try:
# #         if USE_TURSO:
# #             async with get_turso_client() as client:
# #                 rs = await client.execute(
# #                     "SELECT date, amount, category, subcategory, note FROM expenses WHERE id = ?",
# #                     [expense_id]
# #                 )
# #                 if not rs.rows:
# #                     return {"status": "error", "message": f"Expense with ID {expense_id} not found"}
# #                 row = rs.rows[0]
# #                 old_date, old_amount, old_category, old_subcategory, old_note = (
# #                     row[0], row[1], row[2], row[3], row[4]
# #                 )

# #                 date = old_date if date is None else date
# #                 amount = old_amount if amount is None else amount
# #                 category = old_category if category is None else category
# #                 subcategory = old_subcategory if subcategory is None else subcategory
# #                 note = old_note if note is None else note

# #                 if amount <= 0:
# #                     return {"status": "error", "message": "Expense amount must be greater than 0"}

# #                 error = validate_category(category, subcategory)
# #                 if error:
# #                     return {"status": "error", "message": error}

# #                 await client.execute(
# #                     """
# #                     UPDATE expenses
# #                     SET date = ?, amount = ?, category = ?, subcategory = ?, note = ?
# #                     WHERE id = ?
# #                     """,
# #                     [date, amount, category, subcategory, note, expense_id]
# #                 )
# #         else:
# #             async with aiosqlite.connect(DB_PATH) as c:
# #                 cur = await c.execute(
# #                     "SELECT date, amount, category, subcategory, note FROM expenses WHERE id = ?",
# #                     (expense_id,)
# #                 )
# #                 existing = await cur.fetchone()
# #                 if existing is None:
# #                     return {"status": "error", "message": f"Expense with ID {expense_id} not found"}

# #                 old_date, old_amount, old_category, old_subcategory, old_note = existing
# #                 date = old_date if date is None else date
# #                 amount = old_amount if amount is None else amount
# #                 category = old_category if category is None else category
# #                 subcategory = old_subcategory if subcategory is None else subcategory
# #                 note = old_note if note is None else note

# #                 if amount <= 0:
# #                     return {"status": "error", "message": "Expense amount must be greater than 0"}

# #                 error = validate_category(category, subcategory)
# #                 if error:
# #                     return {"status": "error", "message": error}

# #                 await c.execute(
# #                     """
# #                     UPDATE expenses
# #                     SET date = ?, amount = ?, category = ?, subcategory = ?, note = ?
# #                     WHERE id = ?
# #                     """,
# #                     (date, amount, category, subcategory, note, expense_id)
# #                 )
# #                 await c.commit()

# #         return {
# #             "status": "success",
# #             "id": expense_id,
# #             "message": "Expense updated successfully"
# #         }

# #     except Exception as e:
# #         return {"status": "error", "message": f"Error updating expense: {str(e)}"}


# # # ============================================================
# # # DELETE EXPENSE
# # # ============================================================

# # @mcp.tool()
# # async def delete_expense(expense_id: int):
# #     """
# #     Delete an expense by ID.
# #     """
# #     try:
# #         if USE_TURSO:
# #             async with get_turso_client() as client:
# #                 rs = await client.execute("SELECT id FROM expenses WHERE id = ?", [expense_id])
# #                 if not rs.rows:
# #                     return {"status": "error", "message": f"Expense with ID {expense_id} not found"}
# #                 await client.execute("DELETE FROM expenses WHERE id = ?", [expense_id])
# #         else:
# #             async with aiosqlite.connect(DB_PATH) as c:
# #                 cur = await c.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,))
# #                 if await cur.fetchone() is None:
# #                     return {"status": "error", "message": f"Expense with ID {expense_id} not found"}
# #                 await c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
# #                 await c.commit()

# #         return {
# #             "status": "success",
# #             "id": expense_id,
# #             "message": "Expense deleted successfully"
# #         }

# #     except Exception as e:
# #         return {"status": "error", "message": f"Error deleting expense: {str(e)}"}


# # # ============================================================
# # # LIST EXPENSES
# # # ============================================================

# # @mcp.tool()
# # async def list_expenses(start_date: str, end_date: str):
# #     """
# #     List expense entries within an inclusive date range.
# #     """
# #     try:
# #         if USE_TURSO:
# #             async with get_turso_client() as client:
# #                 rs = await client.execute(
# #                     """
# #                     SELECT id, date, amount, category, subcategory, note
# #                     FROM expenses
# #                     WHERE date BETWEEN ? AND ?
# #                     ORDER BY date DESC, id DESC
# #                     """,
# #                     [start_date, end_date]
# #                 )
# #                 cols = ["id", "date", "amount", "category", "subcategory", "note"]
# #                 return [dict(zip(cols, row)) for row in rs.rows]
# #         else:
# #             async with aiosqlite.connect(DB_PATH) as c:
# #                 cur = await c.execute(
# #                     """
# #                     SELECT id, date, amount, category, subcategory, note
# #                     FROM expenses
# #                     WHERE date BETWEEN ? AND ?
# #                     ORDER BY date DESC, id DESC
# #                     """,
# #                     (start_date, end_date)
# #                 )
# #                 rows = await cur.fetchall()
# #                 cols = [desc[0] for desc in cur.description]
# #                 return [dict(zip(cols, row)) for row in rows]

# #     except Exception as e:
# #         return {"status": "error", "message": f"Error listing expenses: {str(e)}"}


# # # ============================================================
# # # SUMMARIZE EXPENSES
# # # ============================================================

# # @mcp.tool()
# # async def summarize(start_date: str, end_date: str, category: str = None):
# #     """
# #     Summarize expenses by category within an inclusive date range.
# #     """
# #     try:
# #         if category:
# #             categories = load_categories()
# #             if category not in categories:
# #                 return {
# #                     "status": "error",
# #                     "message": f"Invalid category '{category}'. Available categories: {', '.join(categories.keys())}"
# #                 }

# #         query = """
# #             SELECT category, SUM(amount) AS total_amount, COUNT(*) AS count
# #             FROM expenses
# #             WHERE date BETWEEN ? AND ?
# #         """
# #         params = [start_date, end_date]

# #         if category:
# #             query += " AND category = ? "
# #             params.append(category)

# #         query += " GROUP BY category ORDER BY total_amount DESC "

# #         if USE_TURSO:
# #             async with get_turso_client() as client:
# #                 rs = await client.execute(query, params)
# #                 cols = ["category", "total_amount", "count"]
# #                 return [dict(zip(cols, row)) for row in rs.rows]
# #         else:
# #             async with aiosqlite.connect(DB_PATH) as c:
# #                 cur = await c.execute(query, tuple(params))
# #                 rows = await cur.fetchall()
# #                 cols = [desc[0] for desc in cur.description]
# #                 return [dict(zip(cols, row)) for row in rows]

# #     except Exception as e:
# #         return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}


# # # ============================================================
# # # ADD CREDIT
# # # ============================================================

# # @mcp.tool()
# # async def add_credit(
# #     date: str,
# #     amount: float,
# #     source: str = "",
# #     note: str = ""
# # ):
# #     """
# #     Add money/credit to the account.
# #     """
# #     try:
# #         if amount <= 0:
# #             return {"status": "error", "message": "Credit amount must be greater than 0"}

# #         if USE_TURSO:
# #             async with get_turso_client() as client:
# #                 rs = await client.execute(
# #                     "INSERT INTO credits(date, amount, source, note) VALUES (?, ?, ?, ?)",
# #                     [date, amount, source, note]
# #                 )
# #                 credit_id = rs.last_insert_rowid
# #         else:
# #             async with aiosqlite.connect(DB_PATH) as c:
# #                 cur = await c.execute(
# #                     "INSERT INTO credits(date, amount, source, note) VALUES (?, ?, ?, ?)",
# #                     (date, amount, source, note)
# #                 )
# #                 credit_id = cur.lastrowid
# #                 await c.commit()

# #         return {
# #             "status": "success",
# #             "id": credit_id,
# #             "message": "Credit added successfully"
# #         }

# #     except Exception as e:
# #         return {"status": "error", "message": f"Database error: {str(e)}"}


# # # ============================================================
# # # LIST CREDITS
# # # ============================================================

# # @mcp.tool()
# # async def list_credits(start_date: str, end_date: str):
# #     """
# #     List credits within an inclusive date range.
# #     """
# #     try:
# #         query = """
# #             SELECT id, date, amount, source, note
# #             FROM credits
# #             WHERE date BETWEEN ? AND ?
# #             ORDER BY date DESC, id DESC
# #         """
# #         if USE_TURSO:
# #             async with get_turso_client() as client:
# #                 rs = await client.execute(query, [start_date, end_date])
# #                 cols = ["id", "date", "amount", "source", "note"]
# #                 return [dict(zip(cols, row)) for row in rs.rows]
# #         else:
# #             async with aiosqlite.connect(DB_PATH) as c:
# #                 cur = await c.execute(query, (start_date, end_date))
# #                 rows = await cur.fetchall()
# #                 cols = [desc[0] for desc in cur.description]
# #                 return [dict(zip(cols, row)) for row in rows]

# #     except Exception as e:
# #         return {"status": "error", "message": f"Error listing credits: {str(e)}"}


# # # ============================================================
# # # DELETE CREDIT
# # # ============================================================

# # @mcp.tool()
# # async def delete_credit(credit_id: int):
# #     """
# #     Delete a credit by ID.
# #     """
# #     try:
# #         if USE_TURSO:
# #             async with get_turso_client() as client:
# #                 rs = await client.execute("SELECT id FROM credits WHERE id = ?", [credit_id])
# #                 if not rs.rows:
# #                     return {"status": "error", "message": f"Credit with ID {credit_id} not found"}
# #                 await client.execute("DELETE FROM credits WHERE id = ?", [credit_id])
# #         else:
# #             async with aiosqlite.connect(DB_PATH) as c:
# #                 cur = await c.execute("SELECT id FROM credits WHERE id = ?", (credit_id,))
# #                 if await cur.fetchone() is None:
# #                     return {"status": "error", "message": f"Credit with ID {credit_id} not found"}
# #                 await c.execute("DELETE FROM credits WHERE id = ?", (credit_id,))
# #                 await c.commit()

# #         return {
# #             "status": "success",
# #             "id": credit_id,
# #             "message": "Credit deleted successfully"
# #         }

# #     except Exception as e:
# #         return {"status": "error", "message": f"Error deleting credit: {str(e)}"}


# # # ============================================================
# # # ACCOUNT SUMMARY
# # # ============================================================

# # @mcp.tool()
# # async def account_summary(start_date: str, end_date: str):
# #     """
# #     Show total credits, total expenses, and net balance for a date range.
# #     """
# #     try:
# #         credit_query = "SELECT COALESCE(SUM(amount), 0) FROM credits WHERE date BETWEEN ? AND ?"
# #         expense_query = "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date BETWEEN ? AND ?"

# #         if USE_TURSO:
# #             async with get_turso_client() as client:
# #                 rs_credits = await client.execute(credit_query, [start_date, end_date])
# #                 rs_expenses = await client.execute(expense_query, [start_date, end_date])
# #                 total_credits = rs_credits.rows[0][0] or 0.0
# #                 total_expenses = rs_expenses.rows[0][0] or 0.0
# #         else:
# #             async with aiosqlite.connect(DB_PATH) as c:
# #                 cur = await c.execute(credit_query, (start_date, end_date))
# #                 total_credits = (await cur.fetchone())[0] or 0.0

# #                 cur = await c.execute(expense_query, (start_date, end_date))
# #                 total_expenses = (await cur.fetchone())[0] or 0.0

# #         net_balance = total_credits - total_expenses

# #         return {
# #             "status": "success",
# #             "start_date": start_date,
# #             "end_date": end_date,
# #             "total_credits": total_credits,
# #             "total_expenses": total_expenses,
# #             "net_balance": net_balance
# #         }

# #     except Exception as e:
# #         return {"status": "error", "message": f"Error generating account summary: {str(e)}"}


# # # ============================================================
# # # CATEGORIES RESOURCE
# # # ============================================================

# # @mcp.resource("expense:///categories", mime_type="application/json")
# # def categories():
# #     """
# #     Return categories.json.
# #     """
# #     try:
# #         with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
# #             return f.read()
# #     except Exception as e:
# #         return json.dumps({"error": f"Could not load categories: {str(e)}"}, indent=2)


# # # ============================================================
# # # START SERVER
# # # ============================================================

# # if __name__ == "__main__":
# #     print("Starting ExpenseTracker MCP server...")
# #     print("Transport: HTTP")
# #     print("Host: 0.0.0.0")
# #     print("Port: 8080")

# #     mcp.run(
# #         transport="http",
# #         host="0.0.0.0",
# #         port=8080
# #     )































# import json
# import os
# import sqlite3
# import tempfile
# import aiosqlite
# from fastmcp import FastMCP

# # Turso / LibSQL client for persistent remote cloud storage
# try:
#     import libsql_client
# except ImportError:
#     libsql_client = None


# # ============================================================
# # PATH & DATABASE CONFIGURATION
# # ============================================================

# TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
# TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
# USE_TURSO = bool(TURSO_URL and TURSO_TOKEN and libsql_client)

# # Fallback local SQLite path
# TEMP_DIR = tempfile.gettempdir()
# DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

# CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

# if USE_TURSO:
#     print(f"Using remote Turso Database: {TURSO_URL}")
# else:
#     print(f"Using local SQLite database: {DB_PATH}")
#     if not (TURSO_URL and TURSO_TOKEN):
#         print("Notice: TURSO_DATABASE_URL or TURSO_AUTH_TOKEN is missing from environment.")
#     if not libsql_client:
#         print("Notice: libsql-client package is not installed.")

# print(f"Categories path: {CATEGORIES_PATH}")


# # ============================================================
# # DATABASE CLIENT & HELPERS
# # ============================================================

# def get_turso_client_sync():
#     """Returns a synchronous Turso client for startup tasks."""
#     url = TURSO_URL.replace("libsql://", "https://")
#     return libsql_client.create_client(url=url, auth_token=TURSO_TOKEN)


# def get_turso_client_async():
#     """Returns an asynchronous Turso client for async MCP tools."""
#     url = TURSO_URL.replace("libsql://", "https://")
#     return libsql_client.create_client_async(url=url, auth_token=TURSO_TOKEN)


# # ============================================================
# # FASTMCP SERVER
# # ============================================================

# mcp = FastMCP("ExpenseTracker")


# # ============================================================
# # DATABASE INITIALIZATION
# # ============================================================

# def init_db():
#     """
#     Initialize the database tables.
#     Runs once on startup synchronously.
#     """
#     create_expenses_sql = """
#         CREATE TABLE IF NOT EXISTS expenses(
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             date TEXT NOT NULL,
#             amount REAL NOT NULL,
#             category TEXT NOT NULL,
#             subcategory TEXT DEFAULT '',
#             note TEXT DEFAULT ''
#         )
#     """

#     create_credits_sql = """
#         CREATE TABLE IF NOT EXISTS credits(
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             date TEXT NOT NULL,
#             amount REAL NOT NULL,
#             source TEXT DEFAULT '',
#             note TEXT DEFAULT ''
#         )
#     """

#     try:
#         if USE_TURSO:
#             with get_turso_client_sync() as client:
#                 client.execute(create_expenses_sql)
#                 client.execute(create_credits_sql)
#             print("Remote Turso database schema verified successfully.")
#         else:
#             with sqlite3.connect(DB_PATH) as c:
#                 c.execute("PRAGMA journal_mode=WAL")
#                 c.execute(create_expenses_sql)
#                 c.execute(create_credits_sql)
#                 c.commit()
#             print("Local SQLite database initialized successfully.")
#     except Exception as e:
#         print(f"Database initialization error: {e}")
#         raise


# init_db()


# # ============================================================
# # CATEGORY HELPERS
# # ============================================================

# def load_categories():
#     with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
#         return json.load(f)


# def validate_category(category, subcategory=""):
#     try:
#         categories = load_categories()
#     except FileNotFoundError:
#         return "categories.json file was not found."
#     except json.JSONDecodeError:
#         return "categories.json contains invalid JSON."
#     except Exception as e:
#         return f"Could not load categories: {str(e)}"

#     if category not in categories:
#         return (
#             f"Invalid category '{category}'. "
#             f"Available categories: {', '.join(categories.keys())}"
#         )

#     if subcategory and subcategory not in categories[category]:
#         return (
#             f"Invalid subcategory '{subcategory}' for category '{category}'. "
#             f"Available subcategories: {', '.join(categories[category])}"
#         )

#     return None


# # ============================================================
# # ADD EXPENSE
# # ============================================================

# @mcp.tool()
# async def add_expense(
#     date: str,
#     amount: float,
#     category: str,
#     subcategory: str = "",
#     note: str = ""
# ):
#     """
#     Add a new expense entry.
#     """
#     try:
#         error = validate_category(category, subcategory)
#         if error:
#             return {"status": "error", "message": error}

#         if amount <= 0:
#             return {"status": "error", "message": "Expense amount must be greater than 0"}

#         if USE_TURSO:
#             async with get_turso_client_async() as client:
#                 rs = await client.execute(
#                     "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
#                     [date, amount, category, subcategory, note]
#                 )
#                 expense_id = rs.last_insert_rowid
#         else:
#             async with aiosqlite.connect(DB_PATH) as c:
#                 cur = await c.execute(
#                     "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
#                     (date, amount, category, subcategory, note)
#                 )
#                 expense_id = cur.lastrowid
#                 await c.commit()

#         return {
#             "status": "success",
#             "id": expense_id,
#             "message": "Expense added successfully"
#         }

#     except Exception as e:
#         return {"status": "error", "message": f"Database error: {str(e)}"}


# # ============================================================
# # EDIT EXPENSE
# # ============================================================

# @mcp.tool()
# async def edit_expense(
#     expense_id: int,
#     date: str = None,
#     amount: float = None,
#     category: str = None,
#     subcategory: str = None,
#     note: str = None
# ):
#     """
#     Edit an existing expense. Only fields provided are updated.
#     """
#     try:
#         if USE_TURSO:
#             async with get_turso_client_async() as client:
#                 rs = await client.execute(
#                     "SELECT date, amount, category, subcategory, note FROM expenses WHERE id = ?",
#                     [expense_id]
#                 )
#                 if not rs.rows:
#                     return {"status": "error", "message": f"Expense with ID {expense_id} not found"}

#                 row = rs.rows[0]
#                 old_date, old_amount, old_category, old_subcategory, old_note = (
#                     row[0], row[1], row[2], row[3], row[4]
#                 )

#                 date = old_date if date is None else date
#                 amount = old_amount if amount is None else amount
#                 category = old_category if category is None else category
#                 subcategory = old_subcategory if subcategory is None else subcategory
#                 note = old_note if note is None else note

#                 if amount <= 0:
#                     return {"status": "error", "message": "Expense amount must be greater than 0"}

#                 error = validate_category(category, subcategory)
#                 if error:
#                     return {"status": "error", "message": error}

#                 await client.execute(
#                     """
#                     UPDATE expenses
#                     SET date = ?, amount = ?, category = ?, subcategory = ?, note = ?
#                     WHERE id = ?
#                     """,
#                     [date, amount, category, subcategory, note, expense_id]
#                 )
#         else:
#             async with aiosqlite.connect(DB_PATH) as c:
#                 cur = await c.execute(
#                     "SELECT date, amount, category, subcategory, note FROM expenses WHERE id = ?",
#                     (expense_id,)
#                 )
#                 existing = await cur.fetchone()
#                 if existing is None:
#                     return {"status": "error", "message": f"Expense with ID {expense_id} not found"}

#                 old_date, old_amount, old_category, old_subcategory, old_note = existing
#                 date = old_date if date is None else date
#                 amount = old_amount if amount is None else amount
#                 category = old_category if category is None else category
#                 subcategory = old_subcategory if subcategory is None else subcategory
#                 note = old_note if note is None else note

#                 if amount <= 0:
#                     return {"status": "error", "message": "Expense amount must be greater than 0"}

#                 error = validate_category(category, subcategory)
#                 if error:
#                     return {"status": "error", "message": error}

#                 await c.execute(
#                     """
#                     UPDATE expenses
#                     SET date = ?, amount = ?, category = ?, subcategory = ?, note = ?
#                     WHERE id = ?
#                     """,
#                     (date, amount, category, subcategory, note, expense_id)
#                 )
#                 await c.commit()

#         return {
#             "status": "success",
#             "id": expense_id,
#             "message": "Expense updated successfully"
#         }

#     except Exception as e:
#         return {"status": "error", "message": f"Error updating expense: {str(e)}"}


# # ============================================================
# # DELETE EXPENSE
# # ============================================================

# @mcp.tool()
# async def delete_expense(expense_id: int):
#     """
#     Delete an expense by ID.
#     """
#     try:
#         if USE_TURSO:
#             async with get_turso_client_async() as client:
#                 rs = await client.execute("SELECT id FROM expenses WHERE id = ?", [expense_id])
#                 if not rs.rows:
#                     return {"status": "error", "message": f"Expense with ID {expense_id} not found"}
#                 await client.execute("DELETE FROM expenses WHERE id = ?", [expense_id])
#         else:
#             async with aiosqlite.connect(DB_PATH) as c:
#                 cur = await c.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,))
#                 if await cur.fetchone() is None:
#                     return {"status": "error", "message": f"Expense with ID {expense_id} not found"}
#                 await c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
#                 await c.commit()

#         return {
#             "status": "success",
#             "id": expense_id,
#             "message": "Expense deleted successfully"
#         }

#     except Exception as e:
#         return {"status": "error", "message": f"Error deleting expense: {str(e)}"}


# # ============================================================
# # LIST EXPENSES
# # ============================================================

# @mcp.tool()
# async def list_expenses(start_date: str, end_date: str):
#     """
#     List expense entries within an inclusive date range.
#     """
#     try:
#         if USE_TURSO:
#             async with get_turso_client_async() as client:
#                 rs = await client.execute(
#                     """
#                     SELECT id, date, amount, category, subcategory, note
#                     FROM expenses
#                     WHERE date BETWEEN ? AND ?
#                     ORDER BY date DESC, id DESC
#                     """,
#                     [start_date, end_date]
#                 )
#                 cols = ["id", "date", "amount", "category", "subcategory", "note"]
#                 return [dict(zip(cols, row)) for row in rs.rows]
#         else:
#             async with aiosqlite.connect(DB_PATH) as c:
#                 cur = await c.execute(
#                     """
#                     SELECT id, date, amount, category, subcategory, note
#                     FROM expenses
#                     WHERE date BETWEEN ? AND ?
#                     ORDER BY date DESC, id DESC
#                     """,
#                     (start_date, end_date)
#                 )
#                 rows = await cur.fetchall()
#                 cols = [desc[0] for desc in cur.description]
#                 return [dict(zip(cols, row)) for row in rows]

#     except Exception as e:
#         return {"status": "error", "message": f"Error listing expenses: {str(e)}"}


# # ============================================================
# # SUMMARIZE EXPENSES
# # ============================================================

# @mcp.tool()
# async def summarize(start_date: str, end_date: str, category: str = None):
#     """
#     Summarize expenses by category within an inclusive date range.
#     """
#     try:
#         if category:
#             categories = load_categories()
#             if category not in categories:
#                 return {
#                     "status": "error",
#                     "message": f"Invalid category '{category}'. Available categories: {', '.join(categories.keys())}"
#                 }

#         query = """
#             SELECT category, SUM(amount) AS total_amount, COUNT(*) AS count
#             FROM expenses
#             WHERE date BETWEEN ? AND ?
#         """
#         params = [start_date, end_date]

#         if category:
#             query += " AND category = ? "
#             params.append(category)

#         query += " GROUP BY category ORDER BY total_amount DESC "

#         if USE_TURSO:
#             async with get_turso_client_async() as client:
#                 rs = await client.execute(query, params)
#                 cols = ["category", "total_amount", "count"]
#                 return [dict(zip(cols, row)) for row in rs.rows]
#         else:
#             async with aiosqlite.connect(DB_PATH) as c:
#                 cur = await c.execute(query, tuple(params))
#                 rows = await cur.fetchall()
#                 cols = [desc[0] for desc in cur.description]
#                 return [dict(zip(cols, row)) for row in rows]

#     except Exception as e:
#         return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}


# # ============================================================
# # ADD CREDIT
# # ============================================================

# @mcp.tool()
# async def add_credit(
#     date: str,
#     amount: float,
#     source: str = "",
#     note: str = ""
# ):
#     """
#     Add money/credit to the account.
#     """
#     try:
#         if amount <= 0:
#             return {"status": "error", "message": "Credit amount must be greater than 0"}

#         if USE_TURSO:
#             async with get_turso_client_async() as client:
#                 rs = await client.execute(
#                     "INSERT INTO credits(date, amount, source, note) VALUES (?, ?, ?, ?)",
#                     [date, amount, source, note]
#                 )
#                 credit_id = rs.last_insert_rowid
#         else:
#             async with aiosqlite.connect(DB_PATH) as c:
#                 cur = await c.execute(
#                     "INSERT INTO credits(date, amount, source, note) VALUES (?, ?, ?, ?)",
#                     (date, amount, source, note)
#                 )
#                 credit_id = cur.lastrowid
#                 await c.commit()

#         return {
#             "status": "success",
#             "id": credit_id,
#             "message": "Credit added successfully"
#         }

#     except Exception as e:
#         return {"status": "error", "message": f"Database error: {str(e)}"}


# # ============================================================
# # LIST CREDITS
# # ============================================================

# @mcp.tool()
# async def list_credits(start_date: str, end_date: str):
#     """
#     List credits within an inclusive date range.
#     """
#     try:
#         query = """
#             SELECT id, date, amount, source, note
#             FROM credits
#             WHERE date BETWEEN ? AND ?
#             ORDER BY date DESC, id DESC
#         """
#         if USE_TURSO:
#             async with get_turso_client_async() as client:
#                 rs = await client.execute(query, [start_date, end_date])
#                 cols = ["id", "date", "amount", "source", "note"]
#                 return [dict(zip(cols, row)) for row in rs.rows]
#         else:
#             async with aiosqlite.connect(DB_PATH) as c:
#                 cur = await c.execute(query, (start_date, end_date))
#                 rows = await cur.fetchall()
#                 cols = [desc[0] for desc in cur.description]
#                 return [dict(zip(cols, row)) for row in rows]

#     except Exception as e:
#         return {"status": "error", "message": f"Error listing credits: {str(e)}"}


# # ============================================================
# # DELETE CREDIT
# # ============================================================

# @mcp.tool()
# async def delete_credit(credit_id: int):
#     """
#     Delete a credit by ID.
#     """
#     try:
#         if USE_TURSO:
#             async with get_turso_client_async() as client:
#                 rs = await client.execute("SELECT id FROM credits WHERE id = ?", [credit_id])
#                 if not rs.rows:
#                     return {"status": "error", "message": f"Credit with ID {credit_id} not found"}
#                 await client.execute("DELETE FROM credits WHERE id = ?", [credit_id])
#         else:
#             async with aiosqlite.connect(DB_PATH) as c:
#                 cur = await c.execute("SELECT id FROM credits WHERE id = ?", (credit_id,))
#                 if await cur.fetchone() is None:
#                     return {"status": "error", "message": f"Credit with ID {credit_id} not found"}
#                 await c.execute("DELETE FROM credits WHERE id = ?", (credit_id,))
#                 await c.commit()

#         return {
#             "status": "success",
#             "id": credit_id,
#             "message": "Credit deleted successfully"
#         }

#     except Exception as e:
#         return {"status": "error", "message": f"Error deleting credit: {str(e)}"}


# # ============================================================
# # ACCOUNT SUMMARY
# # ============================================================

# @mcp.tool()
# async def account_summary(start_date: str, end_date: str):
#     """
#     Show total credits, total expenses, and net balance for a date range.
#     """
#     try:
#         credit_query = "SELECT COALESCE(SUM(amount), 0) FROM credits WHERE date BETWEEN ? AND ?"
#         expense_query = "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date BETWEEN ? AND ?"

#         if USE_TURSO:
#             async with get_turso_client_async() as client:
#                 rs_credits = await client.execute(credit_query, [start_date, end_date])
#                 rs_expenses = await client.execute(expense_query, [start_date, end_date])
#                 total_credits = rs_credits.rows[0][0] or 0.0
#                 total_expenses = rs_expenses.rows[0][0] or 0.0
#         else:
#             async with aiosqlite.connect(DB_PATH) as c:
#                 cur = await c.execute(credit_query, (start_date, end_date))
#                 total_credits = (await cur.fetchone())[0] or 0.0

#                 cur = await c.execute(expense_query, (start_date, end_date))
#                 total_expenses = (await cur.fetchone())[0] or 0.0

#         net_balance = total_credits - total_expenses

#         return {
#             "status": "success",
#             "start_date": start_date,
#             "end_date": end_date,
#             "total_credits": total_credits,
#             "total_expenses": total_expenses,
#             "net_balance": net_balance
#         }

#     except Exception as e:
#         return {"status": "error", "message": f"Error generating account summary: {str(e)}"}


# # ============================================================
# # CATEGORIES RESOURCE
# # ============================================================

# @mcp.resource("expense:///categories", mime_type="application/json")
# def categories():
#     """
#     Return categories.json.
#     """
#     try:
#         with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
#             return f.read()
#     except Exception as e:
#         return json.dumps({"error": f"Could not load categories: {str(e)}"}, indent=2)


# # ============================================================
# # START SERVER
# # ============================================================

# if __name__ == "__main__":
#     print("Starting ExpenseTracker MCP server...")
#     print("Transport: HTTP")
#     print("Host: 0.0.0.0")
#     print("Port: 8080")

#     mcp.run(
#         transport="http",
#         host="0.0.0.0",
#         port=8080
#     )





import asyncio
import json
import os
import sqlite3
import tempfile
import aiosqlite
from fastmcp import FastMCP

# Turso / LibSQL client for persistent remote cloud storage
try:
    import libsql_client
except ImportError:
    libsql_client = None


# ============================================================
# PATH & DATABASE CONFIGURATION
# ============================================================

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
USE_TURSO = bool(TURSO_URL and TURSO_TOKEN and libsql_client)

# Fallback local SQLite path
TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

CATEGORIES_PATH = os.path.join(
    os.path.dirname(__file__),
    "categories.json"
)

if USE_TURSO:
    print(f"Using remote Turso Database: {TURSO_URL}")
else:
    print(f"Using local SQLite database: {DB_PATH}")
    if not (TURSO_URL and TURSO_TOKEN):
        print("Notice: TURSO_DATABASE_URL or TURSO_AUTH_TOKEN is missing from environment.")
    if not libsql_client:
        print("Notice: libsql-client package is not installed.")

print(f"Categories path: {CATEGORIES_PATH}")


# ============================================================
# DATABASE CLIENT & HELPERS
# ============================================================

def get_turso_client_async():
    """Returns an asynchronous Turso client for async MCP tools and initialization."""
    url = TURSO_URL.replace("libsql://", "https://")
    return libsql_client.create_client(url=url, auth_token=TURSO_TOKEN)


# ============================================================
# FASTMCP SERVER
# ============================================================

mcp = FastMCP("ExpenseTracker")


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

async def init_db():
    """
    Initialize the database tables asynchronously.
    Runs once on startup within an asyncio event loop.
    """
    create_expenses_sql = """
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT DEFAULT '',
            note TEXT DEFAULT ''
        )
    """

    create_credits_sql = """
        CREATE TABLE IF NOT EXISTS credits(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            source TEXT DEFAULT '',
            note TEXT DEFAULT ''
        )
    """

    try:
        if USE_TURSO:
            async with get_turso_client_async() as client:
                await client.execute(create_expenses_sql)
                await client.execute(create_credits_sql)
            print("Remote Turso database schema verified successfully.")
        else:
            with sqlite3.connect(DB_PATH) as c:
                c.execute("PRAGMA journal_mode=WAL")
                c.execute(create_expenses_sql)
                c.execute(create_credits_sql)
                c.commit()
            print("Local SQLite database initialized successfully.")
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise


# Run initialization inside an event loop before starting the server
asyncio.run(init_db())


# ============================================================
# CATEGORY HELPERS
# ============================================================

def load_categories():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_category(category, subcategory=""):
    try:
        categories = load_categories()
    except FileNotFoundError:
        return "categories.json file was not found."
    except json.JSONDecodeError:
        return "categories.json contains invalid JSON."
    except Exception as e:
        return f"Could not load categories: {str(e)}"

    if category not in categories:
        return (
            f"Invalid category '{category}'. "
            f"Available categories: {', '.join(categories.keys())}"
        )

    if subcategory and subcategory not in categories[category]:
        return (
            f"Invalid subcategory '{subcategory}' for category '{category}'. "
            f"Available subcategories: {', '.join(categories[category])}"
        )

    return None


# ============================================================
# ADD EXPENSE
# ============================================================

@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
):
    """
    Add a new expense entry.
    """
    try:
        error = validate_category(category, subcategory)
        if error:
            return {"status": "error", "message": error}

        if amount <= 0:
            return {"status": "error", "message": "Expense amount must be greater than 0"}

        if USE_TURSO:
            async with get_turso_client_async() as client:
                rs = await client.execute(
                    "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
                    [date, amount, category, subcategory, note]
                )
                expense_id = rs.last_insert_rowid
        else:
            async with aiosqlite.connect(DB_PATH) as c:
                cur = await c.execute(
                    "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
                    (date, amount, category, subcategory, note)
                )
                expense_id = cur.lastrowid
                await c.commit()

        return {
            "status": "success",
            "id": expense_id,
            "message": "Expense added successfully"
        }

    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


# ============================================================
# EDIT EXPENSE
# ============================================================

@mcp.tool()
async def edit_expense(
    expense_id: int,
    date: str = None,
    amount: float = None,
    category: str = None,
    subcategory: str = None,
    note: str = None
):
    """
    Edit an existing expense. Only fields provided are updated.
    """
    try:
        if USE_TURSO:
            async with get_turso_client_async() as client:
                rs = await client.execute(
                    "SELECT date, amount, category, subcategory, note FROM expenses WHERE id = ?",
                    [expense_id]
                )
                if not rs.rows:
                    return {"status": "error", "message": f"Expense with ID {expense_id} not found"}

                row = rs.rows[0]
                old_date, old_amount, old_category, old_subcategory, old_note = (
                    row[0], row[1], row[2], row[3], row[4]
                )

                date = old_date if date is None else date
                amount = old_amount if amount is None else amount
                category = old_category if category is None else category
                subcategory = old_subcategory if subcategory is None else subcategory
                note = old_note if note is None else note

                if amount <= 0:
                    return {"status": "error", "message": "Expense amount must be greater than 0"}

                error = validate_category(category, subcategory)
                if error:
                    return {"status": "error", "message": error}

                await client.execute(
                    """
                    UPDATE expenses
                    SET date = ?, amount = ?, category = ?, subcategory = ?, note = ?
                    WHERE id = ?
                    """,
                    [date, amount, category, subcategory, note, expense_id]
                )
        else:
            async with aiosqlite.connect(DB_PATH) as c:
                cur = await c.execute(
                    "SELECT date, amount, category, subcategory, note FROM expenses WHERE id = ?",
                    (expense_id,)
                )
                existing = await cur.fetchone()
                if existing is None:
                    return {"status": "error", "message": f"Expense with ID {expense_id} not found"}

                old_date, old_amount, old_category, old_subcategory, old_note = existing
                date = old_date if date is None else date
                amount = old_amount if amount is None else amount
                category = old_category if category is None else category
                subcategory = old_subcategory if subcategory is None else subcategory
                note = old_note if note is None else note

                if amount <= 0:
                    return {"status": "error", "message": "Expense amount must be greater than 0"}

                error = validate_category(category, subcategory)
                if error:
                    return {"status": "error", "message": error}

                await c.execute(
                    """
                    UPDATE expenses
                    SET date = ?, amount = ?, category = ?, subcategory = ?, note = ?
                    WHERE id = ?
                    """,
                    (date, amount, category, subcategory, note, expense_id)
                )
                await c.commit()

        return {
            "status": "success",
            "id": expense_id,
            "message": "Expense updated successfully"
        }

    except Exception as e:
        return {"status": "error", "message": f"Error updating expense: {str(e)}"}


# ============================================================
# DELETE EXPENSE
# ============================================================

@mcp.tool()
async def delete_expense(expense_id: int):
    """
    Delete an expense by ID.
    """
    try:
        if USE_TURSO:
            async with get_turso_client_async() as client:
                rs = await client.execute("SELECT id FROM expenses WHERE id = ?", [expense_id])
                if not rs.rows:
                    return {"status": "error", "message": f"Expense with ID {expense_id} not found"}
                await client.execute("DELETE FROM expenses WHERE id = ?", [expense_id])
        else:
            async with aiosqlite.connect(DB_PATH) as c:
                cur = await c.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,))
                if await cur.fetchone() is None:
                    return {"status": "error", "message": f"Expense with ID {expense_id} not found"}
                await c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
                await c.commit()

        return {
            "status": "success",
            "id": expense_id,
            "message": "Expense deleted successfully"
        }

    except Exception as e:
        return {"status": "error", "message": f"Error deleting expense: {str(e)}"}


# ============================================================
# LIST EXPENSES
# ============================================================

@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    """
    List expense entries within an inclusive date range.
    """
    try:
        if USE_TURSO:
            async with get_turso_client_async() as client:
                rs = await client.execute(
                    """
                    SELECT id, date, amount, category, subcategory, note
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date DESC, id DESC
                    """,
                    [start_date, end_date]
                )
                cols = ["id", "date", "amount", "category", "subcategory", "note"]
                return [dict(zip(cols, row)) for row in rs.rows]
        else:
            async with aiosqlite.connect(DB_PATH) as c:
                cur = await c.execute(
                    """
                    SELECT id, date, amount, category, subcategory, note
                    FROM expenses
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date DESC, id DESC
                    """,
                    (start_date, end_date)
                )
                rows = await cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in rows]

    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}


# ============================================================
# SUMMARIZE EXPENSES
# ============================================================

@mcp.tool()
async def summarize(start_date: str, end_date: str, category: str = None):
    """
    Summarize expenses by category within an inclusive date range.
    """
    try:
        if category:
            categories = load_categories()
            if category not in categories:
                return {
                    "status": "error",
                    "message": f"Invalid category '{category}'. Available categories: {', '.join(categories.keys())}"
                }

        query = """
            SELECT category, SUM(amount) AS total_amount, COUNT(*) AS count
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if category:
            query += " AND category = ? "
            params.append(category)

        query += " GROUP BY category ORDER BY total_amount DESC "

        if USE_TURSO:
            async with get_turso_client_async() as client:
                rs = await client.execute(query, params)
                cols = ["category", "total_amount", "count"]
                return [dict(zip(cols, row)) for row in rs.rows]
        else:
            async with aiosqlite.connect(DB_PATH) as c:
                cur = await c.execute(query, tuple(params))
                rows = await cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in rows]

    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}


# ============================================================
# ADD CREDIT
# ============================================================

@mcp.tool()
async def add_credit(
    date: str,
    amount: float,
    source: str = "",
    note: str = ""
):
    """
    Add money/credit to the account.
    """
    try:
        if amount <= 0:
            return {"status": "error", "message": "Credit amount must be greater than 0"}

        if USE_TURSO:
            async with get_turso_client_async() as client:
                rs = await client.execute(
                    "INSERT INTO credits(date, amount, source, note) VALUES (?, ?, ?, ?)",
                    [date, amount, source, note]
                )
                credit_id = rs.last_insert_rowid
        else:
            async with aiosqlite.connect(DB_PATH) as c:
                cur = await c.execute(
                    "INSERT INTO credits(date, amount, source, note) VALUES (?, ?, ?, ?)",
                    (date, amount, source, note)
                )
                credit_id = cur.lastrowid
                await c.commit()

        return {
            "status": "success",
            "id": credit_id,
            "message": "Credit added successfully"
        }

    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


# ============================================================
# LIST CREDITS
# ============================================================

@mcp.tool()
async def list_credits(start_date: str, end_date: str):
    """
    List credits within an inclusive date range.
    """
    try:
        query = """
            SELECT id, date, amount, source, note
            FROM credits
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC, id DESC
        """
        if USE_TURSO:
            async with get_turso_client_async() as client:
                rs = await client.execute(query, [start_date, end_date])
                cols = ["id", "date", "amount", "source", "note"]
                return [dict(zip(cols, row)) for row in rs.rows]
        else:
            async with aiosqlite.connect(DB_PATH) as c:
                cur = await c.execute(query, (start_date, end_date))
                rows = await cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in rows]

    except Exception as e:
        return {"status": "error", "message": f"Error listing credits: {str(e)}"}


# ============================================================
# DELETE CREDIT
# ============================================================

@mcp.tool()
async def delete_credit(credit_id: int):
    """
    Delete a credit by ID.
    """
    try:
        if USE_TURSO:
            async with get_turso_client_async() as client:
                rs = await client.execute("SELECT id FROM credits WHERE id = ?", [credit_id])
                if not rs.rows:
                    return {"status": "error", "message": f"Credit with ID {credit_id} not found"}
                await client.execute("DELETE FROM credits WHERE id = ?", [credit_id])
        else:
            async with aiosqlite.connect(DB_PATH) as c:
                cur = await c.execute("SELECT id FROM credits WHERE id = ?", (credit_id,))
                if await cur.fetchone() is None:
                    return {"status": "error", "message": f"Credit with ID {credit_id} not found"}
                await c.execute("DELETE FROM credits WHERE id = ?", (credit_id,))
                await c.commit()

        return {
            "status": "success",
            "id": credit_id,
            "message": "Credit deleted successfully"
        }

    except Exception as e:
        return {"status": "error", "message": f"Error deleting credit: {str(e)}"}


# ============================================================
# ACCOUNT SUMMARY
# ============================================================

@mcp.tool()
async def account_summary(start_date: str, end_date: str):
    """
    Show total credits, total expenses, and net balance for a date range.
    """
    try:
        credit_query = "SELECT COALESCE(SUM(amount), 0) FROM credits WHERE date BETWEEN ? AND ?"
        expense_query = "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date BETWEEN ? AND ?"

        if USE_TURSO:
            async with get_turso_client_async() as client:
                rs_credits = await client.execute(credit_query, [start_date, end_date])
                rs_expenses = await client.execute(expense_query, [start_date, end_date])
                total_credits = rs_credits.rows[0][0] or 0.0
                total_expenses = rs_expenses.rows[0][0] or 0.0
        else:
            async with aiosqlite.connect(DB_PATH) as c:
                cur = await c.execute(credit_query, (start_date, end_date))
                total_credits = (await cur.fetchone())[0] or 0.0

                cur = await c.execute(expense_query, (start_date, end_date))
                total_expenses = (await cur.fetchone())[0] or 0.0

        net_balance = total_credits - total_expenses

        return {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "total_credits": total_credits,
            "total_expenses": total_expenses,
            "net_balance": net_balance
        }

    except Exception as e:
        return {"status": "error", "message": f"Error generating account summary: {str(e)}"}


# ============================================================
# CATEGORIES RESOURCE
# ============================================================

@mcp.resource("expense:///categories", mime_type="application/json")
def categories():
    """
    Return categories.json.
    """
    try:
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return json.dumps({"error": f"Could not load categories: {str(e)}"}, indent=2)


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting ExpenseTracker MCP server on port {port}...")

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )