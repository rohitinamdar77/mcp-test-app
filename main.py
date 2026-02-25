"""
NovaPay Credit Card Advisor – MCP Server for ChatGPT
Implements MCP protocol over HTTP (Streamable HTTP / JSON-RPC 2.0)
Deploy on Railway · Connect via ChatGPT MCP settings

NovaPay is a fictional credit card company used for demonstration purposes.

Tools:
  1. search_cards     – filter NovaPay cards by category, annual fee, rewards
  2. get_card_details – full card info, benefits, fees, welcome offer
  3. apply_for_card   – submit a card application and get a reference number
"""

import json
import uuid
import os
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


# ─── NovaPay Card Catalogue ───────────────────────────────────────────────────

CARDS = [
    {
        "id": "nova_obsidian",
        "name": "NovaPay Obsidian Card™",
        "tagline": "The pinnacle of premium — for those who demand the best",
        "tier": "Obsidian",
        "annual_fee": 799,
        "currency": "USD",
        "credit_score_required": "Exceptional (780+)",
        "categories": ["travel", "luxury", "rewards", "concierge"],
        "rewards_rate": {
            "nova_travel_portal": "6x NovaPoints",
            "luxury_hotels": "6x NovaPoints",
            "flights_any_airline": "4x NovaPoints",
            "dining_worldwide": "3x NovaPoints",
            "other_purchases": "1x NovaPoint",
        },
        "welcome_offer": {
            "points": 120000,
            "spend_requirement": 10000,
            "spend_window_months": 6,
            "description": "Earn 120,000 NovaPoints after spending $10,000 in the first 6 months — worth up to $1,500 in travel",
        },
        "points_program": "NovaPoints™",
        "key_benefits": [
            "Up to $400 annual travel credit (flights, hotels, car rentals)",
            "Up to $300 luxury dining credit ($25/month at 5-star restaurants)",
            "Unlimited access to 1,500+ airport lounges via NovaLounge Pass",
            "Dedicated 24/7 Obsidian Concierge service",
            "Global Entry / TSA PreCheck® fee reimbursement ($120)",
            "No foreign transaction fees",
            "Elite status match at 30+ hotel chains",
            "Annual companion flight certificate (economy, domestic)",
            "Cell phone protection up to $1,200/year",
            "Trip cancellation & interruption insurance up to $20,000",
            "Baggage delay reimbursement up to $500",
            "Purchase protection & extended warranty (3 extra years)",
        ],
        "foreign_transaction_fee": 0,
        "apr_range": "20.99%–27.99% variable",
        "intro_apr": None,
        "card_type": "Credit Card",
        "best_for": "Elite travelers and luxury spenders who want maximum perks and concierge service",
    },
    {
        "id": "nova_sapphire",
        "name": "NovaPay Sapphire Reserve™",
        "tagline": "Premium travel rewards with real everyday value",
        "tier": "Sapphire",
        "annual_fee": 395,
        "currency": "USD",
        "credit_score_required": "Excellent (740+)",
        "categories": ["travel", "dining", "rewards"],
        "rewards_rate": {
            "nova_travel_portal": "5x NovaPoints",
            "restaurants_worldwide": "4x NovaPoints",
            "grocery_stores": "3x NovaPoints",
            "streaming_services": "3x NovaPoints",
            "other_purchases": "1x NovaPoint",
        },
        "welcome_offer": {
            "points": 75000,
            "spend_requirement": 5000,
            "spend_window_months": 3,
            "description": "Earn 75,000 NovaPoints after spending $5,000 in the first 3 months — worth up to $1,125 in travel",
        },
        "points_program": "NovaPoints™",
        "key_benefits": [
            "Up to $300 annual travel credit",
            "Up to $150 dining credit ($12.50/month)",
            "Priority Pass™ lounge access (unlimited visits)",
            "Global Entry / TSA PreCheck® credit ($120)",
            "NovaPoints worth 1.5¢ each when redeemed for travel",
            "No foreign transaction fees",
            "Trip delay & cancellation insurance",
            "Primary car rental collision coverage",
            "Baggage insurance plan",
            "Purchase protection & extended warranty",
            "Transfer points to 15+ airline and hotel partners",
        ],
        "foreign_transaction_fee": 0,
        "apr_range": "20.99%–26.99% variable",
        "intro_apr": None,
        "card_type": "Credit Card",
        "best_for": "Frequent travelers who dine out often and want flexible point transfers",
    },
    {
        "id": "nova_gold_plus",
        "name": "NovaPay Gold Plus™",
        "tagline": "Earn big on dining, groceries & everyday life",
        "tier": "Gold",
        "annual_fee": 249,
        "currency": "USD",
        "credit_score_required": "Good–Excellent (700+)",
        "categories": ["dining", "groceries", "travel", "rewards"],
        "rewards_rate": {
            "restaurants_worldwide": "4x NovaPoints",
            "us_grocery_stores": "4x NovaPoints (up to $30k/year)",
            "nova_travel_portal": "3x NovaPoints",
            "other_purchases": "1x NovaPoint",
        },
        "welcome_offer": {
            "points": 60000,
            "spend_requirement": 4000,
            "spend_window_months": 6,
            "description": "Earn 60,000 NovaPoints after spending $4,000 in the first 6 months",
        },
        "points_program": "NovaPoints™",
        "key_benefits": [
            "Up to $120 dining credit annually ($10/month at partner restaurants)",
            "Up to $120 ride-share credit annually ($10/month)",
            "Hotel upgrade credit $75 on stays via NovaPay Travel",
            "No foreign transaction fees",
            "Trip delay insurance",
            "Baggage insurance plan",
            "Purchase protection (90 days, up to $10,000 per claim)",
            "Extended warranty (adds 2 years)",
        ],
        "foreign_transaction_fee": 0,
        "apr_range": "21.49%–28.49% variable",
        "intro_apr": None,
        "card_type": "Credit Card",
        "best_for": "Food lovers and grocery shoppers who want maximum rewards without a huge annual fee",
    },
    {
        "id": "nova_everyday_cash",
        "name": "NovaPay Everyday Cash™",
        "tagline": "Supercharged cash back on what you buy most",
        "tier": "Standard",
        "annual_fee": 95,
        "currency": "USD",
        "credit_score_required": "Good (680+)",
        "categories": ["cashback", "groceries", "gas", "streaming"],
        "rewards_rate": {
            "us_grocery_stores": "5% cash back (up to $8,000/year)",
            "streaming_services": "5% cash back",
            "us_gas_stations": "3% cash back",
            "transit_and_rideshare": "3% cash back",
            "other_purchases": "1.5% cash back",
        },
        "welcome_offer": {
            "points": None,
            "cash_back": 300,
            "spend_requirement": 3000,
            "spend_window_months": 6,
            "description": "Earn $300 cash back after spending $3,000 in the first 6 months",
        },
        "points_program": "Cash Back (statement credit)",
        "key_benefits": [
            "5% cash back at grocery stores and streaming services",
            "3% at gas stations and on transit/rideshare",
            "1.5% on all other purchases — no category cap",
            "0% intro APR for 15 months on purchases",
            "No minimum redemption — cash back redeemed as statement credit",
            "Cell phone protection ($800 per claim, 2 claims/year)",
            "Car rental collision coverage",
            "Purchase protection & return protection",
            "Extended warranty (adds 1 year)",
        ],
        "foreign_transaction_fee": 2.5,
        "apr_range": "19.99%–29.99% variable",
        "intro_apr": "0% for 15 months on purchases",
        "card_type": "Credit Card",
        "best_for": "Households with high grocery, gas, and streaming spend wanting simple, high-rate cash back",
    },
    {
        "id": "nova_zero",
        "name": "NovaPay Zero™",
        "tagline": "Zero fees, zero hassle — real rewards for real life",
        "tier": "Zero",
        "annual_fee": 0,
        "currency": "USD",
        "credit_score_required": "Fair–Good (640+)",
        "categories": ["cashback", "no_annual_fee", "groceries", "gas"],
        "rewards_rate": {
            "us_grocery_stores": "3% cash back (up to $6,000/year)",
            "us_gas_stations": "3% cash back",
            "us_online_shopping": "3% cash back",
            "other_purchases": "1% cash back",
        },
        "welcome_offer": {
            "points": None,
            "cash_back": 200,
            "spend_requirement": 1500,
            "spend_window_months": 6,
            "description": "Earn $200 cash back after spending $1,500 in the first 6 months",
        },
        "points_program": "Cash Back (statement credit)",
        "key_benefits": [
            "No annual fee — ever",
            "3% cash back at groceries, gas, and online shopping",
            "0% intro APR for 18 months on purchases and balance transfers",
            "Free credit score monitoring (FICO® Score updated monthly)",
            "No penalty APR — we won't raise your rate for a late payment",
            "Auto rental collision waiver",
            "Purchase protection (60 days, up to $500 per claim)",
            "24/7 fraud monitoring & $0 fraud liability",
        ],
        "foreign_transaction_fee": 2.5,
        "apr_range": "18.99%–28.99% variable",
        "intro_apr": "0% for 18 months on purchases & balance transfers",
        "card_type": "Credit Card",
        "best_for": "Budget-conscious users or those building credit who want solid rewards with no annual fee",
    },
    {
        "id": "nova_voyage",
        "name": "NovaPay Voyage™",
        "tagline": "Miles that take you further, faster",
        "tier": "Voyage",
        "annual_fee": 175,
        "currency": "USD",
        "credit_score_required": "Good–Excellent (700+)",
        "categories": ["airline", "travel", "rewards", "miles"],
        "rewards_rate": {
            "flights_any_airline": "3x NovaMiles",
            "hotels": "2x NovaMiles",
            "restaurants_worldwide": "2x NovaMiles",
            "other_purchases": "1x NovaMile",
        },
        "welcome_offer": {
            "points": 55000,
            "spend_requirement": 3000,
            "spend_window_months": 3,
            "description": "Earn 55,000 NovaMiles after spending $3,000 in 3 months — enough for a round-trip domestic flight",
        },
        "points_program": "NovaMiles™",
        "key_benefits": [
            "Up to $200 annual airline incidental credit",
            "Free first checked bag on all flights (saves ~$240/yr for 2 travelers)",
            "Priority boarding on partner airlines",
            "No foreign transaction fees",
            "Lounge access via NovaPay Lounge (15 visits/year included)",
            "Transfer NovaMiles to 12 airline partners at 1:1",
            "Trip cancellation/interruption insurance ($7,500 coverage)",
            "Baggage delay insurance (up to $500)",
            "Global Entry / TSA PreCheck® credit",
        ],
        "foreign_transaction_fee": 0,
        "apr_range": "20.49%–27.49% variable",
        "intro_apr": None,
        "card_type": "Credit Card",
        "best_for": "Frequent flyers who want flexible miles redeemable across multiple airlines",
    },
    {
        "id": "nova_student",
        "name": "NovaPay Student Starter™",
        "tagline": "Build credit and earn rewards from day one",
        "tier": "Student",
        "annual_fee": 0,
        "currency": "USD",
        "credit_score_required": "Limited / No credit history required",
        "categories": ["cashback", "no_annual_fee", "student", "starter"],
        "rewards_rate": {
            "restaurants_and_food_delivery": "3% cash back",
            "streaming_services": "3% cash back",
            "bookstores_and_education": "2% cash back",
            "other_purchases": "1% cash back",
        },
        "welcome_offer": {
            "points": None,
            "cash_back": 50,
            "spend_requirement": 500,
            "spend_window_months": 3,
            "description": "Earn $50 cash back after spending $500 in the first 3 months",
        },
        "points_program": "Cash Back (statement credit)",
        "key_benefits": [
            "No annual fee, no foreign transaction fees",
            "No credit history required — designed for first-time cardholders",
            "Good Grade Bonus: $20 cash back each year with GPA 3.0+ (4 years max)",
            "Free credit score monitoring & credit health tips",
            "Automatic credit limit review after 6 months of on-time payments",
            "Fraud protection with $0 liability",
            "Freeze/unfreeze card instantly in the NovaPay app",
            "24/7 customer support via app, chat, or phone",
        ],
        "foreign_transaction_fee": 0,
        "apr_range": "19.99%–24.99% variable",
        "intro_apr": None,
        "card_type": "Credit Card",
        "best_for": "College students and young adults starting their credit journey",
    },
]

# In-memory applications store
applications: dict[str, dict] = {}
CARD_MAP = {c["id"]: c for c in CARDS}


# ─── Tool Logic ───────────────────────────────────────────────────────────────

def tool_search_cards(args: dict) -> dict:
    """Filter and rank NovaPay cards based on user preferences."""
    category    = args.get("category", "").lower()
    max_fee     = args.get("max_annual_fee")
    focus       = args.get("spending_focus", "").lower()
    reward_type = args.get("reward_type", "").lower()

    results = list(CARDS)

    if max_fee is not None:
        results = [c for c in results if c["annual_fee"] <= float(max_fee)]

    if category:
        results = [
            c for c in results
            if any(category in cat for cat in c["categories"])
            or category in c["name"].lower()
            or category in c["best_for"].lower()
            or category in c["tagline"].lower()
        ]

    if reward_type:
        if reward_type in ("cash", "cashback", "cash back"):
            results = [c for c in results if "cashback" in c["categories"] or "Cash Back" in c["points_program"]]
        elif reward_type in ("points", "novapoints"):
            results = [c for c in results if "NovaPoints" in c["points_program"]]
        elif reward_type in ("miles", "novamiles", "airline"):
            results = [c for c in results if "Miles" in c["points_program"] or "airline" in c["categories"]]

    if focus:
        def matches(card):
            return (
                any(focus in k for k in card["rewards_rate"])
                or focus in card["best_for"].lower()
                or focus in card["tagline"].lower()
            )
        results = [c for c in results if matches(c)]

    return {
        "found": len(results),
        "cards": [
            {
                "card_id": c["id"],
                "name": c["name"],
                "tagline": c["tagline"],
                "annual_fee": c["annual_fee"],
                "currency": c["currency"],
                "tier": c["tier"],
                "reward_program": c["points_program"],
                "top_rewards": list(c["rewards_rate"].items())[:3],
                "welcome_offer": c["welcome_offer"]["description"],
                "credit_score_required": c["credit_score_required"],
                "best_for": c["best_for"],
                "card_type": c["card_type"],
            }
            for c in results
        ],
        "message": (
            f"Found {len(results)} NovaPay card(s) matching your criteria."
            if results
            else "No cards matched. Try broadening your search — e.g. increase max_annual_fee or change reward_type."
        ),
    }


def tool_get_card_details(args: dict) -> dict:
    """Return full details for one specific NovaPay card."""
    card_id = args.get("card_id", "")
    card = CARD_MAP.get(card_id)
    if not card:
        return {
            "error": f"Card '{card_id}' not found.",
            "available_card_ids": list(CARD_MAP.keys()),
            "hint": "Use search_cards to find valid card IDs.",
        }
    return card


def tool_apply_for_card(args: dict) -> dict:
    """Submit a NovaPay card application and return a reference number."""
    card_id       = args.get("card_id", "").strip()
    full_name     = args.get("full_name", "").strip()
    email         = args.get("email", "").strip()
    annual_income = args.get("annual_income")
    score_label   = args.get("credit_score_self_reported", "good").strip().lower()
    us_resident   = args.get("us_resident", True)

    if not card_id:
        return {"error": "card_id is required. Use search_cards to find a card."}
    if not full_name:
        return {"error": "full_name is required."}
    if not email or "@" not in email:
        return {"error": "A valid email address is required."}
    if not us_resident:
        return {"error": "NovaPay cards are currently available to U.S. residents only."}

    card = CARD_MAP.get(card_id)
    if not card:
        return {"error": f"Card '{card_id}' not found. Use search_cards to find valid card IDs."}

    # Eligibility heuristic
    score_map = {"poor": 500, "fair": 590, "good": 670, "very good": 720, "excellent": 760, "exceptional": 800}
    applicant_score = score_map.get(score_label, 670)

    req = card["credit_score_required"].lower()
    if "780" in req or "exceptional" in req:
        required_min = 780
    elif "740" in req or "excellent" in req:
        required_min = 740
    elif "700" in req:
        required_min = 700
    elif "680" in req:
        required_min = 680
    elif "640" in req or "limited" in req or "no credit" in req:
        required_min = 0
    else:
        required_min = 640

    status       = "APPROVED" if applicant_score >= required_min else "PENDING_REVIEW"
    status_emoji = "✅" if status == "APPROVED" else "⏳"
    first_name   = full_name.split()[0]

    app_id = f"NP-{uuid.uuid4().hex[:10].upper()}"
    application = {
        "application_id": app_id,
        "status": f"{status} {status_emoji}",
        "card_applied": {
            "id": card["id"],
            "name": card["name"],
            "annual_fee": card["annual_fee"],
            "tier": card["tier"],
        },
        "applicant": {
            "name": full_name,
            "email": email,
            "annual_income": annual_income,
            "credit_score_self_reported": score_label,
        },
        "submitted_at": datetime.utcnow().isoformat() + "Z",
        "next_steps": (
            f"🎉 Congratulations, {first_name}! Your {card['name']} application is approved. "
            f"Your card will arrive in 5–7 business days. Welcome offer: {card['welcome_offer']['description']}. "
            f"Reference: {app_id}"
        ) if status == "APPROVED" else (
            f"Your application is under review, {first_name}. You'll receive a decision at {email} "
            f"within 7–10 business days. Reference: {app_id}"
        ),
        "welcome_offer": card["welcome_offer"]["description"],
        "estimated_card_arrival": "5–7 business days (if approved)",
        "disclaimer": (
            "This is a demonstration application for NovaPay, a fictional card company. "
            "No real credit check or financial transaction occurs."
        ),
    }

    applications[app_id] = application
    return application


# ─── MCP Tool Registry ────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "search_cards",
        "description": (
            "Search and filter NovaPay credit cards by category, annual fee, reward type, "
            "and spending focus. Returns a list of matching cards with welcome offers, fees, "
            "and top rewards rates. Best first tool to call when comparing or recommending cards."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": (
                        "Card category: 'travel', 'dining', 'groceries', 'cashback', "
                        "'airline', 'miles', 'no_annual_fee', 'luxury', 'student', 'starter'"
                    ),
                },
                "max_annual_fee": {
                    "type": "number",
                    "description": "Maximum annual fee in USD (use 0 for no-fee cards)",
                },
                "spending_focus": {
                    "type": "string",
                    "description": (
                        "Where the user spends most: 'restaurants', 'grocery', 'flights', "
                        "'hotels', 'streaming', 'gas', 'transit', 'online shopping', 'education'"
                    ),
                },
                "reward_type": {
                    "type": "string",
                    "description": "Reward preference: 'cashback', 'points' (NovaPoints), or 'miles' (NovaMiles)",
                },
            },
            "required": [],
        },
        "handler": tool_search_cards,
    },
    {
        "name": "get_card_details",
        "description": (
            "Get complete details for a specific NovaPay card: all benefits, full rewards breakdown, "
            "welcome offer, APR, foreign transaction fee, and eligibility. "
            "Call this after search_cards before making a recommendation or starting an application."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "card_id": {
                    "type": "string",
                    "description": (
                        "Card ID from search_cards. Options: "
                        "nova_obsidian, nova_sapphire, nova_gold_plus, nova_everyday_cash, "
                        "nova_zero, nova_voyage, nova_student"
                    ),
                },
            },
            "required": ["card_id"],
        },
        "handler": tool_get_card_details,
    },
    {
        "name": "apply_for_card",
        "description": (
            "Submit a NovaPay card application for the user. Collects name, email, income, "
            "and self-reported credit score. Returns a reference number and instant decision. "
            "Always confirm the card choice with get_card_details before calling this tool."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "card_id":      {"type": "string", "description": "Card ID to apply for"},
                "full_name":    {"type": "string", "description": "Applicant's full legal name"},
                "email":        {"type": "string", "description": "Email for confirmation and decision"},
                "annual_income":{"type": "number", "description": "Annual income in USD"},
                "credit_score_self_reported": {
                    "type": "string",
                    "description": "Credit range: 'poor', 'fair', 'good', 'very good', 'excellent', 'exceptional'",
                },
                "us_resident":  {"type": "boolean", "description": "Must be true — NovaPay requires U.S. residency"},
            },
            "required": ["card_id", "full_name", "email"],
        },
        "handler": tool_apply_for_card,
    },
]

TOOL_MAP = {t["name"]: t for t in TOOLS}


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(title="NovaPay Card Advisor MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Connect Screen ───────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def connect_screen():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>NovaPay Card Advisor – MCP for ChatGPT</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(145deg, #07050f 0%, #120a2e 50%, #05100f 100%);
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    padding: 24px;
  }

  .panel {
    background: #f8f8f6;
    border-radius: 26px;
    padding: 46px 42px 38px;
    max-width: 510px; width: 100%;
    box-shadow: 0 50px 130px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.05);
    position: relative; overflow: hidden;
  }
  .panel::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 5px;
    background: linear-gradient(90deg, #7C3AED, #2563EB, #06B6D4, #10B981, #7C3AED);
    background-size: 300%; animation: glide 5s linear infinite;
  }
  @keyframes glide { to { background-position: 300% 0; } }

  /* ── Logo ── */
  .header { display: flex; align-items: center; gap: 16px; margin-bottom: 8px; }
  .logo-mark {
    width: 62px; height: 62px; flex-shrink: 0; border-radius: 18px;
    background: linear-gradient(145deg, #7C3AED 0%, #2563EB 100%);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    box-shadow: 0 6px 20px rgba(124,58,237,0.45);
  }
  .logo-mark .symbol { font-size: 26px; line-height: 1; }
  .logo-mark .wordmark { font-size: 8px; font-weight: 800; color: rgba(255,255,255,0.75); letter-spacing: 2px; margin-top: 3px; }
  .brand h1 { font-size: 28px; font-weight: 800; color: #1e1060; letter-spacing: -0.5px; }
  .brand p  { font-size: 13px; color: #777; margin-top: 3px; }

  /* ── Live badge ── */
  .live-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0;
    border-radius: 20px; padding: 5px 14px;
    font-size: 12px; font-weight: 600; margin: 20px 0 26px;
  }
  .dot { width: 8px; height: 8px; background: #16a34a; border-radius: 50%; animation: blink 2s ease-in-out infinite; }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

  /* ── Card preview strip ── */
  .strip { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 6px; margin-bottom: 30px; scrollbar-width: none; }
  .strip::-webkit-scrollbar { display: none; }

  .mc {
    flex-shrink: 0; width: 132px; height: 80px;
    border-radius: 10px; padding: 10px 12px;
    display: flex; flex-direction: column; justify-content: space-between;
    box-shadow: 0 6px 20px rgba(0,0,0,0.28);
    transition: transform .2s, box-shadow .2s; cursor: default;
  }
  .mc:hover { transform: translateY(-4px) rotate(-1deg); box-shadow: 0 14px 34px rgba(0,0,0,0.38); }
  .mc-top { display: flex; justify-content: space-between; align-items: center; }
  .chip-icon { width: 18px; height: 14px; background: rgba(255,255,255,0.25); border-radius: 3px; }
  .tap-icon  { font-size: 13px; color: rgba(255,255,255,0.35); }
  .mc-name { font-size: 9.5px; font-weight: 700; color: rgba(255,255,255,.92); line-height: 1.2; }
  .mc-sub  { font-size: 8px; color: rgba(255,255,255,.55); margin-top: 2px; }

  /* card color themes */
  .c-obsidian { background: linear-gradient(135deg, #1c1c1e 0%, #3a3a40 50%, #1c1c1e 100%); }
  .c-sapphire { background: linear-gradient(135deg, #1d4ed8 0%, #7c3aed 100%); }
  .c-gold     { background: linear-gradient(135deg, #b45309 0%, #d97706 50%, #92400e 100%); }
  .c-cash     { background: linear-gradient(135deg, #065f46 0%, #059669 100%); }
  .c-zero     { background: linear-gradient(135deg, #374151 0%, #6b7280 100%); }
  .c-voyage   { background: linear-gradient(135deg, #0c4a6e 0%, #0284c7 100%); }
  .c-student  { background: linear-gradient(135deg, #5b21b6 0%, #8b5cf6 100%); }

  /* ── Feature grid ── */
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 26px; }
  .feat { background: #f2f2ef; border: 1px solid #e2e2dc; border-radius: 13px; padding: 14px 12px; }
  .feat-icon  { font-size: 22px; margin-bottom: 5px; }
  .feat-title { font-size: 12px; font-weight: 700; color: #1e1060; }
  .feat-desc  { font-size: 11px; color: #777; margin-top: 2px; line-height: 1.45; }

  /* ── Prompt chips ── */
  .prompts { margin-bottom: 26px; }
  .p-label { font-size: 10px; font-weight: 700; color: #aaa; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
  .chip {
    display: inline-block; background: white;
    border: 1px solid #dde; border-radius: 20px;
    padding: 5px 12px; font-size: 11px; color: #555;
    margin: 3px 3px 0 0;
  }

  /* ── Endpoint box ── */
  .ep-box {
    background: linear-gradient(135deg, #eef2ff, #f5f3ff);
    border: 1px solid #c7d2fe;
    border-radius: 13px; padding: 13px 16px; margin-bottom: 18px;
  }
  .ep-label { font-size: 10px; font-weight: 700; color: #4f46e5; letter-spacing: 1px; text-transform: uppercase; }
  .ep-url   { font-size: 13px; color: #1e1060; font-weight: 600; margin-top: 5px; word-break: break-all; }

  /* ── CTA ── */
  .cta {
    display: block; width: 100%;
    background: linear-gradient(135deg, #7C3AED 0%, #2563EB 100%);
    color: white; border: none; border-radius: 13px;
    padding: 16px; font-size: 15px; font-weight: 700;
    text-align: center; text-decoration: none;
    transition: transform .15s, box-shadow .15s; margin-bottom: 14px;
    box-shadow: 0 4px 16px rgba(124,58,237,0.3);
  }
  .cta:hover { transform: translateY(-2px); box-shadow: 0 12px 32px rgba(124,58,237,0.45); }

  .meta { font-size: 11px; color: #bbb; text-align: center; line-height: 1.7; }
  .np-tag { color: #7C3AED; font-weight: 700; }
</style>
</head>
<body>
<div class="panel">

  <!-- Header -->
  <div class="header">
    <div class="logo-mark">
      <div class="symbol">◈</div>
      <div class="wordmark">NOVAPAY</div>
    </div>
    <div class="brand">
      <h1>NovaPay Advisor</h1>
      <p>AI-powered card selection for ChatGPT</p>
    </div>
  </div>

  <div class="live-badge"><span class="dot"></span> MCP Server – Ready to Connect</div>

  <!-- Card strip -->
  <div class="strip">
    <div class="mc c-obsidian">
      <div class="mc-top"><div class="chip-icon"></div><div class="tap-icon">◎</div></div>
      <div><div class="mc-name">Obsidian Card™</div><div class="mc-sub">$799/yr · 6x Travel</div></div>
    </div>
    <div class="mc c-sapphire">
      <div class="mc-top"><div class="chip-icon"></div><div class="tap-icon">◎</div></div>
      <div><div class="mc-name">Sapphire Reserve™</div><div class="mc-sub">$395/yr · 5x Portal</div></div>
    </div>
    <div class="mc c-gold">
      <div class="mc-top"><div class="chip-icon"></div><div class="tap-icon">◎</div></div>
      <div><div class="mc-name">Gold Plus™</div><div class="mc-sub">$249/yr · 4x Dining</div></div>
    </div>
    <div class="mc c-cash">
      <div class="mc-top"><div class="chip-icon"></div><div class="tap-icon">◎</div></div>
      <div><div class="mc-name">Everyday Cash™</div><div class="mc-sub">$95/yr · 5% Groceries</div></div>
    </div>
    <div class="mc c-zero">
      <div class="mc-top"><div class="chip-icon"></div><div class="tap-icon">◎</div></div>
      <div><div class="mc-name">Zero™</div><div class="mc-sub">$0/yr · 3% Cash Back</div></div>
    </div>
    <div class="mc c-voyage">
      <div class="mc-top"><div class="chip-icon"></div><div class="tap-icon">◎</div></div>
      <div><div class="mc-name">Voyage™</div><div class="mc-sub">$175/yr · 3x Miles</div></div>
    </div>
    <div class="mc c-student">
      <div class="mc-top"><div class="chip-icon"></div><div class="tap-icon">◎</div></div>
      <div><div class="mc-name">Student Starter™</div><div class="mc-sub">$0/yr · Build Credit</div></div>
    </div>
  </div>

  <!-- Feature grid -->
  <div class="grid">
    <div class="feat">
      <div class="feat-icon">🔍</div>
      <div class="feat-title">Smart Search</div>
      <div class="feat-desc">Filter by fee, category, rewards & credit score</div>
    </div>
    <div class="feat">
      <div class="feat-icon">💳</div>
      <div class="feat-title">Full Details</div>
      <div class="feat-desc">Every benefit, APR, fee & welcome offer</div>
    </div>
    <div class="feat">
      <div class="feat-icon">✍️</div>
      <div class="feat-title">Apply In Chat</div>
      <div class="feat-desc">Submit application & get instant decision</div>
    </div>
    <div class="feat">
      <div class="feat-icon">📊</div>
      <div class="feat-title">7 Cards</div>
      <div class="feat-desc">Obsidian, Sapphire, Gold, Cash, Zero, Voyage, Student</div>
    </div>
  </div>

  <!-- Sample prompts -->
  <div class="prompts">
    <div class="p-label">Try asking ChatGPT</div>
    <span class="chip">"Best NovaPay card for dining"</span>
    <span class="chip">"Cards with no annual fee"</span>
    <span class="chip">"Compare Obsidian vs Sapphire"</span>
    <span class="chip">"Best cashback card under $100/yr"</span>
    <span class="chip">"Apply for the Gold Plus"</span>
    <span class="chip">"Card for a college student"</span>
    <span class="chip">"Best card for flights"</span>
  </div>

  <!-- Endpoint -->
  <div class="ep-box">
    <div class="ep-label">MCP Endpoint — paste into ChatGPT</div>
    <div class="ep-url" id="ep">Loading…</div>
  </div>

  <a class="cta" href="/mcp" target="_blank">🔗 Verify MCP Endpoint</a>

  <div class="meta">
    3 tools &nbsp;·&nbsp; 7 cards &nbsp;·&nbsp; No auth required &nbsp;·&nbsp; JSON-RPC 2.0 over HTTP
    <br><span class="np-tag">NovaPay</span> is a fictional company for demonstration purposes only.
  </div>
</div>
<script>document.getElementById('ep').textContent = location.origin + '/mcp';</script>
</body>
</html>"""
    return HTMLResponse(content=html)


# ─── MCP over HTTP ────────────────────────────────────────────────────────────

@app.get("/mcp")
async def mcp_info():
    return {
        "name": "NovaPay Card Advisor",
        "version": "1.0.0",
        "description": "NovaPay (fictional) credit card search, comparison, and application MCP server",
        "tools": [t["name"] for t in TOOLS],
        "card_count": len(CARDS),
        "transport": "Streamable HTTP (JSON-RPC 2.0)",
        "mcp_endpoint": "/mcp",
    }


@app.post("/mcp")
async def mcp_handler(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    method = body.get("method")
    req_id = body.get("id")
    params = body.get("params", {})

    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "novapay-card-advisor", "version": "1.0.0"},
            },
        })

    if method == "notifications/initialized":
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {}})

    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "tools": [
                    {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
                    for t in TOOLS
                ]
            },
        })

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if tool_name not in TOOL_MAP:
            return JSONResponse({
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Tool '{tool_name}' not found."},
            })
        try:
            result   = TOOL_MAP[tool_name]["handler"](arguments)
            content  = json.dumps(result, indent=2, ensure_ascii=False)
            is_error = isinstance(result, dict) and "error" in result
        except Exception as exc:
            content  = json.dumps({"error": str(exc)})
            is_error = True
        return JSONResponse({
            "jsonrpc": "2.0", "id": req_id,
            "result": {"content": [{"type": "text", "text": content}], "isError": is_error},
        })

    return JSONResponse({
        "jsonrpc": "2.0", "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' not supported."},
    })


# ─── REST helpers ─────────────────────────────────────────────────────────────

@app.get("/api/cards")
async def api_list(category: str = "", max_fee: float = 9999):
    return tool_search_cards({"category": category, "max_annual_fee": max_fee})

@app.get("/api/cards/{card_id}")
async def api_detail(card_id: str):
    result = tool_get_card_details({"card_id": card_id})
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/applications/{app_id}")
async def api_application(app_id: str):
    app = applications.get(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@app.get("/health")
async def health():
    return {"status": "ok", "cards": len(CARDS), "applications": len(applications)}


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n◈  NovaPay Card Advisor MCP Server")
    print(f"   Connect screen : http://0.0.0.0:{port}/")
    print(f"   MCP endpoint   : http://0.0.0.0:{port}/mcp")
    print(f"   REST cards     : http://0.0.0.0:{port}/api/cards")
    print(f"   Health         : http://0.0.0.0:{port}/health\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
