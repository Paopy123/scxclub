import discord
from discord.ext import commands
from discord import ui

# Set up intents properly
intents = discord.Intents.default()
intents.message_content = True  
intents.guilds = True           
intents.members = True          

# Initialize the bot using discord.Bot for slash commands and interaction handling
bot = commands.Bot(command_prefix="!", intents=intents)

# Step 1: Basic Request Form
class RequestFormStep1(ui.Modal, title="Financial Request - Step 1"):
    name = ui.TextInput(label="Requester Nickname", style=discord.TextStyle.short)
    purpose = ui.TextInput(label="Purchased Items", style=discord.TextStyle.short)
    reason = ui.TextInput(label="Description", style=discord.TextStyle.long)
    amount = ui.TextInput(label="Total (THB)", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        # Send a button to proceed to Step 2 instead of another modal directly
        await interaction.response.send_message(
            "✅ Step 1 submitted successfully! Click the button below to continue with **Bank Details**.",
            view=Step2ButtonView(self.name, self.purpose, self.reason, self.amount),
            ephemeral=True
        )

# Button View to Trigger Step 2 Modal
class Step2ButtonView(ui.View):
    def __init__(self, name, purpose, reason, amount):
        super().__init__()
        self.name = name
        self.purpose = purpose
        self.reason = reason
        self.amount = amount

    @ui.button(label="Proceed to Bank Details", style=discord.ButtonStyle.primary)
    async def proceed_to_step2(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RequestFormStep2(self.name, self.purpose, self.reason, self.amount))

# Step 2: Bank Details Form
class RequestFormStep2(ui.Modal, title="Financial Request - Step 2"):
    def __init__(self, name, purpose, reason, amount):
        super().__init__()
        self.name = name
        self.purpose = purpose
        self.reason = reason
        self.amount = amount

    bank_account_name = ui.TextInput(label="Full Name (bank account)", style=discord.TextStyle.short)
    bank_account = ui.TextInput(label="Account Number", style=discord.TextStyle.short)
    bank_name = ui.TextInput(label="Bank (e.g. SCB)", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("📎 Please upload the **Tax Invoice** (.pdf or .jpg).")

        def check(m):
            return m.author == interaction.user and m.attachments

        try:
            msg = await bot.wait_for("message", check=check, timeout=120)
            invoice_file = msg.attachments[0]
        except TimeoutError:
            await interaction.followup.send("⏰ Time expired! Request canceled.", ephemeral=True)
            return

        # Send the request with the approval button to the finance-approval channel
        channel = discord.utils.get(interaction.guild.channels, name="finance-approval")
        if not channel:
            await interaction.followup.send("❌ Cannot find the channel `finance-approval`.", ephemeral=True)
            return

        # Embed with request details
        embed = discord.Embed(title="📩 New Financial Request", color=discord.Color.blue())
        embed.add_field(name="Requester Nickname", value=self.name, inline=True)
        embed.add_field(name="Purchased Items", value=self.purpose, inline=True)
        embed.add_field(name="Description", value=self.reason, inline=False)
        embed.add_field(name="Total (THB)", value=self.amount, inline=True)
        embed.add_field(name="Full Name", value=self.bank_account_name, inline=True)
        embed.add_field(name="Account Number", value=self.bank_account, inline=True)
        embed.add_field(name="Bank", value=self.bank_name, inline=True)
        embed.add_field(name="📎 Tax Invoice", value=f"[Click to View](<{invoice_file.url}>)", inline=False)

        # ✅ **FIXED: Included 'self.purpose' in ApprovalButton**
        await channel.send(embed=embed, view=ApprovalButton(self.name, self.purpose, self.amount, self.bank_account_name, self.bank_account, self.bank_name, msg.channel))
        await interaction.followup.send("✅ Your request has been sent for approval.", ephemeral=True)

# Approval Button for Admins
class ApprovalButton(ui.View):
    def __init__(self, requester, purpose, amount, bank_account_name, bank_account, bank_name, original_channel):
        super().__init__()
        self.purpose = purpose
        self.requester = requester
        self.amount = amount
        self.bank_account_name = bank_account_name
        self.bank_account = bank_account
        self.bank_name = bank_name
        self.original_channel = original_channel

    @ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("📎 Please upload the **Payment Slip**.")

        def check(m):
            return m.author == interaction.user and m.attachments

        try:
            msg = await bot.wait_for("message", check=check, timeout=120)
            slip_file = msg.attachments[0]

            # Send confirmation back to the original channel
            await self.original_channel.send(
                f"✅ **The financial request has been approved!**\n"
                f"🛒 **Purchased Items:** {self.purpose}\n"
                f"📎 **Payment Slip:** {slip_file.url}\n"
                f"📌 **Total Amount:** {self.amount} THB\n"
                f"🏦 **Full Name (bank account):** {self.bank_account_name}\n"
                f"🏦 **Bank:** {self.bank_name}\n"
                f"🏦 **Account Number:** {self.bank_account}"
            )
            await interaction.followup.send("✅ Approval completed and confirmation sent.", ephemeral=True)
        except TimeoutError:
            await interaction.followup.send("⏰ Time expired for slip upload.", ephemeral=True)

# Slash command to initiate the financial request
@bot.tree.command(name="request", description="Open Financial Request Form.")
async def request(interaction: discord.Interaction):
    await interaction.response.send_modal(RequestFormStep1())

# Sync the slash commands on bot startup
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot is online as {bot.user}")

# Run the bot (ensure to replace with your actual token)
bot.run('MTMyNTExODc3MzY5ODQ5NDQ2NA.Ga2UTP.F0eay90nAM45kwo8NagCNXP-rkTM5_Nw00_3NA')
