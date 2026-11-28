import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import Venue, Event, Category
from sqlalchemy import func

EVENT_URL = (
    "https://www.biletix.com/etkinlik/45G63/"
    "TURKIYE/tr/art-paris-the-show-21-12-2026-istanbul"
)

def get_event_urls(limit=3):
    sitemap_url = (
        "https://www.biletix.com/wbtxapi/api/v1/siteMap/event"
    )

    response = requests.get(
        sitemap_url,
        timeout=20,
        headers={
            "User-Agent": "EventDiscoveryAcademicProject/1.0"
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.content, "xml")

    urls = []

    for loc in soup.find_all("loc", limit=limit):
        urls.append(loc.get_text(strip=True))

    return urls


def normalize_category(schema_type):
    category_map = {
        "TheaterEvent": "Tiyatro",
        "MusicEvent": "Konser",
        "SportsEvent": "Spor",
        "VisualArtsEvent": "Sergi",
        "ExhibitionEvent": "Sergi",
        "Festival": "Festival",
        "EducationEvent": "Eğitim",
        "ComedyEvent": "Komedi",
        "DanceEvent": "Dans",
        "Event": "Diğer"
    }

    return category_map.get(schema_type, "Diğer")


def classify_event_category(title, description, current_category):
    if current_category != "Diğer":
        return current_category

    text = f"{title} {description}".casefold()

    if any(word in text for word in [
        "akvaryum", "sualtı hayvanat bahçesi"
    ]):
        return "Aile / Eğlence"

    if any(word in text for word in [
        "müze", "sergi", "galeri"
    ]):
        return "Müze / Sergi"

    if any(word in text for word in [
        "skyview", "skywalk", "seyir terası"
    ]):
        return "Gezi / Deneyim"

    return current_category


def extract_event_tags(title, description):
    text = f"{title} {description}".casefold()

    tag_keywords = {
        "DJ": ["dj"],
        "Yılbaşı": ["yılbaşı", "yeni yıl"],
        "Pop": ["pop"],
        "Parti": ["parti"],
        "Akvaryum": ["akvaryum"],
        "Hayvanat Bahçesi": ["hayvanat bahçesi"],
        "Müze": ["müze", "müzesi", "müzeler", "müzeleri"],
        "Sanat": ["sanat"],
        "Tiyatro": ["tiyatro"],
        "Festival": ["festival"],
        "Çocuk": ["çocuk"],
        "Dans": ["dans"],
    }

    tags = []

    for tag, keywords in tag_keywords.items():

        if any(
            re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text)
            for keyword in keywords
        ):

            tags.append(tag)

    return tags


def get_event_details(url):
    response = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": "EventDiscoveryAcademicProject/1.0"
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    script = soup.find(
        "script",
        id="btx-event-schema"
    )

    if script is None or not script.string:
        print("Etkinlik JSON-LD verisi bulunamadi.")
        return None

    data = json.loads(script.string)

    location = data.get("location") or {}
    address = location.get("address") or {}

    event = {
        "title": data.get("name"),
        "description": data.get("description"),
        "category": normalize_category(data.get("@type")),
        "location": address.get("addressLocality"),
        "venue_name": location.get("name"),
        "start_date": data.get("startDate"),
        "end_date": data.get("endDate"),
        "source_url": data.get("url")
    }

    return event


def get_event_duration(start_date, end_date):
    if not start_date or not end_date:
        return None

    start = datetime.fromisoformat(
        start_date.replace("Z", "+00:00")
    )

    end = datetime.fromisoformat(
        end_date.replace("Z", "+00:00")
    )

    duration = end - start

    return duration.total_seconds() / 86400



def prepare_event_for_database(event):
    start_date = event.get("start_date")
    end_date = event.get("end_date")

    if not start_date:
        raise ValueError("Etkinligin baslangic tarihi eksik.")

    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(
            start_date.replace("Z", "+00:00")
        )

    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(
            end_date.replace("Z", "+00:00")
        )

    return {
        "title": event["title"],
        "description": event.get("description"),
        "category": event.get("category") or "Diğer",
        "location": event.get("location"),
        "start_date": start_date,
        "end_date": end_date,
        "source_url": event.get("source_url")
    }



def prepare_venue_for_database(event):
    venue_name = event.get("venue_name")
    city = event.get("location")

    if not venue_name or not city:
        return None

    venue_name = " ".join(venue_name.split())
    city = " ".join(city.split())

    if not venue_name or not city:
        return None

    return {
        "name": venue_name,
        "city": city
    }


def find_existing_venue(venue_data):
    if venue_data is None:
        return None

    db = SessionLocal()

    try:
        venue = (
            db.query(Venue)
            .filter(
                func.lower(Venue.name) == venue_data["name"].lower(),
                func.lower(Venue.city) == venue_data["city"].lower()
            )
            .first()
        )

        return venue.id if venue else None

    finally:
        db.close()



def get_or_create_venue(venue_data):
    if venue_data is None:
        return None

    db = SessionLocal()

    try:
        venues = db.query(Venue).all()

        for venue in venues:
            same_name = (
                venue.name.strip().casefold()
                == venue_data["name"].strip().casefold()
            )

            same_city = (
                venue.city.strip().casefold()
                == venue_data["city"].strip().casefold()
            )

            if same_name and same_city:
                print("Mekan zaten kayitli.")
                return venue.id

        new_venue = Venue(
            name=venue_data["name"],
            city=venue_data["city"]
        )

        db.add(new_venue)
        db.commit()
        db.refresh(new_venue)

        print("Yeni mekan veritabanina kaydedildi.")

        return new_venue.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_or_create_category(db, category_name):
    category_name = (category_name or "Diğer").strip()

    existing_category = (
        db.query(Category)
        .filter(Category.name == category_name)
        .first()
    )

    if existing_category:
        return existing_category.id

    new_category = Category(name=category_name)

    db.add(new_category)
    db.flush()

    return new_category.id


def find_existing_event(event_data):
    source_url = event_data.get("source_url")

    if not source_url:
        return None

    db = SessionLocal()

    try:
        existing_event = (
            db.query(Event)
            .filter(Event.source_url == source_url)
            .first()
        )

        if existing_event:
            return existing_event.id

        return None

    finally:
        db.close()



def save_event_to_database(event_data):
    source_url = event_data.get("source_url")

    if not source_url:
        print("Kaynak URL eksik, etkinlik kaydedilmedi.")
        return None

    db = SessionLocal()

    try:
        existing_event = (
            db.query(Event)
            .filter(Event.source_url == source_url)
            .first()
        )

        category_name = event_data.get("category") or "Diğer"

        if existing_event:
            if existing_event.category.name != category_name:
                category_id = get_or_create_category(
                    db, category_name
                )

                existing_event.category_id = category_id
                db.commit()

                print("Etkinlik kategorisi guncellendi.")
            else:
                print("Etkinlik zaten kayitli.")

            return existing_event.id

        category_id = get_or_create_category(
            db, category_name
        )

        new_event = Event(
            title=event_data["title"],
            description=event_data.get("description"),
            category_id=category_id,
            start_date=event_data["start_date"],
            end_date=event_data.get("end_date"),
            source="Biletix",
            source_url=source_url,
            venue_id=event_data.get("venue_id")
        )

        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        print("Yeni etkinlik veritabanina kaydedildi.")

        return new_event.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



def main():
    print("Biletix etkinlikleri toplaniyor...")


    event_urls = get_event_urls(limit=10)


    for index, url in enumerate(event_urls, start=1):
        print(f"\n--- Etkinlik {index} ---")

        try:
            event = get_event_details(url)


            if event is not None:
                start_date = event.get("start_date")

                if not start_date:
                    print("Tarih eksik, etkinlik atlandi.")
                    continue

                event_date = datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                )

                if event_date.tzinfo is None:
                    print("Saat dilimi eksik, etkinlik atlandi.")
                    continue


                end_date = event.get("end_date")

                if end_date:
                    final_date = datetime.fromisoformat(
                        end_date.replace("Z", "+00:00")
                    )
                else:
                    final_date = event_date

                if final_date.tzinfo is None:
                    print("Bitis tarihi saat dilimi eksik, atlandi.")
                    continue

                if final_date < datetime.now(timezone.utc):
                    print("Etkinlik tarihi gecmis, atlandi.")
                    continue


                print("Ad:", event["title"])
                print("Kategori:", event["category"])
                print("Sehir:", event["location"])
                print("Mekan:", event["venue_name"])
                print("Baslangic tarihi:", event["start_date"])
                print("Bitis tarihi:", event["end_date"])

                duration = get_event_duration(
                    event["start_date"],
                    event["end_date"]
                )

                if duration is not None:
                    print("Sure (gun):", round(duration, 1))

                    if duration >= 2:
                        print("Etkinlik tipi: Uzun sureli")
                    else:
                        print("Etkinlik tipi: Kisa sureli")

                print("Kaynak:", event["source_url"])

                database_event = prepare_event_for_database(event)

                database_event["category"] = classify_event_category(
                    database_event["title"],
                    database_event.get("description") or "",
                    database_event["category"]
                )

                print(
                    "Otomatik belirlenen kategori:",
                    database_event["category"]
                )

                event_tags = extract_event_tags(
                    database_event["title"],
                    database_event.get("description") or ""
                )

                print("Otomatik cikarilan etiketler:", event_tags)



                print("\nVeritabanina hazir etkinlik:")
                print(database_event)

                database_venue = prepare_venue_for_database(event)

                print("\nVeritabanina hazir mekan:")
                print(database_venue)

                venue_id = get_or_create_venue(database_venue)

                print("Mekan ID:", venue_id)

                database_event["venue_id"] = venue_id

                print("\nMekan ile iliskilendirilmis etkinlik:")
                print(database_event)

                existing_event_id = find_existing_event(database_event)

                print("Mevcut etkinlik ID:", existing_event_id)

                saved_event_id = save_event_to_database(database_event)

                print("Kaydedilen etkinlik ID:", saved_event_id)






            else:
                print("Etkinlik bilgileri bulunamadi.")

        except (requests.RequestException, ValueError) as error:
            print("Etkinlik okunamadi:", error)

        if index < len(event_urls):
            import time
            time.sleep(2)


if __name__ == "__main__":
    main()