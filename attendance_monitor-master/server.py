from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for the app

 # Email Configuration
sender_email = "laverna1914@gmail.com"
sender_password = "uhrjzeqqrasgmivv"


# MongoDB Configuration
MONGO_URI = "mongodb+srv://dhurgatharan16:CYRUSBYTE@cyrusbyte.xidyw.mongodb.net/"  # Replace with your MongoDB URI if necessary
client = MongoClient(MONGO_URI)
db = client["attendance_db"]  # Database name (can be changed as needed)
attendance_collection = db["attendance"]  # Collection name (can be changed)
login_collection = db["users"]  # Collection name (can be changed)

# Helper function to convert MongoDB object to JSON format
def mongo_to_json(mongo_obj):
    mongo_obj["_id"] = str(mongo_obj["_id"])  # Convert ObjectId to string
    return mongo_obj

# Endpoint to submit attendance (POST request)
@app.route('/api/attendance', methods=['POST'])
def submit_attendance():
    try:
        # Get the attendance data from the request body
        data = request.json
        print(data)  # Print the data to help with debugging

        if 'attendance' not in data:
            return jsonify({"success": False, "error": "Missing 'attendance' key in request body"}), 400
        
        attendance_data = data['attendance']
        
        for record in attendance_data:
            reg_no = record.get('regNo')
            status = record.get('status')
            
            if not reg_no or not status:
                continue  # Skip this record if regNo or status is missing
            
            # Find the student by regNo
            student = attendance_collection.find_one({"regNo": reg_no})
            # print(student.get("email"))
            if student:
                email = student.get("email")
                # If the student already exists, update the present or absent count
                if status.lower() == "present":
                    attendance_collection.update_one(
                        {"regNo": reg_no},
                        {"$inc": {"present": 1}}  # Increment present count by 1
                    )
                elif status.lower() == "absent":
                    attendance_collection.update_one(
                        {"regNo": reg_no},
                        {"$inc": {"absent": 1}}  # Increment absent count by 1
                    )
                    user = attendance_collection.find_one({"regNo": reg_no})
                    percentage = (user.get("present")/(user.get("present")+user.get("absent")))*100
                    if percentage < 60:
                        send_percentage_email_to_student(email, record.get('name')  ,  reg_no,  percentage)
                        send_percentage_email_to_mentor(user.get('mentor_email'), record.get('name'),  percentage,reg_no)


                    if email:
                        send_absent_email(email, record.get('name'), reg_no)
            else:
                # If the student doesn't exist, create a new record with regNo, name, and present/absent counts
                attendance_collection.insert_one({
                    "regNo": reg_no,
                    "name": record.get('name'),
                    "present": 1 if status.lower() == "present" else 0,
                    "absent": 1 if status.lower() == "absent" else 0
                })

        return jsonify({"success": True, "message": "Attendance successfully saved"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    
def send_absent_email(email, name, reg_no):
    try:
       
        subject = "Attendance Alert: Absent Notification"

        # Create the email content
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = email
        message['Subject'] = subject

        body = f"""
        Dear {name},

        This is to inform you that you have been marked absent today (Reg No: {reg_no}).

        Please ensure to attend the next session or provide a valid reason for your absence.

        Regards,
        Attendance Management System
        """
        message.attach(MIMEText(body, 'plain'))

        # Connect to the email server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
            print(f"Absent email sent to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}. Error: {e}")


def send_percentage_email_to_student(email, name, reg_no, attendance_percentage):
    try:
       
        subject = "Attendance Warning: Low Attendance Percentage"

        # Create the email content
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = email
        message['Subject'] = subject

        body = f"""
        Dear {name} with Reg No: {reg_no},

        We noticed that your attendance percentage has dropped below 60% (Current: {attendance_percentage:.2f}%).

        Kindly ensure to attend upcoming classes regularly to avoid any academic issues. If you have taken any medical leave, please provide the necessary documents to your class advisors.

        It is important to maintain a good attendance record to avoid any disciplinary actions.

        Thank you for your cooperation.

        Regards,  
        Attendance Management System
        """
        message.attach(MIMEText(body, 'plain'))

        # Connect to the email server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
            print(f"Low attendance email sent to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}. Error: {e}")


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_percentage_email_to_mentor(mentor_email, student_name, attendance_percentage, reg_no):
    try:
        
        subject = f"Alert: {student_name}'s Low Attendance"

        # Create the email content
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = mentor_email
        message['Subject'] = subject

        body = f"""
        Dear Mentor,

        This is to inform you that your student **{student_name} (Reg No: {reg_no})** has an attendance percentage below 60%.  
        **Current Attendance: {attendance_percentage:.2f}%**

        Kindly ensure that the student is aware of this situation.  
        Please advise them to attend classes regularly to avoid academic issues. If they have taken any medical leave, they should provide the necessary documents to the class advisor.

        Your guidance in this matter will be highly appreciated.

        Regards,  
        Attendance Management System
        """
        message.attach(MIMEText(body, 'plain'))

        # Connect to the email server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, mentor_email, message.as_string())
            print(f"Low attendance alert sent to mentor: {mentor_email}")
    except Exception as e:
        print(f"Failed to send email to {mentor_email}. Error: {e}")


# Endpoint to fetch all attendance records (GET request)
@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    try:
        # Fetch student data from the MongoDB collection
        students = attendance_collection.find({}, {'_id': 0})  # Exclude the _id field
        student_list = list(students)
        
        return jsonify({"success": True, "attendance": student_list}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Endpoint to fetch attendance by student registration number (regNo)
@app.route("/api/attendance_one_student/<string:regNo>", methods=["GET"])
def get_attendance_by_regno(regNo):
    try:
        # Fetch attendance data from MongoDB using the regNo
        student_data = attendance_collection.find_one({"regNo": regNo})
        
        if student_data:
            return jsonify(mongo_to_json(student_data)), 200
        else:
            return jsonify({"message": "Student not found"}), 404
    except Exception as e:
        print(f"Error fetching data: {e}")
        return jsonify({"message": "Internal Server Error"}), 500
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    role = data.get("role")
    username = data.get("username")
    password = data.get("password")

    user = login_collection.find_one({"username": username, "password": password, "role": role})
    if user:
        return jsonify({"message": "Login successful", "role": role}), 200
    else:
        return jsonify({"message": "Invalid role, username, or password"}), 401

if __name__ == "__main__":
    app.run(debug=True)
