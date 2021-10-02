import asyncio
from discord.ext import commands, tasks
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import discord
import config


# Initialize headless chrome instance
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument("--window-size=1600,1080")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options, executable_path=ChromeDriverManager().install())
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
    "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
driver.maximize_window()


# Initialize bot
bot = commands.Bot(command_prefix="}", description=config.description)

# Auxiliary dictionary to keep track of the activity already sent in the past.
# This way, we only send the new activity since the last check.
last_trades_sent = {}


@tasks.loop(minutes=config.update_interval)
async def update():
    global last_trades_sent
    
    # Get the discord guild
    guild = discord.utils.get(bot.guilds, id=config.guild_id)

    # For each pair of account and channel id in the config file, check for new activity and send to discord
    for account_url, channel_id in config.accounts_and_channels:
    
        # Get the activity page of this account
        driver.maximize_window()
        driver.get(account_url)
        await asyncio.sleep(10)

        # Get the channel
        channel = discord.utils.get(guild.channels, id=channel_id)
        
        # Auxiliary variable to keep track of the last trade where we stopped checking
        latest_trade_sent = None

        # If this is the first time checking for updates, the current activity is in the past.
        # Prepare everything to start monitoring new activity from this moment onrward.
        if account_url not in last_trades_sent.keys():
            try:
                date = driver.find_element_by_css_selector(f"#__next > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.FlexColumnreact__FlexColumn-sc-1wwz3hp-0.OpenSeaPagereact__DivContainer-sc-65pnmt-0.dBFmez.jYqxGr.ksFzlZ.fiudwD.App > main > div > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.ActivitySearchreact__DivContainer-sc-1pucb9u-0.dBFmez.jYqxGr.ehrjIH > div.Blockreact__Block-sc-1xf18x6-0.dBFmez.ActivitySearch--history > div.EventHistoryreact__DivContainer-sc-1ndm3on-0.eiDGHu > div > div > div > div > div > div > div > div:nth-child(2) > div:nth-child(7) > div > a")
                url = date.get_attribute("href")
                tx_hash = url.replace("https://polygonscan.com/tx/", "")
                last_trades_sent[account_url] = tx_hash
                continue
            except Exception as e:
                continue

        # If this is not the first time, check for new activity and send it to discord
        try:
            i = 2
            
            # For each event in the activity page
            while True:
                # Get price if it is a sale event
                try:
                    price = driver.find_element_by_css_selector(f"#__next > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.FlexColumnreact__FlexColumn-sc-1wwz3hp-0.OpenSeaPagereact__DivContainer-sc-65pnmt-0.dBFmez.jYqxGr.ksFzlZ.fiudwD.App > main > div > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.ActivitySearchreact__DivContainer-sc-1pucb9u-0.dBFmez.jYqxGr.ehrjIH > div.Blockreact__Block-sc-1xf18x6-0.dBFmez.ActivitySearch--history > div.EventHistoryreact__DivContainer-sc-1ndm3on-0.eiDGHu > div > div > div > div > div > div > div > div:nth-child({i}) > div.Row--cell.Row--cellIsSpaced.EventHistory--price-col > div > div > div.Overflowreact__OverflowContainer-sc-10mm0lu-0.fqMVjm.Price--amount").text
                except Exception as e:
                    price = None
                
                # Get the date, transaction URL and transaction hash
                date = driver.find_element_by_css_selector(f"#__next > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.FlexColumnreact__FlexColumn-sc-1wwz3hp-0.OpenSeaPagereact__DivContainer-sc-65pnmt-0.dBFmez.jYqxGr.ksFzlZ.fiudwD.App > main > div > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.ActivitySearchreact__DivContainer-sc-1pucb9u-0.dBFmez.jYqxGr.ehrjIH > div.Blockreact__Block-sc-1xf18x6-0.dBFmez.ActivitySearch--history > div.EventHistoryreact__DivContainer-sc-1ndm3on-0.eiDGHu > div > div > div > div > div > div > div > div:nth-child({i}) > div:nth-child(7) > div > a")
                url = date.get_attribute("href")
                date = date.text.replace(" open_in_new", "")
                tx_hash = url.replace("https://polygonscan.com/tx/", "")
                
                # If we have reached the past activity, stop here
                if last_trades_sent[account_url] == tx_hash:
                    break
                
                # Get the event information and send it to discord
                event_type = driver.find_element_by_css_selector(f"#__next > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.FlexColumnreact__FlexColumn-sc-1wwz3hp-0.OpenSeaPagereact__DivContainer-sc-65pnmt-0.dBFmez.jYqxGr.ksFzlZ.fiudwD.App > main > div > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.ActivitySearchreact__DivContainer-sc-1pucb9u-0.dBFmez.jYqxGr.ehrjIH > div.Blockreact__Block-sc-1xf18x6-0.dBFmez.ActivitySearch--history > div.EventHistoryreact__DivContainer-sc-1ndm3on-0.eiDGHu > div > div > div > div > div > div > div > div:nth-child({i}) > div.Row--cell.Row--cellIsSpaced.EventHistory--event-col > span").text
                item_img = driver.find_element_by_css_selector(f"#__next > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.FlexColumnreact__FlexColumn-sc-1wwz3hp-0.OpenSeaPagereact__DivContainer-sc-65pnmt-0.dBFmez.jYqxGr.ksFzlZ.fiudwD.App > main > div > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.ActivitySearchreact__DivContainer-sc-1pucb9u-0.dBFmez.jYqxGr.ehrjIH > div.Blockreact__Block-sc-1xf18x6-0.dBFmez.ActivitySearch--history > div.EventHistoryreact__DivContainer-sc-1ndm3on-0.eiDGHu > div > div > div > div > div > div > div > div:nth-child({i}) > div.Row--cell.Row--cellIsSpaced.EventHistory--item-col > div > a > div > div > div > div > img").get_attribute("src").replace("=s96", "=w600")
                item_name = driver.find_element_by_css_selector(f"#__next > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.FlexColumnreact__FlexColumn-sc-1wwz3hp-0.OpenSeaPagereact__DivContainer-sc-65pnmt-0.dBFmez.jYqxGr.ksFzlZ.fiudwD.App > main > div > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.ActivitySearchreact__DivContainer-sc-1pucb9u-0.dBFmez.jYqxGr.ehrjIH > div.Blockreact__Block-sc-1xf18x6-0.dBFmez.ActivitySearch--history > div.EventHistoryreact__DivContainer-sc-1ndm3on-0.eiDGHu > div > div > div > div > div > div > div > div:nth-child({i}) > div.Row--cell.Row--cellIsSpaced.EventHistory--item-col > div > a > div > span").text
                quantity = driver.find_element_by_css_selector(f"#__next > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.FlexColumnreact__FlexColumn-sc-1wwz3hp-0.OpenSeaPagereact__DivContainer-sc-65pnmt-0.dBFmez.jYqxGr.ksFzlZ.fiudwD.App > main > div > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.ActivitySearchreact__DivContainer-sc-1pucb9u-0.dBFmez.jYqxGr.ehrjIH > div.Blockreact__Block-sc-1xf18x6-0.dBFmez.ActivitySearch--history > div.EventHistoryreact__DivContainer-sc-1ndm3on-0.eiDGHu > div > div > div > div > div > div > div > div:nth-child({i}) > div.Row--cell.Row--cellIsSpaced.EventHistory--quantity-col").text
                from_user = driver.find_element_by_css_selector(f"#__next > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.FlexColumnreact__FlexColumn-sc-1wwz3hp-0.OpenSeaPagereact__DivContainer-sc-65pnmt-0.dBFmez.jYqxGr.ksFzlZ.fiudwD.App > main > div > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.ActivitySearchreact__DivContainer-sc-1pucb9u-0.dBFmez.jYqxGr.ehrjIH > div.Blockreact__Block-sc-1xf18x6-0.dBFmez.ActivitySearch--history > div.EventHistoryreact__DivContainer-sc-1ndm3on-0.eiDGHu > div > div > div > div > div > div > div > div:nth-child({i}) > div:nth-child(5) > div > a > span").text
                to_user = driver.find_element_by_css_selector(f"#__next > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.FlexColumnreact__FlexColumn-sc-1wwz3hp-0.OpenSeaPagereact__DivContainer-sc-65pnmt-0.dBFmez.jYqxGr.ksFzlZ.fiudwD.App > main > div > div.Blockreact__Block-sc-1xf18x6-0.Flexreact__Flex-sc-1twd32i-0.ActivitySearchreact__DivContainer-sc-1pucb9u-0.dBFmez.jYqxGr.ehrjIH > div.Blockreact__Block-sc-1xf18x6-0.dBFmez.ActivitySearch--history > div.EventHistoryreact__DivContainer-sc-1ndm3on-0.eiDGHu > div > div > div > div > div > div > div > div:nth-child({i}) > div:nth-child(6) > div > a > span").text
                embed = discord.Embed(title=item_name, description="", color=discord.Colour.from_rgb(255, 255, 255), url=url)
                embed.add_field(name="Type", value=event_type)
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="\u200b", value="\u200b")
                if price:
                    embed.add_field(name="Price", value=price)
                    embed.add_field(name="Quantity", value=quantity)
                else:
                    embed.add_field(name="Quantity", value=quantity)
                    embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="From", value=from_user)
                embed.add_field(name="To", value=to_user)
                embed.set_thumbnail(url=item_img)
                embed.set_footer(text=f"{event_type} on OpenSea {date}", icon_url="https://storage.googleapis.com/opensea-static/Logomark/Logomark-Blue.png")
                await channel.send(embed=embed)
                i += 1
                latest_trade_sent = tx_hash
        except Exception as e:
            pass

        last_trades_sent[account_url] = latest_trade_sent


@bot.event
async def on_ready():
    print(f'Bot started. Logged in as {bot.user.name}#{bot.user.discriminator}\n')
    update.start()


bot.run(config.token)
