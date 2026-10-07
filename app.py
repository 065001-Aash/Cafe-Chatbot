"""
app.py : the website (built with Streamlit).
Run locally with:  streamlit run app.py
On Streamlit Cloud, put your key in Settings > Secrets as:  GEMINI_API_KEY = "your key"
"""

import html
import os
import time

import streamlit as st

from brain import (MAX_MSG_CHARS, GeminiWaiter, apply_actions, bill, categories, get_item,
                   load_menu, new_state, order_placed_text, place_order, process_turn)

# Café colours for Streamlit's own buttons, inputs and background
for key, value in {"theme.base": "light", "theme.primaryColor": "#8A4B14", "theme.backgroundColor": "#E4DFD5",
                   "theme.secondaryBackgroundColor": "#EEEAE2", "theme.textColor": "#23211C"}.items():
    try:
        st._config.set_option(key, value)
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
MENU = load_menu(os.path.join(HERE, "menu.json"))
CAFE = MENU["cafe"]
MAX_MESSAGES_PER_VISIT = 60      # protects the free API quota from misuse
E = html.escape
BOT_AVATAR, USER_AVATAR = ":material/local_cafe:", ":material/person:"

st.set_page_config(page_title=f"{CAFE['name']} | Coffee and comfort food", page_icon=":material/local_cafe:", layout="wide")

# ---------------------------------------------------------------- look and feel
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Oswald:wght@500;600&family=Manrope:wght@400;500;600;700&display=swap');
:root {--stone:#E4DFD5; --panel:#EEEAE2; --line:#CFC8BB; --ink:#23211C; --soft:#5F5A50; --caramel:#8A4B14; --caramel-dark:#6E3B0F;}
.stApp {background: var(--stone);}
.block-container {max-width: 1180px; padding-top: 1.2rem;}
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button p {font-family: 'Manrope', sans-serif;}
[data-testid="stHeader"] {background: transparent;}

/* top navigation */
.nav {display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--line);
      border-radius: 14px; padding: 12px 22px; background: var(--panel);}
.nav .logo {font-family: 'Anton', sans-serif; font-size: 1.45rem; color: var(--ink); letter-spacing: .5px;}
.nav .links a {font-family: 'Oswald', sans-serif; color: var(--caramel); text-decoration: none; font-weight: 600;
               letter-spacing: 1.5px; margin-left: 26px; font-size: .95rem;}

/* hero */
.hero {border: 1px solid var(--line); border-radius: 18px; padding: 70px 30px 60px; margin-top: 12px;
       text-align: center; background: var(--panel);}
.hero h1 {font-family: 'Anton', sans-serif !important; font-weight: 400 !important; color: var(--ink);
          font-size: clamp(3.2rem, 9vw, 6.6rem); line-height: .98; margin: 0; padding: 0; letter-spacing: -.5px;}
.hero p {max-width: 560px; margin: 22px auto 26px; color: var(--soft); font-size: 1.05rem; line-height: 1.6;}
.btn {display: inline-block; background: var(--caramel); color: #fff !important; text-decoration: none !important;
      font-family: 'Oswald', sans-serif; letter-spacing: 1.2px; padding: 11px 24px; border-radius: 9px; font-weight: 500;}
.btn:hover {background: var(--caramel-dark);}

/* about + contact row */
.duo {display: grid; grid-template-columns: 1fr 1.25fr; gap: 12px; margin-top: 12px;}
.box {border: 1px solid var(--line); border-radius: 14px; padding: 24px; background: var(--panel); color: var(--ink);}
.box.about {text-align: center;}
.box.about p {color: var(--soft); max-width: 330px; margin: 0 auto 10px; line-height: 1.6;}
.box.about .city {font-weight: 700; font-size: 1.1rem; margin-bottom: 14px;}
.contact {width: 100%; border-collapse: collapse;}
.contact td {border: none; border-bottom: 1px solid var(--line); padding: 10px 2px; font-size: .95rem;}
.contact td:first-child {font-family: 'Oswald', sans-serif; letter-spacing: 1.2px; color: var(--ink);}
.contact td:last-child {text-align: right; color: var(--caramel); font-weight: 600;}

/* section titles */
.sec {font-family: 'Anton', sans-serif; font-size: 2.6rem; color: var(--ink); margin: 46px 0 2px; letter-spacing: .5px;}
.sec-sub {color: var(--soft); margin-bottom: 14px;}

/* printed menu */
.mcat {margin-bottom: 26px;}
.mcat-h {display: inline-block; font-family: 'Oswald', sans-serif; letter-spacing: 1.8px; font-weight: 600; font-size: 1.02rem;
         background: var(--ink); color: var(--stone); padding: 2px 10px; margin-bottom: 10px;}
.mrow {display: flex; align-items: baseline; gap: 8px; margin-top: 9px;}
.mname {font-weight: 700; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.dots {flex: 1; border-bottom: 1.5px dotted #A79F90; transform: translateY(-4px); min-width: 20px;}
.mprice {font-weight: 700; color: var(--ink); white-space: nowrap; font-size: .95rem;}
.mdesc {font-size: .85rem; color: var(--soft); margin: 1px 0 0 23px;}
.best {font-size: .68rem; font-weight: 700; color: var(--caramel); border: 1px solid var(--caramel); border-radius: 999px;
       padding: 0 6px; margin-left: 6px; vertical-align: 1px;}
.oos {color: #A3261E; font-weight: 700; font-size: .78rem; margin-left: 6px;}
.out .mname, .out .mprice {text-decoration: line-through; opacity: .55;}

/* veg / non-veg symbols (standard Indian food marks) */
.vm, .nv {display: inline-block; width: 14px; height: 14px; border: 2px solid; border-radius: 2px; position: relative;
          vertical-align: -2px; margin-right: 8px; background: #fff;}
.vm {border-color: #1E8E3E;} .nv {border-color: #8B3A1E;}
.vm:after {content: ""; position: absolute; width: 6px; height: 6px; border-radius: 50%; background: #1E8E3E; top: 2px; left: 2px;}
.nv:after {content: ""; position: absolute; top: 2px; left: 1px; border-left: 4px solid transparent;
           border-right: 4px solid transparent; border-bottom: 7px solid #8B3A1E;}

/* order panel */
.panel-h {font-family: 'Oswald', sans-serif; letter-spacing: 1.6px; font-weight: 600; font-size: 1.1rem; color: var(--ink); margin: 2px 0 8px;}
.sum {width: 100%; border-collapse: collapse; margin: 0; border: none !important;}
.sum tr, .sum td {border: none !important; background: transparent !important; color: var(--ink);}
.sum td {padding: 3px 0 !important;}
.sum td.r {text-align: right;}
.sum tr.tot td {font-weight: 800; font-size: 1.2rem; padding-top: 8px !important; border-top: 1px solid var(--line) !important;}
.muted {color: var(--soft); font-size: .9rem;}
.oid {font-family: 'Anton', sans-serif; font-size: 2.1rem; color: var(--caramel); letter-spacing: .5px; line-height: 1.1;}
.tag-ok {display: inline-block; font-family: 'Oswald', sans-serif; letter-spacing: 1.4px; background: var(--ink); color: var(--stone);
         padding: 2px 10px; font-size: .85rem;}
.ai-note {font-size: .8rem; color: var(--soft); margin-top: 6px;}
.foot {border-top: 1px solid var(--line); margin-top: 50px; padding: 18px 0 6px; display: flex; justify-content: space-between;
       flex-wrap: wrap; gap: 10px; color: var(--soft); font-size: .88rem;}
.foot b {font-family: 'Anton', sans-serif; font-weight: 400; color: var(--ink); font-size: 1.1rem; letter-spacing: .5px;}

/* Streamlit containers in the café style */
[data-testid="stVerticalBlockBorderWrapper"] {border-color: var(--line) !important; border-radius: 14px !important; background: var(--panel);}
.stButton button[kind="primary"] {font-family: 'Oswald', sans-serif; letter-spacing: 1.2px;}

@media (max-width: 760px) {
  .duo {grid-template-columns: 1fr;}
  .nav {padding: 10px 14px;}
  .nav .logo {font-size: 1.1rem;}
  .nav .links a {margin-left: 10px; font-size: .8rem; letter-spacing: 1px;}
  .hero {padding: 46px 18px 40px;}
  .sec {font-size: 2rem;}
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- setup
def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.environ.get("GEMINI_API_KEY")


def get_model_override():
    try:
        return st.secrets.get("GEMINI_MODEL")
    except Exception:
        return None


@st.cache_resource
def get_waiter(api_key, model):
    return GeminiWaiter(api_key, MENU, model)


if "state" not in st.session_state:
    st.session_state.state = new_state()
    st.session_state.last_msg, st.session_state.last_time = None, 0.0
S = st.session_state.state

API_KEY = get_api_key()
waiter = get_waiter(API_KEY, get_model_override()) if API_KEY else None


def money(x):
    return f"₹{x:,}"


def price_text(item):
    if not item["sizes"]:
        return money(item["price"])
    return " · ".join(f"{MENU['sizes'][s]['short']} {money(item['price'] + MENU['sizes'][s]['extra'])}" for s in item["sizes"])


# ---------------------------------------------------------------- button actions (no AI needed)
def quick_add():
    S = st.session_state.state
    item = get_item(MENU, st.session_state.qa_item)
    size = st.session_state.get(f"qa_size_{item['id']}") if item["sizes"] else None
    qty = st.session_state.get("qa_qty", 1)
    S["cart"], notes = apply_actions(MENU, S["cart"], [{"op": "add", "item_id": item["id"], "qty": qty, "size": size}])
    size_txt = f" ({MENU['sizes'][size]['name']})" if size else ""
    st.toast(f"Added {qty} × {item['name']}{size_txt}" + ("" if not notes else ". " + " ".join(notes)))


def change_qty(line_no, delta):
    S = st.session_state.state
    qty = S["cart"][line_no - 1]["qty"] + delta
    S["cart"], _ = apply_actions(MENU, S["cart"], [{"op": "update_qty", "line": line_no, "qty": qty}])


def save_details():
    S = st.session_state.state
    S["customer_name"] = (st.session_state.get("cust_name") or "").strip()[:40] or None
    S["order_type"] = {"Dine-in": "dine-in", "Takeaway": "takeaway"}.get(st.session_state.get("cust_type"))


def reset_order():
    st.session_state.state = new_state()
    for k in ("cust_name", "cust_type"):
        st.session_state.pop(k, None)


def call_staff():
    st.session_state.state["handoff"] = True


def ask(text):
    st.session_state.pending = text


@st.dialog("Confirm your order")
def confirm_dialog():
    S = st.session_state.state
    b = bill(MENU, S["cart"])
    rows = "".join(f"<tr><td>{r['qty']} × {E(r['item'])}</td><td class='r'>{money(r['amount'])}</td></tr>" for r in b["rows"])
    st.markdown(f"""<table class="sum">{rows}
        <tr><td class="muted">Subtotal</td><td class="r muted">{money(b['subtotal'])}</td></tr>
        <tr><td class="muted">GST {CAFE['gst_percent']}%</td><td class="r muted">{money(b['gst'])}</td></tr>
        <tr class="tot"><td>Total</td><td class="r">{money(b['total'])}</td></tr></table>""", unsafe_allow_html=True)
    st.write(f"Name: **{S['customer_name']}** · {S['order_type'].title()} · Pay at the counter")
    c1, c2 = st.columns(2)
    if c1.button("Confirm order", type="primary", use_container_width=True):
        if not S["order"]:                                   # protects against a double click
            S["order"] = place_order(MENU, S)
            S["messages"].append({"role": "assistant", "content": order_placed_text(S["order"])})
        st.rerun()
    if c2.button("Go back", use_container_width=True):
        st.rerun()


# ---------------------------------------------------------------- page top: nav, hero, about, contact
st.markdown(f"""
<div class="nav"><div class="logo">{E(CAFE['name'].upper())}</div>
  <div class="links"><a href="#menu">MENU</a><a href="#order">ORDER</a><a href="#visit">VISIT</a></div></div>
<div class="hero">
  <h1>Coffee &amp;<br>Comfort Food</h1>
  <p>{E(CAFE['name'])} in Sector 18, {E(CAFE['city'])} serves specialty coffee, cool mocktails, pizzas and desserts.
     Order in seconds by chatting with our assistant, in English or Hindi.</p>
  <a class="btn" href="#order">ORDER NOW</a>
</div>
<div class="duo" id="visit">
  <div class="box about"><p>Freshly brewed coffee and comfort food, made to order by our baristas and chefs every day.</p>
    <div class="city">Sector 18, {E(CAFE['city'])}.</div><a class="btn" href="#menu">SEE THE MENU</a></div>
  <div class="box"><table class="contact">
    <tr><td>CALL</td><td>{E(CAFE['phone'])}</td></tr>
    <tr><td>MAIL</td><td>{E(CAFE['email'])}</td></tr>
    <tr><td>IG</td><td>{E(CAFE['instagram'])}</td></tr>
    <tr><td>HOURS</td><td>{E(CAFE['hours'])}</td></tr></table></div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- menu (lookup)
st.markdown("<div class='sec' id='menu'>OUR MENU</div><div class='sec-sub'>Prices in rupees. S, M, L are drink sizes; pizzas come in 7, 10 and 12 inch.</div>",
            unsafe_allow_html=True)
f1, f2 = st.columns([3, 1], vertical_alignment="center")
query = f1.text_input("Search the menu", placeholder="Search: latte, pizza, shake...", label_visibility="collapsed")
veg_only = f2.toggle("Veg only")
cats = categories(MENU)
chosen = st.pills("Category", ["All"] + cats, default="All", label_visibility="collapsed") or "All"
shown = [i for i in MENU["items"]
         if (chosen == "All" or i["category"] == chosen) and (not veg_only or i["veg"])
         and (not query or query.lower() in (i["name"] + " " + i["desc"] + " " + i["category"]).lower())]


def category_html(cat):
    rows = []
    for it in [i for i in shown if i["category"] == cat]:
        mark = "vm" if it["veg"] else "nv"
        best = "<span class='best'>BESTSELLER</span>" if it.get("popular") else ""
        out = "" if it["available"] else "<span class='oos'>Out of stock today</span>"
        rows.append(f"<div class='{'' if it['available'] else 'out'}'><div class='mrow'><span class='mname'><span class='{mark}'></span>"
                    f"{E(it['name'])}</span>{best}<span class='dots'></span><span class='mprice'>{price_text(it)}</span></div>"
                    f"<div class='mdesc'>{E(it['desc'])}{out}</div></div>")
    return f"<div class='mcat'><div class='mcat-h'>{E(cat.upper())}</div>{''.join(rows)}</div>"


if not shown:
    st.info("No items match your search. Try another word or clear the filters.")
else:
    with st.container(border=True):
        left, right = st.columns(2, gap="large")
        shown_cats = [c for c in cats if any(i["category"] == c for i in shown)]
        half = (len(shown) + 1) // 2
        count, left_html, right_html = 0, "", ""
        for c in shown_cats:                         # fill the left column first, then the right
            n = sum(1 for i in shown if i["category"] == c)
            if count < half or not left_html:
                left_html += category_html(c)
            else:
                right_html += category_html(c)
            count += n
        left.markdown(left_html, unsafe_allow_html=True)
        right.markdown(right_html, unsafe_allow_html=True)

# ---------------------------------------------------------------- ordering: chat + order panel
st.markdown("<div class='sec' id='order'>ORDER WITH OUR ASSISTANT</div>"
            "<div class='sec-sub'>Tell the assistant what you'd like, or add items yourself on the right.</div>", unsafe_allow_html=True)
chat_col, order_col = st.columns([1.6, 1], gap="medium")

with order_col:
    with st.container(border=True):
        if S["order"]:
            o = S["order"]
            rows = "".join(f"<tr><td>{r['qty']} × {E(r['item'])}</td><td class='r'>{money(r['amount'])}</td></tr>"
                           for r in o["bill"]["rows"])
            st.markdown(f"""<span class="tag-ok">ORDER CONFIRMED</span><div class="oid">{o['order_id']}</div>
              <div class="muted">{E(o['name'])} · {o['type'].title()} · {o['time']}</div>
              <table class="sum">{rows}<tr class="tot"><td>Pay at counter</td><td class="r">{money(o['bill']['total'])}</td></tr></table>
              <div class="muted">Ready in about {o['eta_min']} minutes.</div>""", unsafe_allow_html=True)
            st.button("Start a new order", on_click=reset_order, use_container_width=True, type="primary")
        else:
            st.markdown("<div class='panel-h'>QUICK ADD</div>", unsafe_allow_html=True)
            avail = [i for i in MENU["items"] if i["available"]]
            st.selectbox("Item", [i["id"] for i in avail], key="qa_item", label_visibility="collapsed",
                         format_func=lambda x: f"{get_item(MENU, x)['name']}  ({get_item(MENU, x)['category']})")
            sel = get_item(MENU, st.session_state.qa_item)
            q1, q2 = st.columns([2, 1])
            if sel["sizes"]:
                q1.selectbox("Size", sel["sizes"], key=f"qa_size_{sel['id']}", label_visibility="collapsed",
                             format_func=lambda s: f"{MENU['sizes'][s]['name']}  {money(sel['price'] + MENU['sizes'][s]['extra'])}")
            else:
                q1.markdown(f"<div class='muted' style='padding-top:8px'>One size · {money(sel['price'])}</div>", unsafe_allow_html=True)
            q2.number_input("Qty", min_value=1, max_value=20, value=1, key="qa_qty", label_visibility="collapsed")
            st.button("Add to order", on_click=quick_add, use_container_width=True)

            st.markdown("<div class='panel-h' style='margin-top:14px'>YOUR ORDER</div>", unsafe_allow_html=True)
            if not S["cart"]:
                st.markdown("<div class='muted'>Nothing added yet.</div>", unsafe_allow_html=True)
            else:
                b = bill(MENU, S["cart"])
                for r in b["rows"]:
                    c1, c2, c3, c4 = st.columns([5, 1.1, 1.1, 2], vertical_alignment="center")
                    c1.markdown(f"**{r['qty']} ×** {E(r['item'])}")
                    c2.button("", icon=":material/remove:", key=f"minus_{r['line']}", on_click=change_qty, args=(r["line"], -1), help="One less")
                    c3.button("", icon=":material/add:", key=f"plus_{r['line']}", on_click=change_qty, args=(r["line"], 1), help="One more")
                    c4.markdown(f"<div style='text-align:right;font-weight:600'>{money(r['amount'])}</div>", unsafe_allow_html=True)
                st.markdown(f"""<table class="sum">
                  <tr><td class="muted">Subtotal</td><td class="r muted">{money(b['subtotal'])}</td></tr>
                  <tr><td class="muted">GST {CAFE['gst_percent']}%</td><td class="r muted">{money(b['gst'])}</td></tr>
                  <tr class="tot"><td>Total</td><td class="r">{money(b['total'])}</td></tr></table>""", unsafe_allow_html=True)

                # checkout details (the assistant can also fill these from the chat)
                if S["customer_name"] and st.session_state.get("cust_name") != S["customer_name"]:
                    st.session_state.cust_name = S["customer_name"]
                if S["order_type"]:
                    st.session_state.cust_type = "Dine-in" if S["order_type"] == "dine-in" else "Takeaway"
                st.text_input("Your name", key="cust_name", on_change=save_details, max_chars=40, placeholder="e.g. Aman")
                st.radio("Order type", ["Dine-in", "Takeaway"], key="cust_type", on_change=save_details, horizontal=True,
                         **({} if "cust_type" in st.session_state else {"index": None}))
                ready = bool(S["cart"] and S["customer_name"] and S["order_type"])
                if st.button("Review and place order", type="primary", use_container_width=True, disabled=not ready):
                    confirm_dialog()
                if not ready:
                    st.caption("Add your name and choose dine-in or takeaway to place the order.")
                st.button("Clear order", on_click=reset_order, use_container_width=True)
        st.button("Talk to staff", icon=":material/support_agent:", on_click=call_staff, use_container_width=True)
        if S["handoff"]:
            st.warning(f"A staff member will help you. Call **{CAFE['phone']}** or ask at the counter.")

with chat_col:
    with st.container(border=True):
        if not API_KEY:
            st.error("The Gemini API key is missing. On Streamlit Cloud open **Settings → Secrets** and add  "
                     "`GEMINI_API_KEY = \"your key\"`. You can still use Quick add on the right.")
        chat_box = st.container(height=480, border=False)
        with chat_box:
            with st.chat_message("assistant", avatar=BOT_AVATAR):
                st.markdown(f"Hello! I'm the **{CAFE['bot_name']}** of {CAFE['name']}. Tell me what you'd like, "
                            "in English or Hindi, and I'll build your order. You can also ask for suggestions.")
            for m in S["messages"]:
                with st.chat_message(m["role"], avatar=BOT_AVATAR if m["role"] == "assistant" else USER_AVATAR):
                    st.markdown(m["content"])
        if not S["messages"]:
            b1, b2, b3 = st.columns(3)
            b1.button("What's popular?", on_click=ask, args=("What are your bestsellers?",), use_container_width=True)
            b2.button("Something cold", on_click=ask, args=("I want something cold to drink",), use_container_width=True)
            b3.button("Cappuccino + brownie", on_click=ask, args=("One medium cappuccino and a chocolate brownie please",), use_container_width=True)
        typed = st.chat_input("Type your order, e.g. 2 medium iced lattes with oat milk",
                              disabled=bool(S["order"]) or not API_KEY, max_chars=MAX_MSG_CHARS)
        st.markdown("<div class='ai-note'>The assistant is an AI (Google Gemini), not a person. Messages are sent to Google to create "
                    "replies, so please don't share personal or payment details. Prices and totals are calculated by the café "
                    "system, not by the AI.</div>", unsafe_allow_html=True)

st.markdown(f"""<div class="foot"><b>{E(CAFE['name'].upper())}</b>
  <span>Sector 18, {E(CAFE['city'])} · {E(CAFE['hours'])} · {E(CAFE['phone'])}</span>
  <span>Demo website for an academic project</span></div>""", unsafe_allow_html=True)

# ---------------------------------------------------------------- handle a new chat message
user_msg = typed or st.session_state.pop("pending", None)
if user_msg:
    now = time.time()
    duplicate = (user_msg == st.session_state.last_msg and now - st.session_state.last_time < 3)
    st.session_state.last_msg, st.session_state.last_time = user_msg, now
    if duplicate:
        pass                                   # same message sent twice within 3 seconds: ignore the copy
    elif waiter is None:
        st.toast("The assistant is not available. Please use Quick add.")
    elif len(S["messages"]) >= MAX_MESSAGES_PER_VISIT:
        st.toast("You've reached the chat limit for this visit. Please call our staff to continue.")
    else:
        with chat_box:
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(user_msg)
            with st.spinner("The assistant is typing..."):
                reply = process_turn(waiter, MENU, S, user_msg)
        if not S["messages"] or S["messages"][-1]["content"] != reply:
            st.toast(reply)                    # input warnings (empty or too long) are shown as a pop-up
    st.rerun()
