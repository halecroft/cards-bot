from typing import Optional
import random
from webbrowser import Galeon

import discord
from discord import app_commands, ui

GUILD_ID_LIST = [1022006302471372850]
MY_GUILDS = []

for guild_id in GUILD_ID_LIST:
    MY_GUILDS.append(discord.Object(id=guild_id))


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        for guild_item in MY_GUILDS:
            self.tree.copy_global_to(guild=guild_item)
            await self.tree.sync(guild=guild_item)

openGames = []


class GameInstance():
    nextGameID = 0

    def __init__(self, startingInteraction, gameShortName):
        if gameShortName == "cah":
            self.game = cahInstance(self)
        
        self.startingInteraction = startingInteraction
        self.players = []
        self.startingPlayer = startingInteraction.user
        self.id = GameInstance.nextGameID
        GameInstance.nextGameID += 1

        self.players.append(Player(startingInteraction.user))
        self.status = "OPEN" #OPEN, IN PROGRESS OPEN, IN PROGRESS FULL, CLOSED

    def addPlayer(self, player):
        newPlayer = Player(player, self)
        self.game.addPlayer(newPlayer)
        self.players.append(newPlayer)

class Player():
    def __init__(self, player, gameInstance):
        self.id = player.id
        if player.nick is None:
            self.displayName = player.name
        else:
            self.displayName = player.nick

        self.gameInstance = gameInstance

        gameInstance.game.addPlayer(self)

class cahSettings(ui.view):
    def __init__(self, cahInstance) -> None:
        super().__init__(timeout = None)
        self.cahInstance = cahInstance
        self.add_item(cahDeckSelect(self.cahInstance))

        #@ui.button(label="Start", style=discord.ButtonStyle.green, custom_id="start_button")
            
        #@ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel_button")

class cahDeckSelect(ui.Select):
    def __init__(self, cahInstance):
        self.cahInstance = cahInstance
        options=[
            discord.SelectOption(label="US",emoji="🇺🇸",description="The standard US CAH deck"),
            discord.SelectOption(label="Thundadeck",emoji=":thundamoo:",description="A custom deck with Thundamoo stories & server cards")
            ]
        super().__init__(placeholder="Select your deck", max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        self.cahInstance.deckName = self.values[0]

class cahBlackCard():
    def __init__(self, pickNum, text):
        self.text = text
        self.pickNum = pickNum

class cahInstance():
    gameName = "Cards Against Humanity"
    shortName = "cah"
    maxPlayers = 8
    minPlayers = 3
    handSize = 7
    deckList = ["US", "Thundadeck"]

    def __init__(self, gameInstance):
        self.gameInstance = gameInstance
        self.whiteDrawDeck = []
        self.blackDrawDeck = []
        self.whiteDiscardDeck = []
        self.blackDiscardDeck = []

        #TODO Config: Select Deck
        self.deckName = ""

        whiteCardDoc = open("Games/cah/decks/" + self.deckName + " White Cards.txt", "r")
        for cardText in whiteCardDoc:
            self.whiteDrawDeck.append(cardText)
        whiteCardDoc.close()
        random.shuffle(self.whiteDrawDeck)

        blackCardDoc = open("Games/cah/decks/" + self.deckName + " Black Cards.txt", "r")
        for cardText in blackCardDoc:
            cardObject = cahBlackCard(cardText[0:1], cardText[2::])
            self.blackDrawDeck.append(cardObject)
        blackCardDoc.close()
        random.shuffle(self.blackDrawDeck)

    def addPlayer(self, player):
        player.hand = []
        player.blackCardCount = 0
        player.gameInstance.game.buildHand(self)
        for i in range(self.handSize):
            player.hand.append(self.whiteDrawDeck.pop(0))

        


#-----------------------------------------------------------------------------------------------------------------------

intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.tree.command()
@app_commands.rename(gameName="game")
@app_commands.describe(gameName="Which game you want to play")
@app_commands.choices(gameName=[
    app_commands.Choice(name="Cards Against Humanity", value="cah"),
    app_commands.Choice(name="Don't pick this one", value="don't1"),
    app_commands.Choice(name="Don't pick this one either", value="don't2"),
])
async def play(interaction: discord.Interaction, gameName: app_commands.Choice[str]):
    try:
        newGame = GameInstance(interaction, gameName)
    except:
        pass
    await interaction.response.send_message("You want to play " + gameName.name)


@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@client.tree.command()
@app_commands.describe(
    first_value='The first value you want to add something to',
    second_value='The value you want to add to the first value',
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')


# The rename decorator allows us to change the display of the parameter on Discord.
# In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
# Note that other decorators will still refer to it as `text_to_send` in the code.
@client.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(member='The member you want to get the joined date from; defaults to the user who uses the command')
async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined {discord.utils.format_dt(member.joined_at)}')


# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.

# This context menu command only works on members
@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}')


# This context menu command only works on messages
@client.tree.context_menu(name='Report to Moderators')
async def report_message(interaction: discord.Interaction, message: discord.Message):
    # We're sending this response message with ephemeral=True, so only the command executor can see it
    await interaction.response.send_message(
        f'Thanks for reporting this message by {message.author.mention} to our moderators.', ephemeral=True
    )

    # Handle report by sending it into a log channel
    log_channel = interaction.guild.get_channel(0)  # replace with your channel id

    embed = discord.Embed(title='Reported Message')
    if message.content:
        embed.description = message.content

    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    embed.timestamp = message.created_at

    url_view = ui.View()
    url_view.add_item(ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))

    await log_channel.send(embed=embed, view=url_view)


client.run('token')