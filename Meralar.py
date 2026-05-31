import telebot
import requests
from datetime import datetime, timedelta, timezone
from telebot import types
import os
from flask import Flask
import threading

# --- RENDER İÇİN MİNİK WEB SUNUCUSU ---
app = Flask('')

@app.route('/')
def home():
    return "Kanka bot arkada uyanık ve çalışıyor! 🎣"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR VE ANAHTARLAR ---
BOT_TOKEN = "8782001717:AAGzW-zFPRsM2tVF3Noeasdw6LIuxzCX54E"  
WEATHER_API_KEY = "f9697357bf7366489a07264fdbf6ed55"   

bot = telebot.TeleBot(BOT_TOKEN)

# İstanbul sabit olarak UTC+3 zaman dilimindedir
ISTANBUL_TZ = timezone(timedelta(hours=3))

# --- SADECE AVRUPA YAKASI LRF MERALARI ---
MERALAR = {
    "Büyükçekmece Sahil": {"lat": 41.0225, "lon": 28.5812, "zemin": "kumluk_taslik"},
    "Avcılar Ambarlı": {"lat": 40.9695, "lon": 28.6970, "zemin": "taslik_derin"},
    "Yeşilköy Sahil": {"lat": 40.9575, "lon": 28.8250, "zemin": "kumluk_taslik"},
    "Yenikapı Mermerler": {"lat": 41.0010, "lon": 28.9530, "zemin": "iri_taslik"},
    "Eminönü İskele": {"lat": 41.0185, "lon": 28.9740, "zemin": "derin_akinti"},
    "İstinye Koyu": {"lat": 41.1115, "lon": 29.0570, "zemin": "mil_camur"},
    "Tarabya Sahil": {"lat": 41.1405, "lon": 29.0560, "zemin": "taslik_derin"},
    "Kireçburnu": {"lat": 41.1495, "lon": 29.0525, "zemin": "taslik_derin"}
}

def hava_durumu_al(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=tr"
    response = requests.get(url).json()
    if response.get("cod") != 200:
        return None
    return response

def lrf_hedef_analizi(wind_speed, zemin):
    """İstanbul saatine göre İstavrit, Mırmır ve Eşkina skorları üretir."""
    # Sunucu nerede olursa olsun İstanbul'un anlık saatini çekiyoruz
    current_hour = datetime.now(ISTANBUL_TZ).hour
    
    # Saat 20:00 ile 05:00 arası gece kabul edilir.
    is_night = current_hour >= 20 or current_hour <= 5
    
    # --- 1. İSTAVRİT ANALİZİ ---
    istavrit_skor = 75
    if wind_speed > 18: istavrit_skor -= 25
    if wind_speed < 10: istavrit_skor += 15
    istavrit_taktik = "💡 Pembe, beyaz veya simli ince silikonlar (iskele altı ışık alan yerlere atış yap)." if is_night else "💡 Gündüz avı için ufak mikro jigler (3-5 gr) veya koyu renkli silikonları dipten dene."
    
    # --- 2. MIRMIR ANALİZİ ---
    mirmir_skor = 40
    if is_night: mirmir_skor += 35
    if zemin in ["kumluk", "kumluk_taslik"]: mirmir_skor += 20
    if wind_speed > 15: mirmir_skor -= 30
    mirmir_taktik = "💡 Kokulu kurtlar (Isome/Berkley) ile dipte yavaşça tırnaklama/sürütme aksiyonu yap."

    # --- 3. EŞKİNA ANALİZİ ---
    eskina_skor = 20
    if is_night: eskina_skor += 55
    if zemin in ["iri_taslik", "taslik_derin"]: eskina_skor += 25
    if wind_speed > 15: eskina_skor -= 35
    eskina_taktik = "💡 Glow (parlayan) iri silikonlar veya boru kurdu taklidi sahteler kullan. Taş önlerinde askıda bırak."

    istavrit_skor = max(10, min(100, istavrit_skor))
    mirmir_skor = max(10, min(100, mirmir_skor))
    eskina_skor = max(10, min(100, eskina_skor))

    return {
        "is_night": is_night,
        "hour_str": datetime.now(ISTANBUL_TZ).strftime("%H:%M"),
        "istavrit": {"skor": istavrit_skor, "taktik": istavrit_taktik},
        "mirmir": {"skor": mirmir_skor, "taktik": mirmir_taktik},
        "eskina": {"skor": eskina_skor, "taktik": eskina_taktik}
    }

@bot.message_handler(commands=['start', 'help'])
def hosgeldin(message):
    text = (
        "Selam kanka! İstanbul saatine tam uyumlu LRF İstihbarat Botu devrede. 🎣\n\n"
        "Gideceğin merayı seç; hava durumunu, hedef balıkların şansını analiz edeyim "
        "ve hemen altına tam avlanacağın yerin harita konumunu fırlatayım."
    )
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    butonlar = [types.KeyboardButton(mera) for mera in MERALAR.keys()]
    markup.add(*butonlar)
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in MERALAR.keys())
def rapor_ver(message):
    mera_adi = message.text
    mera = MERALAR[mera_adi]
    
    bot.send_message(message.chat.id, f"🔄 {mera_adi} inceleniyor, anlık veriler çekiliyor...")
    
    hava = hava_durumu_al(mera["lat"], mera["lon"])
    if not hava:
        bot.send_message(message.chat.id, "❌ Hava durumu alınamadı kanka, API anahtarını kontrol et.")
        return
        
    temp = hava["main"]["temp"]
    wind_speed = round(hava["wind"]["speed"] * 3.6, 1)
    desc = hava["weather"][0]["description"].capitalize()
    
    analiz = lrf_hedef_analizi(wind_speed, mera["zemin"])
    
    # Mod göstergesi (Gece / Gündüz)
    mod_metni = "🌙 Gece Avı Modu" if analiz["is_night"] else "☀️ Gündüz Avı Modu"
    
    is_weekend = datetime.now(ISTANBUL_TZ).weekday() in [5, 6]
    kalabalik = "🔴 Hafta sonu yoğunluğu olabilir" if (is_weekend and wind_speed < 12) else "🟢 Sakin / Rahat atış alanı"

    rapor_metni = (
        f"📍 *MERA:* {mera_adi}\n"
        f"⏰ *Rapor Saati:* {analiz['hour_str']} ({mod_metni})\n"
        f"🌡️ *Hava:* {temp}°C | {desc}\n"
        f"💨 *Anlık Rüzgâr:* {wind_speed} km/s\n"
        f"👥 *Tahmini Durum:* {kalabalik}\n"
        f"-----------------------------------\n\n"
        f"🐟 *İSTAVRİT ŞANSI: %{analiz['istavrit']['skor']}*\n"
        f"{analiz['istavrit']['taktik']}\n\n"
        f"🦀 *MIRMIR ŞANSI: %{analiz['mirmir']['skor']}*\n"
        f"{analiz['mirmir']['taktik']}\n\n"
        f"🗿 *EŞKİNA ŞANSI: %{analiz['eskina']['skor']}*\n"
        f"{analiz['eskina']['taktik']}\n\n"
        f"🚨 *Genel LRF Notu:* Rüzgâr {wind_speed} km/s olduğundan takımı uçurmamak için "
        f"{'0.5 - 1.5 gr' if wind_speed < 12 else '2.0 - 3.0 gr'} jighead tercih et kanka."
    )
    
    bot.send_message(message.chat.id, rapor_metni, parse_mode="Markdown")
    bot.send_location(message.chat.id, mera["lat"], mera["lon"])

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Zaman Ayarlı Avrupa Yakası LRF Botu Çalışıyor...")
    bot.infinity_polling()
