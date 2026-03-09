"""Messages partagés (source unique : config/settings.yml)."""

from app.config_loader import get_robots_txt_messages

MSG_ROBOTS_TXT_UNAVAILABLE = get_robots_txt_messages()["unavailable"]
