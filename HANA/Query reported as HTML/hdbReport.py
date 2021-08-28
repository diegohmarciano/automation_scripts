#Import your dependencies
import platform
from hdbcli import dbapi
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import argparse

#Start the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

#Parsing arguments
parser = argparse.ArgumentParser(description="Report of SAP* and DDIC usage", prog='hdbReport.py', usage='%(prog)s [options]')
parser.add_argument("-snd", "--sendmail", required=True, type=str, help="Mail of sender")
parser.add_argument("-dst", "--receivers", required=True, type=str, help="List of mails to receive the report splitted wiht ;")
parser.add_argument("-mx", "--smtp", required=True, type=str, help="SMTP Server to send the report")
parser.add_argument("-dt", "--deltadays", required=True, type=int, help="How much delta to use for the report")
parser.add_argument("-hdbk", "--hdbsecstorekey", required=True, type=str, help="Which key to use for the HANA DB Connection")
args = parser.parse_args()

usersIds=('DDIC', 'SAP*')
yesterday = datetime.now() - timedelta(args.deltadays)
queryTimestamp = datetime.strftime(yesterday, '%Y%m%d%H%M%S')
result = '<head><style>table, th, td {border: 1px solid black;border-collapse: collapse;}th, td {padding: 5px;text-align: left;}</style></head>'
result += '<body><table style="width:100%"><tr><td style="text-align:center">REPORT FROM {0} to {1} FOR USERS {2}</td></tr></table><table style="width:100%">'.format(datetime.strftime(yesterday, '%Y-%m-%d %H:%M:%S'), datetime.today().strftime('%Y-%m-%d %H:%M:%S'), usersIds)
me = args.sendmail
you = args.receivers
mxServer = args.smtp

msg = MIMEMultipart('alternative')
msg['From'] = me
msg['To'] = you
msg['Subject'] = "REPORT {0}".format(datetime.today().strftime('%Y-%m-%d'))

#verify the architecture of Python
print ("Platform architecture: " + platform.architecture()[0])

#connect to HANA using the hdbuserstore entry
conn = dbapi.connect(
    #Option 1, retrieve the connection parameters from the hdbuserstore
    key=args.hdbsecstorekey, # address, port, user and password are retrieved from the hdbuserstore

)

#open the SQL cursor
cursor = conn.cursor()

#Prepare and run the query, then close the cursor
sql_command = "SELECT connector,user_id,action,execution_date,terminal,program_id FROM GRACACTUSAGE WHERE execution_date > {0} and user_id in {1}".format(queryTimestamp, usersIds)
cursor.execute(sql_command)
rows = cursor.fetchall()
cursor.close()
conn.close()

#exit if no results
if ( len(rows) == 0 ):
    quit()

#Results to HTML
for row in rows:
    result += "<tr>"
    for col in row:
        result += "<td>%s</td>" % col
    result += "</tr>"

#Close the results html table
result += "</table></body>"

#Prepare mail body in both html and text
text = result
html = result
part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')
msg.attach(part1)
msg.attach(part2)

#Send the email
s = smtplib.SMTP(mxServer)
s.sendmail(me, you, msg.as_string())
s.quit()

quit()


