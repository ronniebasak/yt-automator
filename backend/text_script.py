from groq import Groq
from dotenv import load_dotenv
import os
import json


load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

with open('prompt.json', 'r') as f:
    prompts = json.load(f)

client = Groq(api_key=api_key)
completion = client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[{
        "role": "system",
        "content": prompts["SCRIPT_GENERATION_PROMPT"]
    },
      {
        "role": "user",
        "content": """ Nithin Kamath invests in company whose CEO helped Zerodha in early days: ‘Life comes full circle’
Zerodha's Nithin Kamath shared memories of early support from Deepak Shenoy as he announced an investment in Shenoy's Capitalmind Financial Services.

By Sanya Jain

2 min. readView original
Updated on: Aug 07, 2025 11:23 am IST

Zerodha's Nithin Kamath shared memories of early support from Deepak Shenoy as he announced an investment in Shenoy's Capitalmind Financial Services.
Nithin Kamath’s Zerodha has invested in Capitalmind Financial Services, a SEBI registered portfolio management service led by Deepak Shenoy. The investment was made through Rainmatter, which is Zerodha’s long‑term investment initiative.

Zerodha CEO Nithin Kamath (L) with Deepak Shenoy (C)(X/@Nithin0dha)
Zerodha CEO Nithin Kamath (L) with Deepak Shenoy (C)(X/@Nithin0dha)
In a post shared on social media, Nithin Kamath reflected on how life sometimes comes a full circle as he revealed that Deepak Shenoy was one of the first people to lend his name and credibility to Zerodha.

Compare flights & save up to 30% on your next trip Book Now

Life comes a full circle for Nithin Kamath
“It is sometimes surreal how life comes full circle,” wrote the CEO of Zerodha on X. “Deepak Shenoy was among the first people I spoke to about the idea of Zerodha. When we started, he agreed to lend his credibility by having his name on our website as an advisor,” he revealed.

Kamath announced that he was happy to back Shenoy’s Capitalmind with an investment through Rainmatter.

According to a Moneycontrol report, Capitalmind recently received a mutual fund license. This investment from Rainmatter is its first external institutional funding.

Early days of Zerodha
Zerodha was founded in August 2010 by brothers Nithin and Nikhil Kamath. It began as a bootstrapped startup with the aim of democratising stock trading in India by reducing costs and improving transparency.

The rest, as they say, is history.

Zerodha is today widely recognised as India's largest stockbroker and has turned the Kamath brothers into billionaires. Responding to Nithin Kamath’s post, Bengaluru-based Deepak Shenoy reminisced about the early days of Zerodha.

“Many thanks Nithin! I can't even believe that at one time, I had credibility to give to Zerodha!” he wrote. “I remember carrying the early Zerodha forms in my Hyundai Accent in Gurgaon - telling people how much brokerage they would save”.

“We have been in discussion regarding the businesses for a long time and have known each other for years now. Rainmatter’s investment philosophy has been non-interfering and there is a lot of synergy with Zerodha. We have spoken with Zerodha Fund House as well,” Shenoy told Moneycontrol.

News / Trending / Nithin Kamath invests in company whose CEO helped Zerodha in early days: ‘Life comes full circle’

See Less """
      }
    ],
    temperature=1,
    max_completion_tokens=1024,
    top_p=1,
    stream=True,
    stop=None
)

for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="")
