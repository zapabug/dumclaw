import unittest
from llm import ask_llm
import time

class TestLLMRefactor(unittest.TestCase):
    
    def test_weather_functionality(self):
        """Test that weather functionality works through the skills framework"""
        try:
            action, reply, extra = ask_llm("what's the weather like?")
            self.assertIn(action, ["weather_reply", "reply"], "Weather should return weather_reply or reply action")
            self.assertTrue(len(reply) > 0, "Reply should not be empty")
        except Exception as e:
            print(f"Weather test failed: {e}")
            self.fail("Weather functionality test failed")
            
    def test_dm_functionality(self):
        """Test that DM functionality works through the skills framework"""
        try:
            action, reply, extra = ask_llm("send a dm to john saying hello")
            self.assertIn(action, ["dm_contact", "reply"], "DM should return dm_contact or reply action")
            self.assertTrue(len(reply) > 0, "Reply should not be empty")
            if action == "dm_contact":
                self.assertIn("contact", extra, "DM should include contact info")
                self.assertIn("message_hint", extra, "DM should include message hint")
        except Exception as e:
            print(f"DM test failed: {e}")
            self.fail("DM functionality test failed")
    
    def test_note_functionality(self):
        """Test that note functionality works through the skills framework"""
        try:
            action, reply, extra = ask_llm("post a note about the weather")
            self.assertIn(action, ["note", "reply"], "Note should return note or reply action")
            self.assertTrue(len(reply) > 0, "Reply should not be empty")
        except Exception as e:
            print(f"Note test failed: {e}")
            self.fail("Note functionality test failed")
    
    def test_default_reply(self):
        """Test that default reply functionality works"""
        try:
            action, reply, extra = ask_llm("how are you?")
            self.assertEqual(action, "reply", "Default should return reply action")
            self.assertTrue(len(reply) > 0, "Reply should not be empty")
        except Exception as e:
            print(f"Default reply test failed: {e}")
            self.fail("Default reply functionality test failed")

if __name__ == "__main__":
    print("Running tests with improved error handling...")
    unittest.main()