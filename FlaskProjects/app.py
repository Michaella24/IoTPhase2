from flask import Flask, render_template
#for DHT11
import Freenove_DHT as DHT
import time
#for email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
import RPi.GPIO as GPIO

app = Flask(__name__)
#define the dht pin, i will set it to 11 like in the lab
DHTPin = 11
#need to define the fan GPIO pin here as well
FanPin = 18

#email credentials (add your own credentials when you test it at home. if you have issues, text me -m )
sender_email = "putyoursfortesting"
app_password = "***" #i needed to have an app password to make it work personally
receiver_email = "putyoursfortesting"

#method for sending the email
def send_email(sender_email, sender_password, receiver_email, subject, body):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject #tbh this could be hardcoded
    message.attach(MIMEText(body, 'plain')) #tbh this could be hardcoded (the body i mean)

    with smtplib.SMTP('smtp.gmail.com', 587) as server: #!!dont change the smtp.gmail.com its required!!
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)

#method for receiving email
def receive_email(email_address,app_password,num_emails=5): #take the first 5 emails
    imap_server = "imap.gmail.com"
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(email_address,app_password)
    imap.select('INBOX')

    #look for emails from a specific sender AKA the sender email you set on top
    _, message_numbers = imap.search(None,'FROM youremail') #my email for ex
    email_ids = message_numbers[0].split()[-num_emails:] #retrieve the first string of email ids found
    #imma stop the commenting here cause im getting tired but ill continue tomorrow or so cause this shit is giving me a headache yall
    for email_id in reversed(email_ids):
        _, msg_data = imap.fetch(email_id,'(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                email_body = response_part[1]
                email_message = email.message_from_bytes(email_body)

                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            content = part.get_payload(decode=True).decode()
                            if "YES" in content.strip().upper():  #Check if user replied with yes **need to update that to allow lower case too
                                return True
    imap.close()
    imap.logout()
    return False

@app.route('/')
def home():
    dht = DHT.DHT(DHTPin)  #creating the object 
    readValue = dht.readDHT11()  #read the DHT sensor
    #If the current temperature is greater than 24, send an email to the user with this message 
    if (readValue is dht.DHTLIB_OK):  #if the value is normal
        current_temp = dht.temperature
        current_humidity = dht.humidity #idk if we need it tbh
        #check if the current temperatur is greater than 24
        if(current_temp > 24):
            send_email(
                sender_email, 
                app_password, 
                receiver_email, 
                "Temperature Alert", 
                f"The current temperature is {current_temp}°C. Do you want to turn on the fan? Reply with 'YES' to turn it on."
            )
            #Wait a bit to give the user time to reply
            time.sleep(60) #they got 60 sec, they better speed up esti

            # Check for user's response
            if receiver_email(sender_email, app_password, num_emails=5):
                GPIO.output(FanPin, GPIO.HIGH)  # Turn on the fan
            else:
                GPIO.output(FanPin, GPIO.LOW)  # Turn off the fan

    #If the user replies YES, then turn on the fan. Otherwise, do nothing.
    return render_template('main.html', temperature=current_temp, humidity=current_humidity) #send this to the html so that we can display the data

if __name__ == 'main':
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()

