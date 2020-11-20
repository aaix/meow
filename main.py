import discord
import base64
import config


class meow(discord.Client):
    def __init__(self):
        super().__init__()
        self.futures = list()

        self.reg = {
            "cc":self.clearChannel,
            "dc":self.clearDM,
            "stop":self.cancelFutures,
            "!":self.cancelFutures,
        }

        # Globals
        self.prefix = config.prefix
        self.lock = False
        # Skip on_ready

        if not config.token.startswith("mfa."):
            self.id = int(base64.decodebytes(bytes(config.token.split(".")[0],encoding="utf-8")))
            print(f"Ready as {self.id}")

        else:
            print("Waiting for ready.")
            self.lock = True
            self.id = 0

        # Run
        self.run(config.token,bot=False,reconnect=True)

    async def on_message(self,message):
        if message.author.id != self.id:
            return
        await self.handle(message.content,message)

    async def handle(self,command,msg):
        if not command.startswith(self.prefix):
            return
        handler = self.reg.get(command[len(self.prefix):])

        if handler:
            future = self.loop.create_task(self.invoke(handler,msg))
            if handler != self.cancelFutures:
                self.futures.append(future)
            try:
                await future
            except Exception as e:
                print(f"Exception in command '{command}' invokation {e.__class__.__qualname__} - {e}")
            if handler != self.cancelFutures:
                self.futures.remove(future)

    async def invoke(self,coro,msg):
        guild = msg.guild
        channel = msg.channel
        me = msg.author

        print(f"\nInvoking command {coro.__name__}")
        if await coro(guild,channel,me):
            try:
                await msg.delete()
            except Exception:
                pass
        print(f"Completed invoking command {coro.__name__}")

    async def clearDM(self,guild,channel,me):
        print(f"Clearing {len(self.private_channels)} channels")
        for channel in self.private_channels:
            if not isinstance(channel,discord.DMChannel):
                continue
            try:
                async for m in channel.history(limit=config.dm):
                    if m.author.id == self.id:
                        await m.delete()
            except Exception:
                print(f"Skipping DM with {channel.recipient} due to error")
                continue
        return True

    async def clearChannel(self,guild,channel,me):
        async for m in channel.history(limit=config.channel):
            if m.author.id != self.id:
                continue
            try:
                await m.delete()
            except Exception:
                print(f"Skipping '{m.content}' due to error")
        return True

    async def cancelFutures(self,guild,channel,me):
        futures = len(self.futures)
        for future in self.futures:
            future.cancel()
            self.futures.remove(future)
        await channel.send(f"\U00002714 - {futures} futures",delete_after=5)

    async def on_ready(self):
        if self.lock:
            self.lock = False
            self.id = self.user.id
            print(f"Ready as {self.id}")


meow()
