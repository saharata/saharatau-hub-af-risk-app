import streamlit as st
from PIL import Image
from fpdf import FPDF
import base64
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import os

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="PLAIN & PLAIN-L AF Risk Calculator",
    page_icon="🫀",
    layout="centered"
)

# ================= HEADER =================
col1, col2 = st.columns([1,4])
with col1:
    try:
        logo = Image.open("logo.png")
        st.image(logo, width=100)
    except:
        st.write("🏥")
with col2:
    st.markdown("<h2 style='color:#004aad;'>PLAIN & PLAIN-L AF Risk Calculator</h2>", unsafe_allow_html=True)
    st.caption("Neurological Institute of Thailand | Stroke & Cardiac Team")

st.markdown("---")

# ================= SIDEBAR =================
st.sidebar.header("⚙️ Settings")
model = st.sidebar.radio("Select model:", ["PLAIN", "PLAIN-L"])
st.sidebar.info("PLAIN = ECG + Clinical\nPLAIN-L = + Echocardiogram (LAVI ≥35)")
st.sidebar.markdown("---")
st.sidebar.caption("Developed by Neurology & AI Research Unit, NIT")

# ================= INPUT =================
st.markdown("### 🧩 Input Patient Information")

colA, colB = st.columns(2)
with colA:
    patient_name = st.text_input("Patient Name")
    hn = st.text_input("Hospital Number (HN)")
    age_year = st.number_input("Age (years)", 0, 120, 60)
    ptfv1 = st.checkbox("PTFV1 ≥ 4000 µV·ms")
    lae = st.checkbox("Left atrial enlargement (LAD/Biphasic P/A-IAB)")
with colB:
    insula = st.checkbox("Insular lesion on MRI/CT")
    nihss = st.checkbox("NIHSS ≥ 10 (Severe stroke)")
    lavi = False
    if model == "PLAIN-L":
        lavi = st.checkbox("LAVI ≥ 35 mL/m² (Echocardiogram)")
    email_to = st.text_input("Send result to Gmail (optional)", placeholder="example@gmail.com")

st.markdown("---")

# ================= CALCULATION =================
if st.button("🧮 Calculate AF Risk"):
    # --- Calculate score ---
    if model == "PLAIN":
        score = (4 if ptfv1 else 0) + (2 if lae else 0) + (1 if age_year >= 60 else 0) + (1 if insula else 0) + (1 if nihss else 0)
        cutoff = 4.5
    else:
        score = (2 if ptfv1 else 0) + (1 if age_year >= 60 else 0) + (1 if insula else 0) + (1 if nihss else 0) + (4 if lavi else 0)
        cutoff = 4.5

    st.markdown(f"## 💯 Total Score: <span style='color:#004aad;'>{score}</span>", unsafe_allow_html=True)
    if score >= cutoff:
        risk_text = "Likely AF"
        comment = "High risk of new-onset AF. Consider prolonged ECG monitoring (≥72h)."
        color = "red"
        st.error(f"🚨 **{risk_text}** — {comment}")
    else:
        risk_text = "Not likely AF"
        comment = "Low risk. Routine follow-up is sufficient."
        color = "green"
        st.success(f"✅ **{risk_text}** — {comment}")

    st.progress(min(score/10, 1.0))
    st.caption("Cut-off ≥ 4.5 indicates *Likely AF* (AUC ≈ 0.89, Sens 98.9 %, Spec 73.8 %)")

    # ================= PDF GENERATION =================
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Neurological Institute of Thailand", ln=True, align="C")
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "PLAIN / PLAIN-L AF Risk Report", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Date: {datetime.date.today().strftime('%d %B %Y')}", ln=True)
    pdf.cell(0, 10, f"Patient Name: {patient_name}", ln=True)
    pdf.cell(0, 10, f"HN: {hn}", ln=True)
    pdf.cell(0, 10, f"Model used: {model}", ln=True)
    pdf.cell(0, 10, f"Total Score: {score}", ln=True)
    pdf.cell(0, 10, f"Risk Category: {risk_text}", ln=True)
    pdf.multi_cell(0, 10, f"Interpretation: {comment}")

    pdf.set_text_color(0,0,128)
    pdf.multi_cell(0, 8, 
        "\nThis score estimates the risk of new-onset atrial fibrillation following stroke.\n"
        "Based on the PLAIN / PLAIN-L models (Neurological Institute of Thailand).\n\n"
        "Cut-off ≥ 4.5 indicates 'Likely AF'.\n"
        "Validation: AUC = 0.892, Sensitivity = 98.9%, Specificity = 73.8%.\n\n"
        "Clinical advice: Consider ECG or Holter monitoring for high-risk patients."
    )
    pdf.set_text_color(0,0,0)
    pdf.output("AF_Risk_Report.pdf")

    with open("AF_Risk_Report.pdf", "rb") as f:
        pdf_data = f.read()

    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="AF_Risk_Report.pdf">📄 Download PDF Report</a>'
    st.markdown(href, unsafe_allow_html=True)

    # ================= GMAIL SEND FEATURE =================
    if email_to:
        try:
            sender = os.getenv("GMAIL_USER")      # set in Streamlit secret or env
            password = os.getenv("GMAIL_PASS")
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = email_to
            msg["Subject"] = f"AF Risk Report for {patient_name}"

            body = MIMEText(f"Dear Clinician,\n\nAttached is the AF risk report ({model}) for patient {patient_name}.\n\nBest regards,\nNeurology & AI Research Unit, NIT","plain")
            msg.attach(body)
            attachment = MIMEApplication(pdf_data, _subtype="pdf")
            attachment.add_header("Content-Disposition", "attachment", filename="AF_Risk_Report.pdf")
            msg.attach(attachment)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(sender, password)
                smtp.send_message(msg)

            st.success(f"📧 Report sent to {email_to}")
        except Exception as e:
            st.warning(f"❌ Email not sent: {e}")

st.markdown("---")
st.markdown("<small>Developed by Neurology & AI Research Unit, Neurological Institute of Thailand</small>", unsafe_allow_html=True)
