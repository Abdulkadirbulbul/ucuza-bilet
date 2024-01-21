import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import smtplib
from decouple import config

def send_telegram_message(flight_data):
    telegramApi = config("api_key")
    telegramMessageid = config("messageId")
    api=f'{telegramApi}'
    messageId=f'{telegramMessageid}'
    requests.post(
        url='https://api.telegram.org/bot{0}/{1}'.format(api,
            "sendMessage"),
            data={'chat_id': messageId, 'text': createMessage(flight_data)}
    )

def createMessage(flight_data):
    message = "Ucuz Uçuş Bulundu:\n\n"
    for flight in flight_data:
        print("/" * 22)
        print(flight)

        message += f"Airline: {flight[0]}\n"
        message += f"Flight Number: {flight[1]}\n"
        message += f"Departure Time: {flight[2]}\n"
        message += f"Duration: {flight[3]}\n"
        message += f"Price: {flight[4]}\n"
        message += f"Date: {flight[5]}\n\n"
    return message

def send_mail(flight_data):
    gonderici_mail = config("sender_mail")
    gonderici_mail_uygulama_anahtari = config("sender_mail_app_key")
    alici_mail = config("recipient_mail")
   
    
    content=createMessage(flight_data)   
    try:
        mail = smtplib.SMTP('smtp.gmail.com', 587)
        mail.ehlo()
        mail.starttls()
        sender = f'{gonderici_mail}'
        recipient = f'{alici_mail}'
        # Burada mail şifrenizi girmemeniz gerekiyor 
        # Mail hesabınızda 2 adımlı doğrulamayı açtıkdan sonra 
        # Arama yerinde Uygulama anahtarı yazıp yeni bir anahtar oluşturup
        # İsme herhangi bir isim yazıp şifreyi almanız gerekiyor.
        # Aldığınız 16 haneli şifreyi aşağıya yazmanız gerekiyor.
        mail.login(f'{gonderici_mail}', f'{gonderici_mail_uygulama_anahtari}')
        subject = 'Ucuz Uçuş Bulundu'
        header = f'To: {recipient}\nFrom: {sender}\nSubject: {subject}\n'
        content = header + content
        mail.sendmail(sender, recipient, content.encode('utf-8'))
        mail.close()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")


def ucuzabilet_fiyatlari_al(nereden, nereye, baslangic_tarihi, gun_farki):
    gun_farki = int(gun_farki)
    print(nereden + " " + nereye + " " + str(baslangic_tarihi) + " " + str(gun_farki))
    # fiyatlar = []
    tum_fiyatlar = []
    while gun_farki > -1:
        print(str(baslangic_tarihi)[0:10] + " Tarihindeki uçuşlar aranıyor...")
        baslangic_tarihi_str = str(baslangic_tarihi)[0:10]  # Convert to string in the format YYYY-MM-DD
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
                # print("//////////////////////")
                airlines = tr.find("div", {"class": "airline"}).text
                flight_number = tr.find("div", {"class": "flight-number"}).text.strip()
                flight_time = tr.find("b", {"class": "flight-time"}).text.strip()
                flight_duration = tr.find("span", {"class": "flight-duration"}).text.strip()
                price = tr.find("div", {"class": "btn-center"}).find("i", {"class": "integers"}).text.strip() + "TL"
                # if int(price[:-2]) < istenilen_max_fiyat:
                #    fiyatlar.append([airlines, flight_number, flight_time, flight_duration, price, baslangic_tarihi_str])
                tum_fiyatlar.append(
                    [airlines, flight_number, flight_time, flight_duration, price, baslangic_tarihi_str])
        except:
            print("Uçuş bulunamadı.")
        baslangic_tarihi += timedelta(days=1)
        gun_farki -= 1

    return tum_fiyatlar


if __name__ == "__main__":
    # nereden = "EZS"
    # nereye = "IST"
    # b_tarih = "19.01.2024"
    # bit_tarih = "24.01.2024"
    # istenilen_max_fiyat=1700
    gonderici_mail = config("sender_mail")
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

    # Tarih farkını hesapla
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
            send_mail(result)
            send_telegram_message(result)
    else:
        print("Uygun uçuş bulunamadı.")
