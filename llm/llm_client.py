import os
import json
import threading
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
# pyrefly: ignore [missing-import]
from openai import OpenAI

load_dotenv(override=True)


class LLMClient:

    _quota_lock = threading.Lock()

    def __init__(self, model_name=None):

        provider = os.getenv("LLM_PROVIDER", "groq").lower()
        if provider == "together":
            api_key = os.getenv("TOGETHER_API_KEY")
            if not api_key:
                raise ValueError(
                    "TOGETHER_API_KEY missing in .env"
                )
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.together.xyz/v1"
            )
            self.model_name = model_name or "meta-llama/Meta-Llama-3-8b-instruct"
        else:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError(
                    "GROQ_API_KEY missing in .env"
                )
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model_name = model_name or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        self.daily_request_limit = int(
            os.getenv(
                "LLM_DAILY_REQUEST_LIMIT",
                "1000"
            )
        )

        self.usage_file_path = os.getenv(
            "LLM_DAILY_USAGE_PATH",
            "storage/llm_daily_usage.json"
        )

        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

    def _load_daily_usage(self):

        if not os.path.exists(self.usage_file_path):
            return {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "count": 0
            }

        try:
            with open(
                self.usage_file_path,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)
        except Exception:
            return {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "count": 0
            }

    def _save_daily_usage(self, usage):

        os.makedirs(
            os.path.dirname(self.usage_file_path),
            exist_ok=True
        )

        with open(
            self.usage_file_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                usage,
                f,
                indent=2
            )

    def _consume_daily_quota(self):

        if self.daily_request_limit <= 0:
            return True, 0, 0, datetime.utcnow().strftime("%Y-%m-%d")

        today = datetime.utcnow().strftime("%Y-%m-%d")

        with self._quota_lock:

            usage = self._load_daily_usage()

            if usage.get("date") != today:
                usage = {
                    "date": today,
                    "count": 0
                }

            current_count = int(usage.get("count", 0))

            if current_count >= self.daily_request_limit:
                return (
                    False,
                    0,
                    self.daily_request_limit,
                    today
                )

            usage["count"] = current_count + 1

            self._save_daily_usage(usage)

            remaining = self.daily_request_limit - usage["count"]

            return (
                True,
                remaining,
                self.daily_request_limit,
                today
            )

    def generate(
        self,
        system_prompt,
        user_prompt,
        max_tokens=512,
        temperature=0.3
    ):

        try:

            (
                allowed,
                _remaining,
                total_limit,
                usage_date
            ) = self._consume_daily_quota()

            if not allowed:
                return (
                    "RateLimitError: "
                    f"Daily LLM quota reached for {usage_date}. "
                    f"Limit is {total_limit} requests."
                )

            response = self.client.chat.completions.create(

                model=self.model_name,

                messages=[

                    {
                        "role": "system",
                        "content": system_prompt
                    },

                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],

                max_tokens=max_tokens,
                temperature=temperature
            )

            if hasattr(response, "usage") and response.usage:
                self.last_usage = {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0)
                }
            else:
                self.last_usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }

            return response.choices[0].message.content

        except Exception as e:

            return f"Generation Error: {str(e)}"