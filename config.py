from decouple import config


API_KEY = config('TOKEN')
# Create a bot application and get its token at the Discord Developer Portal.
# Follow this guide if you need help: https://www.writebots.com/discord-bot-token/
# Make sure to enable both privileged intents on the bot tab.
# This is also how you will invite the bot to your server.
token = API_KEY

# Bot description shown in the help menu
description = ""

# ID of the guild
# To find this, go to your discord settings > advanced > enable developer mode
# Then, right click the guild picture on the left sidebar and click copy ID
guild_id = "893321767274303488"

# URLs of the OpenSea accounts that should be monitored and the channel IDs where their activity should be sent.
# These are some examples. Feel free to add/remove as many as you wish but make sure to follow this template.
# To find the IDs, go to your discord settings > advanced > enable developer mode
# Then, right click the channel and click copy ID
accounts_and_channels = [("https://opensea.io/GaryVee?tab=activity", "893687009682554890"), ("https://opensea.io/pranksy?tab=activity", "893687089395277895")]

# Time (in minutes) between checking for new sales
# All sales are always sent, no matter how often we check
update_interval = 5
