import random
import datetime
import mysql.connector
import os
from twilio.rest import Client
import getpass
import hashlib





#Connecting to DB
conn = mysql.connector.connect(
    host = "localhost",
    user = "rebuxphpdbadmin",
    password = "rebuxphpdbadminpassword",
    database = "RebuxDB"
)

cursor = conn.cursor()

#Pre-Requisite Cleanup (NEEDED AS THROUGH TESTING AUTO INCREMENT VALUE WILL KEEP RISING EVEN WITH DELETION OF ROWS IN BETWEEN AI DOESN'T RESET ON ITS OWN)
autoIncrementCleanUpPinSession =  "ALTER TABLE `Pin Session` AUTO_INCREMENT = 1"
autoIncrementCleanUpSession = "ALTER TABLE Session AUTO_INCREMENT = 1"
cursor.execute(autoIncrementCleanUpPinSession)
cursor.execute(autoIncrementCleanUpSession)

conn.commit()

#Asking For Menu Input Choice
isAuthorised = False
userMenuInput = 0

while userMenuInput != 2:

    print("_______________________________________")
    print("WELCOME TO REBUX LOST N FOUND")
    print("_______________________________________")
    print("1. Generate Pin For Locker Unlock")
    print("2. Exit")

    userMenuInput = int(input("Please Enter: "))
    
    if userMenuInput == 2:
        #Closing Connections/ Clean Up with corresponding message to User
        cursor.close()
        conn.commit()
        conn.close()
        
        print("Thank you for using Rebux Lost & Found System. Goodbye.")
        exit()
        
    else:
        #Authorisation Sequence (Asking User for Corresponding Login Credentials)
        #Also Checking For Validity of UserInput such as only INT for UserID, and CASE SENSITIVE Checks for Password via Hasbytes
        while isAuthorised == False:
            
            print("_______________________________________")
            print("Enter Login Credentials")
            print("_______________________________________")
            
            userInputID = input("Please Enter Your User ID: ")

	    #User's Input Password hidden via Getpass libary for increase security
            userInputPassword = getpass.getpass(prompt='Please Enter Your Password: ')
            
            #Hashing User input via SHA 256 for comparrison with Database, Enhanced Security
            hash_object = hashlib.sha256(userInputPassword.encode())
            userInputPasswordHexDigi = hash_object.hexdigest()
            
            if any(s.isdigit() == False for s in userInputID):
                print ("** USER ID SHOULD NOT CONTAIN LETTERS OR SPECIAL CHARACTERS, PLEASE TRY AGAIN !!! **")

            else:
                 #Check if User ID and Password is Valid
                isValidUserQuery = "SELECT * FROM Users WHERE user_id = {0} AND password = '{1}';"
                fullIsValidUserQuery = isValidUserQuery.format(userInputID, userInputPasswordHexDigi)

                cursor.execute(fullIsValidUserQuery)

                result = cursor.fetchall()
                
                #User Found
                if len(result) == 1:
                    isAuthorised = True
                
                #User Not Found
                else:
                    print("** INVALID USERNAME AND PASSWORD COMBINATION PLEASE TRY AGAIN !!! **")
        
        
        #After Authorisation is Complete
        #Ask User for Size of Locker Needed, Hence First Digit of Pin can be hardcoded to fit these requirements
        #Declaration of Public Varaiable
        pin = ""
        userInputSize = 0
        
        print("_______________________________________")
        print("Enter Desired Locker Size")
        print("_______________________________________")
        print("1. Small")
        print("2. Medium")
        print("3. Large")
        
        userInputSize = int(input("Please Enter: "))
        
        #Generating Remaning Digits via Random Function for Pin
        i = 1

        while (i < 5):
            singleRandomPinDigi = random.randint(0,9)
            
            #Hardcoding the First Digi to the respective values of 1, 2 or 3 based on Locker Size selected, Will be used later for opening algorithm
            if i == 1:
                if userInputSize == 1:
                    pin = pin + "1"
                    
                elif userInputSize == 2:
                    pin = pin + "2"
                    
                elif userInputSize == 3:
                    pin = pin + "3"
                    
                i = i + 1
                
            else:
                pin = pin + str(singleRandomPinDigi)
                i = i + 1
        '''
        Asking for User Input Item ID, HOWEVER DO TAKE NOTE THAT THIS SCRIPT WAS SUPPOSED TO RUN ON TOP OF INITAL PHASE 1 COMPLETION, WHERE FORMS ARE COLLECTED
        AND HENCE ITEM ID SHOULD ALREADY BE GENERATED THEN BY THE WEBSITE DEVELOPED IN PHASE 1 AND SAVED NEATLY INTO TEXT DOCUMENTS FORMS OF ITEM REPORTS
        '''
        
        itemIDFound = False

        while itemIDFound == False:

            print("_______________________________________")
            print("Enter Item ID")
            print("_______________________________________")
            userInputItemID = int(input("Please Enter Item ID: "))

            #Verficiation that Item ID indeed exist in DB

            isValidItemIDQuery = "SELECT item_id FROM Item WHERE item_id = {0};"
            fullIsValidItemIDQuery = isValidItemIDQuery.format(userInputItemID)
            cursor.execute(fullIsValidItemIDQuery)
 
            result = cursor.fetchall()

            #Item ID Found
            if len(result) == 1:
                itemIDFound = True

            #Item ID NOT Found
            else:
                print("** INVALID ITEM ID, PLEASE TRY AGAIN !!! **")


        #Codes below do the following
        #1. QUERY 1 = Inserting into "Pin" Table with deatials Newly Generated Pin
        #2. QUERY 2 = Inserting into "Pin" Session Table with details of pin with relevance to user whom created reported the lost item (Phase1) which hence is reciving the generated pin
        #3. QUERY 3 = Inserting into "Session" Tsble with details of session (creating session basically). Sesssion details are filled in with corresponds to pin session id used for locker session.

        currentDateTime = datetime.datetime.now()
        stringCurrentDateTime = currentDateTime.strftime('%Y-%m-%d %H:%M:%S')

        query1 = "INSERT INTO Pin (pin_id, generate_date_time) VALUES('{0}', '{1}');"
        query2 = "INSERT INTO `Pin Session` (pinsession_id, user_id, pin_id, generate_date_time, use_date_time, status) VALUES(NULL, '{0}', '{1}', '{2}', NULL, 'Generated');"
        query3 = "INSERT INTO Session (session_id, user_id, item_id, pinsession_id, type, status) VALUES(NULL, '{0}', '{1}', (SELECT pinsession_id FROM `Pin Session` ORDER BY pinsession_id DESC LIMIT 1), 'Finder', 'Reported');" 
        fullInsertQuery1 = query1.format(pin, stringCurrentDateTime)
        fullInsertQuery2 = query2.format(userInputID, pin, stringCurrentDateTime)
        fullInsertQuery3 = query3.format(userInputID, userInputItemID)

        cursor.execute(fullInsertQuery1)
        cursor.execute(fullInsertQuery2)
        cursor.execute(fullInsertQuery3)


        #Send Pin to User
        
        twilioAccSSID = "ACf5da1645597d0798f4ff3be7c16dfeb4"
        twilioAccTOKEN = "c50ae230182c367e16899412d36773be"
        messageFormat = "REBUX: Dear Finder, Use {0} as a One-Time Password for Locker Opening (do NOT share it with anyone). This OTP expires at {1} SG Time."
        otpExpireDateTime = currentDateTime + datetime.timedelta(minutes=15)
        strOtpExpireDateTime = otpExpireDateTime.strftime('%Y-%m-%d %H:%M:%S')

        actualMessage = messageFormat.format(pin, strOtpExpireDateTime)

        client = Client(twilioAccSSID,twilioAccTOKEN)

        client.messages.create(
                body = actualMessage,
                to = "+6588159408",
                from_ = "+16314961976"
        )
      
