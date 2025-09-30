# 🎮 Gaming Konsol

👉 [Live Demo](https://gaming-web-fqyx.onrender.com)

> A custom gaming console management system — designed as a software-first solution to explore how gaming centers can operate **without constant human intervention**.

---

## 📌 Project Vision

Traditional gaming centers rely heavily on staff to manage game sessions, payments, and revenue tracking. Our project, **Gaming Konsol**, reimagines this process by creating an **automated system** where:

* Players can initiate and close gaming sessions.
* Payments are handled securely and digitally.
* Game time and usage can be tracked automatically.

The vision is to **minimize human overhead** while ensuring a seamless player experience.

---

## 🎯 Features

* 💳 **Digital Payments with Stripe** — secure, fast, and cashless transactions.
* 🕹️ **Session Management** — start and stop gaming sessions with a simple interface.
* 🏪 **Gaming Store Management** — track games and sessions digitally.
* 📊 **Revenue Tracking** — payments and sessions linked in real time for transparent reporting.

*(The original concept used Raspberry Pi & coin acceptors, but our implementation focused on a full software-based solution using Python + Stripe.)*

---

## 🛠️ Tech Stack

* **Python** — backend logic
* **Flask (or FastAPI if used)** — for web-based control
* **Stripe API** — payment gateway integration
* **SQLite / PostgreSQL** — for storing session and payment data
* **HTML / CSS / JS** — lightweight frontend

---

## 🚀 How It Works

1. **User logs in / signs up** to access the system.
2. **Selects a game session** and duration.
3. **Makes payment via Stripe** (credit/debit card).
4. **Session starts automatically**, tracked in the system.
5. At the end, **session closes** and logs are updated.

---

## 💡 Problem Solved

* ❌ No need for coin-operated hardware or human staff to manage revenue.
* ✅ Cashless and digital-first approach makes the system more scalable.
* ✅ Easy to integrate with existing gaming centers as a **plug-and-play software solution**.

---

## 📂 Repository Structure

```
gaming-konsol/
├─ app.py              # Main Python app
├─ payments/           # Stripe integration logic
├─ templates/          # HTML templates
├─ static/             # CSS / JS / Images
├─ database.db         # SQLite database (if used)
├─ requirements.txt    # Dependencies
└─ README.md           # Project documentation
```

---

## 🔮 Future Enhancements

* ⌛ Add session timers visible to players.
* 📱 Create a mobile-friendly UI.
* 🎮 Integrate with real hardware for hybrid operation (Raspberry Pi + Stripe).
* 🧾 Auto-generate receipts and invoices for players.

---

## 👥 Team Contribution

This project was developed as part of a **university project presentation session with industry exposure**.
Our team focused on **the software side** of the concept, showing that the entire model could run **digitally with Python + Stripe payments** without specialized hardware.

---

## 📬 Contact

For questions, collaborations, or improvements:

* **Developer:** Thabo Gelson (aka Nawthviper)
* **Email:** [thabogelson02@gmail.com](mailto:thabogelson02@gmail.com)
* **GitHub:** [NawthviperCodes](https://github.com/NawthviperCodes)
