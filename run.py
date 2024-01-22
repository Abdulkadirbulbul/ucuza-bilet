import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

chat_id=os.getenv("TELEGRAM_MESSAGE_ID")
api_key=os.getenv("TELEGRAM_API_KEY")
gonderici_mail = os.getenv("SENDER_MAIL")
gonderici_mail_uygulama_anahtari = os.getenv("SENDER_MAIL_APP_KEY")
alici_mail = os.getenv("RECIPIENT_MAIL")
url = f"https://api.telegram.org/bot{api_key}/sendMessage"

def send_telegram_message(api_key, chat_id, flight_data):
   
    message = createMessage(flight_data)

    # Telegram mesaj uzunluğu sınırlaması (4096 karakter)
    max_length = 4096

    # Mesajı uygun bir uzunluğa böl
    while len(message) > max_length:
        partial_message = message[:max_length]
        
        # Kalan kısmı al
        message = message[max_length:]
        
        # Mesajı gönder
        send_partial_message(api_key, chat_id, partial_message)

    # Son kısmı gönder
    send_partial_message(api_key, chat_id, message)

def send_partial_message(api_key, chat_id, partial_message):
    data = {'chat_id': chat_id, 'text': partial_message}
    response = requests.post(url, data=data)

    if response.status_code == 200:
        print("Mesaj başarıyla gönderildi.")
    else:
        print(f"Mesaj gönderme hatası: {response.status_code}, {response.text}")


def createMessage(flight_data):
    message = "Ucuz Uçuş Bulundu:\n\n"
    for flight in flight_data:
        message += f"Havayolu: {flight[0]}\n"
        message += f"Uçuş Numarası: {flight[1]}\n"
        message += f"Kalkış Saati: {flight[2]}\n"
        message += f"Süre: {flight[3]}\n"
        message += f"Fiyat: {flight[4]}\n"
        message += f"Tarih: {flight[5]}\n\n"
    return message

def send_mail(flight_data):
    content = createMessage(flight_data)
    try:
        mail = smtplib.SMTP('smtp.gmail.com', 587)
        mail.ehlo()
        mail.starttls()
        sender = gonderici_mail
        recipient = alici_mail
        mail.login("upworkali2289@gmail.com", "vbgl uygg foex wzkw")
        subject = 'Ucuz Uçuş Bulundu'
        header = f'To: {recipient}\nFrom: {sender}\nSubject: {subject}\n'
        content = header + content
        mail.sendmail(sender, recipient, content.encode('utf-8'))
        mail.close()
        print("E-posta başarıyla gönderildi!")
    except Exception as e:
        print(f"Hata: {e}")

def ucuzabilet_fiyatlari_al(nereden, nereye, baslangic_tarihi, gun_farki):
    gun_farki = int(gun_farki)
    tum_fiyatlar = []
    while gun_farki > -1:
        baslangic_tarihi_str = str(baslangic_tarihi)[0:10]
        base_url = "https://www.ucuzabilet.com/ic-hat-arama-sonuc"
        params = {
            "from": nereden,
            "to": nereye,
            "toIsCity": 1,
            "ddate": baslangic_tarihi_str,
            "adult": 1,
            "directflightsonly": "on"
        }

        response = requests.get(base_url, params=params)
        soup = BeautifulSoup(response.content, "html.parser")
        try:
            tbody = soup.find("tbody").find_all("tr", {"data-direction": "flights"})
            for tr in tbody:
                airlines = tr.find("div", {"class": "airline"}).text
                flight_number = tr.find("div", {"class": "flight-number"}).text.strip()
                flight_time = tr.find("b", {"class": "flight-time"}).text.strip()
                flight_duration = tr.find("span", {"class": "flight-duration"}).text.strip()
                price = tr.find("div", {"class": "btn-center"}).find("i", {"class": "integers"}).text.strip() + "TL"
                tum_fiyatlar.append(
                    [airlines, flight_number, flight_time, flight_duration, price, baslangic_tarihi_str]
                )
        except:
            print("Uçuş bulunamadı.")
        baslangic_tarihi += timedelta(days=1)
        gun_farki -= 1

    return tum_fiyatlar

if __name__ == "__main__":
    nereden = input("Nereden: ")
    nereye = input("Nereye: ")
    try:
        b_tarih = input("Başlangıç Tarihi: Örnek > 01.01.2024 ")
        bit_tarih = input("Bitiş Tarihi:  Örnek > 20.01.2024 ")
        baslangic_tarihi = datetime.strptime(b_tarih, "%d.%m.%Y")
        bitis_tarihi = datetime.strptime(bit_tarih, "%d.%m.%Y")
    except:
        print("Tarihleri yanlış girdiniz.")
        exit()
    istenilen_max_fiyat = int(input("Max Fiyat: Örnek 1300 >  "))

    gun_farki = (bitis_tarihi - baslangic_tarihi).days

    fiyatlar = ucuzabilet_fiyatlari_al(nereden, nereye, baslangic_tarihi, gun_farki)
    result = []
    if fiyatlar:
        print("Uygun Uçuş fiyatları Bulundu:")
        for fiyat in fiyatlar:
            if int(fiyat[4][:-2]) < istenilen_max_fiyat:
                result.append(fiyat)
        print(result)
        if len(result) > 0:
            # send_mail(result)
            send_telegram_message(api_key, chat_id, result)
    else:
        print("Uygun uçuş bulunamadı.")
