"""Lightweight HTTP API and static file server for the Tourism Digital Twin UI."""

from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from tourism_twin.config import SETTINGS
from tourism_twin.domain.scenario import ScenarioLever
from tourism_twin.nowcast.serving import NowcastService
from tourism_twin.planning.simulator import TourismDigitalTwin

STATIC_DIR = Path(__file__).resolve().parent / "static"
RESULTS_PATH = SETTINGS.evaluation_results_path

TWIN = TourismDigitalTwin()
NOWCAST_BUNDLE = SETTINGS.predictions_dir / "nowcast_serving.json"
_NOWCAST = {}


def nowcast_service():
    """The nowcast service, loaded once from the bundle (None when `twin predict` has not run)."""
    if "service" not in _NOWCAST and NOWCAST_BUNDLE.exists():
        _NOWCAST["service"] = NowcastService.load(NOWCAST_BUNDLE)
    return _NOWCAST.get("service")


class DigitalTwinHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.serve_file(STATIC_DIR / "index.html", "text/html")
        elif path == "/api/simulate":
            self.handle_simulate(query)
        elif path == "/api/benchmark":
            self.handle_benchmark()
        elif path.startswith("/api/nowcast/"):
            self.handle_nowcast(path[len("/api/nowcast/"):], query)
        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = STATIC_DIR / rel_path
            if file_path.exists() and file_path.is_file():
                content_type = "text/css" if file_path.suffix == ".css" else "application/javascript"
                self.serve_file(file_path, content_type)
            else:
                self.send_error(404, "Static file not found")
        else:
            self.send_error(404, "Endpoint not found")

    def serve_file(self, file_path: Path, content_type: str):
        if not file_path.exists():
            self.send_error(404, "File not found")
            return
        with open(file_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_simulate(self, query):
        try:
            market = query.get("market", ["UNITED KINGDOM"])[0]
            season = query.get("season", ["Winter_Peak"])[0]

            valid_seasons = {"Winter_Peak", "Spring_Shoulder", "Summer_Trough", "Autumn_Shoulder"}
            if season not in valid_seasons:
                self.send_json(
                    {"error": f"Invalid season '{season}'. Must be one of: {sorted(list(valid_seasons))}"},
                    status=400,
                )
                return

            delta_freq = float(query.get("delta_freq", [0.0])[0])
            gauge = float(query.get("gauge", [250.0])[0])
            delta_seats_pct = float(query.get("delta_seats_pct", [0.0])[0])
            delta_lf = float(query.get("delta_lf", [0.0])[0])
            delta_p2p = float(query.get("delta_p2p", [0.0])[0])
            delta_mult_pct = float(query.get("delta_mult_pct", [0.0])[0])
            delta_los = float(query.get("delta_los", [0.0])[0])

            lever = ScenarioLever(
                market=market,
                delta_frequency=delta_freq,
                aircraft_gauge=gauge,
                delta_seats_pct=delta_seats_pct,
                delta_load_factor=delta_lf,
                delta_p2p_share=delta_p2p,
                delta_multiplier_pct=delta_mult_pct,
                delta_los=delta_los,
            )

            report = TWIN.run_scenario(market=market, season=season, lever=lever, n_draws=1000)
            s = report.structural_result
            unc = report.uncertainty_bands
            hyb = report.hybrid_result

            response = {
                "market": report.market,
                "season": report.season,
                "archetype": report.archetype,
                "is_cold_start": report.is_cold_start,
                "recommendation_summary": report.recommendation_summary,
                "conversion_chain": {
                    "seats": {"base": s.base_seats, "sim": s.sim_seats, "delta": s.delta_seats},
                    "pax": {"base": s.base_pax, "sim": s.sim_pax, "delta": s.delta_pax},
                    "p2p": {"base": s.base_p2p, "sim": s.sim_p2p, "delta": s.delta_p2p},
                    "arrivals": {"base": s.base_arrivals, "sim": s.sim_arrivals, "delta": s.delta_arrivals},
                    "guests": {"base": s.base_guests, "sim": s.sim_guests, "delta": s.delta_guests},
                    "load_factor": {"base": s.base_lf, "sim": s.sim_lf, "delta": s.sim_lf - s.base_lf},
                    "p2p_share": {"base": s.base_p2p_share, "sim": s.sim_p2p_share, "delta": s.sim_p2p_share - s.base_p2p_share},
                    "multiplier": {"base": s.base_multiplier, "sim": s.sim_multiplier, "delta": s.sim_multiplier - s.base_multiplier},
                },
                "waterfall": {
                    "seats_effect": s.waterfall_seats,
                    "load_factor_effect": s.waterfall_lf,
                    "p2p_effect": s.waterfall_p2p,
                    "multiplier_effect": s.waterfall_multiplier,
                    "los_effect": s.waterfall_los,
                    "total_lift": s.delta_guests,
                },
                "hybrid": {
                    "base": hyb["hybrid_base"],
                    "sim": hyb["hybrid_sim"],
                    "delta": hyb["hybrid_delta"],
                    "residual_adjustment": hyb["residual_correction"],
                    "is_monotonic": hyb["is_monotonic"],
                },
                "uncertainty": {
                    "p10": unc.p10,
                    "p50": unc.p50,
                    "p90": unc.p90,
                    "delta_p10": unc.delta_p10,
                    "delta_p50": unc.delta_p50,
                    "delta_p90": unc.delta_p90,
                    "coverage_pct": unc.demonstrated_coverage_pct,
                },
                "tornado": report.tornado_sensitivity,
            }

            self.send_json(response)
        except Exception as e:
            self.send_json({"error": str(e)}, status=400)


    def handle_benchmark(self):
        if not RESULTS_PATH.exists():
            self.send_json({"error": "Benchmark results not yet compiled."}, status=404)
            return
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.send_json(data)

    def handle_nowcast(self, endpoint, query):
        """Nowcast answers from the bundle `twin predict` writes (no refitting):
        series; range?series=TOTAL&start=YYYY-MM-DD&end=YYYY-MM-DD; nationalities?start=&end=."""
        service = nowcast_service()
        if service is None:
            self.send_json({"error": f"No nowcast bundle at {NOWCAST_BUNDLE}; run `twin predict` first."}, status=503)
            return
        try:
            if endpoint == "series":
                self.send_json({"series": service.series_names(), "start": service.bundle["test_start"],
                                "end": service.bundle["test_end"], "coverage": service.coverage})
            elif endpoint == "range":
                self.send_json(service.range_total(query.get("series", ["TOTAL"])[0], query["start"][0], query["end"][0]))
            elif endpoint == "nationalities":
                self.send_json({"nationalities": service.nationalities(query["start"][0], query["end"][0])})
            else:
                self.send_error(404, "Endpoint not found")
        except KeyError as e:
            self.send_json({"error": f"Missing or unknown parameter: {e}"}, status=400)
        except ValueError as e:
            self.send_json({"error": str(e)}, status=400)

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = 8080):
    server = HTTPServer(("127.0.0.1", port), DigitalTwinHandler)
    print(f"Abu Dhabi Tourism Digital Twin UI serving at: http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()


if __name__ == "__main__":
    run_server(8080)
