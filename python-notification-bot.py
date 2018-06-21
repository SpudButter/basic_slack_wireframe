import os
import time, threading
import re
from slackclient import SlackClient

FINISHED_JOBS = 5
THRESHOLD = 0

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            #If the channel the message is from is a DM, mentioning(@) the bot isn't needed
            if event["channel"].startswith("D") and not event["text"].startswith('<@'):
                return event["text"], event["channel"]
            #Mentioning(@) the bot will be needed in public channels & group DMs
            else:
                user_id, message = parse_direct_mention(event["text"])
                if user_id == starterbot_id:
                    return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try typing in *HELP*."

    # Finds and executes the given command, filling in response
    response = None

    # This is where you start to implement more commands!
    if command.lower().startswith("help"):
        response = help_handler(response)
    elif command.lower().startswith("finished jobs"):
        response = "{} jobs have been finished.".format(FINISHED_JOBS)
    elif command.lower().startswith("set threshold to"):
        global THRESHOLD
        if command[17:].isdigit() and (command[17:]>=0):
            response = "The threshold has been changed from {} to {}.".format(THRESHOLD, command[17:])
            THRESHOLD = int(command[17:])
        else:
            response = "Invalid input. Please input a number greater than or equal to 0."
    elif command.lower().startswith("current threshold" or "what is the current threshold"):
        response = "The threshold is currently at {}.".format(THRESHOLD)

    # Sends the response back to the channel as a message or attachment
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response,
        )

def help_handler(response):
    response = "Here is a list of commands I can do: \n"
    command_list = {
        "help": "*HELP*: Show a list of commands. \n",
        "finished_jobs": "*FINISHED JOBS*: Shows the number of jobs completed today. \n",
        "change_thres": "\n*SET THRESHOLD TO [new number]*: Change the value that the number of finished jobs are compared to. \n",
        "current_thres": "*CURRENT THRESHOLD*: Shows current threshold."
        }
    for command in command_list:
        response += command_list[command]
    return response

def send_notification():
    threading.Timer(10.0, send_notification).start()
    if (FINISHED_JOBS<THRESHOLD):
        slack_client.api_call("chat.postMessage",link_names=1,channel='CHANNEL ID HERE',text='@channel ALERT')


if __name__ == "__main__":
    # instantiate Slack client
    slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
    if slack_client.rtm_connect(with_team_state=False):
        print("Notification Bot Wireframe connected and running!")
        RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
        # starterbot's user ID in Slack & Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        send_notification()
        while True:
            #
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
