from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_ROOT = STATIC_DIR.resolve()


CAMPAIGNS = [
    {
        "id": "cmp-001",
        "name": "Welcome Series - FR",
        "target": "Nouveaux inscrits",
        "status": "active",
        "template": "Aurora",
        "visual_style": "Hero produit",
        "sent": 182000,
        "delivered": 178360,
        "opens": 91320,
        "clicks": 18640,
        "bounces": 3640,
        "unsubscribes": 728,
        "send_per_hour": 24000,
    },
    {
        "id": "cmp-002",
        "name": "Promo Flash - VIP",
        "target": "Clients VIP",
        "status": "active",
        "template": "Pulse",
        "visual_style": "Dark premium",
        "sent": 96000,
        "delivered": 95040,
        "opens": 59840,
        "clicks": 20160,
        "bounces": 960,
        "unsubscribes": 384,
        "send_per_hour": 48000,
    },
    {
        "id": "cmp-003",
        "name": "Relance panier - EU",
        "target": "Abandon panier",
        "status": "active",
        "template": "Orbit",
        "visual_style": "Minimal e-commerce",
        "sent": 124000,
        "delivered": 121520,
        "opens": 67200,
        "clicks": 24480,
        "bounces": 2480,
        "unsubscribes": 496,
        "send_per_hour": 18000,
    },
    {
        "id": "cmp-004",
        "name": "Newsletter B2B",
        "target": "Prospects B2B",
        "status": "paused",
        "template": "Ledger",
        "visual_style": "Editorial",
        "sent": 78000,
        "delivered": 75660,
        "opens": 25600,
        "clicks": 4680,
        "bounces": 2340,
        "unsubscribes": 195,
        "send_per_hour": 12000,
    },
    {
        "id": "cmp-005",
        "name": "Reactivation Dormants",
        "target": "Inactifs 90 jours",
        "status": "draft",
        "template": "Nova",
        "visual_style": "Light editorial",
        "sent": 54000,
        "delivered": 52380,
        "opens": 14160,
        "clicks": 2700,
        "bounces": 1620,
        "unsubscribes": 324,
        "send_per_hour": 8000,
    },
]


def pct(part: int, total: int) -> float:
    return round((part / total) * 100, 2) if total else 0.0


def enrich_campaign(campaign: dict) -> dict:
    enriched = dict(campaign)
    enriched["delivery_rate"] = pct(campaign["delivered"], campaign["sent"])
    enriched["open_rate"] = pct(campaign["opens"], campaign["delivered"])
    enriched["click_rate"] = pct(campaign["clicks"], campaign["delivered"])
    enriched["bounce_rate"] = pct(campaign["bounces"], campaign["sent"])
    enriched["unsubscribe_rate"] = pct(campaign["unsubscribes"], campaign["delivered"])
    return enriched


def filter_campaigns(target: str | None, status: str | None) -> list[dict]:
    items = [enrich_campaign(campaign) for campaign in CAMPAIGNS]
    if target and target != "all":
        items = [item for item in items if item["target"] == target]
    if status and status != "all":
        items = [item for item in items if item["status"] == status]
    return items


def build_summary(campaigns: list[dict]) -> dict:
    total_sent = sum(item["sent"] for item in campaigns)
    total_delivered = sum(item["delivered"] for item in campaigns)
    total_opens = sum(item["opens"] for item in campaigns)
    total_clicks = sum(item["clicks"] for item in campaigns)
    total_bounces = sum(item["bounces"] for item in campaigns)
    total_unsubs = sum(item["unsubscribes"] for item in campaigns)

    templates = {}
    for item in campaigns:
        bucket = templates.setdefault(
            item["template"],
            {
                "template": item["template"],
                "visual_style": item["visual_style"],
                "sent": 0,
                "delivered": 0,
                "opens": 0,
                "clicks": 0,
            },
        )
        bucket["sent"] += item["sent"]
        bucket["delivered"] += item["delivered"]
        bucket["opens"] += item["opens"]
        bucket["clicks"] += item["clicks"]

    template_summary = []
    for template in templates.values():
        template_summary.append(
            {
                **template,
                "open_rate": pct(template["opens"], template["delivered"]),
                "click_rate": pct(template["clicks"], template["delivered"]),
            }
        )

    template_summary.sort(key=lambda item: item["click_rate"], reverse=True)

    return {
        "kpis": {
            "campaign_count": len(campaigns),
            "total_sent": total_sent,
            "delivery_rate": pct(total_delivered, total_sent),
            "open_rate": pct(total_opens, total_delivered),
            "click_rate": pct(total_clicks, total_delivered),
            "bounce_rate": pct(total_bounces, total_sent),
            "unsubscribe_rate": pct(total_unsubs, total_delivered),
            "avg_send_per_hour": round(
                sum(item["send_per_hour"] for item in campaigns) / len(campaigns), 0
            )
            if campaigns
            else 0,
        },
        "targets": sorted({campaign["target"] for campaign in CAMPAIGNS}),
        "statuses": ["all", "active", "paused", "draft"],
        "template_summary": template_summary,
        "campaigns": campaigns,
    }


class EmailissHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/dashboard":
            self.serve_dashboard_data(parsed.query)
            return

        if parsed.path == "/" or parsed.path == "/index.html":
            self.serve_file(STATIC_DIR / "index.html")
            return

        static_path = (STATIC_DIR / parsed.path.lstrip("/")).resolve()
        if (
            str(static_path).startswith(str(STATIC_ROOT))
            and static_path.exists()
            and static_path.is_file()
        ):
            self.serve_file(static_path)
            return

        self.send_error(404, "Not found")

    def serve_dashboard_data(self, query_string: str) -> None:
        query = parse_qs(query_string)
        target = query.get("target", [None])[0]
        status = query.get("status", [None])[0]
        campaigns = filter_campaigns(target, status)
        payload = json.dumps(build_summary(campaigns)).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def serve_file(self, file_path: Path) -> None:
        content = file_path.read_bytes()
        content_type, _ = mimetypes.guess_type(str(file_path))

        self.send_response(200)
        self.send_header(
            "Content-Type", content_type or "application/octet-stream"
        )
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args) -> None:
        return


def run() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), EmailissHandler)
    print("Emailiss running on http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
