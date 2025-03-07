import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def remove_plus_extension(email: str) -> str:
    if '@' not in email:
        return email

    local_part, domain_part = email.split('@', 1)
    plus_index = local_part.find('+')
    if plus_index != -1:
        local_part = local_part[:plus_index]
    return f"{local_part}@{domain_part}"

def send_appointment_notification(
        doctor_email: str,
        doctor_name: str,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        patient_id: int
):
    subject = "Заплановано огляд пацієнта"
    body_html = f"""
    <p>{doctor_name},</p>
    <br />
    <p>Повідомляємо, що до вас на прийом записаний(а) пацієнт(ка) {patient_name}.</p>

    <p>Дата прийому: {appointment_date}</p>
    <p>Час прийому: {appointment_time}</p>
    <p>Медична картка: https://vitalineph.com/patient/{patient_id}</p>
    <br />

    <p>З повагою,</p>
    <p>Система Сповіщень VitaLine</p>
    """

    message = Mail(
        from_email='appointments@vitalineph.com',
        to_emails=remove_plus_extension(doctor_email),
        subject=subject,
        html_content=body_html
    )

    try:
        SendGridAPIClient(os.environ.get('SENDGRID_API_KEY')).send(message)
    except Exception as e:
        print(f"Error sending email via SendGrid: {e}")

def send_email_verification_notification(
        email: str,
        verification_code: int
):
    subject = "Ваш код підтвердження VitaLine"
    body_html = f"""
    <p>Ваш код підтвердження - {verification_code}.</p>
    <p>З повагою, команда клініки VitaLine</p>
    """

    message = Mail(
        from_email='appointments@vitalineph.com',
        to_emails=remove_plus_extension(email),
        subject=subject,
        html_content=body_html
    )

    try:
        SendGridAPIClient(os.environ.get('SENDGRID_API_KEY')).send(message)
    except Exception as e:
        print(f"Error sending email via SendGrid: {e}")