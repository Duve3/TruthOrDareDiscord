"""
This file is made, so essentially the entire codebase could be updated, and I could just run !restart and refresh the
codebase
"""
from log import setupLogging
from discord.ext import commands
import sys
import logging
from main import main
import json
from main import client
import os


@client.command(name="restart")
async def restart(ctx: commands.Context):
    logging.getLogger("main").info("RESTARTING")
    if ctx.author.id != 680116696819957810:
        return await ctx.send("that's not nice buddy")

    await ctx.reply("Restarting... (last sendable message before shutdown!)")

    await client.saveDB()
    try:
        logging.getLogger("main").info("RESTARTING: client.close")
        await client.close()
    except:  # noqa ; the only way to make it work
        # nothing stops me
        pass
    logging.getLogger("main").info("RESTARTING: os.execv")
    os.execv(sys.executable, ["python"] + sys.argv)


@client.command(name="shutdown")
async def shutdown(ctx: commands.Context):
    logging.getLogger("main").info("SHUTTING DOWN")
    if ctx.author.id != 680116696819957810:
        return await ctx.send("that's not nice buddy")

    await ctx.reply("Shutting down.")

    await client.saveDB()
    await client.close()


if __name__ == "__main__":
    # setup
    setupLogging("discord", level=logging.INFO)
    setupLogging("discord.http", level=logging.INFO)
    try:
        # startup
        main()
    finally:
        # cleanup
        with open("./db.json", "w") as db:
            db.write(json.dumps(client.db))
