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
    "Avcılar Ambarlı": {"lat": 40.969489, "lon": 28.725667, "zemin": "taslik_derin"},
    "Yeşilköy Sahil": {"lat": 40.9575, "lon": 28.8250, "zemin": "kumluk_taslik"},
    "Yenikapı Mermerler": {"lat": 41.0010, "lon": 28.9530, "zemin": "iri_taslik"},
    "Eminönü İskele": {"lat": 41.0185, "lon": 28.9740, "zemin": "derin_akinti"},
    "İstinye Koyu": {"lat": 41.1115, "lon": 29.0570, "zemin": "mil_camur"},
    "Tarabya Sahil": {"lat": 41.1405, "lon": 29.0560, "zemin": "taslik_derin"},
    "Kireçburnu": {"lat": 41.1495, "lon": 29.0525, "zemin": "taslik_derin"}
}

def ay_evresi_hesapla():
    """İstanbul tarihine göre ayın evresini ve avcılığa etkisini hesaplar."""
    simdi = datetime.now(ISTANBUL_TZ)
    # Bilinen bir Yeni Ay referans tarihi (6 Ocak 2000)
    referans = datetime(2000, 1, 6, tzinfo=timezone.utc)
    
    fark = simdi.astimezone(timezone.utc) - referans
    toplam_gun = fark.total_seconds() / 86400
    
    # Bir sinodik ay ortalama 29.53059 gündür
    evre = (toplam_gun % 29.530588853) / 29.530588853
    
    # Evre değerine göre isim, emoji ve LRF çarpanı belirliyoruz
    if evre < 0.03 or evre > 0.97:
        return "🌑 Yeni Ay (Zifiri Karanlık)", "yeni_ay", "🔥 Meralar karanlık! Eşkina ve Mırmır kıyıdadır. Glow/Işıklı sahteleri çantadan çıkar."
    elif evre < 0.22:
        return "🌙 Büyüyen Hilal", "normal", "Stabil durum. Gece avı için uygun ortam."
    elif evre < 0.28:
        return "🌓 İlk Dördün", "normal", "Yarı aydınlık su. Balık taş altından yeni yeni hamle yapar."
    elif evre < 0.47:
        return "🌔 Büyüyen Şişkin Ay", "aydinlik", "Su aydınlanıyor. Gölgelik yerleri veya derin yarıkları tercih et."
    elif evre < 0.53:
        return "🌕 Dolunay (Yüksek Aydınlık)", "dolunay", "⚠️ Ortalık projektör gibi! Balık seni görür ve aşırı ürkek olur. Doğal renkli (şeffaf/UV) sahteler seç ve çok sessiz davran."
    elif evre < 0.72:
        return "🌖 Küçülen Şişkin Ay", "aydinlik", "Aydınlık azalıyor olsa da hala gölgelik bölgeler öncelikli olmalı."
    elif evre < 0.78:
        return "🌗 Son Dördün", "normal", "Su kıvama geliyor. Taş önlerini LRF ile yokla."
    else:
        return "🌙 Küçülen Hilal", "normal", "Karanlık artıyor, av iştahı yükselişte."

def hava_durumu_al(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=tr"
    response = requests.get(url).json()
    if response.get("cod") != 200:
        return None
    return response

def lrf_hedef_analizi(wind_speed, zemin, ay_durumu):
    """Hava, Zemin ve Solunar verilerini birleştirip LRF av şansını hesaplar."""
    current_hour = datetime.now(ISTANBUL_TZ).hour
    is_night = current_hour >= 20 or current_hour <= 5
    
    # --- 1. İSTAVRİT ANALİZİ ---
    istavrit_skor = 75
    if wind_speed > 18: istavrit_skor -= 25
    if wind_speed < 10: istavrit_skor += 15
    
    if is_night:
        if ay_durumu == "dolunay":
            istavrit_taktik = "💡 Dolunayda istavrit dağınık olur. Işık alan iskele altları yerine derin ve karanlık hatlara atış yap."
        else:
            istavrit_taktik = "💡 Pembe, beyaz veya simli ince silikonlar (iskele altı ışık alan projektör önlerine atış yap)."
    else:
        istavrit_taktik = "💡 Gündüz avı için ufak mikro jigler (3-5 gr) veya koyu renkli silikonları dipten dene."
    
    # --- 2. MIRMIR ANALİZİ ---
    mirmir_skor = 40
    if is_night: mirmir_skor += 30
    if zemin in ["kumluk", "kumluk_taslik"]: mirmir_skor += 20
    if wind_speed > 15: mirmir_skor -= 30
    
    # Solunar Etkisi
    if is_night and ay_durumu == "yeni_ay":
        mirmir_skor += 15
        mirmir_taktik = "🔥 SOLUNAR COŞKUSU: Karanlıkta mırmır kokuyu takip eder. Isome/Berkley kurtları dipten yavaşça sürüt."
    elif is_night and ay_durumu == "dolunay":
        mirmir_skor -= 20
        mirmir_taktik = "⚠️ DOLUNAR BASKISI: Su çok aydınlık, mırmır sığlığa girmeye korkar. Uzun atışlar yap, şeffaf sahteler dene."
    else:
        mirmir_taktik = "💡 Kokulu kurtlar (Isome/Berkley) ile dipte yavaşça tırnaklama/sürütme aksiyonu yap."

    # --- 3. EŞKİNA ANALİZİ ---
    eskina_skor = 20
    if is_night: eskina_skor += 50
    if zemin in ["iri_taslik", "taslik_derin"]: eskina_skor += 20
    if wind_speed > 15: eskina_skor -= 35
    
    # Solunar Etkisi
    if is_night and ay_durumu == "yeni_ay":
        eskina_skor += 15
        eskina_taktik = "🔥 SOLUNAR COŞKUSU: Taş altındaki tüm eşkinalar avda! İri gövdeli yoğun glow (parlayan) silikonları taş önünde askıda bırak."
    elif is_night and ay_durumu == "dolunay":
        eskina_skor -= 25
        eskina_taktik = "⚠️ DOLUNAR BASKISI: Eşkina ışıktan nefret eder. Taşların tam dibine, karanlık gölge yapan kuytulara sokulman gerek."
    else:
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
        "Selam kanka! Solunar (Ay Evresi) destekli LRF İstihbarat Botu hazır. 🎣\n\n"
        "Gideceğin merayı seç; hava durumunu, rüzgârı ve o anki Ay'ın durumunu "
        "harmanlayıp hedef balıklarının gerçek şansını sana sunayım."
    )
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    butonlar = [types.KeyboardButton(mera) for mera in MERALAR.keys()]
    markup.add(*butonlar)
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in MERALAR.keys())
def rapor_ver(message):
    mera_adi = message.text
    mera = MERALAR[mera_adi]
    
    bot.send_message(message.chat.id, f"🔄 {mera_adi} için Solunar ve hava verileri çaprazlanıyor...")
    
    hava = hava_durumu_al(mera["lat"], mera["lon"])
    if not hava:
        bot.send_message(message.chat.id, "❌ Hava durumu alınamadı kanka, API anahtarını kontrol et.")
        return
        
    temp = hava["main"]["temp"]
    wind_speed = round(hava["wind"]["speed"] * 3.6, 1)
    desc = hava["weather"][0]["description"].capitalize()
    
    # Ay evresini ve solunar taktiğini alıyoruz
    ay_metni, ay_durumu, solunar_taktik = ay_evresi_hesapla()
    
    analiz = lrf_hedef_analizi(wind_speed, mera["zemin"], ay_durumu)
    
    mod_metni = "🌙 Gece Avı Modu" if analiz["is_night"] else "☀️ Gündüz Avı Modu"
    
    is_weekend = datetime.now(ISTANBUL_TZ).weekday() in [5, 6]
    kalabalik = "🔴 Hafta sonu yoğunluğu olabilir" if (is_weekend and wind_speed < 12) else "🟢 Sakin / Rahat atış alanı"

    rapor_metni = (
        f"📍 *MERA:* {mera_adi}\n"
        f"⏰ *Rapor Saati:* {analiz['hour_str']} ({mod_metni})\n"
        f"🌑 *Ay Evresi:* {ay_metni}\n"
        f"🌡️ *Hava:* {temp}°C | {desc}\n"
        f"💨 *Anlık Rüzgâr:* {wind_speed} km/s\n"
        f"👥 *Tahmini Durum:* {kalabalik}\n"
        f"-----------------------------------\n"
        f"🎯 *SOLUNAR ETKİSİ:* {solunar_taktik}\n"
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
    print("Solunar Destekli LRF Botu Çalışıyor...")
    bot.infinity_polling()
