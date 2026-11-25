import unittest

from buddy_router.engine import route


class RouterTests(unittest.TestCase):
    def test_auto_select_research(self):
        d = route({"trace_id": "t1", "intent": "research_and_summarize"})
        self.assertEqual(d["profile_id"], "grokbot")
        self.assertEqual(d["policy"], "allow_advisory")
        self.assertFalse(d["execution_enabled"])

    def test_plan(self):
        d = route({"trace_id": "t2", "intent": "plan_task"})
        self.assertEqual(d["profile_id"], "manus-patterns")

    def test_missing_fields_denied(self):
        self.assertEqual(route({"trace_id": "t3"})["policy"], "deny")

    def test_unknown_intent_denied(self):
        self.assertEqual(route({"trace_id": "t4", "intent": "unknown"})["policy"], "deny")

    def test_requested_mismatch_denied(self):
        d = route({
            "trace_id": "t5",
            "intent": "plan_task",
            "requested_profile": "buddybot",
        })
        self.assertEqual(d["policy"], "deny")
        self.assertEqual(d["profile_id"], "buddybot")
        self.assertFalse(d["execution_enabled"])

    def test_unknown_requested_profile_denied(self):
        d = route({
            "trace_id": "t7",
            "intent": "plan_task",
            "requested_profile": "not-registered",
        })
        self.assertEqual(d["policy"], "deny")
        self.assertIsNone(d["profile_id"])

    def test_non_string_requested_profile_denied_without_exception(self):
        d = route({
            "trace_id": "t8",
            "intent": "plan_task",
            "requested_profile": {"id": "buddybot"},
        })
        self.assertEqual(d["policy"], "deny")
        self.assertIsNone(d["profile_id"])
        self.assertFalse(d["execution_enabled"])

    def test_disabled_profile_with_wrong_intent_is_denied(self):
        d = route({
            "trace_id": "t9",
            "intent": "plan_task",
            "requested_profile": "computer-forge",
        })
        self.assertEqual(d["policy"], "deny")
        self.assertEqual(d["profile_id"], "computer-forge")
        self.assertFalse(d["execution_enabled"])

    def test_computer_profile_execution_disabled(self):
        d = route({"trace_id": "t6", "intent": "computer_operation_request"})
        self.assertEqual(d["policy"], "approval_required")
        self.assertFalse(d["execution_enabled"])


if __name__ == "__main__":
    unittest.main()
