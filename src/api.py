import logging
from datetime import datetime, date, timezone

from src.types.enums import MoodType
from src.utils.httpclient import http_client
from src.types.schemas import Mood

logger = logging.getLogger(__name__)


async def get_profile(access_token: str) -> tuple[str, str] :
    url = "https://app.xn----8sbivqdhdes5ni.xn--p1ai/rest/v1/profiles?select=id%2Cclass_id"

    js = await http_client.get(url, access_token)
    if not isinstance(js, dict) and not isinstance(js, list):
        logger.warning("get_moods(): empty or invalid response. Token: %s", access_token)
        return "", ""

    student_id = js[0]["id"]
    class_id = js[0]["class_id"]
    return student_id, class_id


async def get_moods(access_token: str, day: date) -> list[Mood]:
    url = (f"https://app.xn----8sbivqdhdes5ni.xn--p1ai/rest/v1/mood_logs?"
           f"select=id%2Cstudent_id%2Cmood%2Cscore%2Ccreated_at%2Clocal_date%2Cprofiles%21mood_logs_student_id_fkey%28full_name%29%2Cclasses%21mood_logs_class_id_fkey%28name%29&"
           f"local_date=gte.{day.strftime("%Y-%m-%d")}&"
           f"order=created_at.asc")

    js = await http_client.get(url, access_token)
    if not isinstance(js, dict) and not isinstance(js, list):
        logger.warning("get_moods(): empty or invalid response. Token: %s", access_token)
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


async def send_mood(access_token: str, mood: Mood) -> bool:
    student_id, class_id = await get_profile(access_token)

    url = "https://app.xn----8sbivqdhdes5ni.xn--p1ai/rest/v1/mood_logs?on_conflict=student_id%2Clocal_date"

    body = {
        "student_id": student_id,
        "class_id": class_id,
        "mood": mood.type.value,
        "score": 5,
        "note": None,
        "local_date": mood.local_date.strftime("%Y-%m-%d"),
    }

    js = await http_client.post(url, access_token, body)
    if js is None:
        logger.warning("send_mood(): empty or invalid response for token %s", access_token)
        return False

    logger.info("send_mood(): mood sent. Token: %s, Type: %s", access_token, mood.type)
    return True
