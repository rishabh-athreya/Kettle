from slack_sdk import WebClient

client = WebClient(token="xoxb-9071687433444-9093822905152-A74Qkhf8Q8dScLxU2TcPucrS")
auth_response = client.auth_test()
print("BOT_USER_ID:", auth_response["user_id"])