import logging
from flask import Flask, request
import subprocess
import traceback

app = Flask(__name__)

SMS_SCRIPT = "/root/Check_SMS/Prometheus_sms.sh"
LOG_FILE = "/var/log/WebHook/WebHook.log"

# 🔹 로그 설정
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

@app.route("/alert", methods=["POST"])
def alert():
    try:
        data = request.json
        alerts = data.get("alerts", [])

        for alert in alerts:
            alert_name = alert.get("labels", {}).get("alertname", "").strip()
            alert_status = alert.get("status", "firing")  # firing 또는 resolved
            instance = alert.get("labels", {}).get("instance", "알 수 없는 서버")
            
            if alert_status == "resolved":
                summary = f"[해결] {alert.get('annotations', {}).get('summary', '[알림] 서버 이벤트 해결')}"
                description = alert.get("annotations", {}).get(
                    "description", "No description available."
                )
            else:
                summary = alert.get("annotations", {}).get("summary", f"[알림] {instance} 서버 이벤트 발생")
                description = alert.get("annotations", {}).get(
                    "description", "No description available."
                )

            # 문자 내용 구성
            message = f"{summary}\n{description}"
            message = " ".join(message.split())
            message = "".join(c for c in message if c.isprintable())
            
            # 소수점 처리 (소수점 2자리까지만 표시)
            import re
            message = re.sub(r'(\d+\.\d{3,})', lambda m: f"{float(m.group(1)):.2f}", message)

            logging.info(f"📢 Received Alert: {alert_name} from {instance}, Message: {message}")

            # 🔹 SMS 알림 전송
            result = subprocess.run(
                [SMS_SCRIPT, message],
                shell=False,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            logging.info(f"✅ SMS Script Output: {result.stdout}")
            if result.stderr:
                logging.warning(f"⚠️ SMS Script Error: {result.stderr}")

        return "Alert received", 200

    except Exception:
        error_message = traceback.format_exc()
        logging.error(f"❌ Error: {error_message}")
        return f"Internal Server Error: {error_message}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9200)
