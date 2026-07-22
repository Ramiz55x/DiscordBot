import discord
from discord.ext import commands
import json
from groq import Groq as G
import asyncio
import re
import os
from datetime import timedelta

# --- إضافة خادم ويب مصغر (Keep Alive) لإرضاء منصة الاستضافة Render ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "UI Bot is Running Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# تشغيل السيرفر المصغر في الخلفية
keep_alive()
# -----------------------------------------------------------------

MODEL = "llama-3.3-70b-versatile"

# ملفات تخزين البيانات
DATA_FILE = "data.json"
CUSTOM_COMMANDS_FILE = "custom_commands.json"
ROOM_COLORS_FILE = "room_colors.json"

def get_token():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)["TOKEN"].strip()

def get_key():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)["KEY"].strip()

disor = G(api_key=get_key())

# تحميل وحفظ الأوامر المخصصة
def load_custom_commands():
    if os.path.exists(CUSTOM_COMMANDS_FILE):
        try:
            with open(CUSTOM_COMMANDS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}
    return {}

def save_custom_commands(cmds):
    with open(CUSTOM_COMMANDS_FILE, "w", encoding="utf-8") as file:
        json.dump(cmds, file, ensure_ascii=False, indent=4)

# تحميل وحفظ ألوان الرومات
def load_room_colors():
    if os.path.exists(ROOM_COLORS_FILE):
        try:
            with open(ROOM_COLORS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}
    return {}

def save_room_colors(colors):
    with open(ROOM_COLORS_FILE, "w", encoding="utf-8") as file:
        json.dump(colors, file, ensure_ascii=False, indent=4)

custom_commands = load_custom_commands()
room_colors = load_room_colors()

# تفعيل الـ Intents بالكامل
intents = discord.Intents.default()
intents.guilds = True        
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged as: {bot.user}")
    for guild in bot.guilds:
        try:
            await guild.chunk()
        except Exception as e:
            print(f"Failed to chunk guild {guild.name}: {e}")

# قائمة الدول العربية
ARAB_COUNTRIES = [
    {"name": "مصر 🇪🇬", "color": "#FF0000"},
    {"name": "السعودية 🇸🇦", "color": "#006400"},
    {"name": "الإمارات 🇦🇪", "color": "#00FF00"},
    {"name": "الكويت 🇰🇼", "color": "#008080"},
    {"name": "قطر 🇶🇦", "color": "#800020"},
    {"name": "البحرين 🇧🇭", "color": "#FF4500"},
    {"name": "عمان 🇴🇲", "color": "#2E8B57"},
    {"name": "العراق 🇮🇶", "color": "#FF1493"},
    {"name": "الأردن 🇯🇴", "color": "#A0522D"},
    {"name": "فلسطين 🇵🇸", "color": "#000000"},
    {"name": "سوريا 🇸🇾", "color": "#4682B4"},
    {"name": "لبنان 🇱🇧", "color": "#FF3E96"},
    {"name": "اليمن 🇾🇪", "color": "#8B0000"},
    {"name": "ليبيا 🇱🇾", "color": "#556B2F"},
    {"name": "السودان 🇸🇩", "color": "#008B8B"},
    {"name": "الجزائر 🇩🇿", "color": "#228B22"},
    {"name": "المغرب 🇲🇦", "color": "#D2691E"},
    {"name": "تونس 🇹🇳", "color": "#FF6347"},
    {"name": "موريتانيا 🇲🇷", "color": "#32CD32"},
    {"name": "الصومال 🇸🇴", "color": "#1E90FF"},
    {"name": "جيبوتي 🇩🇯", "color": "#00BFFF"},
    {"name": "جزر القمر 🇰🇲", "color": "#DAA520"}
]

COLOR_MAP = {
    "اسود": "#010101", "أسود": "#010101", "black": "#010101",
    "abiad": "#ffffff", "ابيض": "#ffffff", "أبيض": "#ffffff", "white": "#ffffff",
    "احمر": "#ff0000", "أحمر": "#ff0000", "red": "#ff0000",
    "اخضر": "#00ff00", "أخضر": "#00ff00", "green": "#00ff00",
    "azraq": "#0000ff", "ازرق": "#0000ff", "أزرق": "#0000ff", "blue": "#0000ff",
    "asfar": "#ffff00", "اصفر": "#ffff00", "أصفر": "#ffff00", "yellow": "#ffff00",
    "wardi": "#ffc0cb", "وردي": "#ffc0cb", "pink": "#ffc0cb",
    "banafsaji": "#800080", "بنفسجي": "#800080", "purple": "#800080",
    "bortoqali": "#ffa500", "برتقالي": "#ffa500", "orange": "#ffa500",
    "ramadi": "#808080", "رمادي": "#808080", "gray": "#808080", "grey": "#808080"
}

def parse_color(color_str: str) -> discord.Colour:
    if not color_str:
        return discord.Colour.default()
    color_clean = color_str.strip().lower().replace("#", "")
    for name, hex_val in COLOR_MAP.items():
        if name in color_clean or color_clean in name:
            return discord.Colour.from_str(hex_val)
    try:
        return discord.Colour.from_str(f"#{color_clean}")
    except:
        return discord.Colour.default()

def return_server_info(guild: discord.Guild):
    if not guild:
        return ""
    info = f"Server: {guild.name} - {guild.id}\nCategories:\n"
    for category in guild.categories:
        info += f"- {category.name} ({category.id})\n"
    info += "Channels:\n"
    for channel in guild.channels:
        info += f"- {channel.name} ({channel.id})\n"
    info += "Roles:\n"
    for role in guild.roles:
        info += f"- Pos: {role.position}, Name: {role.name} ({role.id})\n"
    return info

def has_admin_role(member: discord.Member) -> bool:
    if member.guild.owner_id == member.id:
        return True
    for role in member.roles:
        if role.permissions.administrator:
            return True
    return False

# نظام توجيهات الذكاء الاصطناعي الشامل للصلاحيات والرتب وتكوين السيرفر
AiAbout = "\n".join([
    "You are a highly advanced and intelligent Discord Management Bot named UI.",
    "CRITICAL RULES:",
    "1. Language: Speak ONLY in natural, friendly, and humorous Egyptian Arabic (العامية المصرية).",
    "2. Logic: Analyze user intent precisely before constructing actions. Rely strictly on the provided 'Server Context' for existing roles/channels.",
    "3. Maximum 20 actions per single request to allow building full server categories, channels, and locks at once.",
    "",
    "AVAILABLE ACTIONS (Strict Case-Sensitive JSON format):",
    "- Create Categories: 'CreateCategory' { 'Name': 'string' }",
    "- Create Channels: 'CreateChannel' { 'Name': 'string', 'Type': 'text' or 'voice', 'Category': 'string' }",
    "- Delete Channels: 'DeleteChannel' { 'Name': 'string' }",
    "- Move Channel to another Category or make it unassigned (None): 'MoveChannel' { 'Name': 'string', 'Category': 'string' or null }",
    "- Edit Channel Name: 'EditChannelName' { 'Channel': 'string', 'Name': 'string' }",
    "- Lock Channel: 'LockChannel' { 'Name': 'string' }",
    "- Unlock Channel: 'UnlockChannel' { 'Name': 'string' }",
    "- Hide Channel: 'HideChannel' { 'Name': 'string' }",
    "- Show Channel: 'ShowChannel' { 'Name': 'string' }",
    "- Create Roles with specific granular permissions: 'CreateRole' { 'Name': 'string', 'Color': '#HEX', 'Permissions': { 'administrator': bool, 'manage_channels': bool, 'manage_roles': bool, 'kick_members': bool, 'ban_members': bool, 'manage_messages': bool, 'view_audit_log': bool, 'mention_everyone': bool, 'mute_members': bool, 'deafen_members': bool, 'move_members': bool, 'change_nickname': bool, 'manage_nicknames': bool, 'manage_webhooks': bool, 'manage_emojis': bool } }",
    "- Delete Roles: 'DeleteRole' { 'Name': 'string' }",
    "- Edit Role Color: 'EditRoleColor' { 'Name': 'string', 'Color': '#HEX' }",
    "- Give Roles: 'GrantRole' { 'Name': 'string', 'Member': 'string' }",
    "- Take Roles: 'TakeRole' { 'Name': 'string', 'Member': 'string' }",
    "- Strip Roles: 'StripRoles' { 'Member': 'string' }",
    "- Timeout Member: 'TimeoutMember' { 'Member': 'string', 'Duration': minutes_int, 'Reason': 'string' }",
    "- Kick Member: 'KickMember' { 'Member': 'string', 'Reason': 'string' }",
    "- Ban Member: 'BanMember' { 'Member': 'string', 'Reason': 'string' }",
    "- Delete Messages: 'DeleteMessages' { 'Amount': number_int }",
    "- Teach Custom Command: 'TeachCommand' { 'Trigger': 'string', 'Action': 'string' }",
    "",
    "RESPONSE FORMAT:",
    "You must ALWAYS reply with your friendly Egyptian text first, followed by the valid JSON block enclosed in ```json ... ```. Never embed raw text inside the JSON block.",
    "Example:",
    "من عيوني يا باشا هظبطلك السيرفر والروماات والإيموجيات حالاً! 😉",
    "```json",
    "[",
    "  {\"CreateCategory\": {\"Name\": \"•────────୨الأساسيات୧────────•\"}},",
    "  {\"CreateChannel\": {\"Name\": \"↟❖الاخبار❖↟\", \"Type\": \"text\", \"Category\": \"•────────୨الأساسيات୧────────•\"}},",
    "  {\"EditChannelName\": {\"Channel\": \"old-name\", \"Name\": \"new-name\"}}",
    "]",
    "```"
])

@bot.command(name="create_arab_roles")
@commands.has_permissions(administrator=True)
async def create_arab_roles(ctx):
    status_msg = await ctx.reply("🚀 جاري إنشاء 22 رتبة للدول العربية بألوانها المميزة...")
    created_count = 0
    for country in ARAB_COUNTRIES:
        try:
            existing_role = discord.utils.get(ctx.guild.roles, name=country["name"])
            if not existing_role:
                role_color = discord.Colour.from_str(country["color"])
                await ctx.guild.create_role(name=country["name"], colour=role_color)
                created_count += 1
                await asyncio.sleep(0.3)
        except Exception as e:
            print(f"فشل إنشاء رتبة {country['name']}: {e}")
    await status_msg.edit(content=f"✅ تم إنشاء {created_count} رتبة للدول العربية بنجاح! 🌟")

@bot.command(name="delete_arab_roles")
@commands.has_permissions(administrator=True)
async def delete_arab_roles(ctx):
    status_msg = await ctx.reply("🗑️ جاري حذف جميع رتب الدول العربية الـ 22...")
    deleted_count = 0
    for country in ARAB_COUNTRIES:
        try:
            role = discord.utils.get(ctx.guild.roles, name=country["name"])
            if role:
                await role.delete()
                deleted_count += 1
                await asyncio.sleep(0.3)
        except Exception as e:
            print(f"فشل حذف رتبة {country['name']}: {e}")
    await status_msg.edit(content=f"✅ تم حذف {deleted_count} رتبة من رتب الدول العربية بالكامل! 🧹")

# دوال مساعدة للبحث
def ui_get_category(guild: discord.Guild, target: str):
    if not target:
        return None
    target_clean = str(target).strip().lower()
    for cat in guild.categories:
        if target_clean in cat.name.lower():
            return cat
    return None

def ui_get_channel(guild: discord.Guild, target: str):
    if not target:
        return None
    target_str = str(target).strip()
    chan_id_match = re.search(r"\d+", target_str)
    if chan_id_match:
        channel = guild.get_channel(int(chan_id_match.group()))
        if channel:
            return channel
    for chan in guild.channels:
        if target_str.lower() in chan.name.lower():
            return chan
    return None

def ui_get_role(guild: discord.Guild, target: str):
    if not target:
        return None
    target_str = str(target).strip()
    mention_match = re.search(r"<@&?(\d+)>", target_str)
    if mention_match:
        return guild.get_role(int(mention_match.group(1)))
        
    clean_target = re.sub(r"[<@&>]", "", target_str).strip()
    if clean_target.isdigit():
        return guild.get_role(int(clean_target))
        
    for r in guild.roles:
        if r.name.strip().lower() == target_str.lower():
            return r
    for r in guild.roles:
        if target_str.lower() in r.name.lower():
            return r
    return None

def ui_get_member(guild: discord.Guild, target: str):
    if not target:
        return None
    target_str = str(target).strip()
    user_id_match = re.search(r"<@!?(\d+)>", target_str)
    if user_id_match:
        return guild.get_member(int(user_id_match.group(1)))
        
    clean_target = re.sub(r"[<@!>]", "", target_str).strip()
    if clean_target.isdigit():
        return guild.get_member(int(clean_target))
        
    for m in guild.members:
        if target_str.lower() in m.name.lower() or (m.global_name and target_str.lower() in m.global_name.lower()):
            return m
    return None

# تشغيل ومعالجة الأوامر من الـ AI
async def run_commands(commands_list: list, guild: discord.Guild, current_channel: discord.TextChannel, author: discord.Member):
    for command in commands_list:
        for key in command:
            await asyncio.sleep(0.6)
            try:
                if key.startswith("TeachCommand"):
                    trigger = command[key].get("Trigger")
                    action = command[key].get("Action")
                    if trigger and action:
                        guild_id_str = str(guild.id)
                        if guild_id_str not in custom_commands:
                            custom_commands[guild_id_str] = {}
                        custom_commands[guild_id_str][trigger.strip().lower()] = action.strip()
                        save_custom_commands(custom_commands)
                        await current_channel.send(f"💾 **عيوني ليك يا غالي!** حفظت الأمر: لما تقول `{trigger}`, هقوم فوراً بعمل: `{action}`.")

                elif key.startswith("CreateCategory"):
                    cat_name = command[key]["Name"]
                    existing_cat = ui_get_category(guild, cat_name)
                    if not existing_cat:
                        await guild.create_category(name=cat_name)
                        await current_channel.send(f"📁 تم إنشاء القسم **{cat_name}** بنجاح!")

                elif key.startswith("CreateRole"):
                    role_name = command[key]["Name"]
                    color_hex = command[key].get("Color", "#99AAB5")
                    color_parsed = parse_color(color_hex)
                    
                    perms_dict = command[key].get("Permissions", {})
                    perms = discord.Permissions()
                    
                    for perm_name, value in perms_dict.items():
                        if hasattr(perms, perm_name) and isinstance(value, bool):
                            setattr(perms, perm_name, value)
                            
                    role = await guild.create_role(name=role_name, colour=color_parsed, permissions=perms)
                    await current_channel.send(f"✅ تم إنشاء رتبة **{role.name}** بنجاح! 🛡️")

                elif key.startswith("DeleteMessages"):
                    amount = int(command[key].get("Amount", 100))
                    deleted = await current_channel.purge(limit=amount + 1)
                    await current_channel.send(f"🧹 تم مسح **{len(deleted) - 1}** رسالة بنجاح يا غالي!", delete_after=5)

                elif key.startswith("CreateChannel"):
                    name_to_create = command[key]["Name"]
                    chan_type = command[key].get("Type", "text")
                    if chan_type == "text":
                        channel = await guild.create_text_channel(name=name_to_create)
                    else:
                        channel = await guild.create_voice_channel(name=name_to_create)
                    
                    cat_name = command[key].get("Category")
                    if cat_name:
                        category_obj = ui_get_category(guild, cat_name)
                        if category_obj:
                            await channel.edit(category=category_obj)
                    await current_channel.send(f"✅ عملتلك الروم **{channel.name}** بنجاح!")

                elif key.startswith("EditChannelName"):
                    chan_target = command[key].get("Channel")
                    new_name = command[key].get("Name")
                    channel = ui_get_channel(guild, chan_target)
                    if channel and new_name:
                        old_name = channel.name
                        await channel.edit(name=new_name)
                        await current_channel.send(f"✏️ تم تغيير اسم الروم من **{old_name}** إلى **{new_name}** بنجاح!")
                    else:
                        await current_channel.send(f"❌ لم أجد الروم المطلوب تعديل اسمها: **{chan_target}**!")

                elif key.startswith("MoveChannel"):
                    chan_name = command[key].get("Name")
                    cat_name = command[key].get("Category")
                    
                    channel = ui_get_channel(guild, chan_name)
                    if channel:
                        if cat_name is None:
                            await channel.edit(category=None)
                            await current_channel.send(f"📂 تم إخراج الروم **{channel.name}** لتصبح بدون فئة (برة الأقسام) بنجاح!")
                        else:
                            category_obj = ui_get_category(guild, cat_name)
                            if category_obj:
                                await channel.edit(category=category_obj)
                                await current_channel.send(f"🔄 تم نقل الروم **{channel.name}** إلى القسم **{category_obj.name}** بنجاح!")
                            else:
                                await current_channel.send(f"❌ لم أجد القسم المطلوب باسم: **{cat_name}**!")

                elif key.startswith("DeleteChannel"):
                    chan_name = command[key].get("Name")
                    channel = ui_get_channel(guild, chan_name)
                    if channel:
                        await channel.delete()
                        await current_channel.send(f"🗑️ تم حذف روم **{chan_name}** بنجاح!")

                elif key.startswith("LockChannel"):
                    chan_name = command[key].get("Name")
                    channel = ui_get_channel(guild, chan_name) if chan_name else current_channel
                    if channel:
                        await channel.set_permissions(guild.default_role, send_messages=False)
                        await current_channel.send(f"🔒 تم قفل الروم **{channel.name}** بنجاح!")

                elif key.startswith("UnlockChannel"):
                    chan_name = command[key].get("Name")
                    channel = ui_get_channel(guild, chan_name) if chan_name else current_channel
                    if channel:
                        await channel.set_permissions(guild.default_role, send_messages=None)
                        await current_channel.send(f"🔓 تم فتح الروم **{channel.name}** بنجاح!")

                elif key.startswith("HideChannel"):
                    chan_name = command[key].get("Name")
                    channel = ui_get_channel(guild, chan_name) if chan_name else current_channel
                    if channel:
                        await channel.set_permissions(guild.default_role, view_channel=False)
                        await current_channel.send(f"👁️‍ تم إخفاء الروم **{channel.name}** بنجاح!")

                elif key.startswith("ShowChannel"):
                    chan_name = command[key].get("Name")
                    channel = ui_get_channel(guild, chan_name) if chan_name else current_channel
                    if channel:
                        await channel.set_permissions(guild.default_role, view_channel=None)
                        await current_channel.send(f"👁️ تم إظهار الروم **{channel.name}** بنجاح!")

                elif key.startswith("GrantRole"):
                    role_target = command[key].get("Name") or command[key].get("Role")
                    member_target = command[key].get("Member") or command[key].get("User")
                    
                    role = ui_get_role(guild, role_target)
                    member = ui_get_member(guild, member_target)
                    
                    if role and member:
                        await member.add_roles(role)
                        await current_channel.send(f"✅ تم إعطاء رتبة **{role.name}** للعضو **{member.name}** بنجاح!")

                elif key.startswith("TakeRole"):
                    role_target = command[key].get("Name") or command[key].get("Role")
                    member_target = command[key].get("Member") or command[key].get("User")
                    
                    role = ui_get_role(guild, role_target)
                    member = ui_get_member(guild, member_target)
                    
                    if role and member:
                        await member.remove_roles(role)
                        await current_channel.send(f"✅ تم سحب رتبة **{role.name}** من العضو **{member.name}** بنجاح!")

                elif key.startswith("TimeoutMember"):
                    member_target = command[key].get("Member") or command[key].get("User")
                    duration_mins = int(command[key].get("Duration", 10))
                    reason = command[key].get("Reason", "بواسطة نظام الإشراف بالذكاء الاصطناعي")
                    member = ui_get_member(guild, member_target)
                    
                    if member:
                        time_delta = timedelta(minutes=duration_mins)
                        await member.timeout(time_delta, reason=reason)
                        await current_channel.send(f"⏳ تم إعطاء تايم أوت للعضو **{member.name}** لمدة **{duration_mins}** دقيقة! 🔇")

                elif key.startswith("KickMember"):
                    member_target = command[key].get("Member") or command[key].get("User")
                    reason = command[key].get("Reason", "بواسطة نظام الإشراف بالذكاء الاصطناعي")
                    member = ui_get_member(guild, member_target)
                    
                    if member:
                        await member.kick(reason=reason)
                        await current_channel.send(f"👢 تم طرد العضو **{member.name}** من السيرفر بنجاح! ✈️")

                elif key.startswith("BanMember"):
                    member_target = command[key].get("Member") or command[key].get("User")
                    reason = command[key].get("Reason", "بواسطة نظام الإشراف بالذكاء الاصطناعي")
                    member = ui_get_member(guild, member_target)
                    
                    if member:
                        await member.ban(reason=reason)
                        await current_channel.send(f"🔨 تم تبنيد العضو **{member.name}** نهائياً! 🚪")
                    else:
                        clean_id = re.sub(r"\D", "", str(member_target))
                        if clean_id:
                            user_obj = await bot.fetch_user(int(clean_id))
                            await guild.ban(user_obj, reason=reason)
                            await current_channel.send(f"🔨 تم تبنيد العضو (بالـ ID) بنجاح! 🚪")

                elif key.startswith("EditRoleColor"):
                    role_name = command[key].get("Name")
                    color_hex = command[key].get("Color")
                    role = ui_get_role(guild, role_name)
                    if role and color_hex:
                        color_parsed = parse_color(color_hex)
                        await role.edit(colour=color_parsed)
                        await current_channel.send(f"🎨 تم تغيير لون الرتبة **{role.name}** بنجاح!")

                elif key.startswith("DeleteRole"):
                    role_name = command[key].get("Name")
                    role = ui_get_role(guild, role_name)
                    if role:
                        await role.delete()
                        await current_channel.send(f"🗑️ تم حذف الرتبة **{role_name}** بنجاح!")

            except Exception as e:
                print(f"خطأ أثناء تنفيذ الأمر {key}: {e}")
                await current_channel.send(f"❌ واجهتني مشكلة أثناء تنفيذ الأمر {key} (تأكد من صلاحيات البوت وترتيب رتبه)!")

# نظام فحص الرسائل للأوامر والذكاء الاصطناعي
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild = message.guild
    if not guild:
        return

    guild_id_str = str(guild.id)
    msg_content_clean = message.content.strip().lower()

    if has_admin_role(message.author):
        if guild_id_str in custom_commands:
            for trigger, raw_action in custom_commands[guild_id_str].items():
                if trigger in msg_content_clean:
                    action_lower = raw_action.lower()
                    if "قفل" in action_lower or "lock" in action_lower:
                        try:
                            await message.channel.set_permissions(guild.default_role, send_messages=False)
                            await message.reply(f"🔒 **سمعاً وطاعة يا مدير!** تم تنفيذ الأمر المخصص وقفل الروم فوراً.")
                        except Exception:
                            await message.reply("❌ حاولت أقفل الروم بس الصلاحيات مش كفاية يا غالي!")
                        return
                    elif "فتح" in action_lower or "unlock" in action_lower:
                        try:
                            await message.channel.set_permissions(guild.default_role, send_messages=None)
                            await message.reply(f"🔓 **من عيوني!** تم تنفيذ الأمر المخصص وفتح الروم مجدداً.")
                        except Exception:
                            await message.reply("❌ تعذر فتح الروم، راجع الصلاحيات.")
                        return

    if bot.user.mentioned_in(message) or message.content.startswith(f"<@!{bot.user.id}>") or message.content.startswith(f"<@{bot.user.id}>"):
        user_prompt = message.content.replace(f"<@!{bot.user.id}>", "").replace(f"<@{bot.user.id}>", "").strip()
        if not user_prompt:
            await message.reply("نعم يا غالي؟ آمرني أنا في الخدمة! 😉")
            return

        async with message.channel.typing():
            server_context = return_server_info(guild)
            messages = [
                {"role": "system", "content": AiAbout},
                {"role": "system", "content": f"Server Context:\n{server_context}"},
                {"role": "user", "content": user_prompt}
            ]

            try:
                response = disor.chat.completions.create(
                    model=MODEL,
                    messages=messages
                )
                reply_text = response.choices[0].message.content

                # استخراج الرد النصي وكتلة الـ JSON التنفيذية
                json_match = re.search(r"```json\s*(.*?)\s*```", reply_text, re.DOTALL)
                clean_reply = re.sub(r"```json.*?```", "", reply_text, flags=re.DOTALL).strip()

                if clean_reply:
                    await message.reply(clean_reply)
                else:
                    await message.reply("تمام يا باشا، جاري التنفيذ! 👌")

                if json_match:
                    json_str = json_match.group(1)
                    commands_list = json.loads(json_str)
                    if isinstance(commands_list, list):
                        await run_commands(commands_list, guild, message.channel, message.author)

            except Exception as e:
                print(f"Error communicating with Groq API: {e}")
                await message.reply("❌ حصلت مشكلة وأنا بكلم العقل المدبر (Groq), حاول تاني كمان شوية!")

# تشغيل البوت عبر التوكن المخزن
bot.run(get_token())
