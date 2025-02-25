from discord.ext import commands
import discord.ui
import discord
from log import setupLogging
import random
from TruthOrDareBot.main import Client


def randomTruth(bot: Client, db: dict) -> str:
    Truths: list[str] = db["truths"]

    choice = random.choice(Truths)

    if choice in bot.recentTruths:
        return randomTruth(bot, db)

    bot.recentTruths.append(choice)
    if len(bot.recentTruths) >= 100:
        bot.recentTruths.pop(0)

    return choice


def randomDare(bot, db: dict) -> str:
    Dares: list[str] = db["dares"]

    choice = random.choice(Dares)

    if choice in bot.recentDares:
        return randomDare(bot, db)

    bot.recentDares.append(choice)
    if len(bot.recentDares) >= 100:
        bot.recentDares.pop(0)

    return choice


def locateTruth(db: dict, truth) -> int:
    return int("1" + str(db["truths"].index(truth)))


def locateDare(db: dict, dare) -> int:
    return int("2" + str(db["dares"].index(dare)))


def fromID(db: dict, identifier: int) -> str:
    if int(str(identifier)[0]) == 2:
        return db["dares"][int(str(identifier)[1::])]
    else:
        return db["truths"][int(str(identifier)[1::])]


def removeFromDB(db: dict, identifier: int):
    if int(str(identifier)[0]) == 2:
        db["dares"].remove(fromID(db, identifier))
    else:
        db["truths"].remove(fromID(db, identifier))


def modifyFromDB(db: dict, identifier: int, newValue: str):
    if int(str(identifier)[0]) == 2:
        db["dares"][int(str(identifier)[1::])] = newValue
    else:
        db["truths"][int(str(identifier)[1::])] = newValue


class TruthEmbed(discord.Embed):
    def __init__(self, bot, db: dict, author: list[str, str]):
        super().__init__(color=discord.Color.from_rgb(25, 165, 230))

        self.title = randomTruth(bot, db)

        self.set_author(name=f"Requested by {author[0]}", icon_url=author[1])

        self.set_footer(text=f"Type: Truth | ID: {locateTruth(db, self.title)} | Made with love by Duve3")

        if random.randint(1, 100) == 2:
            self.set_footer(text=f"Type: Truth | ID: {locateTruth(db, self.title)} | Made with hatred by Duve3")


class DareEmbed(TruthEmbed):
    def __init__(self, bot, db: dict, author: list[str, str]):
        super().__init__(bot, db, author)

        self.color = discord.Color.from_rgb(235, 60, 45)
        self.title = randomDare(bot, db)

        self.set_footer(text=f"Type: Dare | ID: {locateDare(db, self.title)} | Made with love by Duve3")


class ReportEmbed(discord.Embed):
    def __init__(self, db: dict, isDare: bool, identifier: int, reasoning: str, name: str):
        super().__init__()
        self.title = f"Report | {'Dare' if isDare else 'Truth'}#{identifier}"
        self.add_field(name="Reasoning", value=f"\"{reasoning}\"")
        self.add_field(name="String Format of item", value=f"\"{fromID(db, identifier)}\"")

        self.set_footer(text=f"Report was made by {name}")


class AllView(discord.ui.View):
    def __init__(self, bot, db: dict):
        super().__init__(timeout=None)
        self.db = db
        self.bot = bot

    @discord.ui.button(label="Truth", custom_id="truth", disabled=False, style=discord.ButtonStyle.green)
    async def TruthButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        embed = TruthEmbed(self.bot, self.db, [user.display_name, user.display_avatar.url])

        await interaction.response.send_message(embed=embed, view=AllView(self.bot, self.db))

    @discord.ui.button(label="Dare", custom_id="dare", disabled=False, style=discord.ButtonStyle.red)
    async def DareButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        embed = DareEmbed(self.bot, self.db, [user.display_name, user.display_avatar.url])

        await interaction.response.send_message(embed=embed, view=AllView(self.bot, self.db))

    @discord.ui.button(label="Random", custom_id="random", disabled=False, style=discord.ButtonStyle.blurple)
    async def RandomButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        if random.randint(0, 1) == 1:
            embed = TruthEmbed(self.bot, self.db, [user.display_name, user.display_avatar.url])
        else:
            embed = DareEmbed(self.bot, self.db, [user.display_name, user.display_avatar.url])
            
        await interaction.response.send_message(embed=embed, view=AllView(self.bot, self.db))


class ReportView(discord.ui.View):
    def __init__(self, bot, db: dict, identifier):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = db
        self.identifier = identifier
        self.isDare = int(str(identifier)[0]) == 2

    @discord.ui.button(label="Keep", custom_id="keep", disabled=False, style=discord.ButtonStyle.green)
    async def KeepButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"Keeping the {'Dare' if self.isDare else 'Truth'}! (ID: {self.identifier})")

    @discord.ui.button(label="Remove", custom_id="remove", disabled=False, style=discord.ButtonStyle.red)
    async def RemoveButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        removeFromDB(self.db, self.identifier)
        await interaction.response.send_message(
            f"Removing the {'Dare' if self.isDare else 'Truth'}! (ID: {self.identifier})")

    @discord.ui.button(label="Modify", custom_id="modify", disabled=False, style=discord.ButtonStyle.blurple)
    async def ModifyButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.followup.send("Send what you want to be the new version of the dare (REMEMBER PUNCTUATION!)")
        old = fromID(self.db, self.identifier)
        new: discord.Message = await self.bot.wait_for('message', timeout=120)

        modifyFromDB(self.db, self.identifier, new.content)

        await interaction.followup.send(
            f"Modifying the {'Dare' if self.isDare else 'Truth'} from \"{old}\" to \"{fromID(self.db, self.identifier)}\"! (ID: {self.identifier})")


class TruthOrDareCog(commands.Cog):
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self.db = bot.db
        self.logger = setupLogging(f"{self.__class__.__name__}")

    @commands.hybrid_command(name="truth", description="Get a random Truth.")
    async def truth(self, ctx: commands.Context):
        user = ctx.author
        await ctx.reply(embed=TruthEmbed(self.bot, self.db, [user.display_name, user.display_avatar.url]), view=AllView(self.bot, self.db))

    @commands.hybrid_command(name="dare", description="Get a random Dare.")
    async def dare(self, ctx: commands.Context):
        user = ctx.author
        await ctx.reply(embed=DareEmbed(self.bot, self.db, [user.display_name, user.display_avatar.url]), view=AllView(self.bot, self.db))

    @commands.hybrid_command(name="random", description="Get a truth or a dare randomly.")
    async def random(self, ctx: commands.Context):
        user = ctx.author

        if random.randint(0, 1) == 1:
            embed = TruthEmbed(self.bot, self.db, [user.display_name, user.display_avatar.url])
        else:
            embed = DareEmbed(self.bot, self.db, [user.display_name, user.display_avatar.url])

        await ctx.reply(embed=embed, view=AllView(self.bot, self.db))

    @commands.hybrid_command(name="report", description="report a truth or a dare")
    async def report(self, ctx: commands.Context, identifier: int, reasoning: str = "No Reason Provided"):
        isDare = int(str(identifier)[0]) == 2

        await self.bot.get_user(680116696819957810).send(
            embed=ReportEmbed(self.db, isDare, identifier, reasoning, ctx.author.display_name),
            view=ReportView(self.bot, self.db, identifier))

        await ctx.reply(f"Successfully reported {'Dare' if isDare else 'Truth'} id {identifier}")

    @commands.hybrid_command(name="from_id", description="get a truth or a dare from their ID")
    async def sendFromID(self, ctx: commands.Context, identifier: int):
        await ctx.reply(f"ID#{identifier} is: \"{fromID(self.db, identifier)}\"")

    @commands.hybrid_command(name="how_many_truths", description="Informs you of how many truths there are")
    async def truthsAmount(self, ctx: commands.Context):
        await ctx.reply(f"There is: {str(len(self.db['truths']))} truths in the database currently!")

    @commands.hybrid_command(name="how_many_dares", description="Informs you of how many dares there are")
    async def daresAmount(self, ctx: commands.Context):
        await ctx.reply(f"There is: {str(len(self.db['dares']))} dares in the database currently!")

    # doing something when the cog gets loaded
    async def cog_load(self):
        self.logger.debug(f"{self.__class__.__name__} loaded!")

    # doing something when the cog gets unloaded
    async def cog_unload(self):
        self.logger.debug(f"{self.__class__.__name__} unloaded!")


# usually you’d use cogs in extensions,
# you would then define a global async function named 'setup', and it would take 'bot' as its only parameter
async def setup(bot):
    # finally, adding the cog to the bot
    await bot.add_cog(TruthOrDareCog(bot=bot))
