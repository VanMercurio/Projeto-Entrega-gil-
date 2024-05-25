from flask import Flask, render_template, request, redirect, url_for
from firebase_admin import credentials, firestore, initialize_app
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import logging
from twilio.rest import Client

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize Firestore DB
cred = credentials.Certificate('serviceAccountKey.json')
initialize_app(cred)
db = firestore.client()
messages_ref = db.collection('messages')

# Twilio configuration
account_sid = 'your_account_sid'
auth_token = 'your_auth_token'
twilio_number = 'your_twilio_number'
client = Client(account_sid, auth_token)

# Flask-WTF form class
class MessageForm(FlaskForm):
    apartment_number = StringField('Apartment Number', validators=[DataRequired()])
    message = StringField('Message', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    submit = SubmitField('Send Message')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MessageForm()
    if form.validate_on_submit():
        apartment_number = form.apartment_number.data
        message = form.message.data
        phone_number = form.phone_number.data

        try:
            # Save message to Firestore
            messages_ref.add({
                'apartment_number': apartment_number,
                'message': message,
                'phone_number': phone_number
            })
            app.logger.info(f'Message sent to Firestore: {apartment_number}, {message}, {phone_number}')

            # Send message via WhatsApp using Twilio
            whatsapp_message = client.messages.create(
                body=message,
                from_=f'whatsapp:{twilio_number}',
                to=f'whatsapp:{phone_number}'
            )
            app.logger.info(f'WhatsApp message sent: {whatsapp_message.sid}')
        except Exception as e:
            app.logger.error(f'Error: {e}')

        return redirect(url_for('success'))
    return render_template('index.html', form=form)

@app.route('/success')
def success():
    return "Message sent successfully!"

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
