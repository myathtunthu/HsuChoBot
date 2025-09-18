import telebot
from telebot import types
import time
import os

# ==================== YOUR BOT TOKEN ====================
BOT_TOKEN = "8234675036:AAFIWLxSxeaT0-VGt_wUwDySCJbHS_0NTN0"
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN)

print("Bot is starting with the provided token...")

# Store user data temporarily
user_data = {}

# Available solar panel wattages
SOLAR_PANEL_WATTAGES = [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750]

# Available battery voltages
BATTERY_VOLTAGES = [12, 12.8, 22.8, 24, 25.6, 36, 48, 51.2, 60, 72, 96, 102.4]

# Battery types
BATTERY_TYPES = ["LiFePO4", "Lead-Acid", "Gel"]

# Step 1: Calculate total daily energy consumption
def calculate_daily_consumption(total_w, hours):
    return total_w * hours

# Step 2: Calculate battery size based on battery type
def calculate_battery_size(daily_wh, battery_voltage, battery_type="lifepo4"):
    if battery_type.lower() == "lifepo4":
        dod_factor = 0.8
        battery_ah = (daily_wh / battery_voltage) * (1 / dod_factor)
    elif battery_type.lower() == "gel":
        dod_factor = 0.6
        battery_ah = (daily_wh / battery_voltage) * (1 / dod_factor)
    else:
        dod_factor = 0.5
        battery_ah = (daily_wh / battery_voltage) * (1 / dod_factor)
    
    return battery_ah, dod_factor

# Step 3: Calculate solar panel requirements
def calculate_solar_panels(daily_wh, panel_wattage, sun_hours=5, efficiency=0.85):
    solar_w = (daily_wh / sun_hours) * (1 / efficiency)
    num_panels = round(solar_w / panel_wattage)
    if num_panels < 1:
        num_panels = 1
    return solar_w, num_panels

# Step 4: Calculate inverter size
def calculate_inverter_size(total_w):
    inverter_w = total_w * 1.3
    return inverter_w

# Step 5: Calculate charge controller size
def calculate_charge_controller(solar_w, battery_voltage):
    controller_amps = (solar_w / battery_voltage) * 1.25
    if solar_w <= 1000 and battery_voltage <= 24:
        controller_type = "PWM"
    else:
        controller_type = "MPPT"
    return controller_type, controller_amps

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        welcome_text = """
☀️ *Hsu Cho Solar Calculator Bot မှ ကြိုဆိုပါတယ်!*

ဆိုလာစနစ်တွက်ချက်မှုအတွက် အဆင့် ၅ ဆင့်ဖြင့် တွက်ချက်ပေးပါမယ်:

1. စုစုပေါင်းစွမ်းအင်သုံးစွဲမှု
2. ဘက်ထရီအရွယ်အစား
3. ဆိုလာပြားလိုအပ်ချက်
4. အင်ဗာတာအရွယ်အစား
5. *Charger Controller*

🔧 *အသုံးပြုနည်း:*
/calculate - တွက်ချက်ရန်
/help - အကူအညီ
        """
        bot.reply_to(message, welcome_text, parse_mode='Markdown')
    except Exception as e:
        print("Error in start:", e)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📖 *အဆင့် ၅ ဆင့်ဖြင့် ဆိုလာစနစ်တွက်ချက်နည်း*

/calculate ကိုနှိပ်ပြီး စတင်�တွက်ချက်ပါ။
        """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['calculate'])
def start_calculation(message):
    try:
        user_data[message.chat.id] = {}
        msg = bot.reply_to(message, "🔌 *ကျေးဇူးပြု၍ စုစုပေါင်း�ဝပ်အား (W) ထည့်ပါ:*\n\nဥပမာ: 500", parse_mode='Markdown')
        bot.register_next_step_handler(msg, ask_usage_hours)
    except Exception as e:
        print("Error in calculate:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def ask_usage_hours(message):
    try:
        chat_id = message.chat.id
        total_w = int(message.text)
        
        if total_w <= 0:
            bot.reply_to(message, "❌ ဝပ်အားသည် 0 ထက်ကြီးရပါမယ်")
            return
            
        user_data[chat_id]['total_w'] = total_w
        msg = bot.reply_to(message, f"⏰ *တစ်ရက်ကိုဘယ်နှနာရီသုံးမှာလဲ?*\n\nဥပမာ: 6", parse_mode='Markdown')
        bot.register_next_step_handler(msg, ask_battery_type)
    except ValueError:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ဂဏန်းမှန်မှန်ထည့်ပါ\n\nဥပမာ: 500")
    except Exception as e:
        print("Error in ask_usage_hours:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def ask_battery_type(message):
    try:
        chat_id = message.chat.id
        hours = float(message.text)
        
        if hours <= 0 or hours > 24:
            bot.reply_to(message, "❌ သုံးမည့်နာရီသည် 1 မှ 24 ကြား�ရှိရပါမယ်")
            return
            
        user_data[chat_id]['hours'] = hours
        
        # Create keyboard for battery type selection
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
        buttons = [types.KeyboardButton(b_type) for b_type in BATTERY_TYPES]
        markup.add(*buttons)
        
        msg = bot.reply_to(message, "🔋 *ဘက်ထရီအမျိုးအစားရွေးချယ်ပါ*", reply_markup=markup, parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_battery_type)
    except ValueError:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ဂဏန်းမှန်မှန်ထည့်ပါ\n\nဥပမာ: 6")
    except Exception as e:
        print("Error in ask_battery_type:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def process_battery_type(message):
    try:
        chat_id = message.chat.id
        battery_type = message.text
        
        if battery_type not in BATTERY_TYPES:
            bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ပေးထားသော option များထဲကရွေးချယ်ပါ", reply_markup=types.ReplyKeyboardRemove())
            return
            
        user_data[chat_id]['battery_type'] = battery_type
        
        # Create keyboard for solar panel selection
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=3)
        buttons = [types.KeyboardButton(f"{wattage}W") for wattage in SOLAR_PANEL_WATTAGES]
        markup.add(*buttons)
        
        msg = bot.reply_to(message, "☀️ *ဆိုလာပြား Wattage ရွေးချယ်ပါ*", reply_markup=markup, parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_solar_panel)
    except Exception as e:
        print("Error in process_battery_type:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def process_solar_panel(message):
    try:
        chat_id = message.chat.id
        panel_text = message.text
        
        # Extract wattage from text (remove "W")
        panel_wattage = int(panel_text.replace("W", ""))
        
        if panel_wattage not in SOLAR_PANEL_WATTAGES:
            bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ပေးထားသော option များထဲကရွေးချယ်ပါ", reply_markup=types.ReplyKeyboardRemove())
            return
            
        user_data[chat_id]['panel_wattage'] = panel_wattage
        
        # Create keyboard for battery voltage selection
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=3)
        buttons = [types.KeyboardButton(f"{voltage}V") for voltage in BATTERY_VOLTAGES]
        markup.add(*buttons)
        
        msg = bot.reply_to(message, "⚡ *ဘက်ထရီဗို့အားရွေးချယ်ပါ*", reply_markup=markup, parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_battery_voltage)
    except ValueError:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ပေးထားသော option များထဲကရွေးချယ်ပါ", reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        print("Error in process_solar_panel:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def process_battery_voltage(message):
    try:
        chat_id = message.chat.id
        voltage_text = message.text
        
        # Extract voltage from text (remove "V")
        battery_voltage = float(voltage_text.replace("V", ""))
        
        if battery_voltage not in BATTERY_VOLTAGES:
            bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ပေးထားသော option များထဲကရွေးချယ်ပါ", reply_markup=types.ReplyKeyboardRemove())
            return
        
        # Get user data
        total_w = user_data[chat_id]['total_w']
        hours = user_data[chat_id]['hours']
        panel_wattage = user_data[chat_id]['panel_wattage']
        battery_type = user_data[chat_id]['battery_type']
        
        # Perform all calculations
        daily_wh = calculate_daily_consumption(total_w, hours)
        battery_ah, dod_factor = calculate_battery_size(daily_wh, battery_voltage, battery_type.lower())
        solar_w, num_panels = calculate_solar_panels(daily_wh, panel_wattage)
        inverter_w = calculate_inverter_size(total_w)
        controller_type, controller_amps = calculate_charge_controller(solar_w, battery_voltage)
        
        # Prepare result message
        result = f"""
📊 *Hsu Cho Solar Calculator - တွက်ချက်မှုရလဒ်များ*

🔋 *ဘက်ထရီအမျိုးအစား:* {battery_type}
⚡ *ဘက်ထရီဗို့အား:* {battery_voltage}V
☀️ *ဆိုလာပြား:* {panel_wattage}W
        
📝 *စွမ်းအင်သုံးစွဲမှုစာရင်း:*
• *စုစုပေါင်းဝပ်အား:* {total_w}W
• *နေ့စဉ်သုံး�စွဲမည့်နာရီ:* {hours}h
• *စုစုပေါင်းစွမ်းအင်သုံးစွဲမှု:* {daily_wh:.0f} Wh/ရက်

🔋 *ဘက်ထရီအရွယ်အစား:* _{battery_ah:.0f} Ah {battery_voltage}V_
   - {battery_type} ဘက်ထရီ (DOD: {dod_factor*100:.0f}%)
   - {battery_ah:.0f}Ah ဘက်ထရီ ၁လုံး (သို့) သေးငယ်သောဘက်ထရီများကို parallel ချိတ်ဆက်အသုံးပြုနိုင်သည်

☀️ *ဆိုလာပြား�လိုအပ်ချက်:* _{solar_w:.0f} W_
   - {panel_wattage}W ဆိုလာပြား {num_panels} ချပ်

⚡ *အင်ဗာတာအရွယ်အစား:* _{inverter_w:.0f} W Pure Sine Wave_
   - စုစုပေါင်းဝပ်အားထက် 30% ပိုကြီးသော အင်ဗာတာရွေးချယ်ထားသည်

🎛️ *Charger Controller:* _{controller_type} {controller_amps:.1f}A_
   - {controller_type} controller {controller_amps:.1f}A အရွယ်အစား

💡 *အထူးအကြံပြုချက်များ:*
"""
        
        if battery_type.lower() == "lifepo4":
            result += """
   - *LiFePO4 ဘက်ထရီများသည် သက်တမ်းရှည်ပြီး စိတ်ချရမှုရှိသည်*
   - *80% Depth of Discharge အထိ အသုံးပြုနိုင်သည်*"""
        elif battery_type.lower() == "gel":
            result += """
   - *Gel ဘက်ထရီများသည် ပြန်လည်အားသွင်းမှုမြန်ဆန်ပြီး ပြင်ပန်းသံဆူညံမှုနည်းသည်*
   - *60% Depth of Discharge အထိ အသုံးပြုနိုင်သည်*"""
        else:
            result += f"""
   - *Lead-Acid ဘက်ထရီကို 50% ထက်ပို၍ မထုတ်သုံးသင့်ပါ*
   - *ရေမှန်မှန်ဖြည့်ပေးရန် လိုအပ်သည်*"""
        
        # Create keyboard for recalculating options
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
        buttons = [
            types.KeyboardButton("🔋 ဘက်ထရီအမျိုးအစားပြန်ရွေးမယ်"),
            types.KeyboardButton("☀️ ဆိုလာပြားပြန်ရွေးမယ်"),
            types.KeyboardButton("🔄 အားလုံးပြန်ရွေးမယ်"),
            types.KeyboardButton("❌ ထွက်မယ်")
        ]
        markup.add(*buttons)
        
        bot.send_message(chat_id, result, parse_mode='Markdown', reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, handle_recalculation)
        
    except Exception as e:
        print("Error in process_battery_voltage:", e)
        bot.reply_to(message, "❌ တွက်ချက်မှုမှားယွင်းနေပါတယ်", reply_markup=types.ReplyKeyboardRemove())

def handle_recalculation(message):
    try:
        chat_id = message.chat.id
        choice = message.text
        
        if choice == "🔋 ဘက်ထရီအမျိုးအစားပြန်ရွေးမယ်":
            # Create keyboard for battery type selection
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
            buttons = [types.KeyboardButton(b_type) for b_type in BATTERY_TYPES]
            markup.add(*buttons)
            
            msg = bot.send_message(chat_id, "🔋 *ဘက်ထရီအမျိုးအစားအသစ်ရွေးချယ်ပါ*", reply_markup=markup, parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_battery_type)
            
        elif choice == "☀️ ဆိုလာပြားပြန်ရွေးမယ်":
            # Create keyboard for solar panel selection
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=3)
            buttons = [types.KeyboardButton(f"{wattage}W") for wattage in SOLAR_PANEL_WATTAGES]
            markup.add(*buttons)
            
            msg = bot.send_message(chat_id, "☀️ *ဆိုလာပြား Wattage အသစ်ရွေးချယ်ပါ*", reply_markup=markup, parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_solar_panel)
            
        elif choice == "🔄 အားလုံးပြန်ရွေး�မယ်":
            # Restart completely
            user_data[chat_id] = {}
            bot.send_message(chat_id, "🔄 *စနစ်အသစ်တွက်ချက်မည်*", parse_mode='Markdown', reply_markup=types.ReplyKeyboardRemove())
            msg = bot.send_message(chat_id, "🔌 *ကျေးဇူးပြု၍ စုစုပေါင်းဝပ်အား (W) ထည့်ပါ*\n\nဥပမာ: 500", parse_mode='Markdown')
            bot.register_next_step_handler(msg, ask_usage_hours)
            
        elif choice == "❌ ထွက်မယ်":
            bot.send_message(chat_id, "👋 *Hsu Cho Solar Calculator ကိုအသုံးပြုတဲ့အတွက်ကျေးဇူးတင်ပါတယ်!*\n\nမည်သည့်အချိန်မဆို /calculate ကိုရိုက်ပို့ပြီး ပြန်လည်တွက်ချက်နိုင်ပါတယ်။", parse_mode='Markdown', reply_markup=types.ReplyKeyboardRemove())
            
        else:
            bot.send_message(chat_id, "❌ ကျေးဇူးပြု၍ ပေးထားသော option များထဲကရွေးချယ်ပါ")
            
    except Exception as e:
        print("Error in handle_recalculation:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        bot.reply_to(message, "❌ မသိသော command ဖြစ်ပါတယ်\n\nအသုံးပြုရန်: /start or /calculate")
    else:
        bot.reply_to(message, "🤖 Hsu Cho Solar Calculator မှ ကြိုဆိုပါတယ်!\n\nစတင်ရန် /start ကိုရိုက်ပို့ပါ")

# Run the bot with polling (no Flask needed)
if __name__ == "__main__":
    try:
        print("Bot is running with token:", BOT_TOKEN)
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print("Bot polling error:", e)
        time.sleep(5)
