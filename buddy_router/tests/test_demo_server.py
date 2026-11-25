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


if __name__ == "__main__":
    unittest.main()
