import smtplib, ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from dotenv import load_dotenv
import os
import pickle

load_dotenv()

FULL_NAME = os.getenv('FULL_NAME')
YEAR = os.getenv('YEAR')
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

try:
    emails_sent = pickle.load(open('emails_sent.pickle', 'rb'))
except:
    emails_sent = []

if FULL_NAME is None or EMAIL is None or PASSWORD is None or YEAR is None:
    raise Exception('Environment variables not set')

def format_email(name, company, recruiter_name, email_type="personal"):
    if email_type == "Regular" or email_type == "Small":
        return (
            PERSONAL_SUBJECT,
            PERSONAL_TEMPLATE.format(
                'Hello' if recruiter_name == 'NO_NAME' else f'Hello {recruiter_name}',
                name,
                YEAR,
                company,
                name.split()[0],
            )
        )
    elif email_type == "Business":
        return (
            PERSONAL_SUBJECT,
            BUSINESS_TEMPLATE.format(
                'Hello' if recruiter_name == 'NO_NAME' else f'Hello {recruiter_name}',
                name,
                YEAR,
                company,
                name.split()[0],
            )
        )

PERSONAL_SUBJECT = 'Recruit top talent through V1 Startup Fair @ University of Michigan!'
with open('templates/personal.html', 'r') as f:
    PERSONAL_TEMPLATE = f.read()

with open('templates/business.html', 'r') as f:
    BUSINESS_TEMPLATE = f.read()

def send_email(email_from, password, from_name, subject, content, email_to, cc):
    email_message = MIMEMultipart()
    email_message['From'] = from_name
    email_message['To'] = ', '.join(email_to)
    email_message['Cc'] = ', '.join(cc)
    email_message['Subject'] = subject

    # attach body of email
    email_message.attach(MIMEText(content, "html"))

    # attach prospectus
    pdf = MIMEApplication(open('assets/prospectus.pdf', 'rb').read())
    pdf.add_header('Content-Disposition', 'attachment', filename='V1 Startup Fair Prospectus.pdf')
    email_message.attach(pdf)

    email_string = email_message.as_string()

    # send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(email_from, password)
        server.sendmail(email_from, (email_to + cc), email_string)

# removes all whitespace and splits by comma
def sanitize_split(field):
    return ''.join(field.split()).split(',')

def main():
    confirm = input('Are you sure you want to send emails? (y/n)\t')
    if confirm != 'y': exit()

    # read in a subset of the company sheet
    df = pd.read_csv('companies.csv')
    df = df[['Company', 'Name', 'Email', 'Type']].dropna()

    for _, row in df.iterrows():
        company = row["Company"]
        email_type = row["Type"]
        names = sanitize_split(row["Name"])
        emails = sanitize_split(row["Email"])
        persons = zip(names, emails)

        if len(names) != len(emails) or email_type is None:
            print(f'Error: {company} row badly formatted, skipping')
            continue

        print(company, names, emails, email_type)

        for name, email in persons:
            if email in emails_sent:
                print(f'Warning: email already sent to {name} <{email}>, skipping')
                continue

            subject, content = format_email(FULL_NAME, company, name, email_type)
            send_email(EMAIL, PASSWORD, FULL_NAME, subject, content, [email], ["v1startupfair@umich.edu"])
            emails_sent.append(email)

        print()

    pickle.dump(emails_sent, open('emails_sent.pickle', 'wb'))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # if script is aborted, save emails that have been sent
        pickle.dump(emails_sent, open('emails_sent.pickle', 'wb'))
