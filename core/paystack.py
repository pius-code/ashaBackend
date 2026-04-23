from dotenv import load_dotenv
import os

load_dotenv()


paystack_test_key = os.getenv("PAYSTACK_TEST_SECRET_KEY")
paystack_live_key = os.getenv("PAYSTACK_LIVE_SECRET_KEY")

headers = {
    "Authorization": f"Bearer {paystack_live_key}",
    "Content-Type": "application/json",
}
