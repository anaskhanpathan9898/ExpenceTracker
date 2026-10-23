"""
models/transaction.py
---------------------
Helper functions for the 'transactions' collection.

Each transaction document looks like:
{
    "_id":         ObjectId,
    "user_id":     ObjectId,   ← links to users._id
    "type":        "income" | "expense",
    "amount":      float,      ← always positive
    "category":    str,        ← from CATEGORIES list below
    "description": str,
    "date":        datetime,   ← date chosen by the user
    "created_at":  datetime,   ← when the record was inserted
}
"""

from datetime import datetime, timezone
from bson import ObjectId

# The fixed list of categories shown in all dropdowns
CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Education",
    "Bills",
    "Health",
    "Salary",
    "Other",
]

TRANSACTION_TYPES = ["income", "expense"]


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_transaction(db, user_id, type_, amount, category, description, date):
    """
    Insert a new transaction.
    - user_id:  string or ObjectId of the logged-in user
    - type_:    "income" or "expense"
    - amount:   positive float
    - category: one of CATEGORIES
    - date:     Python datetime object
    """
    doc = {
        "user_id": ObjectId(user_id),
        "type": type_,
        "amount": float(amount),
        "category": category,
        "description": description.strip(),
        "date": date,
        "created_at": datetime.now(timezone.utc),
    }
    result = db.transactions.insert_one(doc)
    return str(result.inserted_id)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_transactions(db, user_id, filters=None, page=1, per_page=10):
    """
    Return a paginated list of transactions for a user, newest first.
    filters: optional dict with keys: type, category, search, date_from, date_to
    Returns (list_of_docs, total_count)
    """
    query = {"user_id": ObjectId(user_id)}

    if filters:
        if filters.get("type") and filters["type"] in TRANSACTION_TYPES:
            query["type"] = filters["type"]

        if filters.get("category") and filters["category"] in CATEGORIES:
            query["category"] = filters["category"]

        if filters.get("search"):
            # Case-insensitive substring search on description
            query["description"] = {"$regex": filters["search"], "$options": "i"}

        date_filter = {}
        if filters.get("date_from"):
            date_filter["$gte"] = filters["date_from"]
        if filters.get("date_to"):
            date_filter["$lte"] = filters["date_to"]
        if date_filter:
            query["date"] = date_filter

    total = db.transactions.count_documents(query)
    skip = (page - 1) * per_page
    docs = list(
        db.transactions.find(query)
        .sort([("date", -1), ("_id", -1)])
        .skip(skip)
        .limit(per_page)
    )
    return docs, total


def get_transaction_by_id(db, transaction_id, user_id):
    """
    Return a single transaction document, but only if it belongs to user_id.
    This prevents one user from seeing another user's data.
    """
    return db.transactions.find_one({
        "_id": ObjectId(transaction_id),
        "user_id": ObjectId(user_id),
    })


def get_recent_transactions(db, user_id, limit=5):
    """Return the most recent `limit` transactions for the dashboard."""
    return list(
        db.transactions.find({"user_id": ObjectId(user_id)})
        .sort([("date", -1), ("_id", -1)])
        .limit(limit)
    )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def update_transaction(db, transaction_id, user_id, updates):
    """
    Update fields on a transaction. Only allowed if it belongs to user_id.
    updates: dict of fields to change (type, amount, category, description, date)
    """
    db.transactions.update_one(
        {"_id": ObjectId(transaction_id), "user_id": ObjectId(user_id)},
        {"$set": updates},
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def delete_transaction(db, transaction_id, user_id):
    """Delete a transaction only if it belongs to user_id."""
    db.transactions.delete_one({
        "_id": ObjectId(transaction_id),
        "user_id": ObjectId(user_id),
    })


# ---------------------------------------------------------------------------
# Aggregations (used by dashboard charts)
# ---------------------------------------------------------------------------

def get_summary(db, user_id, year=None, month=None):
    """
    Return total income, total expenses, and balance for a user.
    Optionally filter to a specific year/month (both must be provided together).
    """
    match = {"user_id": ObjectId(user_id)}
    if year and month:
        from datetime import date
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        # Last day of month
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        match["date"] = {"$gte": start, "$lt": end}

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"},
            }
        },
    ]
    results = {r["_id"]: r["total"] for r in db.transactions.aggregate(pipeline)}
    income = results.get("income", 0.0)
    expenses = results.get("expense", 0.0)
    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
    }


def get_monthly_totals(db, user_id, year):
    """
    Return monthly income and expense totals for a given year.
    Used by the bar chart on the dashboard.
    Returns a list of 12 dicts: [{month: 1, income: x, expense: y}, ...]
    """
    pipeline = [
        {
            "$match": {
                "user_id": ObjectId(user_id),
                "date": {
                    "$gte": datetime(year, 1, 1, tzinfo=timezone.utc),
                    "$lt": datetime(year + 1, 1, 1, tzinfo=timezone.utc),
                },
            }
        },
        {
            "$group": {
                "_id": {
                    "month": {"$month": "$date"},
                    "type": "$type",
                },
                "total": {"$sum": "$amount"},
            }
        },
    ]
    raw = list(db.transactions.aggregate(pipeline))

    # Build a clean 12-month structure
    months = {i: {"month": i, "income": 0.0, "expense": 0.0} for i in range(1, 13)}
    for r in raw:
        m = r["_id"]["month"]
        t = r["_id"]["type"]
        months[m][t] = r["total"]

    return list(months.values())


def get_category_totals(db, user_id, year=None, month=None):
    """
    Return total expenses grouped by category.
    Used by the doughnut chart on the dashboard.
    """
    match = {"user_id": ObjectId(user_id), "type": "expense"}
    if year and month:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc) if month < 12 \
              else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        match["date"] = {"$gte": start, "$lt": end}

    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
        {"$sort": {"total": -1}},
    ]
    return list(db.transactions.aggregate(pipeline))


def ensure_indexes(db):
    """Create indexes for fast queries. Call once at startup."""
    db.transactions.create_index([("user_id", 1), ("date", -1)])
    db.transactions.create_index([("user_id", 1), ("type", 1)])
    db.transactions.create_index([("user_id", 1), ("category", 1)])
