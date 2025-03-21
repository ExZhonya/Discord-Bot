# /utils/views.py
import discord, json
from discord.ui import View, Button, Select

#"""!!!IMPORTANT!!! ALWAYS MAKE THE FUNCTIONS SEND A NEW MESSAGE INSTEAD OF EDITING!"""


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
        self.game["current_stage"] = 1
        self.game["current_turn_index"] = 0
        await interaction.message.delete()
        await interaction.channel.send(
            content="🧭 **The tower awaits...**",
            view=NextStageButton(self.interaction, self.game)
        )

    @discord.ui.button(label="🛒 Shop", style=discord.ButtonStyle.blurple)
    async def shop_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.game["host"]:
            await interaction.response.send_message("Only the host can access the shop!", ephemeral=True)
            return
        await interaction.message.delete()
        await interaction.channel.send(embed=self.build_shop_embed(), view=ShopMenu(self.interaction, self.game))

    @discord.ui.button(label="📦 Inventory", style=discord.ButtonStyle.gray)
    async def inventory_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.game["host"]:
            await interaction.response.send_message("Only the host can check the inventory!", ephemeral=True)
            return
        await interaction.message.delete()
        await interaction.channel.send(embed=self.build_inventory_embed(), view=self)

    @discord.ui.button(label="🧙 Character", style=discord.ButtonStyle.primary)
    async def character_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.game["host"]:
            await interaction.response.send_message("Only the host can view character sheets!", ephemeral=True)
            return
        await interaction.message.delete()
        for player in self.game["team"]:
            await interaction.channel.send(embed=self.build_character_embed(player), view=CharacterMenu(player, self.game))

    def build_inventory_embed(self):
        embed = discord.Embed(title="Inventory List", color=discord.Color.blue())
        for player, items in self.game["inventory"].items():
            embed.add_field(
                name=f"{player} (:moneybag: {self.game['gold'].get(player, 0)} gold)",
                value=f"**Weapon:** {items['Weapon'] or 'None'}\n**Armor:** {items['Armor'] or 'None'}\n**Potion:** {items['Potion'] or 'None'}",
                inline=False
            )
        return embed

    def build_shop_embed(self):
        return discord.Embed(title="Shop Menu", description="Choose a category:", color=discord.Color.purple())
    
    def build_character_embed(self, player_name):
        player_data = self.game["team_data"].get(player_name, {"class": "None", "stats": {}})
        stats = player_data.get("stats", {})
        embed = discord.Embed(title=f"Character Sheet", color=discord.Color.gold())
        embed.add_field(name="Name", value=f"<@{player_name}>", inline=False)
        embed.add_field(name="Class", value=player_data.get("class", "None").capitalize() or "None", inline=False)
        embed.add_field(name="HP", value=stats.get("HP", 0))
        embed.add_field(name="MP", value=stats.get("MP", 0))
        embed.add_field(name="Str", value=stats.get("Str", 0))
        embed.add_field(name="Int", value=stats.get("Int", 0))
        embed.add_field(name="Def", value=stats.get("Def", 0))
        embed.add_field(name="Dex", value=stats.get("Dex", 0))
        embed.add_field(name="Stats Available", value=stats.get("StatPoints", 0))
        return embed
    


class NextStageButton(View):
    def __init__(self, interaction, game):
        super().__init__()
        self.interaction = interaction
        self.game = game

    @discord.ui.button(label="Next Level", style=discord.ButtonStyle.red)
    async def next_level(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.game["host"]:
            await interaction.response.send_message("Only the host can proceed!", ephemeral=True)
            return

        await self.send_stage(interaction)

    async def send_stage(self, interaction):
        await send_stage_embed(interaction, self.game)


async def send_stage_embed(interaction, game):
    with open("data/stages.json", "r") as f:
        stages = json.load(f)

    stage_num = game.get("current_stage", 1)
    stage_data = stages.get(str(stage_num), None)

    if not stage_data:
        await interaction.channel.send("No more stages!")
        return

    total_hp = sum(mob["hp"] for mob in stage_data["monsters"])
    current_index = game.get("current_turn_index", 0)
    current_turn = game["team"][current_index % len(game["team"])]

    embed = discord.Embed(title="⚔️ Tower Progress Resumed!", color=discord.Color.gold())
    embed.add_field(name="🏰 Stage", value=f"{stage_num} ({stage_data['name']})", inline=False)
    embed.add_field(name="❤️ Health", value=f"{total_hp}/{total_hp}", inline=False)
    embed.add_field(name="🎯 Current Turn", value=f"{current_turn} (Player Turn)", inline=False)
    await interaction.channel.send(embed=embed)

    await interaction.channel.send(
        content=f"🎮 **{current_turn}'s Menu**",
        view=PlayerMenu(current_turn, game)
    )

    @discord.ui.button(label="Shop", style=discord.ButtonStyle.blurple)
    async def shop_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.game["host"]:
            await interaction.response.send_message("Only the host can access the shop!", ephemeral=True)
            return
        await interaction.message.delete()
        await interaction.channel.send(embed=self.build_shop_embed(), view=ShopMenu(self.interaction, self.game))

    @discord.ui.button(label="Inventory", style=discord.ButtonStyle.gray)
    async def inventory_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.game["host"]:
            await interaction.response.send_message("Only the host can check the inventory!", ephemeral=True)
            return
        await interaction.message.delete()
        await interaction.channel.send(embed=self.build_inventory_embed(), view=self)

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

    def build_shop_embed(self):
        return discord.Embed(title="Shop Menu", description="Choose a category:", color=discord.Color.purple())

class ShopMenu(View):
    def __init__(self, interaction, game):
        super().__init__()
        self.interaction = interaction
        self.game = game

    @discord.ui.button(label="Weapons", style=discord.ButtonStyle.primary)
    async def weapons_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await interaction.channel.send(embed=self.build_weapon_shop_embed(), view=WeaponShop(self.interaction, self.game))

    @discord.ui.button(label="Armor", style=discord.ButtonStyle.primary)
    async def armor_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await interaction.channel.send(embed=self.build_armor_shop_embed(), view=ArmorShop(self.interaction, self.game))

    @discord.ui.button(label="Potions", style=discord.ButtonStyle.primary)
    async def potions_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await interaction.channel.send(embed=self.build_potion_shop_embed(), view=PotionShop(self.interaction, self.game))

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

    def build_armor_shop_embed(self):
        embed = discord.Embed(title="Armor Shop 🛡️", description="Choose an item to buy:", color=discord.Color.dark_blue())
        embed.add_field(name="Leather Armor", value="💰 80 gold", inline=False)
        embed.add_field(name="Chainmail", value="💰 120 gold", inline=False)
        embed.add_field(name="Plate Armor", value="💰 250 gold", inline=False)
        return embed

    def build_potion_shop_embed(self):
        embed = discord.Embed(title="Potion Shop 🧪", description="Choose an item to buy:", color=discord.Color.dark_teal())
        embed.add_field(name="Health Potion", value="💰 50 gold", inline=False)
        embed.add_field(name="Mana Potion", value="💰 60 gold", inline=False)
        embed.add_field(name="Stamina Potion", value="💰 70 gold", inline=False)
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
        await interaction.channel.send(embed=ShopMenu(self.interaction, self.game).build_weapon_shop_embed(), view=ShopMenu(self.interaction, self.game))

    async def buy_item(self, interaction: discord.Interaction, item_name, price):
        player_name = interaction.user.name
        player_gold = self.game["gold"].get(player_name, 0)

        if player_gold < price:
            await interaction.response.send_message(f"❌ You don't have enough gold! ({player_gold}g)", ephemeral=True)
            return

        self.game["gold"][player_name] -= price
        self.game["inventory"][player_name]["Weapon"] = item_name

        await interaction.response.send_message(f"✅ {player_name} bought a **{item_name}** for {price} gold!", ephemeral=False)

class ArmorShop(View):
    def __init__(self, interaction, game):
        super().__init__()
        self.interaction = interaction
        self.game = game

    @discord.ui.button(label="Buy Leather Armor (80g)", style=discord.ButtonStyle.green)
    async def buy_leather(self, interaction: discord.Interaction, button: Button):
        await self.buy_item(interaction, "Leather Armor", 80)

    @discord.ui.button(label="Buy Chainmail (120g)", style=discord.ButtonStyle.green)
    async def buy_chainmail(self, interaction: discord.Interaction, button: Button):
        await self.buy_item(interaction, "Chainmail", 120)

    @discord.ui.button(label="Buy Plate Armor (250g)", style=discord.ButtonStyle.green)
    async def buy_plate(self, interaction: discord.Interaction, button: Button):
        await self.buy_item(interaction, "Plate Armor", 250)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await interaction.channel.send(embed=ShopMenu(self.interaction, self.game).build_armor_shop_embed(), view=ShopMenu(self.interaction, self.game))

    async def buy_item(self, interaction: discord.Interaction, item_name, price):
        player_name = interaction.user.name
        player_gold = self.game["gold"].get(player_name, 0)

        if player_gold < price:
            await interaction.response.send_message(f"❌ You don't have enough gold! ({player_gold}g)", ephemeral=True)
            return

        self.game["gold"][player_name] -= price
        self.game["inventory"][player_name]["Armor"] = item_name

        await interaction.response.send_message(f"✅ {player_name} bought **{item_name}** for {price} gold!", ephemeral=False)

class PotionShop(View):
    def __init__(self, interaction, game):
        super().__init__()
        self.interaction = interaction
        self.game = game

    @discord.ui.button(label="Buy Health Potion (50g)", style=discord.ButtonStyle.green)
    async def buy_health(self, interaction: discord.Interaction, button: Button):
        await self.buy_item(interaction, "Health Potion", 50)

    @discord.ui.button(label="Buy Mana Potion (60g)", style=discord.ButtonStyle.green)
    async def buy_mana(self, interaction: discord.Interaction, button: Button):
        await self.buy_item(interaction, "Mana Potion", 60)

    @discord.ui.button(label="Buy Stamina Potion (70g)", style=discord.ButtonStyle.green)
    async def buy_stamina(self, interaction: discord.Interaction, button: Button):
        await self.buy_item(interaction, "Stamina Potion", 70)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        await interaction.channel.send(embed=ShopMenu(self.interaction, self.game).build_potion_shop_embed(), view=ShopMenu(self.interaction, self.game))

    async def buy_item(self, interaction: discord.Interaction, item_name, price):
        player_name = interaction.user.name
        player_gold = self.game["gold"].get(player_name, 0)

        if player_gold < price:
            await interaction.response.send_message(f"❌ You don't have enough gold! ({player_gold}g)", ephemeral=True)
            return

        self.game["gold"][player_name] -= price
        self.game["inventory"][player_name]["Potion"] = item_name

        await interaction.response.send_message(f"✅ {player_name} bought a **{item_name}** for {price} gold!", ephemeral=False)


class PlayerMenu(View):
    def __init__(self, player_name, game):
        super().__init__()
        self.player_name = player_name
        self.game = game

    @discord.ui.button(label="🗡️ Attack", style=discord.ButtonStyle.red)
    async def attack(self, interaction: discord.Interaction, button: Button):
        await self.take_action(interaction)

    @discord.ui.button(label="✨ Skills", style=discord.ButtonStyle.blurple)
    async def skills(self, interaction: discord.Interaction, button: Button):
        await self.take_action(interaction)

    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.grey)
    async def defend(self, interaction: discord.Interaction, button: Button):
        await self.take_action(interaction)

    @discord.ui.button(label="🎒 Bag", style=discord.ButtonStyle.green)
    async def bag(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.player_name:
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return
        await interaction.channel.send(f"{self.player_name} opens their Bag!")

    @discord.ui.button(label="🧙 Character", style=discord.ButtonStyle.primary)
    async def character(self, interaction: discord.Interaction, button: Button):
        if interaction.user.name != self.player_name:
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return
        await interaction.channel.send(view=CharacterMenu(self.player_name, self.game))

    async def take_action(self, interaction):
        if interaction.user.name != self.player_name:
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return
        self.game["current_turn_index"] = (self.game.get("current_turn_index", 0) + 1) % len(self.game["team"])
        await send_stage_embed(interaction, self.game)


class CharacterMenu(View):
    def __init__(self, player_name, game):
        super().__init__()
        self.player_name = player_name
        self.game = game
        self.add_item(CharacterSelect(player_name, game))

class CharacterSelect(Select):
    def __init__(self, player_name, game):
        self.player_name = player_name
        self.game = game
        options = [
            discord.SelectOption(label="Classes", description="View available classes."),
            discord.SelectOption(label="Stats", description="View your character's stats.")
        ]
        super().__init__(placeholder="Choose an option", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.name != self.player_name:
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        if self.values[0] == "Classes":
            await interaction.channel.send(embed=self.build_class_embed())
        elif self.values[0] == "Stats":
            await interaction.channel.send(embed=self.build_stats_embed())

    def build_class_embed(self):
        embed = discord.Embed(title="Available Classes", color=discord.Color.orange())
        embed.add_field(name="Warrior", value="Strong physical attacker.", inline=False)
        embed.add_field(name="Archer", value="High accuracy ranged attacker.", inline=False)
        embed.add_field(name="Mage", value="High magic damage.", inline=False)
        embed.add_field(name="Priest", value="Healer and support.", inline=False)
        return embed

    def build_stats_embed(self):
        stats = self.game.get("team_data", {}).get(self.player_name, {}).get("stats", {})
        embed = discord.Embed(title=f"{self.player_name}'s Stats", color=discord.Color.teal())
        embed.add_field(name="HP", value=stats["HP"])
        embed.add_field(name="MP", value=stats["MP"])
        embed.add_field(name="Str", value=f"{stats['Str']} (+Physical DMG)")
        embed.add_field(name="Int", value=f"{stats['Int']} (+Magic DMG)")
        embed.add_field(name="Def", value=f"{stats['Def']} (Reduces Damage)")
        embed.add_field(name="Dex", value=f"{stats['Dex']} (+Accuracy, +Dodge)")
        embed.add_field(name="Stat Points Available", value=stats["StatPoints"])
        embed.add_field(name="EXP", value=f"{stats['EXP']}%")
        return embed


async def continue_game_logic(ctx, game):
    # Resend current stage info
    current_stage = game.get("current_stage", 1)
    embed = discord.Embed(title=f"Stage {current_stage} Progress", description="Game progress resumed.", color=discord.Color.gold())
    embed.add_field(name="Team Members", value="\n".join(game["team"]))
    await ctx.send(embed=embed)

    # Resend player menus
    for player_name in game["team"]:
        await ctx.send(
            content=f"🎮 **{player_name}'s Menu**",
            view=PlayerMenu(player_name, game)
        )