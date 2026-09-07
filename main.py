from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from google import genai
import os
from pathlib import Path
from fastapi.responses import FileResponse
from dotenv import load_dotenv, dotenv_values


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

# Load .env explicitly from the same folder as main.py
load_dotenv(
    dotenv_path=ENV_FILE,
    override=True
)

# Read .env directly as an additional safeguard
env_values = dotenv_values(ENV_FILE)

GEMINI_API_KEY = (
    env_values.get("GEMINI_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or ""
).strip()

GEMINI_MODEL = (
    env_values.get("GEMINI_MODEL")
    or os.getenv("GEMINI_MODEL")
    or "gemini-3.6-flash"
).strip()


print("")
print("=" * 60)
print("ENVIRONMENT CHECK")
print("=" * 60)
print(f"ENV file: {ENV_FILE}")
print(f"ENV exists: {ENV_FILE.exists()}")
print(f"Gemini API configured: {bool(GEMINI_API_KEY)}")
print(f"Gemini model: {GEMINI_MODEL}")
print("=" * 60)
print("")


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="IT Support Automation Backend",
    version="1.0.0"
)


# ============================================================
# GEMINI AI CONFIGURATION
# ============================================================

client = None

if not GEMINI_API_KEY:

    print(
        "WARNING: GEMINI_API_KEY is not configured."
    )

else:

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        print(
            "Gemini client initialized successfully."
        )

        print(
            f"Gemini model: {GEMINI_MODEL}"
        )

    except Exception as e:

        print(
            "WARNING: Gemini client initialization failed:"
        )

        print(e)

        client = None


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="IT Support Automation Backend",
    version="1.0.0"
)


# ============================================================
# GEMINI AI CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Stable Gemini model
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)

client = None

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set.")
else:
    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )
        print("Gemini client initialized successfully.")
        print(f"Gemini model: {GEMINI_MODEL}")

    except Exception as e:
        print(f"WARNING: Gemini client initialization failed: {e}")
        client = None


# ============================================================
# GEMINI HELPER
# ============================================================

def ask_gemini(prompt: str):

    if not GEMINI_API_KEY:
        raise Exception(
            "GEMINI_API_KEY is not configured."
        )

    if client is None:
        raise Exception(
            "Gemini client is not initialized."
        )

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        if response is None:
            raise Exception(
                "Gemini returned no response."
            )

        text = getattr(response, "text", None)

        if not text:
            raise Exception(
                "Gemini returned an empty response."
            )

        return text.strip()

    except Exception as e:

        raise Exception(
            f"Gemini API error: {str(e)}"
        )


# ============================================================
# AI CONNECTION TEST
# ============================================================

@app.get("/ai-test")
def ai_test():

    try:

        response = ask_gemini(
            "Reply with exactly: Gemini connection successful"
        )

        return {
            "status": "success",
            "gemini_response": response,
            "model": GEMINI_MODEL
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Gemini connection failed: {str(e)}"
        )


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "tickets.db"


def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (

            ticket_id TEXT PRIMARY KEY,

            issue TEXT NOT NULL,

            category TEXT NOT NULL,

            priority TEXT NOT NULL,

            recommended_team TEXT NOT NULL,

            human_escalation BOOLEAN NOT NULL,

            next_action TEXT NOT NULL,

            status TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
    """)

    conn.commit()

    conn.close()


init_db()


# ============================================================
# REQUEST MODELS
# ============================================================

class TicketRequest(BaseModel):

    issue: str


class AISolutionRequest(BaseModel):

    issue: str


class StatusUpdate(BaseModel):

    status: str


# ============================================================
# TICKET CLASSIFICATION
# ============================================================

def classify_ticket(issue: str):

    text = issue.lower().strip()


    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if any(word in text for word in [
        "password",
        "login",
        "log in",
        "sign in",
        "authentication",
        "account",
        "locked",
        "permission",
        "access",
        "sap"
    ]):

        category = "Access"


    elif any(word in text for word in [
        "laptop",
        "computer",
        "mouse",
        "keyboard",
        "monitor",
        "printer",
        "hardware",
        "screen"
    ]):

        category = "Hardware"


    elif any(word in text for word in [
        "wifi",
        "wi-fi",
        "internet",
        "network",
        "vpn",
        "connection"
    ]):

        category = "Network"


    elif any(word in text for word in [
        "software",
        "application",
        "app",
        "install",
        "crash",
        "error",
        "outlook",
        "excel",
        "teams"
    ]):

        category = "Software"


    else:

        category = "General IT Support"


    # --------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------

    critical_phrases = [

        "security breach",
        "ransomware",
        "data loss",
        "production down",
        "server down",
        "critical incident",
        "major outage"

    ]


    high_phrases = [

        "cannot work",
        "can't work",
        "unable to work",
        "completely blocked",
        "business stopped",
        "work is blocked",
        "unable to access",
        "no access"

    ]


    medium_phrases = [

        "slow",
        "intermittent",
        "sometimes",
        "occasionally",
        "performance issue"

    ]


    not_urgent = any(
        phrase in text
        for phrase in [

            "not urgent",
            "not an urgent",
            "not emergency",
            "no urgency",
            "no immediate urgency",
            "whenever possible",
            "when possible"

        ]
    )


    if any(
        phrase in text
        for phrase in critical_phrases
    ):

        priority = "Critical"


    elif (
        not not_urgent
        and any(
            phrase in text
            for phrase in high_phrases
        )
    ):

        priority = "High"


    elif any(
        phrase in text
        for phrase in medium_phrases
    ):

        priority = "Medium"


    else:

        priority = "Low"


    # --------------------------------------------------------
    # RECOMMENDED TEAM
    # --------------------------------------------------------

    if category == "Hardware":

        team = "Workplace Services / IT Support"

    elif category == "Network":

        team = "Network Support"

    elif category == "Access":

        team = (
            "Identity & Access Management (IAM) / IT Support"
        )

    elif category == "Software":

        team = "Application Support"

    else:

        team = "IT Support"


    # --------------------------------------------------------
    # HUMAN ESCALATION
    # --------------------------------------------------------

    human_escalation = (

        priority in [
            "Critical",
            "High"
        ]

        or "security breach" in text
        or "ransomware" in text
        or "data loss" in text

    )


    # --------------------------------------------------------
    # NEXT ACTION
    # --------------------------------------------------------

    if human_escalation:

        next_action = (
            "Escalate to human support team"
        )

    else:

        next_action = (
            "Self-service or standard IT support workflow"
        )


    return {

        "category": category,

        "priority": priority,

        "recommended_team": team,

        "human_escalation": human_escalation,

        "next_action": next_action

    }


# ============================================================
# GENERATE TICKET ID
# ============================================================

def generate_ticket_id():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT ticket_id
        FROM tickets
        ORDER BY ROWID DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()


    if row is None:

        return "TKT-1001"


    last_id = row["ticket_id"]


    try:

        number = int(
            last_id.replace("TKT-", "")
        )

        return f"TKT-{number + 1}"


    except Exception:

        return "TKT-1001"


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {

        "status": "online",

        "message":
            "IT Support Automation Backend is running",

        "model":
            GEMINI_MODEL

    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "gemini_configured":
            bool(GEMINI_API_KEY),

        "gemini_client":
            client is not None,

        "model":
            GEMINI_MODEL

    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/dashboard")
def dashboard():

    dashboard_file = "dashboard.html"

    if not os.path.exists(dashboard_file):

        raise HTTPException(

            status_code=404,

            detail="dashboard.html not found"

        )

    return FileResponse(
        dashboard_file
    )


# ============================================================
# CREATE TICKET
# ============================================================

@app.post("/tickets")
def create_ticket(
    ticket: TicketRequest
):

    issue = ticket.issue.strip()


    if not issue:

        raise HTTPException(

            status_code=400,

            detail="Issue cannot be empty"

        )


    result = classify_ticket(issue)


    ticket_id = generate_ticket_id()


    created_at = datetime.now().isoformat(
        timespec="seconds"
    )


    conn = get_connection()

    cursor = conn.cursor()


    try:

        cursor.execute("""
            INSERT INTO tickets (

                ticket_id,
                issue,
                category,
                priority,
                recommended_team,
                human_escalation,
                next_action,
                status,
                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            ticket_id,

            issue,

            result["category"],

            result["priority"],

            result["recommended_team"],

            result["human_escalation"],

            result["next_action"],

            "Open",

            created_at

        ))


        conn.commit()


    except sqlite3.IntegrityError:

        conn.close()

        raise HTTPException(

            status_code=500,

            detail="Could not create unique ticket ID"

        )


    conn.close()


    return {

        "status": "success",

        "ticket_id": ticket_id,

        "ticket_summary": issue,

        "category": result["category"],

        "priority": result["priority"],

        "recommended_team":
            result["recommended_team"],

        "human_escalation":
            result["human_escalation"],

        "next_action":
            result["next_action"],

        "status": "Open",

        "created_at": created_at

    }


# ============================================================
# AI TROUBLESHOOTING SOLUTION
# ============================================================

@app.post("/ai-solution")
def ai_solution(
    request: AISolutionRequest
):

    issue = request.issue.strip()


    if not issue:

        raise HTTPException(

            status_code=400,

            detail="Issue cannot be empty"

        )


    prompt = f"""
You are an IT Support AI Agent helping a normal employee.

USER ISSUE:
{issue}

Give a practical, safe and beginner-friendly
troubleshooting solution.

Use EXACTLY this structure:

PROBLEM:
Briefly explain the problem.

LIKELY CAUSE:
Explain the most likely cause.

STEPS:
1. Step one
2. Step two
3. Step three
4. Step four
5. Step five

VERIFY:
Explain exactly how the user can check
whether the problem is fixed.

IF STILL NOT SOLVED:
Tell the user to click
"Still Not Solved → Human Support"
to escalate the ticket to human IT support.

IMPORTANT:
- Keep instructions simple.
- Give 3 to 5 useful steps.
- Do not delete files.
- Do not modify dangerous system settings.
- Do not ask the user to perform risky actions.
- If the issue is SAP/login/access related,
  provide appropriate basic troubleshooting steps.
"""


    try:

        solution = ask_gemini(prompt)


        return {

            "status": "success",

            "issue": issue,

            "ai_solution": solution,

            "model": GEMINI_MODEL

        }


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=
                f"AI solution generation failed: {str(e)}"

        )


# ============================================================
# GET ALL TICKETS
# ============================================================

@app.get("/tickets")
def get_tickets():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM tickets
        ORDER BY ROWID DESC
    """)


    tickets = [

        dict(row)

        for row in cursor.fetchall()

    ]


    conn.close()


    return {

        "total": len(tickets),

        "tickets": tickets

    }


# ============================================================
# GET ONE TICKET
# ============================================================

@app.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: str
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM tickets
        WHERE ticket_id = ?
    """, (ticket_id,))


    ticket = cursor.fetchone()

    conn.close()


    if ticket is None:

        raise HTTPException(

            status_code=404,

            detail="Ticket not found"

        )


    return dict(ticket)


# ============================================================
# AI TICKET ANALYSIS
# ============================================================

@app.get("/tickets/{ticket_id}/ai-analysis")
def ai_ticket_analysis(
    ticket_id: str
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM tickets
        WHERE ticket_id = ?
    """, (ticket_id,))


    ticket = cursor.fetchone()

    conn.close()


    if ticket is None:

        raise HTTPException(

            status_code=404,

            detail="Ticket not found"

        )


    ticket = dict(ticket)


    prompt = f"""
You are an AI IT Support Agent.

Analyze this support ticket.

Ticket ID:
{ticket["ticket_id"]}

Issue:
{ticket["issue"]}

Category:
{ticket["category"]}

Priority:
{ticket["priority"]}

Recommended Team:
{ticket["recommended_team"]}

Human Escalation:
{ticket["human_escalation"]}

Current Status:
{ticket["status"]}

Provide:

1. Short problem summary
2. Likely cause
3. Recommended troubleshooting steps
4. Whether human escalation is required
5. Recommended next action

Keep the response practical and suitable
for an IT support team.
"""


    try:

        analysis = ask_gemini(prompt)


        return {

            "status": "success",

            "ticket_id": ticket_id,

            "ai_analysis": analysis,

            "model": GEMINI_MODEL

        }


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=
                f"AI ticket analysis failed: {str(e)}"

        )


# ============================================================
# UPDATE TICKET STATUS
# ============================================================

@app.put("/tickets/{ticket_id}/status")
def update_ticket_status(

    ticket_id: str,

    update: StatusUpdate

):

    allowed_statuses = [

        "Open",

        "In Progress",

        "Resolved",

        "Closed"

    ]


    if update.status not in allowed_statuses:

        raise HTTPException(

            status_code=400,

            detail=
                f"Status must be one of: {allowed_statuses}"

        )


    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        UPDATE tickets
        SET status = ?
        WHERE ticket_id = ?
    """, (

        update.status,

        ticket_id

    ))


    if cursor.rowcount == 0:

        conn.close()

        raise HTTPException(

            status_code=404,

            detail="Ticket not found"

        )


    conn.commit()

    conn.close()


    return {

        "status": "success",

        "ticket_id": ticket_id,

        "new_status": update.status,

        "message":
            "Ticket status updated successfully"

    }


# ============================================================
# AGENTIC AI ACTION
# ============================================================

@app.post("/tickets/{ticket_id}/ai-action")
def ai_ticket_action(
    ticket_id: str
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM tickets
        WHERE ticket_id = ?
    """, (ticket_id,))


    ticket = cursor.fetchone()

    conn.close()


    if ticket is None:

        raise HTTPException(

            status_code=404,

            detail="Ticket not found"

        )


    ticket = dict(ticket)


    prompt = f"""
You are an Agentic AI IT Support Agent.

Review this support ticket.

Ticket ID:
{ticket["ticket_id"]}

Issue:
{ticket["issue"]}

Category:
{ticket["category"]}

Priority:
{ticket["priority"]}

Human Escalation:
{ticket["human_escalation"]}

Current Status:
{ticket["status"]}

Rules:

- Critical issues must be escalated.
- Security issues must be escalated.
- Data-loss issues must be escalated.
- High priority issues must be escalated.
- Otherwise choose STANDARD.

Reply with exactly one word:

ESCALATE

or

STANDARD
"""


    try:

        ai_decision = ask_gemini(prompt).strip().upper()


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=
                f"AI action failed: {str(e)}"

        )


    if ai_decision == "ESCALATE":

        decision = "ESCALATE"

        new_status = "In Progress"

        action_taken = (
            "Ticket escalated to human support team"
        )


    else:

        decision = "STANDARD"

        new_status = "In Progress"

        action_taken = (
            "Ticket moved to In Progress "
            "for standard support workflow"
        )


    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        UPDATE tickets
        SET status = ?
        WHERE ticket_id = ?
    """, (

        new_status,

        ticket_id

    ))


    conn.commit()

    conn.close()


    return {

        "status": "success",

        "ticket_id": ticket_id,

        "ai_decision": decision,

        "action_taken": action_taken,

        "new_status": new_status

    }


# ============================================================
# PROBLEM SOLVED
# ============================================================

@app.post("/tickets/{ticket_id}/solved")
def mark_ticket_solved(
    ticket_id: str
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        UPDATE tickets
        SET
            status = ?,
            next_action = ?
        WHERE ticket_id = ?
    """, (

        "Resolved",

        "Problem solved by AI-guided troubleshooting",

        ticket_id

    ))


    if cursor.rowcount == 0:

        conn.close()

        raise HTTPException(

            status_code=404,

            detail="Ticket not found"

        )


    conn.commit()

    conn.close()


    return {

        "status": "success",

        "ticket_id": ticket_id,

        "new_status": "Resolved",

        "message":
            "Problem marked as solved"

    }


# ============================================================
# HUMAN ESCALATION
# ============================================================

@app.post("/tickets/{ticket_id}/escalate")
def escalate_ticket(
    ticket_id: str
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM tickets
        WHERE ticket_id = ?
    """, (ticket_id,))


    ticket = cursor.fetchone()


    if ticket is None:

        conn.close()

        raise HTTPException(

            status_code=404,

            detail="Ticket not found"

        )


    ticket = dict(ticket)


    cursor.execute("""
        UPDATE tickets
        SET
            human_escalation = ?,
            status = ?,
            next_action = ?
        WHERE ticket_id = ?
    """, (

        True,

        "In Progress",

        "Escalated to human IT support team",

        ticket_id

    ))


    conn.commit()

    conn.close()


    return {

        "status": "success",

        "ticket_id": ticket_id,

        "escalated": True,

        "new_status": "In Progress",

        "recommended_team":
            ticket["recommended_team"],

        "priority":
            ticket["priority"],

        "issue":
            ticket["issue"],

        "message":
            "Ticket escalated to human IT support."

    }


# ============================================================
# ESCALATED TICKETS
# ============================================================

@app.get("/escalated-tickets")
def get_escalated_tickets():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM tickets
        WHERE human_escalation = 1
           OR status = 'In Progress'
        ORDER BY ROWID DESC
    """)


    tickets = [

        dict(row)

        for row in cursor.fetchall()

    ]


    conn.close()


    return {

        "total": len(tickets),

        "tickets": tickets

    }


# ============================================================
# BA ANALYTICS
# ============================================================

@app.get("/analytics")
def get_analytics():

    conn = get_connection()

    cursor = conn.cursor()


    # TOTAL

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM tickets
    """)

    total_tickets = cursor.fetchone()["total"]


    # OPEN

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE status = 'Open'
    """)

    open_tickets = cursor.fetchone()["total"]


    # IN PROGRESS

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE status = 'In Progress'
    """)

    in_progress_tickets = cursor.fetchone()["total"]


    # RESOLVED

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE status = 'Resolved'
    """)

    resolved_tickets = cursor.fetchone()["total"]


    # CLOSED

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE status = 'Closed'
    """)

    closed_tickets = cursor.fetchone()["total"]


    # HIGH / CRITICAL

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE priority IN ('High', 'Critical')
    """)

    high_critical_tickets = (
        cursor.fetchone()["total"]
    )


    # ESCALATED

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM tickets
        WHERE human_escalation = 1
    """)

    escalated_tickets = (
        cursor.fetchone()["total"]
    )


    # CATEGORY

    cursor.execute("""
        SELECT
            category,
            COUNT(*) AS count
        FROM tickets
        GROUP BY category
        ORDER BY count DESC
    """)

    category_breakdown = [

        dict(row)

        for row in cursor.fetchall()

    ]


    # PRIORITY

    cursor.execute("""
        SELECT
            priority,
            COUNT(*) AS count
        FROM tickets
        GROUP BY priority
        ORDER BY count DESC
    """)

    priority_breakdown = [

        dict(row)

        for row in cursor.fetchall()

    ]


    # TEAM WORKLOAD

    cursor.execute("""
        SELECT
            recommended_team,
            COUNT(*) AS count
        FROM tickets
        GROUP BY recommended_team
        ORDER BY count DESC
    """)

    team_workload = [

        dict(row)

        for row in cursor.fetchall()

    ]


    conn.close()


    return {

        "status": "success",

        "summary": {

            "total_tickets":
                total_tickets,

            "open_tickets":
                open_tickets,

            "in_progress_tickets":
                in_progress_tickets,

            "resolved_tickets":
                resolved_tickets,

            "closed_tickets":
                closed_tickets,

            "high_critical_tickets":
                high_critical_tickets,

            "escalated_tickets":
                escalated_tickets

        },

        "category_breakdown":
            category_breakdown,

        "priority_breakdown":
            priority_breakdown,

        "team_workload":
            team_workload

    }


# ============================================================
# STARTUP MESSAGE
# ============================================================

@app.on_event("startup")
def startup_message():

    print("")
    print("=" * 60)
    print("IT SUPPORT AUTOMATION BACKEND")
    print("=" * 60)
    print(f"Gemini model: {GEMINI_MODEL}")
    print(
        f"Gemini API configured: "
        f"{bool(GEMINI_API_KEY)}"
    )
    print("Dashboard: http://127.0.0.1:8000/dashboard")
    print("AI Test:   http://127.0.0.1:8000/ai-test")
    print("=" * 60)
    print("")