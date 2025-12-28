# 🛡️ Automatic-Email-Phishing
An educational phishing simulation platform built to help students and security learners understand how real-world phishing attacks are designed, executed, and analyzed.

The system automatically:
* **Sends** realistic phishing emails
* **Tracks** user responses
* **Classifies** user intent using an LLM
* **Sends** contextual follow-ups and reminders
* **Visualizes** results in a real-time dashboard

> [!CAUTION]
> **For educational and awareness purposes only.** Do NOT use for malicious activities.

---

## 🚀 Features

* 📧 **Automated phishing email simulation** (via Zoho Mail)
* 🧠 **Intent classification** using Google Gemini
* 🔁 **Reminder system** for non-responders
* 📊 **Real-time Streamlit dashboard**
* 📈 **Interactive charts** (Plotly)
* 📜 **Expandable logs** with export option
* 🧩 **Clean separation** between simulation engine and UI

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository
```bash
git clone <repo_link>
cd Automatic-Email-Phishing
```

### 2️⃣ Create and activate virtual environment (recommended)
```bash
# Windows
python3 -m venv venv
venv\Scripts\activate

# MacOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure environment variables
Create a `.env` file in the root directory using `.env.example` as a template and populate it with the following details:

* **Zoho Mail credentials:**
* **Google Gemini API key:**
* **Google Form URL:**

## ▶️ Running the UI
### ⚠️ Always run Streamlit from the project root.
```bash
streamlit run app.py
```

## 🖥️ Using the Dashboard
1. **Enter target email(s)** into the simulation input.
2. **Click Start Simulation** to begin the automated workflow.
3. **Process incoming responses** as they arrive.
4. **Send reminders** to targets who haven't interacted yet.
5. **View live statistics** and intent distribution via the charts.
6. **Expand logs** or download them for post-simulation analysis.

## 🧪 Disclaimer
This project is strictly intended for **cybersecurity education, training, and awareness**.

Misuse of this system for real phishing attacks is unethical and illegal. The author is not responsible for any misuse or damage caused by this application.

## 📌 Author
**Akshit Negi**

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Akshit-1201)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/negi-akshit/)
[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:akshitnegi.work@gmail.com)