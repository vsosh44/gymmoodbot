import logging
from datetime import datetime, date, timezone

from src.types.enums import MoodType
from src.utils.httpclient import http_client
from src.types.schemas import Mood

logger = logging.getLogger(__name__)


async def get_moods(mood_classname: str, day: date) -> list[Mood]:
    date_str = day.isoformat()

    url = f"https://my-garmony-default-rtdb.europe-west1.firebasedatabase.app/moods/{date_str}/{mood_classname}.json"

    js = await http_client.get(url)
    if not isinstance(js, dict):
        logger.warning("get_moods(): empty or invalid response for class %s and day %s", mood_classname, date_str)
        return []

    result = []
    for key, js_mood in js.items():
        try:
            mood = Mood(
                operation_id=key,
                classname=js_mood["class"],
                type=MoodType(js_mood["mood"]),
                id=int(js_mood["name"].split()[-1].removeprefix("№")),
                time=datetime.strptime(js_mood["time"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            )
            result.append(mood)
        except Exception as e:
            logger.warning("get_moods(): skip invalid mood record %s. Error: %s", key, e)

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
