import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders


fromaddr = "lukesfermenter@gmail.com"
passwd = "dubbeltrouble"
toaddr = "hawkjo@gmail.com"
     
def send_email(
        message,
        attachment_fpath=None,
        subject=None,
        ):
    if subject is None:
        subject = "A message from your fermenter"

    msg = MIMEMultipart()
     
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
     
    body = message
    msg.attach(MIMEText(body, 'plain'))
    
    # if sending a graph, attach it to the email:
    if attachment_fpath is not None:
        with open(attachment_fpath, "rb") as f:
            attachment = f.read()
        msg.attach(MIMEText(body, 'plain'))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % attachment_fpath)
        msg.attach(part)
     
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, passwd)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
