import utils_core


def get_alerts():
    roster = utils_core.load_roster()
    news = utils_core.fetch_news()
    alerts = []

    for player in roster.get("players", []):
        name, status = player.get("name"), player.get("status", "")
        if status in ["OUT", "DOUBTFUL", "QUESTIONABLE", "IR"]:
            alerts.append({"player": name, "status": status})

        for n in news:
            if name and name in n.get("title", ""):
                alerts.append(
                    {"player": name, "headline": n.get("title"), "link": n.get("url")}
                )

    return {"alerts": alerts, "count": len(alerts)}
