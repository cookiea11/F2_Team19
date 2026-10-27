"""Exercise real local HTTP requests against the dashboard API."""
from http.server import ThreadingHTTPServer
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from app import Handler


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_dashboard_and_offline_data_served(self):
        with urlopen(self.url) as response:
            self.assertIn(b"Predictive Adaptive Mesh Routing", response.read())
        with urlopen(self.url + "/demo_data.js") as response:
            self.assertTrue(response.read().startswith(b"window.PAMR_DEMO="))

    def test_real_simulation_post(self):
        payload = json.dumps({"nodes": 12, "duration": 80, "seed": 9, "horizon": 20}).encode()
        request = Request(self.url + "/api/simulate", data=payload,
                          headers={"Content-Type": "application/json"})
        with urlopen(request) as response:
            result = json.load(response)
        self.assertEqual(set(result["runs"]), {"shortest", "reactive", "predictive"})
        self.assertEqual(result["config"]["nodes"], 12)

    def test_invalid_config_returns_400(self):
        request = Request(self.url + "/api/simulate", data=b'{"nodes":0}')
        with self.assertRaises(HTTPError) as context:
            urlopen(request)
        self.assertEqual(context.exception.code, 400)

    def test_unknown_path_cannot_read_source(self):
        with self.assertRaises(HTTPError) as context:
            urlopen(self.url + "/../simulator.py")
        self.assertEqual(context.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
