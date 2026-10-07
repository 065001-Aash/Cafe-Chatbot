# Brew & Bite Café: AI Order-Taking Chatbot

**AI Application End Term Project**
Use Case #2: Restaurant / retail order-taking assistant (Chatbot)
Prepared by: **Aash Gupta (065001)**, PGDM (Big Data Analytics), FORE School of Management

**Live website:** _add your Streamlit link here_

---

## What it does

A café website where customers can browse the menu and place an order by chatting with an AI assistant, in English or Hindi.

| Feature | How it works |
|---|---|
| Menu / catalog lookup | 49 items in 8 categories with search, veg-only filter and category buttons |
| Sizes and add-ons | S / M / L for drinks, 7, 10 and 12 inch for pizzas, add-ons like extra shot, oat milk, extra cheese |
| Veg / non-veg | Standard green and brown food marks |
| Order summary with running total | Live bill with quantity buttons, subtotal, 5% GST and total |
| Order confirmation flow | Name and dine-in / takeaway, review screen, confirm, order ID and ready time |
| AI assistant | Google Gemini understands free-text orders, answers menu questions and asks when something is unclear |
| Human handoff | "Talk to staff" button, and automatic handoff for allergies, complaints or repeated confusion |

## How it works

```
Customer message
   -> input check (empty or too long messages are stopped)
   -> Gemini reads the menu, current order and rules, and replies in JSON
   -> Python checks every change against the real menu
      (unknown items, out-of-stock items and wrong add-ons are refused)
   -> Python calculates the bill (the AI never does the maths)
   -> order is placed only after name, order type and confirmation
```

## Guardrails

- The AI can only use items, sizes and prices from `menu.json`.
- Prices and totals are calculated by code, so the AI cannot give discounts or free food.
- Off-topic questions and "ignore your instructions" messages are politely declined.
- Allergy and health questions are passed to staff.
- If Gemini is down, the customer gets a clear message and can still order using Quick add.
- The page tells users they are talking to an AI and that messages are sent to Google.

## Files

| File | Purpose |
|---|---|
| `app.py` | The website (Streamlit) |
| `brain.py` | Chatbot logic: prompt, Gemini call, order checks, bill |
| `menu.json` | Sample data: café details, sizes, add-ons and 49 menu items |
| `requirements.txt` | Python packages needed |
| `Cafe_Chatbot_Builder.ipynb` | Colab notebook used to build and test the chatbot |

## Run it yourself

1. Get a free Gemini API key from Google AI Studio.
2. `pip install -r requirements.txt`
3. Set the key: `GEMINI_API_KEY="your key"` (on Streamlit Cloud: Settings, then Secrets).
4. `streamlit run app.py`

## Tech used

Python, Streamlit, Google Gemini API (google-genai), Google Colab, GitHub, Streamlit Community Cloud.

_Demo project for academic purposes. The café, phone number and email are not real._
