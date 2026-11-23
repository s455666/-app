"""果實時光 — 水果播種成熟日計算機."""

from datetime import date, datetime, timedelta

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from fruits_data import CITIES, ENVIRONMENTS, FRUITS, STAGE_NAMES

load_dotenv()
app = Flask(__name__)

WEEKDAYS = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")


def _parse_date(value):
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
        if parsed.isoformat() != value:
            raise ValueError
        return parsed
    except (TypeError, ValueError):
        raise ValueError("日期格式請使用 YYYY-MM-DD，且必須是有效日期。")


def _calculate(payload):
    fruit = payload.get("fruit", "")
    if fruit == "自訂水果與天數":
        name = str(payload.get("custom_name", "")).strip()
        if not name or len(name) > 30:
            raise ValueError("請輸入 1 至 30 個字的自訂水果名稱。")
        raw_days = payload.get("custom_days", "")
        try:
            days = int(raw_days)
        except (TypeError, ValueError):
            raise ValueError("自訂成熟天數必須是正整數。")
        if str(raw_days).strip() != str(days) or not 1 <= days <= 3650:
            raise ValueError("自訂成熟天數必須是 1 至 3650 的正整數。")
        detail = {"days": days, "stages": (0.12, 0.38, 0.25, 0.25), "sun": "依品種需求提供充足日照", "water": "土壤乾燥時澆透，避免積水", "soil": "選擇疏鬆且排水良好的介質", "tips": "自訂品種的照護資訊為通用建議，請依實際品種調整。"}
    else:
        if fruit not in FRUITS:
            raise ValueError("請從清單選擇有效的水果。")
        name, detail = fruit, FRUITS[fruit]
        days = detail["days"]

    sowing_date = _parse_date(payload.get("sowing_date"))
    environment = payload.get("environment", "露天全日照")
    if environment not in ENVIRONMENTS:
        raise ValueError("請選擇有效的種植環境。")
    city = payload.get("city", "苗栗")
    if city not in CITIES:
        raise ValueError("請選擇清單中的台灣城市。")

    adjusted_days = max(1, round(days * ENVIRONMENTS[environment]))
    harvest_date = sowing_date + timedelta(days=adjusted_days)
    stages = []
    previous = 0
    for index, (stage_name, proportion) in enumerate(zip(STAGE_NAMES, detail["stages"])):
        endpoint = adjusted_days if index == len(STAGE_NAMES) - 1 else round(adjusted_days * sum(detail["stages"][:index + 1]))
        start = sowing_date + timedelta(days=previous)
        end = sowing_date + timedelta(days=max(previous, endpoint - 1))
        stages.append({"name": stage_name, "start": start.isoformat(), "end": end.isoformat()})
        previous = endpoint

    today = date.today()
    remaining = (harvest_date - today).days
    return {"fruit": name, "environment": environment, "sowing_date": sowing_date.isoformat(),
            "maturity_date": harvest_date.isoformat(), "maturity_date_display": f"{harvest_date.year} 年 {harvest_date.month:02d} 月 {harvest_date.day:02d} 日（{WEEKDAYS[harvest_date.weekday()]}）",
            "days_remaining": max(0, remaining), "harvest_ready": remaining <= 0,
            "adjusted_days": adjusted_days, "stages": stages,
            "care": {key: detail[key] for key in ("sun", "water", "soil", "tips")}, "city": city}


def _weather(city):
    latitude, longitude = CITIES[city]
    try:
        response = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": latitude, "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Asia/Taipei", "forecast_days": 1,
        }, timeout=5)
        response.raise_for_status()
        daily = response.json()["daily"]
        return {"available": True, "temperature_min": daily["temperature_2m_min"][0],
                "temperature_max": daily["temperature_2m_max"][0], "rain_probability": daily["precipitation_probability_max"][0],
                "advice": "降雨機率高，留意排水並暫緩澆水。" if daily["precipitation_probability_max"][0] >= 60 else "可依土壤乾濕安排澆水，幼苗保持適度日照。"}
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return {"available": False, "message": "目前無法取得即時天氣，計算功能仍可正常使用；請依現場天候照護。"}


@app.route("/", methods=["GET", "POST"])
def index():
    result = error = None
    form = {"sowing_date": date.today().isoformat(), "environment": "露天全日照", "city": "苗栗", "fruit": "小番茄"}
    if request.method == "POST":
        form.update(request.form.to_dict())
        try:
            result = _calculate(form)
            result["weather"] = _weather(result["city"])
        except ValueError as exc:
            error = str(exc)
    return render_template("index.html", fruits=FRUITS, environments=ENVIRONMENTS, cities=CITIES, form=form, result=result, error=error)


@app.get("/api/fruits")
def fruits_api():
    return jsonify({"fruits": [{"name": name, "days": data["days"], "care": {key: data[key] for key in ("sun", "water", "soil", "tips")}} for name, data in FRUITS.items()], "custom_option": "自訂水果與天數"})


@app.post("/api/calculate")
def calculate_api():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "請提供 JSON 物件。"}), 400
    try:
        result = _calculate(payload)
        result["weather"] = _weather(result["city"])
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=False)
