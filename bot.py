import os
import discord
from discord.ext import commands
import requests
import json
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot Discord est en ligne !"


def run_server():
    app.run(host="0.0.0.0", port=8080)


DB_FILE = "brawlhalla_users.json" #replace the db by your own 


def load_database():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"Users": {}}


def get_user_id(pseudo):
    database = load_database()
    return database["Users"].get(pseudo, None)


def info_user(id):
    url = f'https://bhapi.338.rocks/v1/stats/id?brawlhalla_id={id}'
    response = requests.get(url)
    data = response.json()

    user_name = data['data']['name']
    legends = data['data']['legends']
    clan = data['data']['clan']

    top_legend = max(legends, key=lambda x: x['level'])
    top_legend_name = top_legend['legend_name_key']

    clan_name = clan['clan_name'] if clan else None

    result = {
        'user_name': user_name,
        'top_legend': top_legend_name,
        'clan': clan_name
    }

    return result


def ranking_user(id):
    url = f'https://bhapi.338.rocks/v1/ranked/id?brawlhalla_id={id}'
    response = requests.get(url)
    data = response.json()

    rating1 = data['data']['rating']
    peak_rating1 = data['data']['peak_rating']
    region = data['data']['region']
    ranked_legends = data['data']['legends']
    teams = data['data']['2v2']

    top_ranked_legends = sorted(ranked_legends,
                                key=lambda x: x['rating'],
                                reverse=True)[:3]

    top_team = max(teams, key=lambda x: x['rating'])
    rating2 = top_team['rating']
    peak_rating2 = top_team['peak_rating']
    team_name = top_team['teamname']

    result = {
        'rating 1v1':
        rating1,
        'peak_rating 1v1':
        peak_rating1,
        'region':
        region,
        'top_ranked_legends':
        [legend['legend_name_key'] for legend in top_ranked_legends],
        'rating 2v2':
        rating2,
        'peak_rating 2v2':
        peak_rating2,
        'team_name 2v2':
        team_name
    }

    return result


@bot.command()
async def leaderboard(ctx, *, pseudo: str):
    brawlhalla_id = get_user_id(pseudo)
    if not brawlhalla_id:
        await ctx.send(
            f"Aucun ID Brawlhalla trouvé pour l'utilisateur **{pseudo}**. Ajoutez-le dans la base de données."
        )
        return

    try:
        user_info = info_user(brawlhalla_id)
        ranking_info = ranking_user(brawlhalla_id)

        embed = discord.Embed(title=f"Leaderboard de {user_info['user_name']}",
                              color=discord.Color.blue())
        embed.add_field(
            name="Informations générales",
            value=(f"**Nom :** {user_info['user_name']}\n"
                   f"**Clan :** {user_info['clan'] or 'Aucun'}\n"
                   f"**Top légende :** {user_info['top_legend']}\n"),
            inline=False)
        embed.add_field(
            name="Classement 1v1",
            value=
            (f"**Rating :** {ranking_info['rating 1v1']}\n"
             f"**Peak Rating :** {ranking_info['peak_rating 1v1']}\n"
             f"**Top 3 légendes classées :** {', '.join(ranking_info['top_ranked_legends'])}\n"
             ),
            inline=False)
        embed.add_field(
            name="Classement 2v2",
            value=
            (f"**Rating :** {ranking_info['rating 2v2']}\n"
             f"**Peak Rating :** {ranking_info['peak_rating 2v2']}\n"
             f"**Équipe principale :** {ranking_info['team_name 2v2'] or 'Aucune'}\n"
             ),
            inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(
            f"Erreur lors de la récupération des données pour **{pseudo}** : {e}"
        )


@bot.command()
async def users(ctx):
    database = load_database()
    users = database["Users"]
    if not users:
        await ctx.send("Aucun utilisateur enregistré.")
        return

    message = "**Utilisateurs enregistrés :**\n"
    for pseudo, brawlhalla_id in users.items():
        message += f"- {pseudo} : {brawlhalla_id}\n"

    await ctx.send(message)


def main():
    token = os.environ['token_bot_discord'] #Replace the token by your own
    Thread(target=run_server).start()
    bot.run(token)


if __name__ == "__main__":
    main()
