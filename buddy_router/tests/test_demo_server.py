import unittest

from buddy_router.demo_server import discover_profiles, process_request


class RouterDemoTests(unittest.TestCase):
    def test_directory_exposes_registered_profiles_without_execution(self):
        profiles = discover_profiles()
        self.assertGreaterEqual(len(profiles), 7)
        self.assertTrue(all(item["execution_enabled"] is False for item in profiles))
        forge = next(item for item in profiles if item["profile_id"] == "computer-forge")
        self.assertTrue(forge["disabled_for_execution"])

    def test_research_task_returns_decision_and_six_trace_steps(self):
        result = process_request({
            "task": "Research onboarding improvements",
            "intent": "research_and_summarize",
            "requested_profile": None,
        })
        self.assertEqual(result["decision"]["profile_id"], "grokbot")
        self.assertEqual(result["decision"]["policy"], "allow_advisory")
        self.assertEqual(len(result["trace"]), 6)
        self.assertFalse(result["decision"]["execution_enabled"])
        self.assertFalse(result["safety"]["provider_calls_enabled"])

    def test_manual_mismatch_is_denied_and_explained(self):
        result = process_request({
            "task": "Plan the next sprint",
            "intent": "plan_task",
            "requested_profile": "buddybot",
        })
        self.assertEqual(result["decision"]["policy"], "deny")
        self.assertEqual(result["decision"]["profile_id"], "buddybot")
        self.assertEqual(result["trace"][3]["status"], "blocked")

    def test_malformed_profile_is_denied_without_crash(self):
        result = process_request({
            "task": "Plan the next sprint",
            "intent": "plan_task",
            "requested_profile": {"id": "buddybot"},
        })
        self.assertEqual(result["decision"]["policy"], "deny")
        self.assertEqual(result["trace"][2]["status"], "blocked")

    def test_computer_operation_requires_approval_and_never_executes(self):
        result = process_request({
            "task": "Open a local application",
            "intent": "computer_operation_request",
            "requested_profile": None,
        })
        self.assertEqual(result["decision"]["profile_id"], "computer-forge")
        self.assertEqual(result["decision"]["policy"], "approval_required")
        self.assertFalse(result["decision"]["execution_enabled"])
        self.assertFalse(result["safety"]["computer_execution_enabled"])

    def test_invalid_task_is_rejected(self):
        with self.assertRaises(ValueError):
            process_request({"task": " ", "intent": "plan_task"})

    def test_oversized_task_is_rejected(self):
        with self.assertRaises(ValueError):
            process_request({"task": "x" * 2001, "intent": "plan_task"})


class RouterDemoHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import threading
        from http.server import ThreadingHTTPServer
        from buddy_router.demo_server import DemoHandler

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:%d" % cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_dashboard_is_served(self):
        from urllib.request import urlopen
        with urlopen(self.base_url + "/") as response:
            page = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("UNIFIED ROUTER / COMMAND DECK", page)
            self.assertIn("routeForm", page)
            self.assertIn("/api/profiles", page)

    def test_profile_directory_endpoint(self):
        import json
        from urllib.request import urlopen
        with urlopen(self.base_url + "/api/profiles") as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertGreaterEqual(len(data["profiles"]), 7)

    def test_route_endpoint_returns_trace(self):
        import json
        from urllib.request import Request, urlopen
        body = json.dumps({
            "task": "Research a launch plan",
            "intent": "research_and_summarize",
            "requested_profile": None,
        }).encode("utf-8")
        request = Request(self.base_url + "/api/route", data=body,
                          headers={"Content-Type": "application/json"})
        with urlopen(request) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertEqual(data["decision"]["profile_id"], "grokbot")
        self.assertEqual(len(data["trace"]), 6)
        self.assertFalse(data["safety"]["computer_execution_enabled"])


if __name__ == "__main__":
    unittest.main()
