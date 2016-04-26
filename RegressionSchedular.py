# Import smtplib for the actual sending function
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import glob
import commands

global now
me = "StagingCloudHealth"
#recipients = ["vishnu1.kumar@ril.com", "Anshul.S.Jain@ril.com", "Abhishek.Mehrotra@ril.com"]

def execute_tests():
	global now
	now = datetime.datetime.now()
	cmd = "cd /home/vishnu/JCSHealth/jcsapitests_stag && testr run"
	(status, output) = commands.getstatusoutput(cmd)
	result = output.split("\n")
	l1 = result[-1]
	l2 = result[-2]
	#print l1
	#print l2
	numberFailed = 0
	if(status == 0):
		numberFailed = 0
		timeTaken = l2.split("tests in")[1]
		testExecutionId = l1.split("id=")[1].split(")")[0]	
	if(status == 256):
		numberFailed = int(l1.split("failures=")[1].split(")")[0].split("(")[0])
		timeTaken = l2.split("tests in")[1]
        	testExecutionId = l1.split(", failures")[0].split("id=")[1]

	return (numberFailed, timeTaken, testExecutionId)

def generate_html_report(test_execution_id):
	testStreamPath = "/home/vishnu/JCSHealth/jcsapitests_stag/.testrepository/%s"%test_execution_id
	#newest = max(glob.iglob('.testrepository/[0-9]*'), key=os.path.getctime)
	currentDateTime = now.strftime("%Y_%m_%d_%H_%M_%S")
	outputFileName = "/tmp/output_%s.html"%currentDateTime
	commands.getstatusoutput("subunit2html  %s   %s"%(testStreamPath, outputFileName))

	return outputFileName

def send_mail(subject, test_report_html, to):
	msg = MIMEMultipart('alternative')

	fp = open(test_report_html, 'rb')
	testReportHtml= fp.read()

	currentDateTime = now.strftime("%Y_%m_%d_%H_%M_%S")
	msg['Subject'] = subject
	msg['From'] = me
	msg['To'] = ",".join(to)

	attachment = MIMEText(testReportHtml, "html")
	attachment.add_header('Content-Disposition', 'attachment', filename="TestResult_stag.html")
	msg.attach(attachment)

	bodyContent = MIMEText(testReportHtml, 'html')
	fp.close()

	msg.attach(bodyContent)

	# Send the message via our own SMTP server, but don't include the
	# envelope header.
	s = smtplib.SMTP('localhost')   
	s.sendmail(me, to, msg.as_string())
	s.quit()


def execute_test_send_mail():
	(failed, timeTaken, test_execution_id) = execute_tests()
	cloud_health = "OK"
	if(failed !=0):
		cloud_health = "NOT OK (Please investigate results)"
	currentDateTime = now.strftime("%Y-%m-%d-%H:%M:%S")
	subject = 'Staging Health Status Dated:%s  is %s Failed:%s TimeTaken=%s' % (currentDateTime, cloud_health, failed, timeTaken)
	output_html_path = generate_html_report(test_execution_id)
	"""
	print (failed, timeTaken, test_execution_id)
	print output_html_path
	print subject
	"""
	
	recipients = ["vishnu1.kumar@ril.com", "Anshul.S.Jain@ril.com", "Abhishek.Mehrotra@ril.com",
		     "Varun.Arya@ril.com", "Prashant.Upadhyay@ril.com", "Anant.Kaushik@ril.com",
		     "Devender.Mishra@ril.com", "Akash.Agrawal@ril.com", "Asmita.Sharma@ril.com", "JioCloud.ComputeTeam@ril.com"]
	
	#recipients = ["vishnu1.kumar@ril.com"]
	send_mail(subject, output_html_path, recipients)

if __name__ == "__main__":
	execute_test_send_mail()
