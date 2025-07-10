import os
import re
import csv
import datetime
import streamlit as st
from PyPDF2 import PdfReader

def sanitize_text(text):
    return re.sub(r'[^a-zA-Z0-9 ]', '', text)

def extract_data_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    extracted_data = []
    schedule_data = []
    agent = "agent_n"
    for page in reader.pages:
        text = page.extract_text()
        lines = text.split("\n")
        for i, line in enumerate(lines):
            match = re.search(r'\[(\d+)\] (.+?) (\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})', line)
            if match:
                servicelocal = match.group(1)
                date_time = match.group(3)
                date, hour_full = date_time.split(" ")[:2]
                # Ajusta a hora para o formato hh;mm
                hour = hour_full[:5].replace(":", ":")
                alternative_id_match = re.search(r'Ficha (\d+-\d+)', line)
                alternative_identifier = alternative_id_match.group(1) if alternative_id_match else ""
                observation = lines[i + 1] + " " + lines[i + 2] if i + 2 < len(lines) else ""
                observation = sanitize_text(observation)
                if alternative_identifier:
                    observation += f" / {alternative_identifier}"
                alternative_identifier_type = "entregaCompartilhada" if alternative_identifier else "coleta"
                extracted_data.append([
                    "I",
                    "",  # agent (to be filled later)
                    alternative_identifier_type,
                    "7",
                    servicelocal,
                    "JEMIDIO",
                    observation.strip(),
                    date,
                    hour,
                    alternative_identifier
                ])
                if alternative_identifier:
                    schedule_data.append([alternative_identifier, "jemidioent"])
        agent_match = re.search(r'Entregador: (.*?) \[(\d+)\]', text)
        if agent_match:
            agent = agent_match.group(1)
            agent_number_match = re.search(r'\d+', agent)
            agent = agent_number_match.group(0) if agent_number_match else "agent_n"
    for row in extracted_data:
        row[1] = agent
    return extracted_data, schedule_data

def generate_csv(data, header):
    import io
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(header)
    writer.writerows(data)
    return output.getvalue().encode('utf-8')

st.title("Conversor de PDF para CSV - AGD/IAG")

uploaded_file = st.file_uploader("Selecione um arquivo PDF", type=["pdf"])
if uploaded_file:
    data, schedule_data = extract_data_from_pdf(uploaded_file)
    header_agd = ["command", "agent", "scheduleType", "ActivitiesOrigin", "servicelocal", "team", "observation", "date", "hour", "alternativeIdentifier"]
    csv_agd = generate_csv(data, header_agd)
    st.success("Arquivo AGD gerado!")
    st.download_button(
        label="Baixar CSV AGD",
        data=csv_agd,
        file_name=f"AGD_{datetime.datetime.now().strftime('%d%m%y')}_v2.csv",
        mime="text/csv"
    )
    if schedule_data:
        header_iag = ["schedule", "item"]
        csv_iag = generate_csv(schedule_data, header_iag)
        st.success("Arquivo IAG gerado!")
        st.download_button(
            label="Baixar CSV IAG",
            data=csv_iag,
            file_name=f"IAG_{datetime.datetime.now().strftime('%d%m%y')}_v2.csv",
            mime="text/csv"
        )
