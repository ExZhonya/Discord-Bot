# /utils/views.py
import discord
from discord.ui import View, Button

class GameMenu(View):
    def __init__(self, interaction, game):
        super().__init__()
        self.interaction = interaction
        self.game = game

    @discord.ui.button(label="Start Adventure", style=discord.ButtonStyle.green)
    async def start_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.game["host"]:
            await interaction.response.send_message("Only the host can start!", ephemeral=True)
            return
        await interaction.message.delete()
        await interaction.channel.send("🌍 The adventure begins!")

    @discord.ui.button(label="Shop", style=discord.ButtonStyle.blurple)
    async def shop_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.game["host"]:
            await interaction.response.send_message("Only the host can access the shop!", ephemeral=True)
            return
        await interaction.message.delete()
        await interaction.channel.send(embed=discord.Embed(title="Shop Menu", description="Choose a category:", color=discord.Color.purple()), view=ShopMenu(self.interaction, self.game))

    @discord.ui.button(label="Inventory", style=discord.ButtonStyle.gray)
    async def inventory_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.game["host"]:
            await interaction.response.send_message("Only the host can check the inventory!", ephemeral=True)
            return
        await interaction.message.delete()
        await interaction.channel.send(embed=self.build_inventory_embed())

    def build_inventory_embed(self):
        embed = discord.Embed(title="Inventory List", color=discord.Color.blue())
        for player, items in self.game["inventory"].items():
            embed.add_field(
                name=f"{player} (💰 {self.game['gold'].get(player, 0)} gold)",
                value=f"**Weapon:** {items['Weapon'] or 'None'}\n"
                      f"**Armor:** {items['Armor'] or 'None'}\n"
                      f"**Potion:** {items['Potion'] or 'None'}",
                inline=False
            )
        return embed

class ShopMenu(View):
    def __init__(self, interaction, game):
        super().__init__()
        self.interaction = interaction
        self.game = game

    @discord.ui.button(label="Weapons", style=discord.ButtonStyle.primary)
    async def weapons_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await interaction.channel.send(embed=self.build_weapon_shop_embed(), view=WeaponShop(self.interaction, self.game))

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await interaction.channel.send(embed=discord.Embed(title="Game Menu", description="Choose an option:", color=discord.Color.blue()), view=GameMenu(self.interaction, self.game))

    def build_weapon_shop_embed(self):
        embed = discord.Embed(title="Weapons Shop ⚔️", description="Choose an item to buy:", color=discord.Color.dark_gold())
        embed.add_field(name="Sword", value="💰 100 gold", inline=False)
        embed.add_field(name="Bow", value="💰 150 gold", inline=False)
        embed.add_field(name="Hammer", value="💰 200 gold", inline=False)
        return embed

class WeaponShop(View):
    def __init__(self, interaction, game):
        super().__init__()
        self.interaction = interaction
        self.game = game

    @discord.ui.button(label="Buy Sword (100g)", style=discord.ButtonStyle.green)
    async def buy_sword(self, interaction: discord.Interaction, button: Button):
        await self.buy_item(interaction, "Sword", 100)

    @discord.ui.button(label="Buy Bow (150g)", style=discord.ButtonStyle.green)
    async def buy_bow(self, interaction: discord.Interaction, button: Button):
        await self.buy_item(interaction, "Bow", 150)

    @discord.ui.button(label="Buy Hammer (200g)", style=discord.ButtonStyle.green)
    async def buy_hammer(self, interaction: discord.Interaction, button: Button):
        await self.buy_item(interaction, "Hammer", 200)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await interaction.channel.send(embed=discord.Embed(title="Shop Menu", description="Choose a category:", color=discord.Color.purple()), view=ShopMenu(self.interaction, self.game))

    async def buy_item(self, interaction: discord.Interaction, item_name, price):
        player_name = interaction.user.name
        player_gold = self.game["gold"].get(player_name, 0)

        if player_gold < price:
            await interaction.response.send_message(f"❌ You don't have enough gold! ({player_gold}g)", ephemeral=True)
            return

        self.game["gold"][player_name] -= price
        self.game["inventory"][player_name]["Weapon"] = item_name

        await interaction.response.send_message(f"✅ {player_name} bought a **{item_name}** for {price} gold!", ephemeral=False)
