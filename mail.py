import smtplib
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



def send_mail_to(destination,obj_id):
   
    me = "towards.my.dream13@gmail.com"
    you = destination
    link = "http://localhost:9090/confirmation/{}".format(obj_id)


    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Link"
    msg['From'] = me
    msg['To'] = you

    text = "Hi!\nWelcome to chat application\nHere is the confiramation link you wanted:\nhttp://www.python.org"
    html = """\
    <html>
    <head></head>
    <body>
        <p>Hi!<br>
        HWelcome to chat application<br>
        Here is the <a href={} >confirmation link</a> you wanted.
        </p>
    </body>
    </html>
    """.format(link,link)
    try:
        part2 = MIMEText(html, 'html')
        msg.attach(part2)
        mailserver = smtplib.SMTP('smtp.gmail.com',587)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.ehlo()
        mailserver.login('towards.my.dream13@gmail.com', 'jobinJOSE13')
        try:
            mailserver .sendmail(me, you, msg.as_string())
        finally:
            mailserver .quit()
    except Exception, exc:
        sys.exit( "mail failed; %s" % str(exc) )


if __name__ == "__main__":
    main()
