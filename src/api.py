import logging
from datetime import datetime, date, timezone

from src.types.enums import MoodType
from src.utils.httpclient import http_client
from src.types.schemas import Mood

logger = logging.getLogger(__name__)


async def get_moods(access_token: str, day: date) -> list[Mood]:
    date_str = day.isoformat()

    url = (f"https://app.xn----8sbivqdhdes5ni.xn--p1ai/rest/v1/mood_logs?"
           f"select=id%2Cstudent_id%2Cmood%2Cscore%2Ccreated_at%2Clocal_date%2Cprofiles%21mood_logs_student_id_fkey%28full_name%29%2Cclasses%21mood_logs_class_id_fkey%28name%29&"
           f"local_date=gte.{day.strftime("%Y-%m-%d")}&"
           f"order=created_at.asc")

    js = await http_client.get(url, access_token)
    if not isinstance(js, dict) and not isinstance(js, list):
        logger.warning("get_moods(): empty or invalid response for class %s and day %s", date_str)
        return []

    result = []
    for i, item in enumerate(js):
        try:
            mood = Mood(
                classname=item["classes"]["name"],
                type=MoodType(item["mood"]),
                id=item["id"],
                score=item["score"],
                profile=item["profiles"]["full_name"],
                student_id=item["student_id"],
                created_at=datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=timezone.utc),
                local_date=datetime.strptime(item["local_date"], "%Y-%m-%d")
            )
            result.append(mood)
        except Exception as e:
            logger.warning("get_moods(): skip invalid mood record %s. Error: %s", i, e)

    return result


async def send_mood(mood: Mood) -> bool:
    date_str = mood.time.date().isoformat()
    datetime_str = mood.time.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    url = f"https://my-garmony-default-rtdb.europe-west1.firebasedatabase.app/moods/{date_str}/{mood.classname}.json"
    data = {
        "name": f"Ученик {mood.classname} №{mood.id}",
        "mood": mood.type.value,
        "time": datetime_str,
        "class": mood.classname
    }

    result = await http_client.post(url, data)

    if result is None:
        logger.warning("send_mood(): mood was not sent. Class: %s. Id: %s. Type: %s", mood.classname, mood.id, mood.type)
        return False

    logger.info("send_mood(): mood sent. Class: %s. Id: %s. Type: %s", mood.classname, mood.id, mood.type)
    return True
